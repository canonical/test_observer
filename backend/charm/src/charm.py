#!/usr/bin/env python3

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import Layer
from requests import request

from charms.data_platform_libs.v0.data_interfaces import (
    DatabaseCreatedEvent,
    DatabaseEndpointsChangedEvent,
    DatabaseRequires,
    RelationJoinedEvent,
    RelationChangedEvent,
)

from charms.traefik_k8s.v1.ingress import (
    IngressPerAppRequirer,
)

# from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route

import logging

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class TestObserverBackendCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer-api"
        self.container = self.unit.get_container("api")

        self.framework.observe(self.on.api_pebble_ready, self._on_api_pebble_ready)
        self.framework.observe(self.on.config_changed, self._update_layer_and_restart)

        self.database = DatabaseRequires(
            self, relation_name="database", database_name="test_observer_db"
        )
        self.framework.observe(
            self.database.on.database_created, self._on_database_changed
        )
        self.framework.observe(
            self.database.on.endpoints_changed, self._on_database_changed
        )
        self.framework.observe(
            self.database.on.database_relation_broken, self._on_database_relation_broken
        )

        self.framework.observe(
            self.on.test_observer_rest_api_v1_relation_joined,
            self._test_observer_rest_api_client_joined,
        )
        self.framework.observe(
            self.on.test_observer_rest_api_v1_relation_changed,
            self._test_observer_rest_api_client_changed,
        )

        self.ingress = IngressPerAppRequirer(
            self, host=self.config["hostname"], port=self.config["port"]
        )
        self.framework.observe(self.on.migrate_database_action, self._migrate_database)

    def _migrate_database(self, event):
        process = self.container.exec(
            ["alembic", "upgrade", "head"], working_dir="./backend", timeout=None
        )
        stdout, stderr = process.wait_output()

        for line in stdout.splitlines():
            logger.info(line.strip())

        if stderr:
            for line in stderr.splitlines():
                logger.error(line.strip())

    def _on_config_changed(self, event):
        logger.info(event)
        self.unit.status = MaintenanceStatus(
            "Updating layer and restarting after config change"
        )
        self._update_layer_and_restart(None)
        self.unit.status = ActiveStatus()

    def _on_database_changed(
        self,
        event: DatabaseCreatedEvent | DatabaseEndpointsChangedEvent,
    ):
        logger.info("Database changed event: %s", event)
        self._update_layer_and_restart(None)

    def _on_database_relation_broken(self, event):
        self.unit.status = WaitingStatus("Waiting for database relation")
        raise SystemExit(0)

    def _update_layer_and_restart(self, event):
        self.unit.status = MaintenanceStatus(
            f"Updating {self.pebble_service_name} layer"
        )

        if self.container.can_connect():
            self.container.add_layer(
                self.pebble_service_name, self._pebble_layer, combine=True
            )
            self.container.restart(self.pebble_service_name)
            # self.unit.set_workload_version(self.version)
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API")

    def _postgres_relation_data(self) -> dict:
        data = self.database.fetch_relation_data()
        logger.debug("Got following database relation data: %s", data)
        for key, val in data.items():
            if not val:
                continue
            logger.info("New PSQL database endpoint is %s", val["endpoints"])
            host, port = val["endpoints"].split(":")
            db_url = f"postgresql+pg8000://{val['username']}:{val['password']}@{host}:{port}/test_observer_db"
            return {"DB_URL": db_url}

        self.unit.status = WaitingStatus("Waiting for database relation")
        raise SystemExit(0)

    def _test_observer_rest_api_client_joined(self, event: RelationJoinedEvent) -> None:
        logger.info(f"Test Observer REST API client joined {event}")

    def _test_observer_rest_api_client_changed(
        self, event: RelationChangedEvent
    ) -> None:
        if self.unit.is_leader():
            logger.debug(
                f"Setting hostname in data bag for {self.app}: {self.config['hostname']}"
            )
            event.relation.data[self.app].update(
                {"hostname": self.config["hostname"], "port": str(self.config["port"])}
            )

    @property
    def version(self) -> str | None:
        if self.container.can_connect() and self.container.get_services(
            self.pebble_service_name
        ):
            try:
                return request(
                    "GET", f"http://localhost:{self.config['port']}/version"
                ).json()["version"]
            except Exception as e:
                logger.warning(f"Failed to get version: {e}")
                logger.exception(e)
        return None

    @property
    def _pebble_layer(self) -> Layer:
        return Layer(
            {
                "summary": "test observer",
                "description": "pebble config layer for Test Observer",
                "services": {
                    self.pebble_service_name: {
                        "override": "replace",
                        "summary": "test observer API server",
                        "command": " ".join(
                            [
                                "uvicorn",
                                "src.main:app",
                                "--host",
                                "0.0.0.0",
                                f"--port={self.config['port']}",
                            ]
                        ),
                        "startup": "enabled",
                        "environment": {**self._postgres_relation_data(), **{}},
                    }
                },
            }
        )

    def _on_api_pebble_ready(self, event):
        container = event.workload
        container.add_layer("test-observer-api", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    main(TestObserverBackendCharm)

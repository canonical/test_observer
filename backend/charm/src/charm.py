#!/usr/bin/env python3

import logging

from charms.data_platform_libs.v0.data_interfaces import DatabaseRequires
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from faults import UnitReadinessFault
from ops import RelationChangedEvent, RelationJoinedEvent
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError, Layer
from requests import get

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class TestObserverBackendCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer-api"
        self.container = self.unit.get_container("api")

        self.framework.observe(self.on.api_pebble_ready, self._update_layer_and_restart)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

        self.database = DatabaseRequires(
            self, relation_name="database", database_name="test_observer_db"
        )
        self.framework.observe(self.database.on.database_created, self._on_database_changed)
        self.framework.observe(self.database.on.endpoints_changed, self._on_database_changed)
        self.framework.observe(
            self.on.database_relation_broken,
            self._on_database_relation_broken,
        )

        self.framework.observe(
            self.on.test_observer_rest_api_relation_joined,
            self._test_observer_rest_api_client_joined,
        )
        self.framework.observe(
            self.on.test_observer_rest_api_relation_changed,
            self._test_observer_rest_api_client_changed,
        )

        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)

        self._setup_nginx()

    def _setup_nginx(self):
        require_nginx_route(
            charm=self,
            service_hostname=self.config["hostname"],
            service_name=self.app.name,
            service_port=int(self.config["port"]),
        )

    def _on_upgrade_charm(self, event):
        self._attempt_database_migration()

    def _attempt_database_migration(self) -> bool | UnitReadinessFault:
        """Return true if migrations were attempted, false if not attempted (if unit is not the leader).

        If unit is not ready for migrations, return UnitReadinessFault.
        """
        if not self.unit.is_leader():
            return False

        if not self.container.can_connect():
            return UnitReadinessFault("Waiting for Pebble for API")

        pg_data = self._postgres_relation_data()

        if isinstance(pg_data, UnitReadinessFault):
            return pg_data

        self.unit.status = MaintenanceStatus("Migrating database")

        process = self.container.exec(
            ["alembic", "upgrade", "head"],
            working_dir="/home/app",
            environment=pg_data,
        )

        try:
            stdout, _ = process.wait_output()
            logger.info(stdout)
            self.unit.status = ActiveStatus()

            return True

        except ExecError as e:
            logger.error(e.stdout)
            logger.error(e.stderr)
            self.unit.status = BlockedStatus("Database migration failed")

        return True

    def _on_database_changed(self, event):
        if not self._attempt_database_migration():
            self.unit.status = WaitingStatus("Waiting for database relation")

        self._update_layer_and_restart(None)

    def _on_database_relation_broken(self, event):
        self.unit.status = WaitingStatus("Waiting for database relation after breaking relation")
        raise SystemExit(0)

    def _on_config_changed(self, event):
        if self.unit.is_leader():
            for relation in self.model.relations["test-observer-rest-api"]:
                host = self.config["hostname"]
                port = str(self.config["port"])
                relation.data[self.app].update({"hostname": host, "port": port})

        self._update_layer_and_restart(event)

    def _update_layer_and_restart(self, event):
        self.unit.status = MaintenanceStatus(f"Updating {self.pebble_service_name} layer")

        if self.container.can_connect():
            layer = self._pebble_layer

            if isinstance(layer, UnitReadinessFault):
                self.unit.status = layer.__str__()
                return

            self.container.add_layer(self.pebble_service_name, layer, combine=True)
            self.container.restart(self.pebble_service_name)

            version = self.version
            if version:
                self.unit.set_workload_version(self.version)

            self.unit.status = ActiveStatus()

        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API")

    def _postgres_relation_data(self) -> dict | UnitReadinessFault:
        data = self.database.fetch_relation_data()
        logger.debug("Got following database relation data: %s", data)

        for key, val in data.items():
            if not val:
                continue
            logger.info("New PSQL database endpoint is %s", val["endpoints"])
            host, port = val["endpoints"].split(":")
            db_url = f"postgresql+pg8000://{val['username']}:{val['password']}@{host}:{port}/test_observer_db"
            return {"DB_URL": db_url}

        return UnitReadinessFault("No database relation data")

    @property
    def _app_environment(self) -> dict | UnitReadinessFault:
        """Environment variables needed by the application."""
        env = {"SENTRY_DSN": self.config["sentry_dsn"]}

        db_data = self._postgres_relation_data()

        if not isinstance(db_data, dict):
            return UnitReadinessFault("App environment not ready", parent=db_data)

        env.update(db_data)
        return env

    def _test_observer_rest_api_client_joined(self, event: RelationJoinedEvent) -> None:
        logger.info(f"Test Observer REST API client joined {event}")

    def _test_observer_rest_api_client_changed(self, event: RelationChangedEvent) -> None:
        if self.unit.is_leader():
            logger.debug(f"Setting hostname in data bag for {self.app}: {self.config['hostname']}")
            event.relation.data[self.app].update(
                {
                    "hostname": self.config["hostname"],
                    "port": str(self.config["port"]),
                }
            )

    @property
    def version(self) -> str | None:
        if self.container.can_connect() and self.container.get_services(self.pebble_service_name):
            # 0.0.0.0 instead of config['hostname'] intentional:
            # request made from pebble's container to api in the same unit (same pod).
            try:
                return get(f"http://0.0.0.0:{self.config['port']}/v1/version").json()["version"]
            except Exception as e:
                logger.warning(f"Failed to get version: {e}")
                logger.exception(e)
        return None

    @property
    def _pebble_layer(self) -> Layer | UnitReadinessFault:
        env = self._app_environment

        if isinstance(env, UnitReadinessFault):
            return UnitReadinessFault("Pebble layer not ready", parent=env)

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
                                "test_observer.main:app",
                                "--host",
                                "0.0.0.0",
                                f"--port={self.config['port']}",
                            ]
                        ),
                        "startup": "enabled",
                        "environment": env,
                    }
                },
                "checks": {
                    "online": {
                        "exec": {
                            "command": "curl --fail --silent --head http://0.0.0.0:8000/v1/version",
                        },
                        "timeout": "5s",
                        "period": "15s",
                        "override": "replace",
                    }
                },
            }
        )


if __name__ == "__main__":  # pragma: nocover
    main(TestObserverBackendCharm)

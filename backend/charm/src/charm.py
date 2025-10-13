#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging
import sys
from collections import ChainMap

from charms.data_platform_libs.v0.data_interfaces import (
    DatabaseRequires,
    RelationChangedEvent,
    RelationJoinedEvent,
)
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRequires
from ops import StoredState
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError, Layer
from requests import get

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class TestObserverBackendCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()
    on = RedisRelationCharmEvents()

    def __init__(self, *args):
        super().__init__(*args)
        self.api_pebble_service_name = "test-observer-api"
        self.api_container = self.unit.get_container("api")

        self.celery_pebble_service_name = "celery-worker"
        self.celery_container = self.unit.get_container("celery")

        self.framework.observe(self.on.api_pebble_ready, self._update_api_layer)
        self.framework.observe(self.on.celery_pebble_ready, self._update_celery_layer)
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

        self._setup_redis()

        self.framework.observe(self.on.delete_artefact_action, self._on_delete_artefact_action)
        self.framework.observe(self.on.add_user_action, self._on_add_user_action)
        self.framework.observe(self.on.change_assignee_action, self._on_change_assignee_action)
        self.framework.observe(
            self.on.promote_user_to_admin_action, self._on_promote_user_to_admin_action
        )

    def _setup_nginx(self):
        require_nginx_route(
            charm=self,
            service_hostname=self.config["hostname"],
            service_name=self.app.name,
            service_port=int(self.config["port"]),
        )

    def _setup_redis(self):
        self._stored.set_default(redis_relation={})
        self.redis = RedisRequires(self, self._stored)
        self.framework.observe(
            self.on.redis_relation_updated,
            self._on_config_changed,
        )

    def _on_upgrade_charm(self, event):
        self._migrate_database()

    def _migrate_database(self):
        # only leader runs database migrations
        if not self.unit.is_leader():
            raise SystemExit(0)

        if not self.api_container.can_connect():
            self.unit.status = WaitingStatus("Waiting for Pebble for API")
            raise SystemExit(0)

        self.unit.status = MaintenanceStatus("Migrating database")

        process = self.api_container.exec(
            ["alembic", "upgrade", "head"],
            working_dir="/home/app",
            environment=self._app_environment,
        )

        try:
            stdout, _ = process.wait_output()
            logger.info(stdout)
            self.unit.status = ActiveStatus()
        except ExecError as e:
            logger.error(e.stdout)
            logger.error(e.stderr)
            self.unit.status = BlockedStatus("Database migration failed")
            raise SystemExit(0)

    def _on_database_changed(self, event):
        if not self._validate_saml_config():
            self.unit.status = BlockedStatus(
                "SAML config incomplete: if any SAML setting is provided, "
                "all of saml_idp_metadata_url, saml_sp_cert, and saml_sp_key must be set"
            )
            return

        self._migrate_database()
        self._update_api_layer(None)
        self._update_celery_layer(None)

    def _on_database_relation_broken(self, event):
        self.unit.status = WaitingStatus("Waiting for database relation")
        raise SystemExit(0)

    def _validate_saml_config(self) -> bool:
        """Validate SAML configuration.

        If any SAML config is provided, all three must be provided.
        Returns True if config is valid, False otherwise.
        """
        saml_idp_metadata_url = self.config.get("saml_idp_metadata_url", "")
        saml_sp_cert = self.config.get("saml_sp_cert", "")
        saml_sp_key = self.config.get("saml_sp_key", "")

        # Check if any SAML config is provided
        has_any_saml = bool(saml_idp_metadata_url or saml_sp_cert or saml_sp_key)

        # If any is provided, all must be provided
        if has_any_saml:
            has_all_saml = bool(saml_idp_metadata_url and saml_sp_cert and saml_sp_key)
            return has_all_saml

        # If none are provided, that's valid
        return True

    def _on_config_changed(self, event):
        if not self._validate_saml_config():
            self.unit.status = BlockedStatus(
                "SAML config incomplete: if any SAML setting is provided, "
                "all of saml_idp_metadata_url, saml_sp_cert, and saml_sp_key must be set"
            )
            return

        if self.unit.is_leader():
            for relation in self.model.relations["test-observer-rest-api"]:
                host = self.config["hostname"]
                port = str(self.config["port"])
                relation.data[self.app].update({"hostname": host, "port": port})

        self._update_api_layer(event)
        self._update_celery_layer(event)

    def _update_api_layer(self, event):
        if not self._validate_saml_config():
            self.unit.status = BlockedStatus(
                "SAML config incomplete: if any SAML setting is provided, "
                "all of saml_idp_metadata_url, saml_sp_cert, and saml_sp_key must be set"
            )
            return

        self.unit.status = MaintenanceStatus(f"Updating {self.api_pebble_service_name} layer")

        if self.api_container.can_connect():
            self.api_container.add_layer(
                self.api_pebble_service_name, self._api_pebble_layer, combine=True
            )
            self.api_container.restart(self.api_pebble_service_name)
            version = self.version
            if version:
                self.unit.set_workload_version(self.version)
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API")

    def _update_celery_layer(self, _):
        if not self._validate_saml_config():
            self.unit.status = BlockedStatus(
                "SAML config incomplete: if any SAML setting is provided, "
                "all of saml_idp_metadata_url, saml_sp_cert, and saml_sp_key must be set"
            )
            return

        self.unit.status = MaintenanceStatus(f"Updating {self.celery_pebble_service_name} layer")

        if self.celery_container.can_connect():
            self.celery_container.add_layer(
                self.celery_pebble_service_name, self._celery_pebble_layer, combine=True
            )
            self.celery_container.replan()
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for Celery")

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

    @property
    def _app_environment(self):
        """This creates a dictionary of environment variables needed by the application."""
        env = {
            "SENTRY_DSN": self.config["sentry_dsn"],
            "CELERY_BROKER_URL": self._celery_broker_url,
            "SAML_SP_BASE_URL": f"https://{self.config['hostname']}",
            "FRONTEND_URL": f"https://{self.config['frontend_hostname']}",
            "SESSIONS_SECRET": self.config["sessions_secret"],
            "IGNORE_PERMISSIONS": self.config.get("ignore_permissions", ""),
        }
        # Only set SAML environment variables if IDP metadata URL is provided
        if self.config.get("saml_idp_metadata_url"):
            env["SAML_IDP_METADATA_URL"] = self.config["saml_idp_metadata_url"]
            env["SAML_SP_X509_CERT"] = self.config.get("saml_sp_cert", "")
            env["SAML_SP_KEY"] = self.config.get("saml_sp_key", "")
        env.update(self._postgres_relation_data())
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
        if self.api_container.can_connect() and self.api_container.get_services(
            self.api_pebble_service_name
        ):
            # 0.0.0.0 instead of config['hostname'] intentional:
            # request made from pebble's container to api in the same unit (same pod).
            try:
                return get(f"http://0.0.0.0:{self.config['port']}/v1/version").json()["version"]
            except Exception as e:
                logger.warning(f"Failed to get version: {e}")
                logger.exception(e)
        return None

    @property
    def _api_pebble_layer(self) -> Layer:
        return Layer(
            {
                "summary": "test observer",
                "description": "pebble config layer for Test Observer",
                "services": {
                    self.api_pebble_service_name: {
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
                        "environment": self._app_environment,
                    }
                },
            }
        )

    @property
    def _celery_pebble_layer(self) -> Layer:
        celery_command = "celery -A tasks.celery worker -c 1"
        if self.unit.is_leader():
            # Add celery beat to leader unit
            celery_command += " -B"

        return Layer(
            {
                "summary": "celery worker",
                "description": "pebble config layer for celery worker",
                "services": {
                    self.celery_pebble_service_name: {
                        "override": "replace",
                        "summary": "celery worker",
                        "command": celery_command,
                        "startup": "enabled",
                        "environment": self._app_environment,
                    }
                },
            }
        )

    @property
    def _celery_broker_url(self) -> str:
        redis_relation = self.model.get_relation("redis")
        if not redis_relation:
            self.unit.status = WaitingStatus("Waiting for redis relation")
            sys.exit()

        redis_units = (u for u in redis_relation.units if u.app is not self.app)
        redis_unit_databags = (redis_relation.data[ru] for ru in redis_units)
        redis_data = ChainMap(*redis_unit_databags)

        redis_host = redis_data.get("hostname")
        redis_port = redis_data.get("port")
        if redis_host is None or redis_port is None:
            self.unit.status = WaitingStatus("Waiting for redis relation data")
            sys.exit()

        return f"redis://{redis_host}:{redis_port}"

    def _on_delete_artefact_action(self, event) -> None:
        artefact_id = event.params["artefact-id"]
        process = self.api_container.exec(
            command=["python", "-m", "scripts.delete_artefact", str(artefact_id)],
            working_dir="/home/app",
            environment=self._app_environment,
        )
        try:
            process.wait_output()
            event.set_results({"result": "Deleted successfuly"})
        except ExecError as e:
            event.fail(e.stderr)

    def _on_add_user_action(self, event) -> None:
        launchpad_email = event.params["launchpad-email"]
        process = self.api_container.exec(
            command=["python", "-m", "scripts.add_user", launchpad_email],
            working_dir="/home/app",
            environment=self._app_environment,
        )
        try:
            process.wait_output()
            event.set_results({"result": "Added successfuly"})
        except ExecError as e:
            event.fail(e.stderr)

    def _on_change_assignee_action(self, event) -> None:
        artefact_id = event.params["artefact-id"]
        user_id = event.params["user-id"]
        process = self.api_container.exec(
            command=["python", "-m", "scripts.change_assignee", str(artefact_id), str(user_id)],
            working_dir="/home/app",
            environment=self._app_environment,
        )
        try:
            process.wait_output()
            event.set_results({"result": "Changed successfuly"})
        except ExecError as e:
            event.fail(e.stderr)

    def _on_promote_user_to_admin_action(self, event) -> None:
        email = event.params["email"]
        process = self.api_container.exec(
            command=["python", "-m", "scripts.promote_user_to_admin", email],
            working_dir="/home/app",
            environment=self._app_environment,
        )
        try:
            process.wait_output()
            event.set_results({"result": "Promoted successfuly"})
        except ExecError as e:
            event.fail(e.stderr)


if __name__ == "__main__":  # pragma: nocover
    main(TestObserverBackendCharm)

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
import time
from collections import ChainMap

from charms.data_platform_libs.v0.data_interfaces import DatabaseCreatedEvent, DatabaseEndpointsChangedEvent, DatabaseRequires
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRelationUpdatedEvent, RedisRequires
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer, IngressPerAppReadyEvent, IngressPerAppRevokedEvent

import ops
from ops import StoredState
from ops.charm import CharmBase, RelationChangedEvent, RelationCreatedEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError, Layer
from requests import get

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

DATABASE_NAME = "test_observer_db"
DATABASE_RELATION_NAME = "database"

# The container names must match the container names defined in charmcraft.yaml
PEBBLE_CONTAINER_NAME_API = "api"
PEBBLE_CONTAINER_NAME_CELERY = "celery"
PEBBLE_SERVICE_NAME_API = "test-observer-api"
PEBBLE_SERVICE_NAME_CELERY = "celery-worker"


class TestObserverBackendCharm(CharmBase):
    """Charm the service."""

    on = RedisRelationCharmEvents()

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)

        # self.framework.observe(self.on.api_pebble_ready, self._update_api_layer)
        # self.framework.observe(self.on.celery_pebble_ready, self._update_celery_layer)

        # Juju automatically generates a <container_name>_pebble_ready event for each container defined in charmcraft.yaml
        framework.observe(self.on.api_pebble_ready, self._on_api_pebble_ready)
        framework.observe(self.on.celery_pebble_ready, self._on_celery_pebble_ready)

        # The ops framework triggers a CollectStatusEvent at the end of each hook
        framework.observe(self.on.collect_unit_status, self._on_collect_unit_status)

        self.database = DatabaseRequires(
            charm=self, relation_name=DATABASE_RELATION_NAME, database_name=DATABASE_NAME
        )
        framework.observe(self.database.on.database_created, self._on_database_created)
        framework.observe(self.database.on.endpoints_changed, self._on_database_endpoints_changed)
        framework.observe(
            self.on.database_relation_broken,
            self._on_database_relation_broken,
        )

        self.redis = RedisRequires(charm=self, relation_name="redis")
        framework.observe(self.on.redis_relation_updated, self._on_redis_relation_updated)

        # Traefik will default to prefixing routes with <model-name>-<app-name>,
        # so we need to use strip_prefix=True to remove that and keep the API working with expected routes
        # Additionally, Traefik automatically uses the underlying K8s service name when no hostname is provided,
        # and providing a custom hostname requires more effort to support
        self.ingress = IngressPerAppRequirer(
            charm=self,
            port=int(self.config["port"]),
            strip_prefix=True,
        )
        framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

        # self.framework.observe(self.on.config_changed, self._on_config_changed)


        # self.framework.observe(
        #     self.on.test_observer_rest_api_relation_joined,
        #     self._test_observer_rest_api_client_joined,
        # )
        # self.framework.observe(
        #     self.on.test_observer_rest_api_relation_changed,
        #     self._test_observer_rest_api_client_changed,
        # )

        # self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)

        # self.framework.observe(self.on.delete_artefact_action, self._on_delete_artefact_action)
        # self.framework.observe(self.on.add_user_action, self._on_add_user_action)
        # self.framework.observe(self.on.change_assignee_action, self._on_change_assignee_action)
        # self.framework.observe(
        #     self.on.promote_user_to_admin_action, self._on_promote_user_to_admin_action
        # )

    def _on_api_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
        self._update_pebble_container(PEBBLE_CONTAINER_NAME_API, PEBBLE_SERVICE_NAME_API)

    def _on_celery_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
        self._update_pebble_container(PEBBLE_CONTAINER_NAME_CELERY, PEBBLE_SERVICE_NAME_CELERY)

    def _on_collect_unit_status(self, event: ops.CollectStatusEvent) -> None:
        """
        Set the unit status based on the current state.
        The ops framework triggers a CollectStatusEvent at the end of each hook
        """

        # The database relation is required to make any requests at all,
        # because test_observer/main.py includes the router,
        # which in turn includes additional routers that import models for database access
        if not self.model.get_relation(DATABASE_RELATION_NAME):
            event.add_status(ops.BlockedStatus("Missing database relation"))
            return

        if not self.model.get_relation("redis"):
            event.add_status(ops.BlockedStatus("Missing redis relation"))
            return
        
        if not self.model.get_relation("ingress"):
            event.add_status(ops.BlockedStatus("Missing ingress relation"))
            return
        
        # event.add_status(ops.ActiveStatus())

    def _on_database_created(self, event: DatabaseCreatedEvent) -> None:
        """Event triggered when a database was created for this application."""
        self._process_database_updated(event.relation.id)
    
    def _on_database_endpoints_changed(self, event: DatabaseEndpointsChangedEvent) -> None:
        """Event triggered when database endpoints changed for this application."""
        self._process_database_updated(event.relation.id)

    def _on_database_relation_broken(self, _: ops.RelationBrokenEvent):
        self.unit.status = BlockedStatus("Missing database relation")

    def _on_redis_relation_updated(self, _: RedisRelationUpdatedEvent) -> None:
        """Event triggered when the redis relation is updated."""
        redis_url = self.redis.url

        # Under some circumstances, it seems possible for the returned value of redis.url
        # to be return f"redis://None:None", apparently due to bad checks in the redis library
        if redis_url is None or "None" in redis_url:
            logger.info("Redis URL is not ready yet")
            return
        self._update_pebble_container(
            PEBBLE_CONTAINER_NAME_CELERY,
            PEBBLE_SERVICE_NAME_CELERY,
            environment={"CELERY_BROKER_URL": redis_url},
        )

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        self.unit.status = ActiveStatus(f"Ingress is available at {event.url}")

    def _on_ingress_revoked(self, _: IngressPerAppRevokedEvent) -> None:
        self.unit.status = BlockedStatus(f"Ingress revoked")

    def _update_pebble_container(self, pebble_container_name: str, pebble_service_name: str, environment: dict[str, str] | None = None) -> None:
        self.unit.status = MaintenanceStatus(f"Starting workload for {pebble_service_name}")

        layer = self._build_pebble_layer(pebble_service_name, environment=environment)
        container = self.unit.get_container(pebble_container_name)
        container.add_layer("base", layer, combine=True)
        container.replan()
        self._wait_for_pebble_container_ready(pebble_container_name)

        # TODO: Make test_observer/backend/controllers/application/version.py work,
        # so we can set the workload version properly.
        # if pebble_container_name == PEBBLE_CONTAINER_NAME_API:
        #     version = self._version()
        #     if version is not None:
        #         self.unit.set_workload_version(version)

        self.unit.status = ops.ActiveStatus()

    def _build_pebble_layer(self, pebble_service_name: str, environment: dict[str, str] | None = None) -> ops.pebble.Layer:
        if environment is None:
            environment = {}
        
        if pebble_service_name == PEBBLE_SERVICE_NAME_API:
            command = " ".join(
                [
                    "uvicorn",
                    "test_observer.main:app",
                    "--host",
                    "0.0.0.0",
                    f"--port={self.config['port']}",
                ]
            )
            
            service = {
                "override": "replace",
                "summary": "The Test Observer API service",
                "command": command,
                "startup": "enabled",
                "environment": environment,
            }

        elif pebble_service_name == PEBBLE_SERVICE_NAME_CELERY:
            command = "celery -A tasks.celery worker -c 1"
            if self.unit.is_leader():
                # Add celery beat to leader unit
                command += " -B"

            service = {
                "override": "replace",
                "summary": "The Celery worker service",
                "command": command,
                "startup": "enabled",
                "environment": environment,
            }
        
        else:
            logger.error(f"Unknown Pebble service name: {pebble_service_name}")
            service = {}

        # Make type checker happy
        service: ops.pebble.ServiceDict = service
        layer: ops.pebble.LayerDict = {
            "services": {
                pebble_service_name: service,
            }
        }
        return ops.pebble.Layer(layer)       

    def _wait_for_pebble_container_ready(self, pebble_container_name: str) -> None:
        """
        Wait for the workload to be ready to use.
        This function is based on what `charmcraft init --profile kubernetes` generates
        with Charmcraft v4.0.1.
        """

        for _ in range(3):
            if self._is_pebble_container_ready(pebble_container_name):
                return
            time.sleep(1)
        logger.error("The workload was not ready within the expected time")
        raise RuntimeError("Workload is not ready")

    def _is_pebble_container_ready(self, pebble_container_name: str) -> bool:
        """
        Check whether the workload is ready to use.
        This function is based on what `charmcraft init --profile kubernetes` generates
        with Charmcraft v4.0.1.
        """

        if pebble_container_name not in self.unit.containers:
            logger.info(f"The workload is not ready (container {pebble_container_name} not found)")
            return False

        container = self.unit.get_container(pebble_container_name)
        # We'll first check whether all Pebble services are running.
        for name, service_info in container.get_services().items():
            if not service_info.is_running():
                logger.info(f"The workload is not ready (service {name} is not running)")
                return False
        # The Pebble services are running, but the workload might not be ready to use.
        # So we'll check whether all Pebble 'ready' checks are passing.
        checks = container.get_checks(level=ops.pebble.CheckLevel.READY)
        for check_info in checks.values():
            if check_info.status != ops.pebble.CheckStatus.UP:
                return False
        return True

    # def _version(self) -> str | None:
    #     container = self.unit.get_container(PEBBLE_CONTAINER_NAME_API)
    #     if container.can_connect() and container.get_services(PEBBLE_SERVICE_NAME_API):
    #         # 0.0.0.0 instead of config['hostname'] intentional:
    #         # request made from pebble's container to api in the same unit (same pod).
    #         try:
    #             return get(f"http://0.0.0.0:{self.config['port']}/v1/version").json().get("version")
    #         except Exception as e:
    #             logger.warning(f"Failed to get version: {e}")
    #             logger.exception(e)
    #     return None

    def _process_database_updated(self, relation_id: int) -> None:
        logger.info("Processing database relation change")
        
        # if not self._validate_saml_config():
        #     self.unit.status = BlockedStatus(
        #         "SAML config incomplete: if any SAML setting is provided, "
        #         "all of saml_idp_metadata_url, saml_sp_cert, and saml_sp_key must be set"
        #     )
        #     return

        db_url = self._db_url(relation_id)
        if db_url is None:
            logger.info("Database URL is not ready yet")
            return

        self._migrate_database(db_url)
        self._update_pebble_container(
            PEBBLE_CONTAINER_NAME_API,
            PEBBLE_SERVICE_NAME_API,
            environment={"DB_URL": db_url},
        )

    #     self._update_api_layer(None)
    #     self._update_celery_layer(None)

    def _db_url(self, relation_id: int | None = None) -> str | None:
        """Construct the database URL from relation data."""

        if relation_id is None:
            return None
        
        data = self.database.fetch_relation_data().get(relation_id, {})
        database = data.get("database")
        username = data.get("username")
        password = data.get("password")
        endpoints = data.get("endpoints")
        
        # Make type checker happy with str()
        endpoints = str(endpoints)
        host, port = None, None
        if ":" in endpoints:
            host, port = endpoints.split(":")

        if None in [database, username, password, host, port]:
            logger.info(
                f"Database relation data is incomplete. "
                f"Relation data:\n{data}"
            )
            return None

        db_url = (
            f"postgresql+pg8000://{username}:{password}"
            f"@{host}:{port}/{DATABASE_NAME}"
        )
        logger.debug(f"DB_URL: {db_url}")
        return db_url

    def _migrate_database(self, db_url: str) -> None:
        # only leader runs database migrations
        if not self.unit.is_leader():
            raise SystemExit(0)
    
        container = self.unit.get_container(PEBBLE_CONTAINER_NAME_API)
        if not container.can_connect():
            self.unit.status = WaitingStatus("Waiting for Pebble for API")
            raise SystemExit(0)

        self.unit.status = MaintenanceStatus("Migrating database")

        # The database connection checks the "DB_URL" environment variable
        # See test_observer/backend/test_observer/data_access/setup.py
        process = container.exec(
            ["alembic", "upgrade", "head"],
            working_dir="/home/app",
            environment={"DB_URL": db_url},
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

    # def _api_pebble_layer(self, environment: dict[str, str] | None = None) -> Layer:
    #     logger.info(f"Creating Pebble layer for {self.api_pebble_service_name}")
    #     if environment is None:
    #         environment = dict()

    #     return Layer(
    #         {
    #             "summary": "test observer",
    #             "description": "pebble config layer for Test Observer",
    #             "services": {
    #                 self.api_pebble_service_name: {
    #                     "override": "replace",
    #                     "summary": "test observer API server",
    #                     "command": " ".join(
    #                         [
    #                             "uvicorn",
    #                             "test_observer.main:app",
    #                             "--host",
    #                             "0.0.0.0",
    #                             f"--port={self.config['port']}",
    #                         ]
    #                     ),
    #                     "startup": "enabled",
    #                     "environment": environment,
    #                 }
    #             },
    #         }
    #     )

    def _environment(self) -> dict[str, str]:
        """This creates a dictionary of environment variables needed by the application."""
        return dict()
        # env = dict()
        # if 
        
        # if sentry_dsn := self.config.get("sentry_dsn"):
        #     env["SENTRY_DSN"] = str(sentry_dsn)
        
        # saml_sp_base_url = ""
        # if hostname := self._hostname():
        #     saml_sp_base_url = f"https://{hostname}"

        # frontend_url = ""
        # if hostname_frontend := self._hostname_frontend():
        #     frontend_url = f"https://{hostname_frontend}"

        # # See backend/test_observer/common/config.py and backend/tasks/celery.py
        # env = {
        #     "SENTRY_DSN": str(self.config["sentry_dsn"]),
        #     "CELERY_BROKER_URL": self._celery_broker_url,
        #     "SAML_SP_BASE_URL": saml_sp_base_url,
        #     "FRONTEND_URL": frontend_url,
        #     "SESSIONS_SECRET": str(self.config["sessions_secret"]),
        #     "IGNORE_PERMISSIONS": str(self.config.get("ignore_permissions", "")),
        # }
        # # Only set SAML environment variables if IDP metadata URL is provided
        # if self.config.get("saml_idp_metadata_url"):
        #     env["SAML_IDP_METADATA_URL"] = str(self.config["saml_idp_metadata_url"])
        #     env["SAML_SP_X509_CERT"] = str(self.config.get("saml_sp_cert", ""))
        #     env["SAML_SP_KEY"] = str(self.config.get("saml_sp_key", ""))
        # env.update(self._postgres_relation_data())
        # return env

    # def _celery_broker_url(self) -> str:
    #     url = self.config.get("celery_broker_url")
    #     if not url:
    #         if relation := self.model.get_relation("redis"):

    #     if not redis_relation:
    #         self.unit.status = WaitingStatus("Waiting for redis relation")
    #         sys.exit()

    #     redis_units = (u for u in redis_relation.units if u.app is not self.app)
    #     redis_unit_databags = (redis_relation.data[ru] for ru in redis_units)
    #     redis_data = ChainMap(*redis_unit_databags)

    #     redis_host = redis_data.get("hostname")
    #     redis_port = redis_data.get("port")
    #     if redis_host is None or redis_port is None:
    #         self.unit.status = WaitingStatus("Waiting for redis relation data")
    #         sys.exit()

    #     return f"redis://{redis_host}:{redis_port}"

    def _hostname(self) -> str | None:
        hostname = str(self.config.get("hostname"))
        if not hostname:
            hostname = self.app.name
        return hostname

    def _hostname_frontend(self) -> str | None:
        frontend = str(self.config.get("hostname_frontend"))
        if not frontend:
            if relation := self.model.get_relation("test-observer-rest-api"):
                frontend = relation.data[relation.app].get("hostname")
        return frontend

    def _on_upgrade_charm(self, event):
        self._migrate_database()

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

    def _on_config_changed(self, event: ops.ConfigChangedEvent):
        if not self._validate_saml_config():
            self.unit.status = BlockedStatus(
                "SAML config incomplete: if any SAML setting is provided, "
                "all of saml_idp_metadata_url, saml_sp_cert, and saml_sp_key must be set"
            )
            return

        if self.unit.is_leader():
            for relation in self.model.relations["test-observer-rest-api"]:
                port = str(self.config["port"])
                relation.data[self.app].update({"hostname": self._hostname, "port": port})

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
            version = self.version()
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

    def _postgres_relation_data(self) -> dict[str, str]:
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

    def _test_observer_rest_api_client_joined(self, event: RelationCreatedEvent) -> None:
        logger.info(f"Test Observer REST API client joined {event}")

    def _test_observer_rest_api_client_changed(self, event: RelationChangedEvent) -> None:
        if self.unit.is_leader():
            logger.debug(f"Setting hostname in data bag for {self.app}: {self._hostname}")
            event.relation.data[self.app].update(
                {
                    "port": str(self.config["port"]),
                }
            )

    # @property
    # def _celery_pebble_layer(self) -> Layer:
    #     celery_command = "celery -A tasks.celery worker -c 1"
    #     if self.unit.is_leader():
    #         # Add celery beat to leader unit
    #         celery_command += " -B"

    #     return Layer(
    #         {
    #             "summary": "celery worker",
    #             "description": "pebble config layer for celery worker",
    #             "services": {
    #                 self.celery_pebble_service_name: {
    #                     "override": "replace",
    #                     "summary": "celery worker",
    #                     "command": celery_command,
    #                     "startup": "enabled",
    #                     "environment": self._app_environment,
    #                 }
    #             },
    #         }
    #     )

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

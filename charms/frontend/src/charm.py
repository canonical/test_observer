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
#
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

"""Test Observer frontend charm."""

import logging
from typing import Optional, Tuple

import ops
import yaml
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from charms.traefik_k8s.v2.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    ConfigData,
    MaintenanceStatus,
    ModelError,
    WaitingStatus,
)
from ops.pebble import Layer

from nginx_config import html_503, nginx_503_config, nginx_config

logger = logging.getLogger(__name__)

INGRESS_RELATION_NAME = "ingress"
INGRESS_CONFLICT_MESSAGE = "Cannot have both ingress and nginx-route relations at the same time"


class TestObserverFrontendCharm(ops.CharmBase):
    """The frontend charm operates serving the frontend through nginx."""

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer-frontend"
        self.container = self.unit.get_container("frontend")

        self.framework.observe(self.on.frontend_pebble_ready, self._update_layer_and_restart)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(
            self.on.test_observer_rest_api_relation_joined,
            self._on_rest_api_relation_update,
        )
        self.framework.observe(
            self.on.test_observer_rest_api_relation_changed,
            self._on_rest_api_relation_update,
        )
        self.framework.observe(
            self.on.test_observer_rest_api_relation_broken,
            self._on_rest_api_relation_broken,
        )

        # Traefik will default to prefixing routes with <model-name>-<app-name>,
        # so we need to use strip_prefix=True to remove that and keep the API working with expected routes
        self.ingress = IngressPerAppRequirer(
            charm=self,
            relation_name=INGRESS_RELATION_NAME,
            port=int(self.config["port"]),
            strip_prefix=True,
        )
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

        self._setup_nginx()

        # The ops framework triggers a CollectStatusEvent at the end of each hook
        self.framework.observe(self.on.collect_unit_status, self._on_collect_unit_status)

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        """Process the ingress URL and provide the hostname where needed."""
        logger.info("Ingress is ready with url %s", event.url)
        self._update_backend_relation_data()

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        logger.info("Ingress revoked")
        self._update_backend_relation_data()

    def _setup_nginx(self):
        require_nginx_route(
            charm=self,
            service_hostname=self.config["hostname"],
            service_name=self.app.name,
            service_port=int(self.config["port"]),
        )

    def _on_config_changed(self, _):
        is_valid, reason = self._config_is_valid(self.config)

        if not is_valid:
            self.unit.status = BlockedStatus(reason)
            return

        self.ingress.provide_ingress_requirements(port=int(self.config["port"]))
        self._update_backend_relation_data()
        self._update_layer_and_restart()

    def _config_is_valid(self, config: ConfigData) -> Tuple[bool, Optional[str]]:
        """Validate the provided config."""
        if not isinstance(config["port"], int):
            return False, "port must be an integer"

        if int(config["port"]) < 1 or int(config["port"]) > 65535:
            return False, "port must be between 1 and 65535"

        if config["test-observer-api-scheme"] not in ["http://", "https://"]:
            return (
                False,
                "test-observer-api-scheme must be http:// or https://",
            )

        if config["hostname"] == "":
            return False, "hostname must be set"

        if not self._validate_frontend_config(str(config["frontend-config"])):
            return False, "frontend-config must be valid YAML with the correct structure"

        return True, None

    def _on_rest_api_relation_update(self, event):
        self._update_backend_relation_data()
        self._update_layer_and_restart()

    def _update_frontend_config(self):
        """Update the frontend configuration file from the charm config's frontend-config option."""
        frontend_config = str(self.config.get("frontend-config", ""))
        if not self._validate_frontend_config(frontend_config):
            logger.warning("frontend-config YAML is invalid. Skipping update.")
            return

        frontend_config = yaml.safe_load(frontend_config)
        self.container.push(
            "/usr/share/nginx/html/assets/assets/config.yaml",
            yaml.dump(frontend_config),
            make_dirs=True,
        )
        logger.info("Updated frontend config from charm config")

    def _validate_frontend_config(self, frontend_config: str) -> bool:
        # An empty string is considered valid, as it means the frontend will use the default configuration
        # from the frontend code itself (in the image, not the charm)
        if not frontend_config:
            return True

        try:
            config = yaml.safe_load(frontend_config)
        except yaml.YAMLError:
            return False

        if not isinstance(config, dict):
            return False
        if "require_authentication" in config and not isinstance(
            config["require_authentication"], bool
        ):
            return False
        if "tabs" in config and not isinstance(config["tabs"], list):
            return False

        return True

    def _update_header_image(self):
        try:
            image_path = self.model.resources.fetch("custom-header-image")
            with open(image_path, "rb") as f:
                self.container.push(
                    "/usr/share/nginx/html/assets/assets/logo.png",
                    f,
                    make_dirs=True,
                )
            logger.info("Updated header image from resource")
        except (ModelError, NameError):
            logger.info("No custom-header-image resource provided")
        except Exception as e:
            logger.warning(f"Failed to update header image: {e}")

    def _on_rest_api_relation_broken(self, event):
        logger.debug("REST API relation broken")
        self._handle_no_api_relation()

    def _update_layer_and_restart(self, _=None):
        self.unit.status = MaintenanceStatus(f"Updating {self.pebble_service_name} layer")

        if self.container.can_connect():
            self._update_frontend_config()
            self._update_header_image()
            api_url = self._api_url
            if api_url:
                self.container.push(
                    "/etc/nginx/sites-available/test-observer-frontend",
                    nginx_config(base_uri=api_url),
                    make_dirs=True,
                )
                self.container.add_layer(
                    self.pebble_service_name, self._pebble_layer, combine=True
                )
                # If only a file like the nginx config is updated, Pebble won't detect a change,
                # so replan won't trigger a restart, and the new config won't be applied.
                # As a result, we explicitly restart to ensure the new config is always applied.
                self.container.restart(self.pebble_service_name)
                self.unit.status = ActiveStatus()
            else:
                self._handle_no_api_relation()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API to set available state")

    @property
    def _api_url(self) -> str | None:
        api_relation = self.model.get_relation("test-observer-rest-api")

        if api_relation is None:
            self._handle_no_api_relation()
            return None

        relation_data = api_relation.data[api_relation.app]
        if not relation_data:
            self.unit.status = WaitingStatus("Waiting for test observer api relation data")
            return None

        # As of revision 351, the backend charm provides the URL directly in the relation data,
        # so if that is available, we prioritize it
        if "url" in relation_data:
            return relation_data["url"]

        hostname = relation_data["hostname"]
        port = relation_data["port"]

        scheme = self.config["test-observer-api-scheme"]

        logger.info(f"Hostname: {hostname} (from relation: {hostname})")
        logger.info(f"Port: {port} (from relation: {port})")

        if int(port) == 80 or int(port) == 443:
            base_uri = f"{scheme}{hostname}"
        else:
            base_uri = f"{scheme}{hostname}:{port}"
        return base_uri

    def _handle_no_api_relation(self):
        if self.container.can_connect():
            self.container.push(
                "/etc/nginx/sites-available/test-observer-frontend",
                nginx_503_config(),
                make_dirs=True,
            )
            self.container.push(
                "/usr/share/nginx/html/503.html",
                html_503(),
                make_dirs=True,
            )
            self.container.add_layer(self.pebble_service_name, self._pebble_layer, combine=True)
            self.container.restart(self.pebble_service_name)
            self.unit.status = MaintenanceStatus("test-observer-rest-api relation not connected.")
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API to set maintenance state")

    @property
    def _pebble_layer(self):
        """Return a dictionary representing a Pebble layer."""
        return Layer(
            {
                "summary": "nginx",
                "description": "nginx serving the frontend app",
                "services": {
                    self.pebble_service_name: {
                        "override": "replace",
                        "summary": "nginx",
                        "command": "nginx -g 'daemon off;'",
                        "startup": "enabled",
                    }
                },
            }
        )

    # TODO: This really needs to handle all possible states
    # and should act as a state-reconciliation function.
    # For now though, we only use it to handle ingress-related conflicts
    def _on_collect_unit_status(self, event: ops.CollectStatusEvent) -> None:
        """Set the unit status based on the current state.

        For example, this can be used to block the charm if config values are missing or invalid,
        or if there are conflicting relations.
        The ops framework triggers a CollectStatusEvent at the end of each hook.
        """
        has_ingress_conflict = self.model.get_relation("ingress") and self.model.get_relation(
            "nginx-route"
        )
        if has_ingress_conflict:
            event.add_status(BlockedStatus(INGRESS_CONFLICT_MESSAGE))
            return

        # For now, we don't want this function to overwrite any status other than BlockedStatus related to ingress conflicts
        if self.unit.status == BlockedStatus(INGRESS_CONFLICT_MESSAGE):
            # If the conflict is resolved, we can set the status to active again
            if not has_ingress_conflict:
                event.add_status(ActiveStatus())
            return

    def _get_url(self) -> str:
        """Get the URL to use for this charm's service."""
        # If the ingress relation is present and provides a URL,
        # that is the authoritative URL, so we use that instead
        if self.model.get_relation(INGRESS_RELATION_NAME) and self.ingress.url is not None:
            return self.ingress.url.rstrip("/")

        # For compatibility with older charm revisions and deployments,
        # we default to HTTPS with the hostname
        port = int(self.config["port"])
        url = f"https://{self.config['hostname']}".rstrip("/")
        if port not in {80, 443}:
            url = f"{url}:{port}"
        return url

    def _update_backend_relation_data(self):
        if not self.unit.is_leader():
            return

        url = self._get_url()
        # Prior to revision 242, this charm provided no relation data. Subsequent revisions provide the URL.
        data = {"url": url}
        logger.debug("Updating data bag for %s with\n: %s", self.app, data)
        for relation in self.model.relations["test-observer-rest-api"]:
            bag = relation.data[self.app]
            if any(bag.get(k) != v for k, v in data.items()):
                bag.update(data)


if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverFrontendCharm)

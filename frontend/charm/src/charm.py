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

import json
import logging
import re
from typing import Optional, Tuple

import ops
import yaml
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer, IngressPerAppReadyEvent, IngressPerAppRevokedEvent

from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    ModelError,
    WaitingStatus,
)
from ops.pebble import Layer

from nginx_config import html_503, nginx_503_config, nginx_config

logger = logging.getLogger(__name__)

INGRESS_RELATION_NAME = "ingress"


class TestObserverFrontendCharm(ops.CharmBase):
    """The frontend charm operates serving the frontend through nginx."""

    def __init__(self, *args):
        super().__init__(*args)

        # The ops framework triggers a CollectStatusEvent at the end of each hook
        self.framework.observe(self.on.collect_unit_status, self._on_collect_unit_status)

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

        self._setup_nginx()

        # Traefik will default to prefixing routes with <model-name>-<app-name>,
        # so we need to use strip_prefix=True to remove that and keep the frontend working with expected routes
        self.ingress = IngressPerAppRequirer(
            charm=self,
            relation_name=INGRESS_RELATION_NAME,
            port=int(self.config["port"]),
            strip_prefix=True,
        )
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

    def _on_collect_unit_status(self, event: ops.CollectStatusEvent) -> None:
        """
        Set the unit status based on the current state.
        For example, this can be used to block the charm if config values are missing or invalid,
        or if there are conflicting relations.
        The ops framework triggers a CollectStatusEvent at the end of each hook.
        """
        if not self.model.get_relation("test-observer-rest-api"):
            event.add_status(BlockedStatus("Missing test-observer-rest-api relation"))
            return

        if self.model.get_relation("ingress") and self.model.get_relation("nginx-route"):
            event.add_status(BlockedStatus("Cannot have both ingress and nginx-route relations at the same time"))
            return

        event.add_status(ActiveStatus())

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        """
        Process the ingress URL and provide the hostname where needed.
        """
        logger.info("Ingress is ready with url %s", event.url)
        self._update_backend_relation_data()

    def _on_ingress_revoked(self, _: IngressPerAppRevokedEvent) -> None:
        logger.info("Ingress revoked")

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

        self._update_layer_and_restart()

    def _config_is_valid(self, config) -> Tuple[bool, Optional[str]]:
        """Validate the provided config."""
        if config["port"] < 1 or config["port"] > 65535:
            return False, "port must be between 1 and 65535"

        if config["test-observer-api-scheme"] not in ["http://", "https://"]:
            return (
                False,
                "test-observer-api-scheme must be http:// or https://",
            )

        if config["hostname"] == "":
            return False, "hostname must be set"

        return True, None

    def _on_rest_api_relation_update(self, event):
        if self.unit.is_leader():
            self._update_backend_relation_data()
        self._update_layer_and_restart()

    def _update_frontend_config(self):
        config_str = self.config.get("frontend-config", "")
        if not config_str:
            logger.info("No frontend-config provided, using defaults")
            return

        try:
            config = yaml.safe_load(config_str)
        except yaml.YAMLError:
            logger.warning("frontend-config contains invalid YAML")
            return

        if not isinstance(config, dict):
            logger.warning("frontend-config must be a YAML mapping")
            return

        self.container.push(
            "/usr/share/nginx/html/assets/assets/config.yaml",
            yaml.dump(config),
            make_dirs=True,
        )
        logger.info("Updated frontend config from charm config")

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

    def _update_layer_and_restart(self, _ = None):
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
                # If only the nginx config was updated, Pebble won't detect a change,
                # so the service won't be restarted and the new config won't be applied.
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

        url = relation_data.get("url")
        if not url:
            self.unit.status = WaitingStatus("Waiting for test observer api relation url")
            return None
        return url

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

    def _get_url(self) -> str:
        """
        Get the URL to use for the API/backend service.
        For backwards compatibility with legacy deployments
        using old versions of the nginx-ingress-integrator charm,
        we default to the charm config value.

        If the ingress relation is present,
        we pull the URL from the relation data instead.
        """
        # Hardcoding HTTPS here is not ideal, but it will work for now
        url = f"https://{self.config['hostname']}"
        if int(self.config["port"]) not in (80, 443):
            url = f"{url}:{self.config['port']}"
        if relation := self.model.get_relation(INGRESS_RELATION_NAME):
            # This should be a JSON string containing a "url" key and value
            ingress_data = relation.data[relation.app].get(INGRESS_RELATION_NAME)
            if ingress_data:
                try:
                    json_ = json.loads(ingress_data)
                    url = json_.get("url", url)
                except json.JSONDecodeError:
                    logger.error("Failed to decode ingress relation data as JSON: %s", ingress_data)
                except Exception as e:
                    logger.error("Unexpected error while parsing ingress relation data: %s", e)
        return url

    def _get_backend_url(self) -> str:
        """
        Get the backend URL from the relation data.
        """
        url = ""
        if relation := self.model.get_relation("test-observer-rest-api"):
            url = relation.data[relation.app].get("url", url)
        logger.debug("%s found the backend URL %s", self.app.name, url)
        return url

    def _update_backend_relation_data(self) -> None:
        """
        Update the relation data for the backend relation with the current hostname and port.
        This provides the API/backend data so it's available to the frontend.
        """
        data = {"url": self._get_url()}
        logger.debug("Updating data bag for %s with\n: %s", self.app, data)

        for relation in self.model.relations["test-observer-rest-api"]:
            relation.data[self.app].update(data)

if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverFrontendCharm)

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


"""Test Observer frontend charm."""

import logging
from typing import Optional, Tuple

import ops
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    WaitingStatus,
)
from ops.pebble import Layer

from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer, IngressPerAppReadyEvent, IngressPerAppRevokedEvent
from nginx_config import html_503, nginx_503_config, nginx_config

logger = logging.getLogger(__name__)


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

        self.ingress = IngressPerAppRequirer(
            charm=self,
            port=int(self.config["port"]),
            strip_prefix=True,
        )
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

    def _on_config_changed(self, event):
        is_valid, reason = self._config_is_valid(self.config)

        if not is_valid:
            self.unit.status = BlockedStatus(reason)
            return

        self._update_layer_and_restart(event)

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

    def _on_rest_api_relation_update(self, event: ops.RelationChangedEvent):
        api_hostname = event.relation.data[event.app].get("hostname")
        api_port = event.relation.data[event.app].get("port")
        logger.debug(f"API hostname: {api_hostname}, port: {api_port} (app: {event.app})")
        self._update_layer_and_restart(event)

    def _on_rest_api_relation_broken(self, event):
        logger.debug("REST API relation broken")
        self._handle_no_api_relation()

    def _update_layer_and_restart(self, event):
        self.unit.status = MaintenanceStatus(f"Updating {self.pebble_service_name} layer")

        if self.container.can_connect():
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
                self.container.replan()
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

        hostname = api_relation.data[api_relation.app]
        port = relation_data["port"]

        scheme = self.config["test-observer-api-scheme"]

        logger.info(f"Hostname: {hostname}")
        logger.info(f"Port: {port}")

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

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        self.unit.status = ActiveStatus(f"Ingress is available at {event.url}")

    def _on_ingress_revoked(self, _: IngressPerAppRevokedEvent) -> None:
        self.unit.status = BlockedStatus(f"Ingress removed")


if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverFrontendCharm)

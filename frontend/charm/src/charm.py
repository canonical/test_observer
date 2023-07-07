#!/usr/bin/env python3
# Copyright 2023 Matias Piipari
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Test Observer frontend charm."""

import logging
from typing import Tuple

import ops
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from ops.framework import StoredState
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    WaitingStatus,
)
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class TestObserverFrontendCharm(ops.CharmBase):
    """The frontend charm operates serving the frontend through nginx."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer-frontend"
        self.container = self.unit.get_container("frontend")

        self.framework.observe(self.on.frontend_pebble_ready, self._on_frontend_pebble_ready)
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

        self._stored.set_default(backend_hostname=None, backend_port=None)

        self._setup_ingress()

    def _setup_ingress(self):
        require_nginx_route(
            charm=self,
            service_hostname=self.config["hostname"],
            service_name=self.app.name,
            service_port=int(self.config["port"]),
        )

    def _on_frontend_pebble_ready(self, event: ops.PebbleReadyEvent):
        container = event.workload
        container.add_layer("frontend", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ops.ActiveStatus()

    def _on_config_changed(self, event):
        is_valid, reason = self._config_is_valid(self.config)

        if not is_valid:
            self.unit.status = BlockedStatus(reason)
            return

        self._update_layer_and_restart(event)

    def _config_is_valid(self, config) -> Tuple[bool, str]:
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
        api_hostname = event.relation.data[event.app].get("hostname")
        api_port = event.relation.data[event.app].get("port")
        logger.debug(f"API hostname: {api_hostname} (app: {event.app})")

        if self.unit.is_leader():
            self._stored.backend_hostname = api_hostname
            self._stored.backend_port = api_port

        self._update_layer_and_restart(event)

    def _on_rest_api_relation_broken(self, event):
        logger.debug("REST API relation broken -> removing backend hostname")

        if self.unit.is_leader():
            self._stored.backend_hostname = None
            self._stored.backend_port = None

    def nginx_config(self, base_uri: str) -> str:
        """Return a config where the backend port `base_uri` is adjusted."""
        return f"""
        server {{
            listen       80;
            server_name  localhost;

            location / {{
                root   /usr/share/nginx/html;
                index  index.html index.htm;
                try_files $uri $uri/ /index.html =404;

                sub_filter 'http://api-placeholder:30000/' '{base_uri}';
                sub_filter_once on;
            }}

            error_page   500 502 503 504  /50x.html;
            location = /50x.html {{
                root   /usr/share/nginx/html;
            }}
        }}
        """

    def _update_layer_and_restart(self, event):
        self.unit.status = MaintenanceStatus(f"Updating {self.pebble_service_name} layer")

        scheme = self.config["test-observer-api-scheme"]
        hostname = self._stored.backend_hostname
        port = self._stored.backend_port

        if int(port) == 80 or int(port) == 443:
            base_uri = f"{scheme}{hostname}"
        else:
            base_uri = f"{scheme}{hostname}:{port}"

        self.container.push(
            "/etc/nginx/sites-available/test-observer-frontend",
            self.nginx_config(base_uri=base_uri),
            make_dirs=True,
        )

        if self.container.can_connect():
            self.container.add_layer(self.pebble_service_name, self._pebble_layer, combine=True)
            self.container.restart(self.pebble_service_name)
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API")

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


if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverFrontendCharm)

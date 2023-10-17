#!/usr/bin/env python3
# Copyright 2023 Matias Piipari
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Test Observer frontend charm."""

import logging
import sys
from typing import Tuple

import ops
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
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

        self._setup_ingress()

    def _setup_ingress(self):
        require_nginx_route(
            charm=self,
            service_hostname=self.config["hostname"],
            service_name=self.app.name,
            service_port=int(self.config["port"]),
        )

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
        logger.debug(f"API hostname: {api_hostname}, port: {api_port} (app: {event.app})")
        self._update_layer_and_restart(event)

    def _on_rest_api_relation_broken(self, event):
        logger.debug("REST API relation broken")
        self._handle_no_api_relation()

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

                # Ensure no caching
                expires -1;
                add_header Cache-Control "no-store, no-cache, must-revalidate, post-check=0, pre-check=0";

                sub_filter 'http://localhost:30000/' '{base_uri}';
                sub_filter_once on;
            }}

            error_page   500 502 503 504  /50x.html;
            location = /50x.html {{
                root   /usr/share/nginx/html;
            }}
        }}
        """

    def nginx_503_config(self) -> str:
        """Return a config for the situation when the backend is not yet available."""
        return """
        server {
            listen 80 default_server;
            server_name _;
            return 503;
            error_page 503 @maintenance;

            location @maintenance {
                rewrite ^(.*)$ /503.html break;
                root /usr/share/nginx/html;

                # Ensure no caching
                expires -1;
                add_header Cache-Control "no-store, no-cache, must-revalidate, post-check=0, pre-check=0";
            }
        }
        """

    def html_503(self) -> str:
        """Return a 503 response page."""
        return """
        <html>
            <head>
                <title>503 Service Unavailable</title>
            </head>
            <body>
                <h1>503 Service Unavailable</h1>
                <p>Backend not yet configured.</p>
            </body>
        </html>
        """

    def _update_layer_and_restart(self, event):
        self.unit.status = MaintenanceStatus(f"Updating {self.pebble_service_name} layer")

        if self.container.can_connect():
            self.container.push(
                "/etc/nginx/sites-available/test-observer-frontend",
                self.nginx_config(base_uri=self._api_url),
                make_dirs=True,
            )
            self.container.add_layer(self.pebble_service_name, self._pebble_layer, combine=True)
            self.container.replan()
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for Pebble for API to set available state")

    @property
    def _api_url(self):
        api_relation = self.model.get_relation("test-observer-rest-api")

        if api_relation is None:
            self._handle_no_api_relation()
            sys.exit()

        relation_data = api_relation.data[api_relation.app]
        if not relation_data:
            self.unit.status = WaitingStatus("Waiting for test observer api relation data")
            sys.exit()

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
                self.nginx_503_config(),
                make_dirs=True,
            )
            self.container.push(
                "/usr/share/nginx/html/503.html",
                self.html_503(),
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


if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverFrontendCharm)

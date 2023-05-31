#!/usr/bin/env python3
# Copyright 2023 Matias Piipari
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Test Observer frontend charm."""

import logging

import ops
from charms.traefik_k8s.v1.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)
from ops.framework import StoredState
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class TestObserverFrontendCharm(ops.CharmBase):
    """Test Observer frontend charm exists chiefly to modulate the nginx config for the served app."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer-frontend"
        self.container = self.unit.get_container("frontend")

        self.framework.observe(self.on.frontend_pebble_ready, self._on_frontend_pebble_ready)
        self.framework.observe(self.on.config_changed, self._update_layer_and_restart)
        self.framework.observe(
            self.on.test_observer_rest_api_relation_joined,
            self._test_observer_rest_api_relation_joined,
        )
        self.framework.observe(
            self.on.test_observer_rest_api_relation_broken,
            self._test_observer_rest_api_relation_broken,
        )

        self.ingress = IngressPerAppRequirer(self, port=self.config["port"])
        self.framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        self.framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)


        self._stored.set_default(backend_hostname=None)

    def _on_frontend_pebble_ready(self, event: ops.PebbleReadyEvent):
        container = event.workload
        container.add_layer("frontend", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ops.ActiveStatus()

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent):
        logger.info("Ingress ready: %s", event.url)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent):
        logger.info("App ingress revoked")

    def _test_observer_rest_api_relation_joined(self, event):
        api_hostname = event.relation.data[event.app].get("hostname")
        logger.debug(f"API hostname: {api_hostname} (app: {event.app})")

        if self.unit.is_leader():
            self._stored.backend_hostname = api_hostname

    def _test_observer_rest_api_relation_broken(self, event):
        logger.debug("REST API relation broken -> removing backend hostname")

        if self.unit.is_leader():
            self._stored.backend_hostname = None

    def nginx_config(self, base_uri: str) -> str:
        """Return an nginx config where the index.html served is replaced with the specified `base_uri`."""
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
        self.unit.status = MaintenanceStatus(
            f"Updating {self.pebble_service_name} layer"
        )

        scheme = self.config["test-observer-api-scheme"]
        hostname = self._stored.backend_hostname
        base_uri = f"{scheme}{hostname}"

        self.container.push(
            "/etc/nginx/conf.d/default.conf", self.nginx_config(base_uri=base_uri)
        )

        if self.container.can_connect():
            self.container.add_layer(
                self.pebble_service_name, self._pebble_layer, combine=True
            )
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

#!/usr/bin/env python3
# Copyright 2023 Matias Piipari
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging

import ops
from ops.pebble import Layer
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus

logger = logging.getLogger(__name__)

VALID_LOG_LEVELS = ["info", "debug", "warning", "error", "critical"]

class TestObserverFrontendCharm(ops.CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        self.pebble_service_name = "test-observer-frontend"
        self.container = self.unit.get_container("frontend")
        
        self.framework.observe(self.on.frontend_pebble_ready, self._on_frontend_pebble_ready)
        self.framework.observe(self.on.config_changed, self._update_layer_and_restart)
            
    def _on_frontend_pebble_ready(self, event: ops.PebbleReadyEvent):
        container = event.workload
        container.add_layer("frontend", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ops.ActiveStatus()

    def _update_layer_and_restart(self, event):
        self.unit.status = MaintenanceStatus(
            f"Updating {self.pebble_service_name} layer"
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
        return Layer({
            "summary": "nginx layer",
            "description": "pebble config layer for nginx",
            "services": {
                "nginx": {
                    "override": "replace",
                    "summary": "nginx",
                    "command": "nginx -g 'daemon off;'",
                    "startup": "enabled",
                    "environment": {
                        "TEST_OBSERVER_API_BASE_URI": self.config["test-observer-api-base-uri"],
                    },
                }
            },
        })


if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverFrontendCharm)

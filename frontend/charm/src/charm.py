#!/usr/bin/env python3
# Copyright 2023 Matias Piipari
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging

import ops
from ops.pebble import Layer

logger = logging.getLogger(__name__)

VALID_LOG_LEVELS = ["info", "debug", "warning", "error", "critical"]

class TestObserverFrontendCharm(ops.CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.test_observer_frontend_pebble_ready, self._on_frontend_pebble_ready)
        
    def _on_frontend_pebble_ready(self, event: ops.PebbleReadyEvent):
        container = event.workload
        container.add_layer("frontend", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ops.ActiveStatus()

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
                    "startup": "enabled"
                }
            },
        })


if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverFrontendCharm)

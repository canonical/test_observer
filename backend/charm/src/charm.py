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

"""This module contains the charmed Kubernetes operator for the Test Observer backend."""

import logging
import time

import ops

# A standalone module for workload-specific logic (no charming concerns):
import workload

logger = logging.getLogger(__name__)

BACKEND_CONTAINER_NAME = "api"
BACKEND_SERVICE_NAME = "test-observer-backend"


class TestObserverBackendCharm(ops.CharmBase):
    """This class implements a charmed operator for the Test Observer backend on Kubernetes."""

    __test__ = False  # Prevent pytest from trying to test this class.

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on[BACKEND_CONTAINER_NAME].pebble_ready, self._on_pebble_ready)
        self.container = self.unit.get_container(BACKEND_CONTAINER_NAME)

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Handle pebble-ready event."""
        self.unit.status = ops.MaintenanceStatus("starting workload")
        # To start the workload, we'll add a Pebble layer to the workload container.
        # The layer specifies which service to run.
        layer: ops.pebble.LayerDict = {
            "services": {
                BACKEND_SERVICE_NAME: {
                    "override": "replace",
                    "summary": "A service that runs in the workload container",
                    "command": "/bin/foo",  # Change this!
                    "startup": "enabled",
                }
            }
        }
        self.container.add_layer("base", layer, combine=True)
        # If the container image is a rock, the container already has a Pebble layer.
        # In this case, you could remove 'add_layer' or use 'add_layer' to extend the rock's layer.
        # To learn about rocks, see https://documentation.ubuntu.com/rockcraft/en/stable/
        self.container.replan()  # Starts the service (because 'startup' is enabled in the layer).
        self.wait_for_ready()
        version = workload.get_version()
        if version is not None:
            self.unit.set_workload_version(version)
        self.unit.status = ops.ActiveStatus()

    def is_ready(self) -> bool:
        """Check whether the workload is ready to use."""
        # We'll first check whether all Pebble services are running.
        for name, service_info in self.container.get_services().items():
            if not service_info.is_running():
                logger.info("the workload is not ready (service '%s' is not running)", name)
                return False
        # The Pebble services are running, but the workload might not be ready to use.
        # So we'll check whether all Pebble 'ready' checks are passing.
        checks = self.container.get_checks(level=ops.pebble.CheckLevel.READY)
        for check_info in checks.values():
            if check_info.status != ops.pebble.CheckStatus.UP:
                return False
        return True

    def wait_for_ready(self) -> None:
        """Wait for the workload to be ready to use."""
        for _ in range(3):
            if self.is_ready():
                return
            time.sleep(1)
        logger.error("the workload was not ready within the expected time")
        raise RuntimeError("workload is not ready")
        # The runtime error is for you (the charm author) to see, not for the user of the charm.
        # Make sure that this function waits long enough for the workload to be ready.


if __name__ == "__main__":  # pragma: nocover
    ops.main(TestObserverBackendCharm)

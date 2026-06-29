# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0
#
# To learn more about testing, see https://documentation.ubuntu.com/ops/latest/explanation/testing/

import ops
import pytest
from ops import testing

from charm import (
    BACKEND_CONTAINER_NAME,
    BACKEND_SERVICE_NAME,
    TestObserverBackendCharm,
)

CHECK_NAME = "service-ready"  # Name of Pebble check in the mock workload container.

# A minimal Pebble layer for our testing.Container objects.
# Our charm doesn't retrieve the service command or the check URL
# from Pebble, so this layer doesn't need a real command or URL.
MOCK_LAYER = ops.pebble.Layer(
    {
        "services": {
            BACKEND_SERVICE_NAME: {
                "override": "replace",
                "command": "mock-command",
                "startup": "enabled",
            }
        },
        "checks": {
            CHECK_NAME: {
                "override": "replace",
                "level": "ready",
                "threshold": 3,
                "startup": "enabled",
                "http": {
                    "url": "http://localhost:1234/mock-endpoint",
                },
            }
        },
    }
)


def mock_get_version():
    """Get a mock version string without executing the workload code."""
    return "1.0.0"


def test_pebble_ready(monkeypatch: pytest.MonkeyPatch):
    """Test that the charm has the correct state after handling the pebble-ready event."""
    # Arrange:
    ctx = testing.Context(TestObserverBackendCharm)
    check_in = testing.CheckInfo(
        CHECK_NAME,
        level=ops.pebble.CheckLevel.READY,
        status=ops.pebble.CheckStatus.UP,  # Simulate the Pebble check passing.
    )
    container_in = testing.Container(
        BACKEND_CONTAINER_NAME,
        can_connect=True,
        layers={"base": MOCK_LAYER},
        service_statuses={BACKEND_SERVICE_NAME: ops.pebble.ServiceStatus.INACTIVE},
        check_infos={check_in},
    )
    state_in = testing.State(containers={container_in})
    monkeypatch.setattr("charm.workload.get_version", mock_get_version)

    # Act:
    state_out = ctx.run(ctx.on.pebble_ready(container_in), state_in)

    # Assert:
    container_out = state_out.get_container(container_in.name)
    assert container_out.service_statuses[BACKEND_SERVICE_NAME] == ops.pebble.ServiceStatus.ACTIVE
    assert state_out.workload_version is not None
    assert state_out.unit_status == testing.ActiveStatus()


def test_pebble_ready_service_not_ready():
    """Test that the charm raises an error if the workload isn't ready after Pebble starts it."""
    # Arrange:
    ctx = testing.Context(TestObserverBackendCharm)
    check_in = testing.CheckInfo(
        CHECK_NAME,
        level=ops.pebble.CheckLevel.READY,
        status=ops.pebble.CheckStatus.DOWN,  # Simulate the Pebble check failing.
    )
    container_in = testing.Container(
        BACKEND_CONTAINER_NAME,
        can_connect=True,
        layers={"base": MOCK_LAYER},
        service_statuses={BACKEND_SERVICE_NAME: ops.pebble.ServiceStatus.INACTIVE},
        check_infos={check_in},
    )
    state_in = testing.State(containers={container_in})

    # Act & assert:
    with pytest.raises(testing.errors.UncaughtCharmError):
        ctx.run(ctx.on.pebble_ready(container_in), state_in)

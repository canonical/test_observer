import requests

from test_observer.controllers.test_execution.models import StartTestExecutionRequest

BASE_URL = "http://localhost:30000/v1"
START_TEST_EXECUTION_URL = f"{BASE_URL}/test-execution/start"

REQUESTS = [
    StartTestExecutionRequest(
        family="snap",
        name="core22",
        version="20230531",
        revision=1,
        source={"track": "22"},
        arch="armhf",
        execution_stage="beta",
        environment="rpi2",
    ),
    StartTestExecutionRequest(
        family="snap",
        name="docker",
        version="20.10.24",
        revision=1,
        source={"track": "latest"},
        arch="armhf",
        execution_stage="beta",
        environment="rpi2",
    ),
    StartTestExecutionRequest(
        family="snap",
        name="docker",
        version="20.10.24",
        revision=1,
        source={"track": "core18"},
        arch="armhf",
        execution_stage="beta",
        environment="rpi2",
    ),
    StartTestExecutionRequest(
        family="snap",
        name="bluez",
        version="5.64-2",
        revision=1,
        source={"track": "22"},
        arch="amd64",
        execution_stage="edge",
        environment="dawson-i",
    ),
    StartTestExecutionRequest(
        family="snap",
        name="core22",
        version="20230531",
        revision=1,
        source={"track": "22"},
        arch="arm64",
        execution_stage="candidate",
        environment="cm3",
    ),
    StartTestExecutionRequest(
        family="snap",
        name="checkbox22",
        version="2.6",
        revision=1,
        source={"track": "latest"},
        arch="arm64",
        execution_stage="stable",
        environment="cm3",
    ),
    StartTestExecutionRequest(
        family="snap",
        name="snapd",
        version="2.59.4",
        revision=1,
        source={"track": "latest"},
        arch="arm64",
        execution_stage="stable",
        environment="dragonboard",
    ),
    StartTestExecutionRequest(
        family="deb",
        name="linux-raspi",
        version="5.15.0.73.71",
        source={"series": "jammy", "repo": "main"},
        arch="arm64",
        execution_stage="proposed",
        environment="rpi400",
    ),
    StartTestExecutionRequest(
        family="deb",
        name="linux-raspi",
        version="5.15.0.73.70",
        source={"series": "jammy", "repo": "main"},
        arch="arm64",
        execution_stage="updates",
        environment="rpi400",
    ),
]


def seed_data():
    for request in REQUESTS:
        requests.put(START_TEST_EXECUTION_URL, json=request.dict())


if __name__ == "__main__":
    seed_data()
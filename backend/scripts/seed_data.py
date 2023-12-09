import requests
from fastapi.testclient import TestClient

from test_observer.controllers.test_executions.models import StartTestExecutionRequest
from test_observer.data_access.models_enums import FamilyName

BASE_URL = "http://localhost:30000/v1"
START_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/start-test"

REQUESTS = [
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage="beta",
        environment="rpi2",
        ci_link="http://example1",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="docker",
        version="20.10.24",
        revision=1,
        track="latest",
        store="ubuntu",
        arch="armhf",
        execution_stage="beta",
        environment="rpi2",
        ci_link="http://example2",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="docker",
        version="20.10.24",
        revision=1,
        track="core18",
        store="ubuntu",
        arch="armhf",
        execution_stage="beta",
        environment="rpi2",
        ci_link="http://example3",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="bluez",
        version="5.64-2",
        revision=1,
        track="22",
        store="ubuntu",
        arch="amd64",
        execution_stage="edge",
        environment="dawson-i",
        ci_link="http://example4",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="arm64",
        execution_stage="candidate",
        environment="cm3",
        ci_link="http://example5",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="checkbox22",
        version="2.6",
        revision=1,
        track="latest",
        store="ubuntu",
        arch="arm64",
        execution_stage="stable",
        environment="cm3",
        ci_link="http://example6",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="snapd",
        version="2.59.4",
        revision=1,
        track="latest",
        store="ubuntu",
        arch="arm64",
        execution_stage="stable",
        environment="dragonboard",
        ci_link="http://example7",
    ),
    StartTestExecutionRequest(
        family=FamilyName.DEB,
        name="linux-raspi",
        version="5.15.0.73.71",
        series="jammy",
        repo="main",
        arch="arm64",
        execution_stage="proposed",
        environment="rpi400",
        ci_link="http://example8",
    ),
    StartTestExecutionRequest(
        family=FamilyName.DEB,
        name="linux-raspi",
        version="5.15.0.73.70",
        series="jammy",
        repo="main",
        arch="arm64",
        execution_stage="updates",
        environment="rpi400",
        ci_link="http://example9",
    ),
]


def seed_data(client: TestClient | requests.Session):
    for request in REQUESTS:
        client.put(
            START_TEST_EXECUTION_URL, json=request.model_dump(mode="json")
        ).raise_for_status()


if __name__ == "__main__":
    seed_data(requests.Session())

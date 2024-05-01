#!/usr/bin/env python

# ruff: noqa: E501 Line too long

from datetime import date, timedelta
from textwrap import dedent

import requests
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.controllers.test_executions.models import (
    C3TestResult,
    C3TestResultStatus,
    EndTestExecutionRequest,
    StartTestExecutionRequest,
)
from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import SessionLocal
from test_observer.users.add_user import add_user

BASE_URL = "http://localhost:30000/v1"
START_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/start-test"
END_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/end-test"
RERUN_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/reruns"

START_TEST_EXECUTION_REQUESTS = [
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
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage="beta",
        environment="rpi4",
        ci_link="http://example10",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage="beta",
        environment="rpi3aplus",
        ci_link="http://example11",
    ),
    StartTestExecutionRequest(
        family=FamilyName.SNAP,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage="beta",
        environment="rp3bplus",
        ci_link="http://example12",
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

END_TEST_EXECUTION_REQUESTS = [
    EndTestExecutionRequest(
        ci_link="http://example1",
        test_results=[
            C3TestResult(
                name="docker/compose-and-basic_armhf",
                status=C3TestResultStatus.PASS,
                category="Docker containers",
                comment="",
                io_log=dedent(
                    """
                    test Pulling 
                    test Pulled 
                    Network 4506_default  Creating
                    Network 4506_default  Created
                    Container 4506-test-1  Creating
                    Container 4506-test-1  Created
                    Container 4506-test-1  Starting
                    Container 4506-test-1  Started
                    Container 4506-test-1  Stopping
                    Container 4506-test-1  Stopped
                    Container 4506-test-3  Creating
                    Container 4506-test-2  Creating
                    Container 4506-test-1  Recreate
                    Container 4506-test-3  Created
                    Container 4506-test-2  Created
                    Container 4506-test-1  Recreated
                    Container 4506-test-1  Starting
                    Container 4506-test-1  Started
                    Container 4506-test-2  Starting
                    Container 4506-test-2  Started
                    Container 4506-test-3  Starting
                    Container 4506-test-3  Started
                    3
                    Container 4506-test-1  Running
                    Container 4506-test-1  Stopping
                    Container 4506-test-1  Stopping
                    Container 4506-test-1  Stopped
                    Container 4506-test-1  Removing
                    Container 4506-test-1  Removed
                    Network 4506_default  Removing
                    Network 4506_default  Removed
                    """
                ),
            ),
            C3TestResult(
                name="after-suspend-audio/alsa-loopback-automated",
                status=C3TestResultStatus.SKIP,
                category="Audio tests",
                comment="""job cannot be started: resource expression "manifest.has_audio_loopback_connector == 'True'" evaluates to false, required dependency 'com.canonical.certification::audio/alsa-loopback-automated' has failed, required dependency 'com.canonical.certification::audio/detect-capture-devices' has failed, required dependency 'com.canonical.certification::audio/detect-playback-devices' has failed, required dependency 'com.canonical.certification::suspend/suspend_advanced_auto' has failed""",
                io_log="",
            ),
            C3TestResult(
                name="bluetooth4/beacon_eddystone_url_hci0",
                status=C3TestResultStatus.FAIL,
                category="Bluetooth tests",
                comment="",
                io_log=dedent(
                    """
                    Exception in thread Thread-1:
                    Traceback (most recent call last):
                    File "/snap/checkbox/4506/checkbox-runtime/usr/lib/python3.10/threading.py", line 1016, in _bootstrap_inner
                        self.run()
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/vendor/beacontools/scanner.py", line 147, in run
                        self.hci_version = self.get_hci_version()
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/vendor/beacontools/scanner.py", line 172, in get_hci_version
                        resp = self.backend.send_req(self.socket, OGF_INFO_PARAM, OCF_READ_LOCAL_VERSION,
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/vendor/beacontools/backend/linux.py", line 23, in send_req
                        return bluez.hci_send_req(socket, group_field, command_field, event, rlen, params, timeout)
                    _bluetooth.error: (100, 'Network is down')
                    Traceback (most recent call last):
                    File "/snap/checkbox/4506/checkbox-runtime/bin/checkbox-support-eddystone_scanner", line 8, in <module>
                        sys.exit(main())
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/scripts/eddystone_scanner.py", line 91, in main
                        rc = beacon_scan(hci_device)
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/scripts/eddystone_scanner.py", line 60, in beacon_scan
                        scanner.stop()
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/vendor/beacontools/scanner.py", line 95, in stop
                        self._mon.terminate()
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/vendor/beacontools/scanner.py", line 340, in terminate
                        self.toggle_scan(False)
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/vendor/beacontools/scanner.py", line 261, in toggle_scan
                        self.backend.send_cmd(self.socket, OGF_LE_CTL, command_field, command)
                    File "/snap/checkbox/4506/checkbox-runtime/lib/python3.10/site-packages/checkbox_support/vendor/beacontools/backend/linux.py", line 19, in send_cmd
                        return bluez.hci_send_cmd(socket, group_field, command_field, data)
                    _bluetooth.error: (100, 'Network is down')
                    """
                ),
            ),
        ],
    ),
    EndTestExecutionRequest(
        ci_link="http://example2",
        test_results=[
            C3TestResult(
                name="test7",
                status=C3TestResultStatus.PASS,
                category="",
                comment="",
                io_log="",
            ),
            C3TestResult(
                name="test8",
                status=C3TestResultStatus.SKIP,
                category="",
                comment="",
                io_log="",
            ),
        ],
    ),
]


def seed_data(client: TestClient | requests.Session, session: Session | None = None):
    session = session or SessionLocal()

    for email in (
        "omar.selo@canonical.com",
        "nadzeya.hutsko@canonical.com",
        "andrej.velichkovski@canonical.com",
    ):
        add_user(email, session)

    test_executions = []
    for start_request in START_TEST_EXECUTION_REQUESTS:
        response = client.put(
            START_TEST_EXECUTION_URL, json=start_request.model_dump(mode="json")
        )
        response.raise_for_status()
        test_executions.append(response.json())

    for end_request in END_TEST_EXECUTION_REQUESTS:
        client.put(
            END_TEST_EXECUTION_URL, json=end_request.model_dump(mode="json")
        ).raise_for_status()

    _rerun_some_test_executions(client, test_executions)

    _add_bugurl_and_duedate(session)


def _rerun_some_test_executions(
    client: TestClient | requests.Session, test_executions: list[dict]
) -> None:
    for te in test_executions[::2]:
        client.post(
            RERUN_TEST_EXECUTION_URL,
            json={"test_execution_id": te["id"]},
        ).raise_for_status()


def _add_bugurl_and_duedate(session: Session) -> None:
    artefact = session.scalar(select(Artefact).limit(1))

    if artefact:
        artefact.bug_link = (
            "https://bugs.launchpad.net/kernel-sru-workflow/+bug/2052031"
        )
        artefact.due_date = date.today() + timedelta(days=7)
        session.commit()


if __name__ == "__main__":
    seed_data(requests.Session())

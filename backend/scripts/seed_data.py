#!/usr/bin/env python
# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


# ruff: noqa

from datetime import date, timedelta
from textwrap import dedent

import requests
from fastapi.testclient import TestClient
from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.controllers.environments.models import (
    EnvironmentReportedIssueRequest,
)
from test_observer.controllers.test_cases.models import TestReportedIssueRequest
from test_observer.controllers.test_executions.models import (
    C3TestResult,
    C3TestResultStatus,
    EndTestExecutionRequest,
    StartCharmTestExecutionRequest,
    StartDebTestExecutionRequest,
    StartImageTestExecutionRequest,
    StartSnapTestExecutionRequest,
)
from test_observer.controllers.issues.models import (
    IssuePutRequest,
    IssueTestResultAttachmentRulePostRequest,
)
from test_observer.common.permissions import Permission

from test_observer.controllers.artefacts.models import TestExecutionRelevantLinkCreate

from test_observer.data_access.models import Artefact, User, TestResult, Application
from test_observer.data_access.models_enums import (
    FamilyName,
    SnapStage,
    DebStage,
    CharmStage,
    ImageStage,
    IssueStatus,
    IssueSource,
)
from test_observer.data_access.setup import SessionLocal
from test_observer.users.add_user import add_user
from tests.fake_launchpad_api import FakeLaunchpadAPI

BASE_URL = "http://localhost:30000/v1"
START_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/start-test"
END_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/end-test"
RERUN_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/reruns"
TEST_CASE_ISSUE_URL = f"{BASE_URL}/test-cases/reported-issues"
ENVIRONMENT_ISSUE_URL = f"{BASE_URL}/environments/reported-issues"
ISSUE_URL = f"{BASE_URL}/issues"
PATCH_TEST_EXECUTION_URL = f"{BASE_URL}/test-executions/{{id}}"
POST_ISSUE_ATTACHMENT_URL = f"{BASE_URL}/issues/{{id}}/attach"
POST_TEST_RESULT_ISSUE_ATTACHMENT_URL = f"{BASE_URL}/issues/{{id}}/attachment-rules"

ISSUE_REQUESTS = [
    IssuePutRequest(
        url=HttpUrl("https://github.com/canonical/test_observer/issues/71"),
        title="no way to filter and ctrl+f does not work",
        status=IssueStatus.GITHUB_CLOSED,
    ),
    IssuePutRequest(
        url=HttpUrl("https://warthogs.atlassian.net/browse/TO-142"),
        title="Create issues model and associated management APIs",
        status=IssueStatus.JIRA_NEW,
    ),
    IssuePutRequest(
        url=HttpUrl("https://bugs.launchpad.net/some-project/+bug/123456"),
    ),
]

TEST_RESULT_ATTACHMENT_RULE_REQUESTS = [
    (
        "https://github.com/canonical/test_observer/issues/71",
        IssueTestResultAttachmentRulePostRequest(
            environment_names=["rpi2"],
        ),
    )
]

START_TEST_EXECUTION_REQUESTS = [
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        branch="test-branch",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rpi2",
        ci_link="http://example1",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rpi2",
        ci_link="http://example13",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rpi2",
        ci_link="http://example14",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rpi4",
        ci_link="http://example10",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rpi3aplus",
        ci_link="http://example11",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rp3bplus",
        ci_link="http://example12",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="docker",
        version="20.10.24",
        revision=1,
        track="latest",
        store="ubuntu",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rpi2",
        ci_link="http://example2",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-18-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="docker",
        version="20.10.24",
        revision=1,
        track="core18",
        store="ubuntu",
        arch="armhf",
        execution_stage=SnapStage.beta,
        environment="rpi2",
        ci_link="http://example3",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-18-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="bluez",
        version="5.64-2",
        revision=1,
        track="22",
        store="ubuntu",
        arch="amd64",
        execution_stage=SnapStage.edge,
        environment="dawson-i",
        ci_link="http://example4",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="core22",
        version="20230531",
        revision=1,
        track="22",
        store="ubuntu",
        arch="arm64",
        execution_stage=SnapStage.candidate,
        environment="cm3",
        ci_link="http://example5",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="checkbox22",
        version="2.6",
        revision=1,
        track="latest",
        store="ubuntu",
        arch="arm64",
        execution_stage=SnapStage.stable,
        environment="cm3",
        ci_link="http://example6",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartSnapTestExecutionRequest(
        family=FamilyName.snap,
        name="snapd",
        version="2.59.4",
        revision=1,
        track="latest",
        store="ubuntu",
        arch="arm64",
        execution_stage=SnapStage.stable,
        environment="dragonboard",
        ci_link="http://example7",
        test_plan="com.canonical.certification::client-cert-iot-ubuntucore-22-automated",
    ),
    StartDebTestExecutionRequest(
        family=FamilyName.deb,
        name="linux-raspi",
        version="5.15.0.73.70",
        series="jammy",
        repo="main",
        arch="arm64",
        execution_stage=DebStage.updates,
        environment="rpi400",
        ci_link="http://example9",
        test_plan="com.canonical.certification::sru",
    ),
    StartDebTestExecutionRequest(
        family=FamilyName.deb,
        name="linux-raspi",
        version="5.15.0.73.71",
        series="jammy",
        repo="main",
        arch="arm64",
        execution_stage=DebStage.proposed,
        environment="rpi400",
        ci_link="http://example8",
        test_plan="com.canonical.certification::sru",
    ),
    StartDebTestExecutionRequest(
        family=FamilyName.deb,
        name="linux-raspi",
        version="5.15.0.73.71",
        series="jammy",
        repo="main",
        arch="arm64",
        execution_stage=DebStage.proposed,
        environment="rpi400",
        ci_link="http://example15",
        test_plan="com.canonical.certification::sru",
    ),
    StartDebTestExecutionRequest(
        family=FamilyName.deb,
        name="linux-raspi",
        version="5.15.0.73.71",
        series="jammy",
        repo="main",
        arch="arm64",
        execution_stage=DebStage.proposed,
        environment="rpi400",
        ci_link="http://example16",
        test_plan="com.canonical.certification::sru",
    ),
    StartDebTestExecutionRequest(
        family=FamilyName.deb,
        name="linux-raspi",
        version="5.15.0.73.71",
        series="jammy",
        repo="main",
        arch="arm64",
        execution_stage=DebStage.proposed,
        environment="rpi400",
        ci_link="http://example17",
        test_plan="com.canonical.certification::sru-server",
    ),
    StartDebTestExecutionRequest(
        family=FamilyName.deb,
        name="linux-raspi",
        version="5.15.0.73.71",
        series="jammy",
        repo="main",
        source="ppa/test",
        arch="arm64",
        environment="rpi400",
        test_plan="com.canonical.certification::sru-server",
    ),
    StartCharmTestExecutionRequest(
        family=FamilyName.charm,
        name="postgresql-k8s",
        version="123",
        revision=123,
        track="14",
        arch="arm64",
        execution_stage=CharmStage.candidate,
        environment="juju=3.5 ubuntu=22.04 cloud=k8s",
        ci_link="http://example13",
        relevant_links=[
            TestExecutionRelevantLinkCreate(
                label="Doc", url=HttpUrl("https://example.com/1")
            )
        ],
        test_plan="com.canonical.solutions-qa::tbd",
    ),
    StartImageTestExecutionRequest(
        name="noble-live-desktop-amd64",
        os="ubuntu",
        release="noble",
        arch="amd64",
        version="20240827",
        sha256="e71fb5681e63330445eec6fc3fe043f365289c2e595e3ceeac08fbeccfb9a957",
        owner="foundations",
        image_url=HttpUrl(
            "https://cdimage.ubuntu.com/noble/daily-live/20240827/noble-desktop-amd64.iso"
        ),
        execution_stage=ImageStage.pending,
        test_plan="image test plan",
        environment="xps",
    ),
    StartImageTestExecutionRequest(
        name="noble-live-desktop-amd64",
        os="ubuntu",
        release="noble",
        arch="amd64",
        version="20240827",
        sha256="e71fb5681e63330445eec6fc3fe043f365289c2e595e3ceeac08fbeccfb9a957",
        owner="foundations",
        image_url=HttpUrl(
            "https://cdimage.ubuntu.com/noble/daily-live/20240827/noble-desktop-amd64.iso"
        ),
        execution_stage=ImageStage.pending,
        test_plan="desktop image test plan",
        environment="xps",
    ),
    StartImageTestExecutionRequest(
        name="ubuntu-core-20-arm64-raspi",
        os="ubuntu-core",
        release="20",
        arch="amd64+raspi",
        version="20221025.4",
        sha256="e94418aa109cf5886a50e828e98ac68361ea7e3ca1ab4aed2bbddc0a299b334f",
        owner="snapd",
        image_url=HttpUrl(
            "https://cdimage.ubuntu.com/ubuntu-core/20/stable/20221025.4/ubuntu-core-20-arm64+raspi.img.xz"
        ),
        execution_stage=ImageStage.pending,
        test_plan="core image test plan",
        environment="rpi3",
    ),
]

END_TEST_EXECUTION_REQUESTS = [
    EndTestExecutionRequest(
        ci_link="http://example1",
        test_results=[
            C3TestResult(
                name="docker/compose-and-basic_armhf",
                status=C3TestResultStatus.FAIL,
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
                template_id="bluetooth4/beacon_eddystone_url_interface",
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
        ci_link="http://example13",
        test_results=[
            C3TestResult(
                name="docker/compose-and-basic_armhf",
                status=C3TestResultStatus.PASS,
                category="Docker containers",
                comment="",
                io_log="",
            ),
            C3TestResult(
                name="after-suspend-audio/alsa-loopback-automated",
                status=C3TestResultStatus.FAIL,
                category="Audio tests",
                comment="",
                io_log="",
            ),
        ],
    ),
    EndTestExecutionRequest(
        ci_link="http://example10",
        test_results=[
            C3TestResult(
                name="docker/compose-and-basic_armhf",
                status=C3TestResultStatus.PASS,
                category="Docker containers",
                comment="",
                io_log="",
            ),
            C3TestResult(
                name="after-suspend-audio/alsa-loopback-automated",
                status=C3TestResultStatus.FAIL,
                category="Audio tests",
                comment="",
                io_log="",
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
    EndTestExecutionRequest(
        ci_link="http://example8",
        test_results=[
            C3TestResult(
                name="test",
                status=C3TestResultStatus.FAIL,
                category="",
                comment="",
                io_log="",
            ),
        ],
    ),
    EndTestExecutionRequest(
        ci_link="http://example15",
        test_results=[
            C3TestResult(
                name="test",
                status=C3TestResultStatus.FAIL,
                category="",
                comment="",
                io_log="",
            ),
        ],
    ),
    EndTestExecutionRequest(
        ci_link="http://example16",
        test_results=[
            C3TestResult(
                name="test",
                status=C3TestResultStatus.PASS,
                category="",
                comment="",
                io_log="",
            ),
        ],
    ),
    EndTestExecutionRequest(
        ci_link="http://example9",
        test_results=[
            C3TestResult(
                name="test",
                status=C3TestResultStatus.PASS,
                category="",
                comment="",
                io_log="",
            ),
        ],
    ),
]

TEST_CASE_ISSUE_REQUESTS = [
    TestReportedIssueRequest(
        template_id=END_TEST_EXECUTION_REQUESTS[0].test_results[2].template_id,  # type: ignore
        url=HttpUrl("https://github.com"),
        description="known issue 1",
    ),
    TestReportedIssueRequest(
        case_name=END_TEST_EXECUTION_REQUESTS[0].test_results[0].name,
        url=HttpUrl("https://warthogs.atlassian.net"),
        description="known issue 2",
    ),
    TestReportedIssueRequest(
        case_name=END_TEST_EXECUTION_REQUESTS[0].test_results[1].name,
        url=HttpUrl("https://bugs.launchpad.net"),
        description="known issue 3",
    ),
]

ENVIRONMENT_ISSUE_REQUESTS = [
    EnvironmentReportedIssueRequest(
        environment_name=START_TEST_EXECUTION_REQUESTS[0].environment,
        url=HttpUrl("https://github.com"),
        description="known issue 1",
        is_confirmed=True,
    ),
    EnvironmentReportedIssueRequest(
        environment_name=START_TEST_EXECUTION_REQUESTS[1].environment,
        url=HttpUrl("https://warthogs.atlassian.net"),
        description="known issue 2",
        is_confirmed=False,
    ),
    EnvironmentReportedIssueRequest(
        environment_name=START_TEST_EXECUTION_REQUESTS[2].environment,
        url=HttpUrl("https://bugs.launchpad.net"),
        description="known issue 3",
        is_confirmed=True,
    ),
]

SAMPLE_EXECUTION_METADATA = [
    {
        "category1": ["value1", "value2"],
        "category2": ["value3"],
        "category3:4-5": ["weird strange value:/!@#$%^&*()"],
    },
    {
        "category1": ["value1", "long message " + " ".join(str(n) for n in range(50))],
        "category2": ["value3"],
    },
    {
        "category1": [
            "value1",
            "value1",
            "value2",
            "value3",
            "value4",
            "value5",
            "value6",
            "value7",
        ]
    },
    {"category1": ["value4"], "category2": ["value5", "value6"]},
    {"category3": ["value4"], "category2": ["value5", "value6"]},
    {"category4": ["value7", "value8"], "category5": ["value1", "value10"]},
    {"category6": ["value11", "value12"], "category7": ["value13"]},
]

SAMPLE_ISSUE_ATTACHMENT_SEQUENCE = [
    [0, 1, 2],
    [0, 2],
    [],
    [0],
]


def seed_data(client: TestClient | requests.Session, session: Session | None = None):
    session = session or SessionLocal()

    # Check if data has already been seeded by looking for existing users or artefacts
    existing_users = session.scalar(select(User).limit(1))
    existing_artefacts = session.scalar(select(Artefact).limit(1))

    if existing_users or existing_artefacts:
        print("Database already contains data. Skipping seed operation.")
        return

    print("Seeding database with test data...")

    add_user("john.doe@canonical.com", session, launchpad_api=FakeLaunchpadAPI())

    certbot = add_user(
        "certbot@canonical.com", session, launchpad_api=FakeLaunchpadAPI()
    )
    certbot.is_admin = True

    # Create an application with all permissions
    application = session.scalar(
        select(Application).where(Application.name == "seed_data_app")
    )
    if not application:
        application = Application(
            name="seed_data_app", permissions=[p.value for p in Permission]
        )
        session.add(application)
        session.commit()
        session.refresh(application)
    auth_headers = {"Authorization": f"Bearer {application.api_key}"}

    issues = []
    for issue_request in ISSUE_REQUESTS:
        response = client.put(
            ISSUE_URL,
            json=issue_request.model_dump(mode="json"),
            headers=auth_headers,
        )
        response.raise_for_status()
        issues.append(response.json())

    attachment_rules = []
    for issue_url, attachment_rule_request in TEST_RESULT_ATTACHMENT_RULE_REQUESTS:
        issue_id = None
        for issue in issues:
            if issue["url"] == issue_url:
                issue_id = issue["id"]
        if issue_id is None:
            print(f"Could not find issue ID for URL: {issue_url}")
            continue
        response = client.post(
            POST_TEST_RESULT_ISSUE_ATTACHMENT_URL.format(id=issue_id),
            json=attachment_rule_request.model_dump(mode="json"),
            headers=auth_headers,
        )
        response.raise_for_status()
        attachment_rules.append(response.json())

    test_executions = []
    for start_request in START_TEST_EXECUTION_REQUESTS:
        response = client.put(
            START_TEST_EXECUTION_URL,
            json=start_request.model_dump(mode="json"),
            headers=auth_headers,
        )
        response.raise_for_status()
        test_executions.append(response.json())

    for end_request in END_TEST_EXECUTION_REQUESTS:
        client.put(
            END_TEST_EXECUTION_URL,
            json=end_request.model_dump(mode="json"),
            headers=auth_headers,
        ).raise_for_status()

    for case_issue_request in TEST_CASE_ISSUE_REQUESTS:
        client.post(
            TEST_CASE_ISSUE_URL,
            json=case_issue_request.model_dump(mode="json"),
            headers=auth_headers,
        ).raise_for_status()

    for environment_issue_request in ENVIRONMENT_ISSUE_REQUESTS:
        client.post(
            ENVIRONMENT_ISSUE_URL,
            json=environment_issue_request.model_dump(mode="json"),
            headers=auth_headers,
        ).raise_for_status()

    _rerun_some_test_executions(client, test_executions, auth_headers)

    _add_some_execution_metadata(client, test_executions, auth_headers)

    _add_bugurl_and_duedate(session)

    _add_issue_attachments(client, session, issues, auth_headers)

    print("Database seeding completed successfully!")


def _rerun_some_test_executions(
    client: TestClient | requests.Session,
    test_executions: list[dict],
    auth_headers: dict,
) -> None:
    te_ids = [te["id"] for te in test_executions[::2]]
    client.post(
        RERUN_TEST_EXECUTION_URL,
        json={"test_execution_ids": te_ids},
        headers=auth_headers,
    ).raise_for_status()


def _add_some_execution_metadata(
    client: TestClient | requests.Session,
    test_executions: list[dict],
    auth_headers: dict,
) -> None:
    te_ids = [te["id"] for te in test_executions[::2]]
    for idx, te_id in enumerate(te_ids):
        client.patch(
            PATCH_TEST_EXECUTION_URL.format(id=te_id),
            json={
                "execution_metadata": SAMPLE_EXECUTION_METADATA[
                    idx % len(SAMPLE_EXECUTION_METADATA)
                ]
            },
            headers=auth_headers,
        ).raise_for_status()


def _add_bugurl_and_duedate(session: Session) -> None:
    artefact = session.scalar(select(Artefact).limit(1))

    if artefact:
        artefact.bug_link = (
            "https://bugs.launchpad.net/kernel-sru-workflow/+bug/2052031"
        )
        artefact.due_date = date.today() + timedelta(days=7)
        session.commit()


def _add_issue_attachments(
    client: TestClient | requests.Session,
    session: Session,
    issues: list[dict],
    auth_headers: dict,
) -> None:
    for idx, test_result in enumerate(session.scalars(select(TestResult)).all()):
        idxs_to_attach = SAMPLE_ISSUE_ATTACHMENT_SEQUENCE[
            idx % len(SAMPLE_ISSUE_ATTACHMENT_SEQUENCE)
        ]
        for issue_idx, issue in enumerate(issues):
            if issue_idx not in idxs_to_attach:
                continue
            client.post(
                POST_ISSUE_ATTACHMENT_URL.format(id=issue["id"]),
                json={"test_results": [test_result.id]},
                headers=auth_headers,
            ).raise_for_status()
    session.commit()


if __name__ == "__main__":
    seed_data(requests.Session())

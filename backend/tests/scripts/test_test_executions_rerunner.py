import base64

from requests_mock import Mocker

from scripts.test_executions_rerunner import Main, reruns_link
from test_observer.data_access.models_enums import FamilyName

jenkins_request_headers = {
    "Authorization": f"Basic {base64.b64encode(b'admin:token').decode()}"
}


def test_does_nothing_when_no_reruns_requested(requests_mock: Mocker):
    requests_mock.get(reruns_link, json=[])

    execute()

    assert requests_mock.called_once


def test_correctly_submits_deb_rerun_request(requests_mock: Mocker):
    job_link = "http://10.102.156.15:8080/job/fake-job/"

    ci_link = f"{job_link}1/"
    requests_mock.get(
        reruns_link,
        json=[{"test_execution_id": 1, "ci_link": ci_link, "family": FamilyName.DEB}],
    )

    def is_data_valid(request) -> bool:  # noqa: ANN001
        return request.json() == {"TESTPLAN": "full"}

    rerun_link = f"{job_link}/buildWithParameters"
    matcher = requests_mock.post(
        rerun_link,
        request_headers=jenkins_request_headers,
        additional_matcher=is_data_valid,
    )

    execute()

    assert matcher.called_once


def test_correctly_submits_snap_rerun_request(requests_mock: Mocker):
    job_link = "http://10.102.156.15:8080/job/fake-job/"

    ci_link = f"{job_link}1/"
    requests_mock.get(
        reruns_link,
        json=[{"test_execution_id": 1, "ci_link": ci_link, "family": FamilyName.SNAP}],
    )

    rerun_link = f"{job_link}/build"
    matcher = requests_mock.post(
        rerun_link,
        request_headers=jenkins_request_headers,
    )

    execute()

    assert matcher.called_once


def execute():
    Main(jenkins_api_token="token").run()

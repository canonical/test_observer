import base64
import re
from typing import TypedDict

from requests import Request

import pytest
from requests_mock import Mocker

from test_observer.external_apis.c3.c3 import C3Api
from test_observer.external_apis.c3.models import (
    Report,
    SubmissionProcessingStatus,
    SubmissionStatus,
    TestResultStatus,
)


class StatusDict(TypedDict):
    id: int
    report_id: int | None
    status: SubmissionProcessingStatus


class C3TestCaseDict(TypedDict):
    id: int
    name: str


class C3TestResultDict(TypedDict):
    id: int
    comment: str
    io_log: str
    test: C3TestCaseDict
    status: str


class C3ReportSummaryAPIResponse(TypedDict):
    id: int
    failed_test_count: int
    testresult_set: list[C3TestResultDict]


@pytest.fixture
def prepare_c3api(
    requests_mock: Mocker, monkeypatch: pytest.MonkeyPatch
) -> tuple[C3Api, str]:
    client_id = "foo"
    client_secret = "bar"
    basic_token = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(
        "utf-8"
    )
    bearer_token = "token"
    requests_mock.post(
        "https://certification.canonical.com/oauth2/token/",
        request_headers={"Authorization": f"Basic {basic_token}"},
        json={"access_token": bearer_token},
    )
    requests_mock.get(
        re.compile("^https://certification.canonical.com/api/v2/.*"),
        request_headers={"Authorization": "Bearer "},
        status_code=401,
    )
    monkeypatch.setenv("C3_CLIENT_ID", client_id)
    monkeypatch.setenv("C3_CLIENT_SECRET", client_secret)
    c3 = C3Api()
    return c3, bearer_token


def test_authenticate_and_send_invalid_token(
    requests_mock: Mocker, prepare_c3api: tuple[C3Api, str]
):
    c3, bearer_token = prepare_c3api

    unauthorized_response_codes = [401, 403]
    for error_code in unauthorized_response_codes:
        requests_mock.get(
            re.compile("^https://certification.canonical.com/api/v2/.*"),
            request_headers={"Authorization": f"Bearer {bearer_token}"},
            status_code=error_code,
        )

        test_request = Request(
            method="GET",
            url="https://certification.canonical.com/api/v2/submissions/status",
        )

        # Reset mock to clear the request history
        requests_mock.reset_mock()

        c3._authenticate_and_send(test_request)

        # Verify three requests were called: unauthenticated request,
        # authentication request, repeated request with the correct
        # authentication details
        assert len(requests_mock.request_history) == 3
        # Verify the last request was to the intended URL
        assert (
            requests_mock.request_history[-1].method == "GET"
            and requests_mock.request_history[-1].url
            == "https://certification.canonical.com/api/v2/submissions/status"
        )
        # Verify the second to last request was an authentication API call
        # to get the token
        assert (
            requests_mock.request_history[-2].method == "POST"
            and requests_mock.request_history[-2].url
            == "https://certification.canonical.com/oauth2/token/"
        )


def test_get_submissions_statuses(
    requests_mock: Mocker, prepare_c3api: tuple[C3Api, str]
):
    c3, bearer_token = prepare_c3api
    status: StatusDict = {
        "id": 111111,
        "report_id": 237670,
        "status": SubmissionProcessingStatus.PASS,
    }
    requests_mock.get(
        f"https://certification.canonical.com/api/v2/submissions/status/?id__in={status['id']}&limit=1",
        request_headers={"Authorization": f"Bearer {bearer_token}"},
        json={"results": [status]},
    )

    statuses = c3.get_submissions_statuses([status["id"]])

    assert statuses == {status["id"]: SubmissionStatus(**status)}


def test_get_reports(requests_mock: Mocker, prepare_c3api: tuple[C3Api, str]):
    c3, bearer_token = prepare_c3api
    c3_api_response: C3ReportSummaryAPIResponse = {
        "id": 237670,
        "failed_test_count": 0,
        "testresult_set": [],
    }
    requests_mock.get(
        f"https://certification.canonical.com/api/v2/reports/summary/?id__in={c3_api_response['id']}&limit=1",
        request_headers={"Authorization": f"Bearer {bearer_token}"},
        json={"results": [c3_api_response]},
    )

    reports = c3.get_reports([c3_api_response["id"]])

    # The type checker cannot recognize that the testresult_set is an alias
    # to the test_results field, we ignore the call-arg error because of this
    expected_report = Report(**c3_api_response)  # type: ignore

    assert reports == {expected_report.id: expected_report}


def test_get_reports_with_test_results(
    requests_mock: Mocker, prepare_c3api: tuple[C3Api, str]
):
    c3, bearer_token = prepare_c3api
    c3_api_response: C3ReportSummaryAPIResponse = {
        "id": 237670,
        "failed_test_count": 0,
        "testresult_set": [
            {
                "id": 123123,
                "comment": "Test comment",
                "io_log": "IO log of the test run",
                "status": "pass",
                "test": {
                    "id": 12,
                    "name": "wireless",
                },
            },
            {
                "id": 123124,
                "comment": "Test comment",
                "io_log": "IO log of the test run",
                "status": "fail",
                "test": {
                    "id": 12,
                    "name": "camera",
                },
            },
        ],
    }

    requests_mock.get(
        f"https://certification.canonical.com/api/v2/reports/summary/?id__in={c3_api_response['id']}&limit=1",
        request_headers={"Authorization": f"Bearer {bearer_token}"},
        json={"results": [c3_api_response]},
    )

    reports = c3.get_reports([c3_api_response["id"]])

    assert len(reports[237670].test_results) == 2

    count_pass = 0
    count_fail = 0
    for test_result in reports[237670].test_results:
        if test_result.status == TestResultStatus.PASS:
            count_pass += 1
        elif test_result.status == TestResultStatus.FAIL:
            count_fail += 1

    assert count_pass == 1 and count_fail == 1

    # The type checker cannot recognize that the testresult_set is an alias
    # to the test_results field, we ignore the call-arg error because of this
    expected_report = Report(**c3_api_response)  # type: ignore

    assert reports == {expected_report.id: expected_report}

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
)


class StatusDict(TypedDict):
    id: int
    report_id: int | None
    status: SubmissionProcessingStatus


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

    UNAUTHORIZED_RESPONSE_CODES = [401, 403]
    for error_code in UNAUTHORIZED_RESPONSE_CODES:
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
        # authentication request, repeated request with the correct authentication details
        assert len(requests_mock.request_history) == 3
        # Verify the last request was to the intended URL
        assert (
            requests_mock.request_history[-1].method == "GET"
            and requests_mock.request_history[-1].url
            == "https://certification.canonical.com/api/v2/submissions/status"
        )
        # Verify the second to last request was an authentication API call to get the token
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
    report = {"id": 237670, "failed_test_count": 0}
    requests_mock.get(
        f"https://certification.canonical.com/api/v2/reports/summary/?id__in={report['id']}&limit=1",
        request_headers={"Authorization": f"Bearer {bearer_token}"},
        json={"results": [report]},
    )

    reports = c3.get_reports([report["id"]])

    assert reports == {report["id"]: Report(**report)}

import logging
import os
from collections.abc import Iterable

import requests
from requests import Request, Response

from .models import Report, SubmissionStatus

logger = logging.getLogger("test-observer-backend")


class C3Api:
    def __init__(self):
        self._client_id = os.environ.get("C3_CLIENT_ID", "")
        self._client_secret = os.environ.get("C3_CLIENT_SECRET", "")
        self._bearer_token = ""

    def get_submissions_statuses(
        self, ids: Iterable[int]
    ) -> dict[int, SubmissionStatus]:
        response = self._authenticate_and_send(
            Request(
                method="GET",
                url="https://certification.canonical.com/api/v2/submissions/status/",
                params={"id__in": ",".join([str(status_id) for status_id in ids])},
            )
        )

        if response.ok:
            statuses = response.json()["results"]
            return {json["id"]: SubmissionStatus(**json) for json in statuses}
        else:
            logger.warning(response.text)
            return {}

    def get_reports(self, ids: Iterable[int]) -> dict[int, Report]:
        response = self._authenticate_and_send(
            Request(
                method="GET",
                url="https://certification.canonical.com/api/v2/reports/summary/",
                params={"id__in": ",".join([str(report_id) for report_id in ids])},
            )
        )

        if response.ok:
            reports = response.json()["results"]
            return {json["id"]: Report(**json) for json in reports}
        else:
            logger.warning(response.text)
            return {}

    def _authenticate_and_send(self, request: Request) -> Response:
        prepared_request = request.prepare()
        prepared_request.headers["Authorization"] = f"Bearer {self._bearer_token}"
        session = requests.session()
        response = session.send(prepared_request)
        if response.status_code in (401, 403):
            self._authenticate()
            prepared_request.headers["Authorization"] = f"Bearer {self._bearer_token}"
            response = session.send(prepared_request)
        return response

    def _authenticate(self) -> None:
        response = requests.post(
            "https://certification.canonical.com/oauth2/token/",
            auth=(self._client_id, self._client_secret),
            data={"grant_type": "client_credentials"},
        )

        if response.ok:
            self._bearer_token = response.json().get("access_token", "")

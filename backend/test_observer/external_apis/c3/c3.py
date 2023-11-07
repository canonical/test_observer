import os
from collections.abc import Iterable

import requests
from requests import Request, Response

from .models import Report, SubmissionStatus


class C3Api:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        if not client_id:
            client_id = os.environ["C3_CLIENT_ID"]
        if not client_secret:
            client_secret = os.environ["C3_CLIENT_SECRET"]

        self.client_id = client_id
        self.client_secret = client_secret

        self.bearer_token = ""

    def get_submissions_statuses(self, ids: Iterable[int]) -> list[SubmissionStatus]:
        response = self._authenticate_and_send(
            Request(
                method="GET",
                url="https://certification.canonical.com/api/v2/submissions/status/",
                params={"id__in": ",".join([str(status_id) for status_id in ids])},
            )
        )

        statuses = response.json()["results"]
        return [SubmissionStatus(**json) for json in statuses]

    def get_reports(self, ids: Iterable[int]) -> list[Report]:
        response = self._authenticate_and_send(
            Request(
                method="GET",
                url="https://certification.canonical.com/api/v2/reports/summary/",
                params={"id__in": ",".join([str(report_id) for report_id in ids])},
            )
        )

        reports = response.json()["results"]
        return [Report(**json) for json in reports]

    def _authenticate_and_send(self, request: Request) -> Response:
        prepared_request = request.prepare()
        prepared_request.headers["Authorization"] = f"Bearer {self.bearer_token}"
        session = requests.session()
        response = session.send(prepared_request)
        if response.status_code in (401, 403):
            self._authenticate()
            prepared_request.headers["Authorization"] = f"Bearer {self.bearer_token}"
            response = session.send(prepared_request)
        return response

    def _authenticate(self) -> None:
        response = requests.post(
            "https://certification.canonical.com/oauth2/token/",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
        )

        if response.ok:
            self.bearer_token = response.json().get("access_token", "")

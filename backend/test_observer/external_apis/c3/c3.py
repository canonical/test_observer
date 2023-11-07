import os
from collections.abc import Iterable

import requests
from requests import Request

from .models import SubmissionStatus


class C3Api:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        if not client_id:
            client_id = os.environ["C3_CLIENT_ID"]
        if not client_secret:
            client_secret = os.environ["C3_CLIENT_SECRET"]

        self.client_id = client_id
        self.client_secret = client_secret

        self.bearer_token = ""

    def get_submissions_statuses(self, ids: Iterable[int]):
        session = requests.session()
        request = Request(
            method="GET",
            url="https://certification.canonical.com/api/v2/submissions/status/",
            headers={"Authorization": f"Bearer {self.bearer_token}"},
            params={"id__in": ",".join([str(status_id) for status_id in ids])},
        ).prepare()

        response = session.send(request)
        if response.status_code in (401, 403):
            self._authenticate()
            request.headers["Authorization"] = f"Bearer {self.bearer_token}"
            response = session.send(request)

        statuses = response.json()["results"]
        return [SubmissionStatus(**json) for json in statuses]

    def _authenticate(self) -> None:
        response = requests.post(
            "https://certification.canonical.com/oauth2/token/",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
        )

        if response.ok:
            self.bearer_token = response.json().get("access_token", "")

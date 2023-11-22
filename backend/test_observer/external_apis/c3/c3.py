import json
import logging
import os
from collections.abc import Iterable

import requests
from requests import Request, Response

from .models import Report, SubmissionStatus, TestResult

from redis import Redis

logger = logging.getLogger("test-observer-backend")


class C3Api:
    def __init__(self):
        self._client_id = os.environ.get("C3_CLIENT_ID", "")
        self._client_secret = os.environ.get("C3_CLIENT_SECRET", "")
        self._bearer_token = ""

    def get_submissions_statuses(self, ids: set[int]) -> dict[int, SubmissionStatus]:
        str_ids = [str(status_id) for status_id in ids]

        # We don't need to make an API call in case there are 0 submissions
        if not str_ids:
            return {}

        response = self._authenticate_and_send(
            Request(
                method="GET",
                url="https://certification.canonical.com/api/v2/submissions/status/",
                params={"id__in": ",".join(str_ids), "limit": len(str_ids)},
            )
        )

        if response.ok:
            statuses = response.json()["results"]
            return {json["id"]: SubmissionStatus(**json) for json in statuses}
        else:
            logger.warning(response.text)
            return {}

    def get_reports(self, ids: Iterable[int], redis: Redis) -> dict[int, Report]:
        str_ids = [str(report_id) for report_id in ids]

        # We don't need to make an API call in case there are 0 reports
        if not str_ids:
            return {}

        response = self._authenticate_and_send(
            Request(
                method="GET",
                url="https://certification.canonical.com/api/v2/reports/summary/",
                params={"id__in": ",".join(str_ids), "limit": len(str_ids)},
            )
        )

        test_results = self._get_test_results(str_ids, redis)

        if response.ok:
            reports = response.json()["results"]
            return {
                json["id"]: Report(**json, test_results=test_results[json["id"]])
                for json in reports
            }
        else:
            logger.warning(response.text)
            return {}

    def _get_test_results(self, str_ids: list[str], redis: Redis) -> dict[int, list[TestResult]]:
        test_results = {}
        for id in str_ids:
            test_results[int(id)] = self._get_test_results_by_report_id(id, redis)
        return test_results

    def _get_test_results_by_report_id(self, report_id: str, redis: Redis) -> list[TestResult]:
        # TODO: After PR 151 in C3 we can replace with only one API call to C3
        cached_report_object = redis.get(report_id)
        if cached_report_object:
            print("getting from cache")
            test_results = []
            reports = json.loads(cached_report_object)["results"]
            for test_result in reports[0]["testresult_set"]:
                test_results.append(
                    TestResult(
                        id=test_result["test"]["id"],
                        name=test_result["test"]["name"],
                        status=test_result["status"],
                        type=test_result["test"]["type"],
                        io_log=test_result["io_log"],
                        comments=test_result["comment"],
                        historic_results=[],
                    )
                )
            return test_results

        response = self._authenticate_and_send(
            Request(
                method="GET",
                url=f"https://certification.canonical.com/api/v2/reports/summary/{report_id}/",
            )
        )

        if response.ok:
            test_results = []
            reports = response.json()["results"]
            redis.set(reports[0]["id"], json.dumps(response.json()))
            for test_result in reports[0]["testresult_set"]:
                test_results.append(
                    TestResult(
                        id=test_result["test"]["id"],
                        name=test_result["test"]["name"],
                        status=test_result["status"],
                        type=test_result["test"]["type"],
                        io_log=test_result["io_log"],
                        comments=test_result["comment"],
                        historic_results=[],
                    )
                )
            return test_results
        else:
            logger.warning(response.text)
            return []

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

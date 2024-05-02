"""
This script will be used by jenkins to rerun test executions as requested
by test observer. Please note that jenkins will download this file then run it.
Therefore, this script can't import from the rest of the codebase and shouldn't be
renamed. Dependencies used by this script must be installed on jenkins.
"""

import logging
import re
from os import environ

import requests
from requests.auth import HTTPBasicAuth

reruns_link = "https://test-observer.canonical.com/v1/test-executions/reruns"


class Main:
    def __init__(self, jenkins_api_token: str | None = None):
        self.jenkins_auth = HTTPBasicAuth(
            "admin", jenkins_api_token or environ["JENKINS_API_TOKEN"]
        )

    def run(self):
        self._load_rerun_requests()
        self._submit_rerun_requests()

    def _load_rerun_requests(self) -> None:
        response = requests.get(reruns_link)
        self.rerun_requests = response.json()
        logging.info(f"Received the following rerun requests:\n{self.rerun_requests}")

    def _submit_rerun_requests(self) -> None:
        for rerun_request in self.rerun_requests:
            self._submit_rerun(rerun_request)

    def _submit_rerun(self, rerun_request: dict) -> None:
        base_job_link = self._extract_base_job_link_from_ci_link(
            rerun_request["ci_link"]
        )
        if base_job_link:
            family = rerun_request["family"]
            if family == "deb":
                self._submit_deb_rerun(base_job_link)
            elif family == "snap":
                self._submit_snap_rerun(base_job_link)
            else:
                logging.error(f"Invalid family name {family}")

    def _extract_base_job_link_from_ci_link(self, ci_link: str) -> str | None:
        matching = re.match(r"(.+/)\d+/", ci_link)
        if matching:
            return matching.group(1)
        return None

    def _submit_snap_rerun(self, base_job_link: str) -> None:
        rerun_link = f"{base_job_link}/build"
        logging.info(f"POST {rerun_link}")
        requests.post(rerun_link, auth=self.jenkins_auth)

    def _submit_deb_rerun(self, base_job_link: str) -> None:
        rerun_link = f"{base_job_link}/buildWithParameters"
        data = {"TESTPLAN": "full"}
        logging.info(f"POST {rerun_link} {data}")
        requests.post(rerun_link, auth=self.jenkins_auth, json=data)

import random
import time

from locust import HttpUser, between, task


class APIUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def normal_usage(self):
        artefacts = self._get_artefacts()
        time.sleep(1)
        for artefact in random.choices(artefacts, k=10):
            test_executions = self._get_test_executions(artefact)
            time.sleep(1)
            for te in random.choices(test_executions, k=30):
                self._get_test_results(te)
                time.sleep(1)

    def _get_artefacts(self) -> list[dict]:
        return self.client.get("/v1/artefacts").json()

    def _get_test_executions(self, artefact: dict) -> list[dict]:
        json = self.client.get(
            f"/v1/artefacts/{artefact['id']}/builds",
            name="/v1/artefacts/<id>/builds",
        ).json()
        return [te for build in json for te in build["test_executions"]]

    def _get_test_results(self, test_execution: dict) -> list[dict]:
        return self.client.get(
            f"/v1/test-executions/{test_execution['id']}/test-results",
            name="/v1/test-executions/<id>/test-results",
        ).json()

import requests
import json
import time

response = requests.get("http://test-observer-api.canonical.com/v1/artefacts/10074")

artefact = json.loads(response.content)

# for artefact in artefacts:
print(artefact["id"])
builds = requests.get(
    f"http://test-observer-api.canonical.com/v1/artefacts/{artefact['id']}/builds"
)
builds_dict = json.loads(builds.content)
print(builds_dict)

for arch in builds_dict:
    for test_exec in arch["test_executions"]:
        req_data = {
            "family": "snap",
            "name": artefact["name"],
            "version": artefact["version"],
            "revision": arch["revision"],
            "track": artefact["track"],
            "store": artefact["store"],
            "series": None,
            "repo": None,
            "arch": test_exec["environment"]["architecture"],
            "execution_stage": artefact["stage"],
            "environment": test_exec["environment"]["name"],
        }

        requests.put("http://localhost:30000/v1/test-executions/start-test", json=req_data)

# Wait for some time before making a new request, to avoid DDOS-ing the server
time.sleep(2)

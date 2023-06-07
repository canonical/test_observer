import requests

BASE_URL = "http://localhost:30000/v1"
START_TEST_EXECUTION_URL = f"{BASE_URL}/test-execution/start"

REQUESTS = [
    {
        "family": "snap",
        "name": "core22",
        "version": "20230531",
        "source": {"track": "22"},
        "arch": "arm64",
        "execution_stage": "beta",
        "environment": "env1",
    },
    {
        "family": "snap",
        "name": "docker",
        "version": "20.10.24",
        "source": {"track": "latest"},
        "arch": "arm64",
        "execution_stage": "beta",
        "environment": "env1",
    },
    {
        "family": "snap",
        "name": "docker",
        "version": "20.10.24",
        "source": {"track": "core18"},
        "arch": "arm64",
        "execution_stage": "beta",
        "environment": "env1",
    },
    {
        "family": "snap",
        "name": "bluez",
        "version": "5.64-2",
        "source": {"track": "22"},
        "arch": "arm64",
        "execution_stage": "edge",
        "environment": "env2",
    },
    {
        "family": "snap",
        "name": "core22",
        "version": "20230531",
        "source": {"track": "22"},
        "arch": "amd64",
        "execution_stage": "candidate",
        "environment": "env3",
    },
    {
        "family": "snap",
        "name": "checkbox22",
        "version": "2.6",
        "source": {"track": "latest"},
        "arch": "amd64",
        "execution_stage": "stable",
        "environment": "env3",
    },
    {
        "family": "snap",
        "name": "snapd",
        "version": "2.59.4",
        "source": {"track": "latest"},
        "arch": "arm64",
        "execution_stage": "stable",
        "environment": "env4",
    },
    {
        "family": "deb",
        "name": "linux-generic",
        "version": "5.15.0.73.71",
        "source": {"series": "jammy", "repo": "universe"},
        "arch": "arm64",
        "execution_stage": "proposed",
        "environment": "caracalla",
    },
    {
        "family": "deb",
        "name": "linux-generic",
        "version": "5.15.0.73.70",
        "source": {"series": "jammy", "repo": "universe"},
        "arch": "arm64",
        "execution_stage": "updates",
        "environment": "caracalla",
    },
]


def seed_data():
    for request in REQUESTS:
        requests.put(START_TEST_EXECUTION_URL, json=request)


if __name__ == "__main__":
    seed_data()

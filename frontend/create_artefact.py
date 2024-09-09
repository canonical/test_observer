import requests


def main():
    requests.put(
        "http://canonical:30000/v1/test-executions/start-test",
        json={
            "family": "snap",
            "name": "core22",
            "version": "20230532",
            "revision": 1,
            "track": "22",
            "store": "ubuntu",
            "arch": "armhf",
            "execution_stage": "beta",
            "environment": "rpi2",
            "ci_link": "http://example20",
        },
    )

    requests.put(
        "http://canonical:30000/v1/test-executions/end-test",
        json={
            "ci_link": "http://example20",
            "test_results": [
                {
                    "name": "bluetooth4/beacon_eddystone_url_hci0",
                    "template_id": "bluetooth4/beacon_eddystone_url_interface",
                    "status": "fail",
                    "category": "Bluetooth tests",
                    "comment": "",
                    "io_log": "",
                }
            ],
        },
    )


if __name__ == "__main__":
    main()

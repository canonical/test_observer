from datetime import date

from requests_mock import Mocker

from test_observer.kernel_swm_integration.swm_reader import get_artefacts_swm_info


def test_get_artefacts_swm_info(requests_mock: Mocker):
    bug_id = "2052085"
    artefact_id = 22996
    requests_mock.get(
        "https://kernel.ubuntu.com/swm/status.json",
        json={
            "trackers": {
                bug_id: {
                    "test-observer": {
                        "beta": artefact_id,
                        "due-date": "2024-02-28",
                    }
                }
            }
        },
    )

    artefacts_swm_info = get_artefacts_swm_info()

    assert artefacts_swm_info == {
        artefact_id: {
            "bug_id": bug_id,
            "due_date": date(2024, 2, 28),
        }
    }

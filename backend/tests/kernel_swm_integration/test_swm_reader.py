# Copyright (C) 2023-2025 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


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
                    },
                    "task": {
                        "kernel-sru-workflow": {
                            "status": "In Progress",
                        }
                    },
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

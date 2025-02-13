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


from datetime import date, datetime
from typing import TypedDict

import requests

from test_observer.data_access.models_enums import StageName


class ArtefactTrackerInfo(TypedDict):
    bug_id: str
    due_date: date | None


def get_artefacts_swm_info() -> dict[int, ArtefactTrackerInfo]:
    json = _fetch_stable_workflow_manager_status()
    return _extract_artefact_bug_info_from_swm(json)


def _fetch_stable_workflow_manager_status() -> dict:
    url = "https://kernel.ubuntu.com/swm/status.json"
    return requests.get(url, timeout=30).json()


def _extract_artefact_bug_info_from_swm(json: dict) -> dict[int, ArtefactTrackerInfo]:
    result: dict[int, ArtefactTrackerInfo] = {}
    for bug_id, tracker in json["trackers"].items():
        artefact_id = _extract_artefact_id(tracker)

        if artefact_id and _is_tracker_open(tracker):
            result[artefact_id] = {
                "bug_id": bug_id,
                "due_date": _extract_due_date(tracker),
            }

    return result


def _is_tracker_open(tracker: dict) -> bool:
    closed_statuses = ("Fix Committed", "Fix Released")
    status = tracker.get("task", {}).get("kernel-sru-workflow", {}).get("status")
    return status and status not in closed_statuses


def _extract_artefact_id(tracker: dict) -> int | None:
    to_info = tracker.get("test-observer")
    if to_info:
        for stage in StageName:
            if stage in to_info:
                return to_info[stage]
    return None


def _extract_due_date(tracker: dict) -> date | None:
    date_string = tracker.get("test-observer", {}).get("due-date")
    if date_string:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    return None

from datetime import date, datetime
from typing import TypedDict

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact


class ArtefactTrackerInfo(TypedDict):
    bug_id: str
    due_date: date | None


def get_artefacts_swm_info(db: Session) -> dict[int, ArtefactTrackerInfo]:
    json = _fetch_stable_workflow_manager_status()
    return _extract_artefact_bug_info_from_swm(json, db)


def _fetch_stable_workflow_manager_status() -> dict:
    url = "https://kernel.ubuntu.com/swm/status.json"
    return requests.get(url, timeout=30).json()


def _extract_artefact_bug_info_from_swm(
    json: dict, db: Session
) -> dict[int, ArtefactTrackerInfo]:
    result: dict[int, ArtefactTrackerInfo] = {}
    stage_names = _get_stage_names(db)
    for bug_id, tracker in json["trackers"].items():
        artefact_id = _extract_artefact_id(tracker, stage_names)

        if artefact_id and _is_tracker_open(tracker):
            result[artefact_id] = {
                "bug_id": bug_id,
                "due_date": _extract_due_date(tracker),
            }

    return result


def _get_stage_names(db: Session) -> list[str]:
    return list(db.scalars(select(Artefact.stage).distinct()))


def _is_tracker_open(tracker: dict) -> bool:
    closed_statuses = ("Fix Committed", "Fix Released")
    status = tracker.get("task", {}).get("kernel-sru-workflow", {}).get("status")
    return status and status not in closed_statuses


def _extract_artefact_id(tracker: dict, stage_names: list[str]) -> int | None:
    to_info = tracker.get("test-observer")
    if to_info:
        for stages in stage_names:
            if stages in to_info:
                return to_info[stages]
    return None


def _extract_due_date(tracker: dict) -> date | None:
    date_string = tracker.get("test-observer", {}).get("due-date")
    if date_string:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    return None

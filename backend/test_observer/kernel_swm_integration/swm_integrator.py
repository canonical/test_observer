from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact

from .swm_reader import ArtefactTrackerInfo


def update_artefacts_with_tracker_info(
    db: Session, artefacts_tracker_info: dict[int, ArtefactTrackerInfo]
):
    stmt = select(Artefact).where(Artefact.id.in_(artefacts_tracker_info.keys()))
    artefacts = db.scalars(stmt)

    for artefact in artefacts:
        tracker_info = artefacts_tracker_info[artefact.id]
        artefact.due_date = tracker_info["due_date"]
        artefact.bug_link = _get_bug_link(tracker_info["bug_id"])

    db.commit()


def _get_bug_link(bug_id: str) -> str:
    return f"https://bugs.launchpad.net/kernel-sru-workflow/+bug/{bug_id}"

# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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

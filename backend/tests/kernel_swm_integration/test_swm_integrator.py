# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import date

from sqlalchemy.orm import Session

from test_observer.data_access.models_enums import FamilyName, StageName
from test_observer.kernel_swm_integration.swm_integrator import (
    update_artefacts_with_tracker_info,
)
from test_observer.kernel_swm_integration.swm_reader import ArtefactTrackerInfo
from tests.data_generator import DataGenerator


def test_update_artefacts_with_tracker_info(
    db_session: Session, generator: DataGenerator
):
    tracker_info_1: ArtefactTrackerInfo = {
        "bug_id": "1111111",
        "due_date": date(2024, 2, 28),
    }
    tracker_info_2: ArtefactTrackerInfo = {
        "bug_id": "2222222",
        "due_date": date(2024, 2, 20),
    }
    artefact1 = generator.gen_artefact(StageName.beta)
    artefact2 = generator.gen_artefact(StageName.proposed, family=FamilyName.deb)
    artefacts_swm_info = {artefact2.id: tracker_info_2, artefact1.id: tracker_info_1}

    update_artefacts_with_tracker_info(db_session, artefacts_swm_info)

    assert (
        artefact1.bug_link
        == f"https://bugs.launchpad.net/kernel-sru-workflow/+bug/{tracker_info_1['bug_id']}"
    )
    assert artefact1.due_date == tracker_info_1["due_date"]
    assert (
        artefact2.bug_link
        == f"https://bugs.launchpad.net/kernel-sru-workflow/+bug/{tracker_info_2['bug_id']}"
    )
    assert artefact2.due_date == tracker_info_2["due_date"]

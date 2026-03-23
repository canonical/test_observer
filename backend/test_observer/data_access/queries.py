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

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact, ArtefactBuild, ArtefactMatchingRule

latest_artefact_builds = (
    select(ArtefactBuild)
    .distinct(ArtefactBuild.artefact_id, ArtefactBuild.architecture)
    .order_by(
        ArtefactBuild.artefact_id,
        ArtefactBuild.architecture,
        ArtefactBuild.revision.desc(),
    )
)


def match_artefact(artefact: Artefact, db: Session) -> list[ArtefactMatchingRule]:
    family_str = artefact.family.value

    possible_rules = (
        db.execute(
            select(ArtefactMatchingRule).where(
                and_(
                    ArtefactMatchingRule.family == family_str,
                    or_(ArtefactMatchingRule.stage == artefact.stage, ArtefactMatchingRule.stage == ""),
                    or_(ArtefactMatchingRule.track == artefact.track, ArtefactMatchingRule.track == ""),
                    or_(ArtefactMatchingRule.branch == artefact.branch, ArtefactMatchingRule.branch == ""),
                ),
            )
        )
        .scalars()
        .all()
    )

    # sort rules by number of non-empty fields to prioritize specificity
    rules_with_score = [
        [r, sum(1 for field in [r.stage, r.track, r.branch] if field != "")] for r in possible_rules
    ]
    sorted_rules = sorted(rules_with_score, key=lambda x: x[1], reverse=True)
    highest_score = sorted_rules[0][1] if sorted_rules else 0
    rules = [r[0] for r in sorted_rules if r[1] == highest_score]

    return rules

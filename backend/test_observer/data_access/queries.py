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

from sqlalchemy import Select, and_, case, func, or_, select

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


def match_artefact_considering_specificity(artefact: Artefact) -> Select[tuple[int]]:
    """Match an artefact to the most specific AMR(s) based on the number of non-empty fields (stage, track, branch, name)."""
    # Calculate specificity score as the sum of non-empty fields
    specificity = (
        case((ArtefactMatchingRule.stage != "", 1), else_=0)
        + case((ArtefactMatchingRule.track != "", 1), else_=0)
        + case((ArtefactMatchingRule.branch != "", 1), else_=0)
        + case((ArtefactMatchingRule.name != "", 1), else_=0)
    )

    # Subquery to get the highest specificity score
    max_specificity_subquery = (
        select(func.max(specificity))
        .where(
            and_(
                ArtefactMatchingRule.family == artefact.family,
                or_(ArtefactMatchingRule.stage == artefact.stage, ArtefactMatchingRule.stage == ""),
                or_(ArtefactMatchingRule.track == artefact.track, ArtefactMatchingRule.track == ""),
                or_(ArtefactMatchingRule.branch == artefact.branch, ArtefactMatchingRule.branch == ""),
                or_(ArtefactMatchingRule.name == artefact.name, ArtefactMatchingRule.name == ""),
            )
        )
        .scalar_subquery()
    )

    # Select rules matching the highest specificity
    select_rules = select(ArtefactMatchingRule.id).where(
        and_(
            ArtefactMatchingRule.family == artefact.family,
            or_(ArtefactMatchingRule.stage == artefact.stage, ArtefactMatchingRule.stage == ""),
            or_(ArtefactMatchingRule.track == artefact.track, ArtefactMatchingRule.track == ""),
            or_(ArtefactMatchingRule.branch == artefact.branch, ArtefactMatchingRule.branch == ""),
            or_(ArtefactMatchingRule.name == artefact.name, ArtefactMatchingRule.name == ""),
            specificity == max_specificity_subquery,
        )
    )

    return select_rules


def match_artefact(artefact: Artefact) -> Select[tuple[int]]:
    """Match an artefact to all valid AMR(s)"""
    select_rules = select(ArtefactMatchingRule.id).where(
        and_(
            ArtefactMatchingRule.family == artefact.family,
            or_(ArtefactMatchingRule.stage == artefact.stage, ArtefactMatchingRule.stage == ""),
            or_(ArtefactMatchingRule.track == artefact.track, ArtefactMatchingRule.track == ""),
            or_(ArtefactMatchingRule.branch == artefact.branch, ArtefactMatchingRule.branch == ""),
            or_(ArtefactMatchingRule.name == artefact.name, ArtefactMatchingRule.name == ""),
        )
    )

    return select_rules

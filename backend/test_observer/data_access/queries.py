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

from sqlalchemy import Integer, Select, and_, case, false, func, literal, or_, select, union_all

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
    """Match an artefact to the most specific AMR(s)

    Based on the number of non-empty fields (stage, track, branch, name, store, series, os, release, owner)."""
    # Calculate specificity score as the sum of non-empty fields
    specificity = (
        case((ArtefactMatchingRule.stage != "", 1), else_=0)
        + case((ArtefactMatchingRule.track != "", 1), else_=0)
        + case((ArtefactMatchingRule.branch != "", 1), else_=0)
        + case((ArtefactMatchingRule.name != "", 1), else_=0)
        + case((ArtefactMatchingRule.store != "", 1), else_=0)
        + case((ArtefactMatchingRule.series != "", 1), else_=0)
        + case((ArtefactMatchingRule.os != "", 1), else_=0)
        + case((ArtefactMatchingRule.release != "", 1), else_=0)
        + case((ArtefactMatchingRule.owner != "", 1), else_=0)
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
                or_(
                    ArtefactMatchingRule.store == artefact.store,
                    ArtefactMatchingRule.store == "",
                ),
                or_(
                    ArtefactMatchingRule.series == artefact.series,
                    ArtefactMatchingRule.series == "",
                ),
                or_(
                    ArtefactMatchingRule.os == artefact.os,
                    ArtefactMatchingRule.os == "",
                ),
                or_(
                    ArtefactMatchingRule.release == artefact.release,
                    ArtefactMatchingRule.release == "",
                ),
                or_(
                    ArtefactMatchingRule.owner == artefact.owner,
                    ArtefactMatchingRule.owner == "",
                ),
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
            or_(
                ArtefactMatchingRule.store == artefact.store,
                ArtefactMatchingRule.store == "",
            ),
            or_(
                ArtefactMatchingRule.series == artefact.series,
                ArtefactMatchingRule.series == "",
            ),
            or_(
                ArtefactMatchingRule.os == artefact.os,
                ArtefactMatchingRule.os == "",
            ),
            or_(
                ArtefactMatchingRule.release == artefact.release,
                ArtefactMatchingRule.release == "",
            ),
            or_(
                ArtefactMatchingRule.owner == artefact.owner,
                ArtefactMatchingRule.owner == "",
            ),
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
            or_(
                ArtefactMatchingRule.store == artefact.store,
                ArtefactMatchingRule.store == "",
            ),
            or_(
                ArtefactMatchingRule.series == artefact.series,
                ArtefactMatchingRule.series == "",
            ),
            or_(
                ArtefactMatchingRule.os == artefact.os,
                ArtefactMatchingRule.os == "",
            ),
            or_(
                ArtefactMatchingRule.release == artefact.release,
                ArtefactMatchingRule.release == "",
            ),
            or_(
                ArtefactMatchingRule.owner == artefact.owner,
                ArtefactMatchingRule.owner == "",
            ),
        )
    )

    return select_rules


def batch_match_artefacts(artefacts: list[Artefact]) -> Select[tuple[int, int]]:
    """Match multiple artefacts to their AMRs in a single query.

    Returns a query that produces (artefact_id, amr_id) tuples for all matching pairs.
    This replaces calling match_artefact() N times with a single batched query.

    Args:
        artefacts: List of Artefact objects to match

    Returns:
        SQLAlchemy Select query returning (artefact_id, amr_id) tuples
    """
    if not artefacts:
        # Return empty result if no artefacts provided
        return select(literal(0, type_=Integer).label("artefact_id"), literal(0, type_=Integer).label("amr_id")).where(
            false()
        )

    # Build a SELECT for each artefact and UNION them
    queries = []
    for artefact in artefacts:
        query = select(
            literal(artefact.id, type_=Integer).label("artefact_id"),
            ArtefactMatchingRule.id.label("amr_id"),
        ).where(
            and_(
                ArtefactMatchingRule.family == artefact.family,
                or_(ArtefactMatchingRule.stage == artefact.stage, ArtefactMatchingRule.stage == ""),
                or_(ArtefactMatchingRule.track == artefact.track, ArtefactMatchingRule.track == ""),
                or_(ArtefactMatchingRule.branch == artefact.branch, ArtefactMatchingRule.branch == ""),
                or_(ArtefactMatchingRule.name == artefact.name, ArtefactMatchingRule.name == ""),
                or_(
                    ArtefactMatchingRule.store == artefact.store,
                    ArtefactMatchingRule.store == "",
                ),
                or_(
                    ArtefactMatchingRule.series == artefact.series,
                    ArtefactMatchingRule.series == "",
                ),
                or_(
                    ArtefactMatchingRule.os == artefact.os,
                    ArtefactMatchingRule.os == "",
                ),
                or_(
                    ArtefactMatchingRule.release == artefact.release,
                    ArtefactMatchingRule.release == "",
                ),
                or_(
                    ArtefactMatchingRule.owner == artefact.owner,
                    ArtefactMatchingRule.owner == "",
                ),
            )
        )
        queries.append(query)

    # UNION all queries into one
    return select(union_all(*queries).subquery())

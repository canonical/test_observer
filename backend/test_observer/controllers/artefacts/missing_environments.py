# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Report the environments an artefact is missing versus the C3 source of truth.

This is a family-specific external integration (C3 only knows about deb/snap) and
is acknowledged technical debt per the project's generic-platform design principle.
"""

import logging
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from test_observer.common.enums import Permission
from test_observer.common.helpers import get_artefact_url
from test_observer.common.permissions import permission_checker
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.queries import latest_artefact_builds
from test_observer.data_access.setup import get_db
from test_observer.external_apis import c3
from test_observer.external_apis.c3_models import TestingPool

from .models import MissingEnvironment, MissingEnvironmentsResponse

logger = logging.getLogger("test-observer-backend")

# Tags come from the parent artefacts router; setting them here duplicates them.
router = APIRouter()

# Families for which C3 has a source of truth (testing pools).
_C3_FAMILIES = {FamilyName.snap, FamilyName.deb}

# C3 pool metadata key -> Artefact attribute it must equal, per family.
# For both families the pocket/channel/risk maps to the artefact's stage.
_DEB_METADATA_FIELDS = {"kernel": "name", "series": "series", "repo": "repo", "source": "stage"}
_SNAP_METADATA_FIELDS = {"snap": "name", "track": "track", "channel": "stage", "store": "store"}
_METADATA_FIELDS = {FamilyName.deb: _DEB_METADATA_FIELDS, FamilyName.snap: _SNAP_METADATA_FIELDS}


@router.get(
    "/{artefact_id}/missing-environments",
    response_model=MissingEnvironmentsResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_artefact])],
)
def get_missing_environments(
    artefact_id: int,
    db: Session = Depends(get_db),
) -> MissingEnvironmentsResponse:
    artefact = db.get(Artefact, artefact_id)
    if artefact is None:
        raise HTTPException(status_code=404, detail=f"Artefact with id {artefact_id} not found")

    if FamilyName(artefact.family) not in _C3_FAMILIES:
        # No source of truth exists for this family.
        return MissingEnvironmentsResponse(missing_environments=[])

    try:
        pools = c3.get_testing_pools(artefact.family)
    except c3.C3NotConfiguredError:
        return MissingEnvironmentsResponse(missing_environments=[])
    except requests.RequestException as e:
        logger.exception("Failed to fetch testing pools from C3 for artefact %s", artefact_id)
        raise HTTPException(status_code=502, detail="Failed to reach the C3 source of truth") from e

    expected = resolve_expected_environments(artefact, pools)
    actual = _get_actual_environments(db, artefact_id)
    missing = sorted(expected - actual)

    previous_artefact_link = None
    if missing:
        previous = _get_previous_artefact(db, artefact)
        if previous is not None:
            previous_artefact_link = _build_filtered_link(previous, missing)

    return MissingEnvironmentsResponse(
        missing_environments=[MissingEnvironment(name=name, architecture=arch) for name, arch in missing],
        previous_artefact_link=previous_artefact_link,
    )


def resolve_expected_environments(
    artefact: Artefact,
    pools: list[TestingPool],
) -> set[tuple[str, str]]:
    """Resolve an artefact's expected environments from C3 pools as (name, arch) pairs.

    Each C3 pool validates exactly one artefact, matched by its structured
    ``metadata``. Each environment is returned with its architecture so the diff
    against the artefact's environments is architecture-aware. This function
    (with its helpers) owns the mapping.
    """
    expected: set[tuple[str, str]] = set()
    family = FamilyName(artefact.family)
    if family not in _C3_FAMILIES:
        return expected

    for pool in pools:
        if not _pool_matches_artefact(artefact, pool):
            continue

        for environment in pool.environments:
            expected.add((environment.name, environment.arch))

    return expected


def _pool_matches_artefact(artefact: Artefact, pool: TestingPool) -> bool:
    if pool.family != artefact.family:
        return False

    field_map = _METADATA_FIELDS.get(FamilyName(artefact.family))
    if field_map is None:
        return False

    # Require every expected metadata key to be present and equal; partial
    # metadata must not match (e.g. matching a snap by name while ignoring channel).
    return all(
        key in pool.metadata and pool.metadata[key] == getattr(artefact, attr) for key, attr in field_map.items()
    )


def _get_actual_environments(db: Session, artefact_id: int) -> set[tuple[str, str]]:
    latest_builds = db.scalars(
        latest_artefact_builds.where(ArtefactBuild.artefact_id == artefact_id).options(
            selectinload(ArtefactBuild.environment_reviews).selectinload(ArtefactBuildEnvironmentReview.environment)
        )
    ).all()
    return {
        (review.environment.name, review.environment.architecture)
        for build in latest_builds
        for review in build.environment_reviews
    }


def _get_previous_artefact(db: Session, artefact: Artefact) -> Artefact | None:
    """The version immediately preceding the given artefact, or None."""
    return db.scalars(
        select(Artefact)
        .where(Artefact.family == artefact.family)
        .where(Artefact.name == artefact.name)
        .where(Artefact.track == artefact.track)
        .where(Artefact.branch == artefact.branch)
        .where(Artefact.series == artefact.series)
        .where(Artefact.repo == artefact.repo)
        .where(Artefact.os == artefact.os)
        .where(Artefact.release == artefact.release)
        .where(Artefact.source == artefact.source)
        .where(Artefact.bundled_builds_hash == artefact.bundled_builds_hash)
        .where(Artefact.id < artefact.id)
        .order_by(Artefact.id.desc())
        .limit(1)
    ).first()


def _build_filtered_link(artefact: Artefact, environments: list[tuple[str, str]]) -> str:
    # The frontend Environment filter is keyed on name, so dedupe names (an env
    # missing on multiple arches only needs one filter entry) while preserving order.
    names = list(dict.fromkeys(name for name, _arch in environments))
    query = urlencode([("Environment", name) for name in names])
    return f"{get_artefact_url(artefact)}?{query}"

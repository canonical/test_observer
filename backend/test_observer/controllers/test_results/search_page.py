# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import base64
import binascii
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Security
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, load_only, raiseload

from test_observer.common.config import MAX_RESULT_PAGE_LIMIT
from test_observer.common.constants import QueryValue
from test_observer.common.enums import Permission
from test_observer.common.permissions import permission_checker
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestCase,
    TestExecution,
    TestPlan,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName, TestExecutionStatus, TestResultStatus
from test_observer.data_access.setup import get_db

from .filter_test_results import filter_test_results
from .search_page_models import (
    SearchPageArtefact,
    SearchPageArtefactBuild,
    SearchPageEnvironment,
    SearchPageTestExecution,
    SearchPageTestResult,
    TestResultSearchPage,
    TestResultSearchPageRow,
)
from .shared_models import TestResultSearchFilters

router = APIRouter(tags=["test-results"])


@router.get(
    "/search-page",
    response_model=TestResultSearchPage,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_test_results_search_page(
    request: Request,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_RESULT_PAGE_LIMIT, description="Maximum number of results to return"),
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    include_count: Annotated[
        bool,
        Query(description="Include the exact total count; null is returned when false"),
    ] = True,
    families: Annotated[
        list[FamilyName] | None, Query(description="Exact artefact family values; repeat for OR")
    ] = None,
    artefact_ids: Annotated[list[int] | None, Query(description="Exact artefact IDs; repeat for OR")] = None,
    test_result_statuses: Annotated[
        list[TestResultStatus] | None,
        Query(description="Exact result status values; repeat for OR"),
    ] = None,
    artefacts: Annotated[list[str] | None, Query(description="Exact artefact names; repeat for OR")] = None,
    artefact_versions: Annotated[list[str] | None, Query(description="Exact artefact versions; repeat for OR")] = None,
    artefact_stages: Annotated[
        list[str] | None,
        Query(description="Exact artefact stages; repeat for OR; an empty value matches an empty stage"),
    ] = None,
    artefact_tracks: Annotated[list[str] | None, Query(description="Exact artefact tracks; repeat for OR")] = None,
    artefact_is_archived: Annotated[
        bool | None,
        Query(description="Filter by whether the artefact is archived; use lowercase true or false"),
    ] = None,
    environments: Annotated[list[str] | None, Query(description="Exact environment names; repeat for OR")] = None,
    test_cases: Annotated[list[str] | None, Query(description="Exact test case names; repeat for OR")] = None,
    test_plans: Annotated[list[str] | None, Query(description="Exact test plan names; repeat for OR")] = None,
    test_execution_statuses: Annotated[
        list[TestExecutionStatus] | None,
        Query(description="Exact execution status values; repeat for OR"),
    ] = None,
    rerun_is_requested: Annotated[
        bool | None,
        Query(description="Filter by whether a rerun is requested for the execution group"),
    ] = None,
    execution_is_latest: Annotated[
        bool | None,
        Query(description="Filter using the existing execution-group latest-ID semantics"),
    ] = None,
    template_ids: Annotated[list[str] | None, Query(description="Exact test case template IDs; repeat for OR")] = None,
    issues: Annotated[
        list[str] | None,
        Query(description="Positive issue IDs (repeat for OR), or a sole any/none attachment sentinel"),
    ] = None,
    reviewer_ids: Annotated[
        list[str] | None,
        Query(description="Positive reviewer IDs (repeat for OR), or a sole any/none sentinel"),
    ] = None,
    execution_metadata: Annotated[
        list[str] | None,
        Query(description="Base64 UTF-8 category:value pairs; repeat for OR within a category"),
    ] = None,
    from_date: Annotated[datetime | None, Query(description="Inclusive UTC lower bound on result created_at")] = None,
    until_date: Annotated[datetime | None, Query(description="Inclusive UTC upper bound on result created_at")] = None,
    db: Session = Depends(get_db),
) -> TestResultSearchPage:
    """Return a bounded, server-filtered page of compact results, newest first.

    Repeated list values are exact-match ORs; distinct filters are ANDed. An explicit empty
    ``artefact_stages=`` matches an empty stage. Issue and reviewer filters accept positive IDs
    or a sole ``any``/``none`` sentinel. Execution metadata uses repeated Base64 UTF-8
    ``category:value`` pairs, ORed within each category and ANDed across categories. Optional
    booleans use canonical lowercase ``true``/``false``. ``count`` is exact and independent of
    the requested page. It is null when ``include_count`` is false. Unsupported query keys and
    invalid date ranges are rejected instead of being silently ignored.
    """
    supported_keys = {
        "limit",
        "offset",
        "include_count",
        "families",
        "artefact_ids",
        "test_result_statuses",
        "artefacts",
        "artefact_versions",
        "artefact_stages",
        "artefact_tracks",
        "artefact_is_archived",
        "environments",
        "test_cases",
        "test_plans",
        "test_execution_statuses",
        "rerun_is_requested",
        "execution_is_latest",
        "template_ids",
        "issues",
        "reviewer_ids",
        "execution_metadata",
        "from_date",
        "until_date",
    }
    unknown_keys = sorted(set(request.query_params.keys()) - supported_keys)
    if unknown_keys:
        raise HTTPException(status_code=422, detail=f"Unsupported query parameter(s): {', '.join(unknown_keys)}")
    scalar_keys = (
        "limit",
        "offset",
        "include_count",
        "artefact_is_archived",
        "rerun_is_requested",
        "execution_is_latest",
        "from_date",
        "until_date",
    )
    for key in scalar_keys:
        if len(request.query_params.getlist(key)) > 1:
            raise HTTPException(status_code=422, detail=f"Provide at most one {key} value")

    for key in ("artefact_is_archived", "rerun_is_requested", "execution_is_latest"):
        values = request.query_params.getlist(key)
        if values and values[0] not in {"true", "false"}:
            raise HTTPException(status_code=422, detail=f"{key} must be lowercase true or false")

    def as_utc(value: datetime | None, name: str) -> datetime | None:
        if value is None:
            return None
        if value.utcoffset() is None:
            raise HTTPException(status_code=422, detail=f"{name} must include a UTC offset")
        return value.astimezone(UTC)

    from_utc = as_utc(from_date, "from_date")
    until_utc = as_utc(until_date, "until_date")
    if from_utc is not None and until_utc is not None and from_utc > until_utc:
        raise HTTPException(status_code=422, detail="from_date must not be after until_date")

    list_values = {
        "artefacts": artefacts,
        "artefact_versions": artefact_versions,
        "artefact_stages": artefact_stages,
        "artefact_tracks": artefact_tracks,
        "environments": environments,
        "test_cases": test_cases,
        "test_plans": test_plans,
        "template_ids": template_ids,
    }
    if any(
        value.strip() == "" and not (key == "artefact_stages" and value == "")
        for key, values in list_values.items()
        for value in (values or [])
    ):
        raise HTTPException(status_code=422, detail="Filter values must not be empty")

    def parse_id_filter(
        name: str,
        parsed_values: list[str] | None,
    ) -> list[int] | Literal[QueryValue.ANY, QueryValue.NONE]:
        raw_values = request.query_params.getlist(name)
        if not raw_values:
            return []
        if parsed_values is None or parsed_values != raw_values:
            raise HTTPException(status_code=422, detail=f"Invalid {name} filter values")
        values = parsed_values
        if values == ["any"]:
            return QueryValue.ANY
        if values == ["none"]:
            return QueryValue.NONE
        if any(value in {"any", "none"} for value in values):
            raise HTTPException(status_code=422, detail=f"{name} any/none must be the sole value")
        parsed: list[int] = []
        for value in values:
            if not value.isascii() or not value.isdecimal() or value.startswith("0") or len(value) > 10:
                raise HTTPException(status_code=422, detail=f"{name} values must be positive integer IDs")
            identifier = int(value)
            if identifier <= 0 or identifier > 2_147_483_647:
                raise HTTPException(status_code=422, detail=f"{name} values must be positive supported integer IDs")
            parsed.append(identifier)
        return list(dict.fromkeys(parsed))

    def parse_metadata(values: list[str] | None) -> dict[str, list[str]]:
        metadata: dict[str, list[str]] = {}
        for item in values or []:
            if item.count(":") != 1:
                raise HTTPException(status_code=422, detail="execution_metadata must use base64 category:value pairs")
            encoded_category, encoded_value = item.split(":", 1)
            try:
                category_bytes = base64.b64decode(encoded_category, validate=True)
                value_bytes = base64.b64decode(encoded_value, validate=True)
                if (
                    base64.b64encode(category_bytes).decode("ascii") != encoded_category
                    or base64.b64encode(value_bytes).decode("ascii") != encoded_value
                ):
                    raise ValueError("noncanonical base64")
                category = category_bytes.decode("utf-8")
                value = value_bytes.decode("utf-8")
            except (binascii.Error, UnicodeDecodeError, ValueError) as error:
                raise HTTPException(
                    status_code=422,
                    detail="execution_metadata must contain canonical base64 UTF-8",
                ) from error
            if not (1 <= len(category) <= 200 and 1 <= len(value) <= 200):
                raise HTTPException(
                    status_code=422,
                    detail="execution_metadata categories and values must contain 1–200 characters",
                )
            bucket = metadata.setdefault(category, [])
            if value not in bucket:
                bucket.append(value)
        return metadata

    parsed_issues = parse_id_filter("issues", issues)
    parsed_reviewers = parse_id_filter("reviewer_ids", reviewer_ids)
    metadata_values = ExecutionMetadata(parse_metadata(execution_metadata))

    filters = TestResultSearchFilters(
        families=families or [],
        artefact_ids=artefact_ids or [],
        test_result_statuses=test_result_statuses or [],
        artefacts=artefacts or [],
        artefact_versions=artefact_versions or [],
        artefact_stages=artefact_stages or [],
        artefact_tracks=artefact_tracks or [],
        artefact_is_archived=artefact_is_archived,
        environments=environments or [],
        test_cases=test_cases or [],
        template_ids=template_ids or [],
        test_plans=test_plans or [],
        execution_metadata=metadata_values,
        issues=parsed_issues,
        test_execution_statuses=test_execution_statuses or [],
        reviewer_ids=parsed_reviewers,
        rerun_is_requested=rerun_is_requested,
        execution_is_latest=execution_is_latest,
        from_date=from_utc,
        until_date=until_utc,
    )

    count = None
    count_query = filter_test_results(
        select(func.count()).select_from(TestResult),
        filters.model_copy(update={"offset": None, "limit": None}),
    )
    if include_count:
        count = db.execute(count_query).scalar_one()

    stmt = (
        filter_test_results(
            select(TestResult),
            filters.model_copy(update={"offset": offset, "limit": limit}),
        )
        .options(
            load_only(
                TestResult.id,
                TestResult.created_at,
                TestResult.status,
                TestResult.test_case_id,
                TestResult.test_execution_id,
                raiseload=True,
            ),
            joinedload(TestResult.test_case).load_only(
                TestCase.id,
                TestCase.name,
                TestCase.category,
                raiseload=True,
            ),
            joinedload(TestResult.test_execution)
            .load_only(
                TestExecution.id,
                TestExecution.artefact_build_id,
                TestExecution.environment_id,
                TestExecution.test_plan_id,
                raiseload=True,
            )
            .joinedload(TestExecution.environment)
            .load_only(
                Environment.id,
                Environment.name,
                raiseload=True,
            ),
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.test_plan)
            .load_only(TestPlan.id, TestPlan.name, raiseload=True),
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.artefact_build)
            .load_only(
                ArtefactBuild.id,
                ArtefactBuild.artefact_id,
                ArtefactBuild.architecture,
                raiseload=True,
            )
            .joinedload(ArtefactBuild.artefact)
            .load_only(
                Artefact.id,
                Artefact.name,
                Artefact.version,
                Artefact.track,
                Artefact.family,
                raiseload=True,
            ),
            raiseload("*"),
        )
        .order_by(desc(TestResult.created_at), desc(TestResult.id))
    )
    results = db.execute(stmt).scalars().all()

    return TestResultSearchPage(
        count=count,
        limit=limit,
        offset=offset,
        test_results=[
            TestResultSearchPageRow(
                test_result=SearchPageTestResult(
                    id=result.id,
                    created_at=result.created_at,
                    name=result.test_case.name,
                    category=result.test_case.category,
                    status=result.status,
                ),
                test_execution=SearchPageTestExecution(
                    id=result.test_execution.id,
                    environment=SearchPageEnvironment(
                        name=result.test_execution.environment.name,
                    ),
                    test_plan=result.test_execution.test_plan.name,
                ),
                artefact=SearchPageArtefact(
                    id=result.test_execution.artefact_build.artefact.id,
                    name=result.test_execution.artefact_build.artefact.name,
                    version=result.test_execution.artefact_build.artefact.version,
                    track=result.test_execution.artefact_build.artefact.track,
                    family=FamilyName(result.test_execution.artefact_build.artefact.family),
                ),
                artefact_build=SearchPageArtefactBuild(
                    architecture=result.test_execution.artefact_build.architecture,
                ),
            )
            for result in results
        ],
    )

# Copyright (C) 2024 Canonical Ltd.
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

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, distinct, select, func
from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestExecution,
    TestResult,
    TestCase,
    Issue,
    IssueTestResultAttachment,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

from .models import TestResultSearchResponse

router = APIRouter(tags=["test-results"])


@router.get("", response_model=TestResultSearchResponse)
def search_test_results(
    family: str | None = Query(
        None, description="Filter by artefact family (e.g., Charm, Snap)"
    ),
    environment: str | None = Query(
        None,
        description="Filter by environment name (e.g., Juju:3/stable ubuntu:20.04)",
    ),
    test_case: str | None = Query(
        None, description="Filter by test case name (e.g., test_deploy)"
    ),
    template_id: str | None = Query(None, description="Filter by template ID"),
    issues: str | None = Query(
        None, description="Filter by Jira or GitHub issue IDs (comma-separated)"
    ),
    from_date: datetime | None = Query(
        None, description="Filter results from this timestamp"
    ),
    until: datetime | None = Query(
        None, description="Filter results until this timestamp"
    ),
    limit: int = Query(
        50, ge=1, le=1000, description="Maximum number of results to return"
    ),
    offset: int = Query(
        0, ge=0, description="Number of results to skip for pagination"
    ),
    db: Session = Depends(get_db),
) -> TestResultSearchResponse:
    """
    Search test results across artefacts using flexible filters.

    This endpoint uses a single optimized query with window functions to get both
    the total count and paginated results in one database round trip.
    """

    # Build filters
    filters = []

    if family:
        try:
            family_enum = FamilyName(family.lower())
            filters.append(Artefact.family == family_enum)
        except ValueError:
            filters.append(Artefact.family.is_(None))

    if environment:
        filters.append(Environment.name.ilike(f"%{environment}%"))

    if test_case:
        filters.append(TestCase.name.ilike(f"%{test_case}%"))

    if template_id:
        filters.append(TestCase.template_id == template_id)

    if issues:
        # Handle multiple issue IDs separated by commas
        issue_list = [issue.strip() for issue in issues.split(",") if issue.strip()]
        if issue_list:
            try:
                issue_ids = [int(issue_id) for issue_id in issue_list]
                filters.append(
                    TestResult.id.in_(
                        select(IssueTestResultAttachment.test_result_id)
                        .join(IssueTestResultAttachment.issue)
                        .where(Issue.id.in_(issue_ids))
                    )
                )
            except ValueError:
                return TestResultSearchResponse(count=0, test_results=[])

    if from_date:
        filters.append(TestExecution.created_at >= from_date)

    if until:
        filters.append(TestExecution.created_at <= until)

    # Build the main query with window function for total count in a single query
    query = (
        select(TestResult, func.count().over().label("total_count"))
        .join(TestResult.test_execution)
        .join(TestExecution.environment)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestResult.test_case)
        .options(
            joinedload(TestResult.test_execution).joinedload(TestExecution.environment),
            joinedload(TestResult.test_execution)
            .joinedload(TestExecution.artefact_build)
            .joinedload(ArtefactBuild.artefact),
            joinedload(TestResult.test_case),
        )
        .order_by(desc(TestExecution.created_at), desc(TestResult.id))
        .offset(offset)
        .limit(limit)
    )

    # Apply all filters
    if filters:
        query = query.where(and_(*filters))

    result = db.execute(query).all()

    if result:
        test_results = [row[0] for row in result]
        total_count = result[0][1]
    else:
        test_results = []
        total_count = 0

    return TestResultSearchResponse(count=total_count, test_results=test_results)


@router.get("/families", response_model=list[str])
def get_families(db: Session = Depends(get_db)) -> list[str]:
    """
    Returns all families that have test results.
    """
    families = (
        db.execute(
            select(distinct(Artefact.family))
            .join(ArtefactBuild)
            .join(TestExecution)
            .join(TestResult)
            .order_by(Artefact.family)
        )
        .scalars()
        .all()
    )

    return [family.value for family in families]


@router.get("/environments", response_model=list[str])
def get_environments(
    family: str | None = Query(None, description="Filter environments by family"),
    test_case: str | None = Query(
        None, description="Filter environments by test case"
    ),
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Returns list of distinct environments, optionally filtered by other criteria.
    """

    query = (
        select(distinct(Environment.name))
        .join(TestExecution)
        .join(TestResult)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestResult.test_case)
    )

    # Apply cascading filters
    if family:
        try:
            family_enum = FamilyName(family.lower())
            query = query.where(Artefact.family == family_enum)
        except ValueError:
            return []  # Invalid family

    if test_case:
        query = query.where(TestCase.name.ilike(f"%{test_case}%"))

    query = query.order_by(Environment.name)

    environments = db.execute(query).scalars().all()
    return list(environments)


@router.get("/test-cases", response_model=list[str])
def get_test_cases(
    family: str | None = Query(None, description="Filter test cases by family"),
    environment: str | None = Query(
        None, description="Filter test cases by environment"
    ),
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Returns all test cases, optionally filtered by other criteria.
    """

    query = (
        select(distinct(TestCase.name))
        .join(TestResult)
        .join(TestResult.test_execution)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestExecution.environment)
    )

    # Apply cascading filters
    if family:
        try:
            family_enum = FamilyName(family.lower())
            query = query.where(Artefact.family == family_enum)
        except ValueError:
            return []

    if environment:
        query = query.where(Environment.name.ilike(f"%{environment}%"))

    query = query.order_by(TestCase.name)

    test_cases = db.execute(query).scalars().all()
    return list(test_cases)


@router.get("/issues", response_model=list[dict])
def get_issues(
    family: str | None = Query(None, description="Filter issues by family"),
    environment: str | None = Query(
        None, description="Filter issues by environment"
    ),
    test_case: str | None = Query(None, description="Filter issues by test case"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Returns all known issues, optionally filtered by other criteria.
    """

    query = (
        select(
            distinct(Issue.id),
            Issue.url,
            Issue.title,
            Issue.source,
            Issue.project,
            Issue.key,
        )
        .join(IssueTestResultAttachment)
        .join(TestResult)
        .join(TestResult.test_execution)
        .join(TestExecution.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestExecution.environment)
        .join(TestResult.test_case)
    )

    # Apply cascading filters
    if family:
        try:
            family_enum = FamilyName(family.lower())
            query = query.where(Artefact.family == family_enum)
        except ValueError:
            return []

    if environment:
        query = query.where(Environment.name.ilike(f"%{environment}%"))

    if test_case:
        query = query.where(TestCase.name.ilike(f"%{test_case}%"))

    query = query.order_by(Issue.id.desc())

    issues = db.execute(query).all()

    return [
        {
            "id": issue.id,
            "url": issue.url,
            "title": issue.title,
            "display_name": (
                f"{issue.source.value.upper()}-{issue.project}-{issue.key}: "
                f"{issue.title}"
            )[:100],
        }
        for issue in issues
    ]

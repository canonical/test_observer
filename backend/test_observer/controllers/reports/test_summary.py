# Copyright (C) 2025 Canonical Ltd.
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

from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.setup import get_db

router = APIRouter()


class TestSummaryItem(BaseModel):
    test_identifier: str
    total: int
    failed: int
    passed: int
    skipped: int


class TestSummaryResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    total_tests: int
    total_executions: int
    summary: list[TestSummaryItem]


@router.get("/test-summary", response_model=TestSummaryResponse)
def get_test_summary(
    start_date: datetime = datetime.min,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    """
    Returns an aggregated summary of test results within a given date range.
    Similar to the sample script but returns JSON instead of CSV.
    """
    if end_date is None:
        end_date = datetime.now()

    # Query for test results with all necessary joins
    results = db.execute(
        select(
            TestCase.template_id,
            TestCase.name,
            TestResult.status,
            Artefact.family,
        )
        .join_from(Artefact, ArtefactBuild)
        .join_from(ArtefactBuild, TestExecution)
        .join_from(TestExecution, TestResult)
        .join_from(TestResult, TestCase)
        .where(
            TestResult.created_at >= start_date,
            TestResult.created_at <= end_date,
            Artefact.family.in_(["snap", "deb"]),  # Filter for relevant families
            ~TestCase.name.contains("mir"),  # Exclude mir tests
        )
    )

    # Aggregate results by test identifier
    test_summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {"FAILED": 0, "PASSED": 0, "SKIPPED": 0}
    )
    
    total_executions = 0
    for row in results:
        test_identifier = row.template_id if row.template_id else row.name
        test_summary[test_identifier][row.status] += 1
        total_executions += 1

    # Convert to response format
    summary_items = []
    for test_id, counts in test_summary.items():
        summary_items.append(
            TestSummaryItem(
                test_identifier=test_id,
                total=counts["FAILED"] + counts["PASSED"],
                failed=counts["FAILED"],
                passed=counts["PASSED"],
                skipped=counts["SKIPPED"],
            )
        )

    # Sort by total count descending
    summary_items.sort(key=lambda x: x.total, reverse=True)

    return TestSummaryResponse(
        start_date=start_date,
        end_date=end_date,
        total_tests=len(summary_items),
        total_executions=total_executions,
        summary=summary_items,
    )


class ArtefactStatusCount(BaseModel):
    status: str
    count: int


class ArtefactSummaryResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    by_family: dict[str, list[ArtefactStatusCount]]
    total_artefacts: int
    recent_artefacts: list[dict[str, Any]]


@router.get("/artefact-summary", response_model=ArtefactSummaryResponse)
def get_artefact_summary(
    start_date: datetime = datetime.min,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    """
    Returns a summary of artefacts by family and status within a given date range.
    """
    if end_date is None:
        end_date = datetime.now()

    # Query for artefact counts by family and status
    results = db.execute(
        select(
            Artefact.family,
            Artefact.status,
            Artefact.name,
            Artefact.version,
            Artefact.created_at,
        )
        .where(
            Artefact.created_at >= start_date,
            Artefact.created_at <= end_date,
        )
        .order_by(Artefact.created_at.desc())
    )

    # Aggregate by family and status
    by_family: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    recent_artefacts = []
    total_count = 0
    
    for row in results:
        by_family[row.family][row.status] += 1
        total_count += 1
        
        # Keep first 10 recent artefacts
        if len(recent_artefacts) < 10:
            recent_artefacts.append({
                "family": row.family,
                "name": row.name,
                "version": row.version,
                "status": row.status,
                "created_at": row.created_at,
            })

    # Convert to response format
    family_summary = {}
    for family, status_counts in by_family.items():
        family_summary[family] = [
            ArtefactStatusCount(status=status, count=count)
            for status, count in status_counts.items()
        ]

    return ArtefactSummaryResponse(
        start_date=start_date,
        end_date=end_date,
        by_family=family_summary,
        total_artefacts=total_count,
        recent_artefacts=recent_artefacts,
    )
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

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    TestCase,
    TestCaseIssue,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import FamilyName
from test_observer.data_access.setup import get_db

router = APIRouter()


@router.get("/test-summary")
def get_test_summary_report(
    start_date: datetime = Query(default=datetime.min),
    end_date: datetime = Query(default_factory=datetime.now),
    families: list[str] = Query(default=['snap', 'deb']),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns an optimized test summary report with aggregated data.
    
    This endpoint performs database-level aggregation instead of transferring
    all test results to the frontend for processing.
    """
    
    # Validate families
    valid_families = [f.value for f in FamilyName if f.value in families]
    if not valid_families:
        valid_families = ['snap', 'deb']
    
    # Build the optimized aggregation query
    # This query does all the heavy lifting in the database
    query = (
        select(
            # Group by test identifier (prefer template_id, fallback to name)
            func.coalesce(
                func.nullif(TestCase.template_id, ''), 
                TestCase.name
            ).label('test_identifier'),
            
            # Aggregate counts by status
            func.count(TestResult.id).label('total'),
            func.sum(
                case((TestResult.status == 'PASSED', 1), else_=0)
            ).label('passed'),
            func.sum(
                case((TestResult.status == 'FAILED', 1), else_=0)
            ).label('failed'),
            func.sum(
                case((TestResult.status == 'SKIPPED', 1), else_=0)
            ).label('skipped'),
        )
        .select_from(TestResult)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestExecution, TestResult.test_execution_id == TestExecution.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .where(
            and_(
                Artefact.created_at >= start_date,
                Artefact.created_at <= end_date,
                Artefact.family.in_(valid_families),
                # Exclude mir tests as done in the frontend processing
                ~TestCase.name.contains('mir')
            )
        )
        .group_by('test_identifier')
        .order_by(func.count(TestResult.id).desc())
    )
    
    # Execute the query
    result = db.execute(query).fetchall()
    
    # Convert to the expected format
    summary_items = []
    total_executions = 0
    
    for row in result:
        # Exclude skipped from total like frontend
        total_count = row.passed + row.failed
        summary_items.append({
            'test_identifier': row.test_identifier,
            'total': total_count,
            'passed': row.passed,
            'failed': row.failed,
            'skipped': row.skipped,
        })
        total_executions += row.total
    
    # Get aggregate statistics
    total_tests = len(summary_items)
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_tests': total_tests,
        'total_executions': total_executions,
        'summary': summary_items,
    }


@router.post("/test-summary/batch-issues-check")
def batch_check_test_case_issues(
    test_identifiers: list[str] = Body(..., embed=True),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """
    Efficiently check which test cases have reported issues.
    
    Returns a mapping of test_identifier -> has_issues (bool).
    """
    
    # Query all issues for the given test identifiers in one database call
    issues_query = (
        select(TestCase.template_id, TestCase.name)
        .select_from(TestCase)
        .join(TestCaseIssue, or_(
            and_(
                TestCase.template_id == TestCaseIssue.template_id, 
                TestCaseIssue.template_id != ''
            ),
            and_(TestCase.name == TestCaseIssue.case_name, TestCaseIssue.case_name != '')
        ))
        .where(or_(
            TestCase.template_id.in_(test_identifiers),
            TestCase.name.in_(test_identifiers)
        ))
        .distinct()
    )
    
    # Execute query and collect identifiers that have issues
    result = db.execute(issues_query).fetchall()
    identifiers_with_issues = set()
    
    for row in result:
        # Add both template_id and name to cover all cases
        if row.template_id:
            identifiers_with_issues.add(row.template_id)
        if row.name:
            identifiers_with_issues.add(row.name)
    
    # Build response mapping
    response = {}
    for identifier in test_identifiers:
        response[identifier] = identifier in identifiers_with_issues
    
    return response
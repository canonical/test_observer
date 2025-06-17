# Copyright (C) 2023 Canonical Ltd.
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
from fastapi import APIRouter, Depends
from sqlalchemy import select, and_, or_, func, distinct
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    TestCaseIssue, TestCase, TestResult, TestExecution, ArtefactBuild, Artefact, Environment
)
from test_observer.data_access.setup import get_db

from .models import TestReportedIssueRequest, TestReportedIssueResponse

router = APIRouter()


endpoint = "/reported-issues"


@router.get(endpoint)
def get_reported_issues(
    template_id: str | None = None,
    case_name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    # Get basic issue data
    stmt = select(TestCaseIssue)
    if template_id:
        stmt = stmt.where(TestCaseIssue.template_id == template_id)
    if case_name:
        stmt = stmt.where(TestCaseIssue.case_name == case_name)
    if start_date:
        stmt = stmt.where(TestCaseIssue.created_at >= start_date)
    if end_date:
        stmt = stmt.where(TestCaseIssue.created_at <= end_date)
    
    issues = list(db.execute(stmt).scalars())
    
    # For each issue, calculate the failure combinations count
    result = []
    for issue in issues:
        # Query to count distinct (artefact, environment) combinations with failures for this issue
        failure_combinations_query = (
            select(func.count(distinct(func.concat(Artefact.id, '-', Environment.id))))
            .select_from(TestCaseIssue)
            .join(TestCase, or_(
                and_(TestCase.template_id == TestCaseIssue.template_id, TestCaseIssue.template_id != ''),
                and_(TestCase.name == TestCaseIssue.case_name, TestCaseIssue.case_name != '')
            ))
            .join(TestResult, TestResult.test_case_id == TestCase.id)
            .join(TestExecution, TestResult.test_execution_id == TestExecution.id)
            .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
            .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
            .join(Environment, TestExecution.environment_id == Environment.id)
            .where(and_(
                TestCaseIssue.id == issue.id,
                TestResult.status == 'FAILED'
            ))
        )
        
        failure_count = db.execute(failure_combinations_query).scalar() or 0
        
        # Convert to dict and add failure count
        issue_dict = {
            'id': issue.id,
            'template_id': issue.template_id,
            'case_name': issue.case_name,
            'description': issue.description,
            'url': str(issue.url),
            'created_at': issue.created_at,
            'updated_at': issue.updated_at,
            'external_id': issue.external_id,
            'issue_status': issue.issue_status,
            'sync_status': issue.sync_status,
            'last_synced_at': issue.last_synced_at,
            'sync_error': issue.sync_error,
            'failure_combinations_count': failure_count
        }
        result.append(issue_dict)
    
    return result


@router.post(endpoint, response_model=TestReportedIssueResponse)
def create_reported_issue(
    request: TestReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = TestCaseIssue(
        template_id=request.template_id,
        url=request.url,
        description=request.description,
        case_name=request.case_name,
    )
    db.add(issue)
    db.commit()

    return issue


@router.put(endpoint + "/{issue_id}", response_model=TestReportedIssueResponse)
def update_reported_issue(
    issue_id: int, request: TestReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = db.get(TestCaseIssue, issue_id)
    for field in request.model_fields:
        setattr(issue, field, getattr(request, field))
    db.commit()
    return issue


@router.delete(endpoint + "/{issue_id}")
def delete_reported_issue(issue_id: int, db: Session = Depends(get_db)):
    db.delete(db.get(TestCaseIssue, issue_id))
    db.commit()


@router.get(endpoint + "/{issue_id}/affected-artefacts")
def get_affected_artefacts(issue_id: int, db: Session = Depends(get_db)):
    """
    Get artefacts affected by a specific test case issue.
    
    Returns artefacts that have test results matching the test cases 
    associated with the given issue.
    """
    # Query to find artefacts affected by the issue
    affected_artefacts_query = (
        select(
            Artefact.id.label('artefact_id'),
            Artefact.name.label('artefact_name'), 
            Artefact.version.label('artefact_version'),
            Artefact.family.label('artefact_family'),
            Artefact.due_date.label('artefact_due_date'),
            Environment.name.label('environment_name'),
            TestResult.status.label('test_result_status'),
            TestExecution.id.label('test_execution_id')
        )
        .select_from(TestCaseIssue)
        .join(TestCase, or_(
            and_(TestCase.template_id == TestCaseIssue.template_id, TestCaseIssue.template_id != ''),
            and_(TestCase.name == TestCaseIssue.case_name, TestCaseIssue.case_name != '')
        ))
        .join(TestResult, TestResult.test_case_id == TestCase.id)
        .join(TestExecution, TestResult.test_execution_id == TestExecution.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .join(Environment, TestExecution.environment_id == Environment.id)
        .where(TestCaseIssue.id == issue_id)
        .distinct()
    )
    
    results = db.execute(affected_artefacts_query).fetchall()
    
    # Group results by artefact and track success/failure status
    artefacts_dict = {}
    for row in results:
        artefact_key = f"{row.artefact_id}"
        if artefact_key not in artefacts_dict:
            artefacts_dict[artefact_key] = {
                'id': row.artefact_id,
                'name': row.artefact_name,
                'version': row.artefact_version,
                'family': row.artefact_family,
                'due_date': row.artefact_due_date.isoformat() if row.artefact_due_date else None,
                'environments': set(),
                'has_failures': False,
                'test_executions': []
            }
        
        artefacts_dict[artefact_key]['environments'].add(row.environment_name)
        artefacts_dict[artefact_key]['test_executions'].append({
            'test_execution_id': row.test_execution_id,
            'environment_name': row.environment_name,
            'test_result_status': row.test_result_status
        })
        
        # Track environments by success/failure status
        if 'success_environments' not in artefacts_dict[artefact_key]:
            artefacts_dict[artefact_key]['success_environments'] = set()
            artefacts_dict[artefact_key]['failure_environments'] = set()
        
        # Track environment-specific results
        if row.test_result_status == 'FAILED':
            artefacts_dict[artefact_key]['has_failures'] = True
            artefacts_dict[artefact_key]['failure_environments'].add(row.environment_name)
        elif row.test_result_status == 'PASSED':
            artefacts_dict[artefact_key]['success_environments'].add(row.environment_name)
    
    # Separate artefacts into success-only and those with failures
    success_only_artefacts = []
    artefacts_with_failures = []
    
    for artefact_data in artefacts_dict.values():
        # Convert environments sets to sorted lists and add counts
        environments = sorted(list(artefact_data['environments']))
        success_environments = sorted(list(artefact_data.get('success_environments', set())))
        failure_environments = sorted(list(artefact_data.get('failure_environments', set())))
        
        artefact_data['environment_count'] = len(environments)
        artefact_data['environments'] = environments
        artefact_data['success_environments'] = success_environments
        artefact_data['failure_environments'] = failure_environments
        artefact_data['success_environment_count'] = len(success_environments)
        artefact_data['failure_environment_count'] = len(failure_environments)
        
        if artefact_data['has_failures']:
            artefacts_with_failures.append(artefact_data)
        else:
            success_only_artefacts.append(artefact_data)
    
    return {
        'success_only_artefacts': success_only_artefacts,
        'artefacts_with_failures': artefacts_with_failures,
        'total_artefacts': len(artefacts_dict)
    }

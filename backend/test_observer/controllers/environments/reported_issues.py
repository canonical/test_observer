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
from sqlalchemy import select, and_, func, distinct
from sqlalchemy.orm import Session

from test_observer.data_access.models import (
    EnvironmentIssue, Environment, TestExecution, ArtefactBuild, Artefact, TestResult
)
from test_observer.data_access.setup import get_db

from .models import EnvironmentReportedIssueRequest, EnvironmentReportedIssueResponse

router = APIRouter()

endpoint = "/reported-issues"


@router.get(endpoint)
def get_reported_issues(
    is_confirmed: bool | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    # Get basic issue data
    stmt = select(EnvironmentIssue)
    if is_confirmed is not None:
        stmt = stmt.where(EnvironmentIssue.is_confirmed == is_confirmed)
    
    issues = list(db.execute(stmt).scalars())
    
    # For each issue, calculate the affected artifacts count
    result = []
    for issue in issues:
        # Query to count distinct artifacts with failures in this environment within date range
        affected_artifacts_query = (
            select(func.count(distinct(Artefact.id)))
            .select_from(TestExecution)
            .join(Environment, TestExecution.environment_id == Environment.id)
            .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
            .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
            .join(TestResult, TestResult.test_execution_id == TestExecution.id)
            .where(and_(
                Environment.name == issue.environment_name,
                TestResult.status == 'FAILED'
            ))
        )
        
        # Apply date filtering if provided
        if start_date:
            affected_artifacts_query = affected_artifacts_query.where(TestExecution.created_at >= start_date)
        if end_date:
            affected_artifacts_query = affected_artifacts_query.where(TestExecution.created_at <= end_date)
        
        affected_count = db.execute(affected_artifacts_query).scalar() or 0
        
        # Convert to dict and add affected count
        issue_dict = {
            'id': issue.id,
            'environment_name': issue.environment_name,
            'description': issue.description,
            'url': str(issue.url) if issue.url else None,
            'is_confirmed': issue.is_confirmed,
            'external_id': issue.external_id,
            'issue_status': issue.issue_status,
            'sync_status': issue.sync_status,
            'last_synced_at': issue.last_synced_at,
            'sync_error': issue.sync_error,
            'affected_artifacts_count': affected_count
        }
        result.append(issue_dict)
    
    return result


@router.post(endpoint, response_model=EnvironmentReportedIssueResponse)
def create_reported_issue(
    request: EnvironmentReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = EnvironmentIssue(
        environment_name=request.environment_name,
        url=request.url,
        description=request.description,
        is_confirmed=request.is_confirmed,
    )
    db.add(issue)
    db.commit()

    return issue


@router.put(endpoint + "/{issue_id}", response_model=EnvironmentReportedIssueResponse)
def update_reported_issue(
    issue_id: int,
    request: EnvironmentReportedIssueRequest,
    db: Session = Depends(get_db),
):
    issue = db.get(EnvironmentIssue, issue_id)
    for field in request.model_fields:
        setattr(issue, field, getattr(request, field))
    db.commit()
    return issue


@router.delete(endpoint + "/{issue_id}")
def delete_reported_issue(issue_id: int, db: Session = Depends(get_db)):
    db.delete(db.get(EnvironmentIssue, issue_id))
    db.commit()


@router.get(endpoint + "/{issue_id}/affected-artefacts")
def get_affected_artefacts(
    issue_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    """
    Get artefacts affected by a specific environment issue.
    
    Returns artefacts that have test failures in the environment 
    associated with the given issue within the specified date range.
    """
    # Get the environment issue
    issue = db.get(EnvironmentIssue, issue_id)
    if not issue:
        return {"error": "Environment issue not found"}
    
    # Query to find artefacts affected by the environment issue with detailed information
    affected_artefacts_query = (
        select(
            Artefact.id.label('artefact_id'),
            Artefact.name.label('artefact_name'), 
            Artefact.version.label('artefact_version'),
            Artefact.family.label('artefact_family'),
            Artefact.due_date.label('artefact_due_date'),
            ArtefactBuild.id.label('artefact_build_id'),
            ArtefactBuild.architecture.label('architecture'),
            ArtefactBuild.revision.label('revision'),
            TestResult.status.label('test_result_status'),
            TestExecution.id.label('test_execution_id'),
            TestExecution.created_at.label('test_execution_created_at'),
            TestExecution.c3_link.label('c3_link'),
            TestExecution.ci_link.label('ci_link'),
            TestResult.test_case_id.label('test_case_id'),
            TestResult.name.label('test_case_name'),
            TestResult.io_log.label('io_log')
        )
        .select_from(TestExecution)
        .join(Environment, TestExecution.environment_id == Environment.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .join(TestResult, TestResult.test_execution_id == TestExecution.id)
        .where(and_(
            Environment.name == issue.environment_name,
            TestResult.status == 'FAILED'
        ))
    )
    
    # Apply date filtering if provided
    if start_date:
        affected_artefacts_query = affected_artefacts_query.where(TestExecution.created_at >= start_date)
    if end_date:
        affected_artefacts_query = affected_artefacts_query.where(TestExecution.created_at <= end_date)
    
    affected_artefacts_query = affected_artefacts_query.distinct()
    
    results = db.execute(affected_artefacts_query).fetchall()
    
    # Group results by artefact (by artefact_build_id for individual builds)
    artefacts_dict = {}
    for row in results:
        # Use artefact_build_id as key to separate different builds of same artefact
        artefact_key = f"{row.artefact_build_id}"
        if artefact_key not in artefacts_dict:
            artefacts_dict[artefact_key] = {
                'id': row.artefact_id,
                'build_id': row.artefact_build_id,
                'name': row.artefact_name,
                'version': row.artefact_version,
                'family': row.artefact_family,
                'due_date': row.artefact_due_date.isoformat() if row.artefact_due_date else None,
                'architecture': row.architecture,
                'revision': row.revision,
                'created_at': row.test_execution_created_at.isoformat() if row.test_execution_created_at else None,
                'test_execution_details': [],
                'failure_count': 0,
                'c3_links': [],
                'io_logs': []
            }
        
        # Add test execution details
        artefacts_dict[artefact_key]['test_execution_details'].append({
            'test_execution_id': row.test_execution_id,
            'test_case_name': row.test_case_name,
            'test_result_status': row.test_result_status,
            'created_at': row.test_execution_created_at.isoformat() if row.test_execution_created_at else None
        })
        
        # Add C3 links if available
        if row.c3_link:
            artefacts_dict[artefact_key]['c3_links'].append({
                'url': row.c3_link,
                'test_execution_id': row.test_execution_id,
                'status': row.test_result_status
            })
        
        # Add IO logs if available
        if row.io_log:
            artefacts_dict[artefact_key]['io_logs'].append({
                'test_execution_id': row.test_execution_id,
                'content': row.io_log,
                'test_case_name': row.test_case_name
            })
        
        if row.test_result_status == 'FAILED':
            artefacts_dict[artefact_key]['failure_count'] += 1
    
    # Convert to list and sort by name, then by created_at (newest first)
    affected_artefacts = sorted(
        list(artefacts_dict.values()), 
        key=lambda x: (x['name'], x['created_at'] or ''),
        reverse=True
    )
    
    return {
        'affected_artefacts': affected_artefacts,
        'total_artefacts': len(affected_artefacts),
        'environment_name': issue.environment_name
    }

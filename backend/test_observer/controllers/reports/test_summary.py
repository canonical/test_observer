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
    Environment,
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
                TestResult.created_at >= start_date,
                TestResult.created_at <= end_date,
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


@router.get("/test-case/associated-artefacts")
def get_test_case_associated_artefacts(
    test_identifier: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Get artefacts associated with a specific test case, separated by success vs failure status.
    
    Returns artefacts that have test results for the given test case,
    categorized by whether they have any failures or only successes.
    """
    # Query to find artefacts that have test results for this test case
    artefacts_query = (
        select(
            Artefact.id.label('artefact_id'),
            Artefact.name.label('artefact_name'),
            Artefact.version.label('artefact_version'),
            Artefact.family.label('artefact_family'),
            Artefact.due_date.label('artefact_due_date'),
            Artefact.created_at.label('created_at'),
            Environment.name.label('environment_name'),
            TestResult.status.label('test_result_status'),
            TestResult.id.label('test_result_id'),
            TestResult.io_log.label('io_log'),
            TestExecution.id.label('test_execution_id'),
            TestExecution.c3_link.label('c3_link'),
            TestExecution.ci_link.label('ci_link')
        )
        .select_from(TestCase)
        .join(TestResult, TestResult.test_case_id == TestCase.id)
        .join(TestExecution, TestResult.test_execution_id == TestExecution.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .join(Environment, TestExecution.environment_id == Environment.id)
        .where(or_(
            and_(TestCase.template_id == test_identifier, TestCase.template_id != ''),
            and_(TestCase.name == test_identifier, TestCase.name != '')
        ))
        .distinct()
    )
    
    results = db.execute(artefacts_query).fetchall()
    
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
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'environments': set(),
                'has_failures': False,
                'test_results': [],
                'environment_details': {}  # Map of environment_name -> details
            }
        
        artefacts_dict[artefact_key]['environments'].add(row.environment_name)
        artefacts_dict[artefact_key]['test_results'].append({
            'test_execution_id': row.test_execution_id,
            'environment_name': row.environment_name,
            'test_result_status': row.test_result_status
        })
        
        # Track environment details with C3 links
        if row.environment_name not in artefacts_dict[artefact_key]['environment_details']:
            artefacts_dict[artefact_key]['environment_details'][row.environment_name] = {
                'name': row.environment_name,
                'test_executions': []
            }
        
        artefacts_dict[artefact_key]['environment_details'][row.environment_name]['test_executions'].append({
            'test_execution_id': row.test_execution_id,
            'test_result_id': row.test_result_id,
            'c3_link': row.c3_link,
            'ci_link': row.ci_link,
            'io_log': row.io_log,
            'status': row.test_result_status
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
        
        # Convert environment_details to list format for frontend consumption
        environment_details_list = []
        for env_name in environments:
            env_details = artefact_data['environment_details'][env_name]
            
            # Collect all C3 links for this environment
            c3_links = []
            io_logs = []
            primary_c3_link = None
            
            for exec_detail in env_details['test_executions']:
                if exec_detail['c3_link']:
                    c3_links.append({
                        'url': exec_detail['c3_link'],
                        'test_execution_id': exec_detail['test_execution_id'],
                        'status': exec_detail['status']
                    })
                    # Use the most recent C3 link as primary, preferring failed ones
                    if not primary_c3_link or exec_detail['status'] == 'FAILED':
                        primary_c3_link = exec_detail['c3_link']
                
                if exec_detail['io_log']:
                    io_logs.append({
                        'content': exec_detail['io_log'],
                        'test_result_id': exec_detail['test_result_id'],
                        'test_execution_id': exec_detail['test_execution_id'],
                        'status': exec_detail['status']
                    })
            
            environment_details_list.append({
                'name': env_name,
                'c3_link': primary_c3_link,  # Primary C3 link for quick access
                'c3_links': c3_links,  # All C3 links for this environment
                'io_logs': io_logs,  # All IO logs for this environment
                'has_failure': env_name in failure_environments,
                'test_executions': env_details['test_executions']
            })
        
        artefact_data['environment_details'] = environment_details_list
        
        if artefact_data['has_failures']:
            artefacts_with_failures.append(artefact_data)
        else:
            success_only_artefacts.append(artefact_data)
    
    # Sort artefacts within each group by name for consistent ordering
    artefacts_with_failures.sort(key=lambda x: x['name'])
    success_only_artefacts.sort(key=lambda x: x['name'])
    
    return {
        'test_identifier': test_identifier,
        'success_only_artefacts': success_only_artefacts,
        'artefacts_with_failures': artefacts_with_failures,
        'total_artefacts': len(artefacts_dict)
    }


@router.get("/test-summary-with-trends")
def get_test_summary_report_with_trends(
    start_date: datetime = Query(default=datetime.min),
    end_date: datetime = Query(default_factory=datetime.now),
    families: list[str] = Query(default=['snap', 'deb']),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns test summary report with trend analysis comparing current vs previous period.
    """
    
    # Calculate the duration of the current period
    period_duration = end_date - start_date
    
    # Calculate previous period (same duration, ending when current period starts)
    prev_end_date = start_date
    prev_start_date = prev_end_date - period_duration
    
    # Get current period data
    current_data = get_test_summary_report(start_date, end_date, families, db)
    
    # Get previous period data
    prev_data = get_test_summary_report(prev_start_date, prev_end_date, families, db)
    
    # Build lookup for previous period success rates
    prev_success_rates = {}
    for item in prev_data['summary']:
        test_id = item['test_identifier']
        total = item['total']
        passed = item['passed']
        if total > 0:
            prev_success_rates[test_id] = (passed / total) * 100
    
    # Add trend analysis to current data
    summary_with_trends = []
    for item in current_data['summary']:
        test_id = item['test_identifier']
        total = item['total']
        passed = item['passed']
        
        # Calculate current success rate
        current_success_rate = (passed / total * 100) if total > 0 else 0
        
        # Compare with previous period (based on fail rate, not success rate)
        trend = 'none'  # none, improving, worsening
        if test_id in prev_success_rates:
            prev_rate = prev_success_rates[test_id]
            current_fail_rate = 100 - current_success_rate
            prev_fail_rate = 100 - prev_rate
            
            # Green (improving) when fail rate decreases by >10%
            if current_fail_rate < prev_fail_rate - 10:
                trend = 'improving'
            # Red (worsening) when fail rate increases by >10%
            elif current_fail_rate > prev_fail_rate + 10:
                trend = 'worsening'
        
        # Add trend info to item
        item_with_trend = dict(item)
        item_with_trend['trend'] = trend
        item_with_trend['current_success_rate'] = current_success_rate
        item_with_trend['previous_success_rate'] = prev_success_rates.get(test_id)
        
        summary_with_trends.append(item_with_trend)
    
    # Update the response with trend data
    result = dict(current_data)
    result['summary'] = summary_with_trends
    result['previous_period'] = {
        'start_date': prev_start_date.isoformat(),
        'end_date': prev_end_date.isoformat(),
        'total_tests': prev_data['total_tests'],
        'total_executions': prev_data['total_executions']
    }
    
    return result
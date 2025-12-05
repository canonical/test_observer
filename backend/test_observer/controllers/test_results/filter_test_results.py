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

from sqlalchemy import and_, select, exists, true, Select
from sqlalchemy.orm import aliased


from test_observer.common.constants import QueryValue
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    IssueTestResultAttachment,
    TestCase,
    TestExecution,
    TestResult,
    TestExecutionMetadata,
    TestExecutionRerunRequest,
    ColumnElement,
)
from test_observer.data_access.models import test_execution_metadata_association_table
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.controllers.test_results.shared_models import TestResultSearchFilters


def filter_execution_metadata(
    execution_metadata: ExecutionMetadata,
) -> ColumnElement[bool]:
    # For each category, require that a matching value exists for the execution
    conditions = []
    for category, values in execution_metadata.root.items():
        subq = select(true()).select_from(test_execution_metadata_association_table)
        subq = subq.join(
            TestExecutionMetadata,
            test_execution_metadata_association_table.c.test_execution_metadata_id
            == TestExecutionMetadata.id,
        )
        subq = subq.where(
            test_execution_metadata_association_table.c.test_execution_id
            == TestExecution.id,
            TestExecutionMetadata.category == category,
            TestExecutionMetadata.value.in_(values),
        )
        subq = subq.limit(1)
        conditions.append(exists(subq))

    # All categories must match
    return and_(*conditions)


def build_query_filters_and_joins(
    filters: TestResultSearchFilters,
) -> tuple[list[ColumnElement[bool]], set[str]]:
    query_filters: list[ColumnElement[bool]] = []
    joins_needed = set()

    if len(filters.families) > 0:
        query_filters.append(Artefact.family.in_(filters.families))
        joins_needed.update(["test_execution", "artefact_build", "artefact"])

    if len(filters.artefacts) > 0:
        query_filters.append(Artefact.name.in_(filters.artefacts))
        joins_needed.update(["test_execution", "artefact_build", "artefact"])

    if filters.artefact_is_archived is not None:
        query_filters.append(Artefact.archived == filters.artefact_is_archived)
        joins_needed.update(["test_execution", "artefact_build", "artefact"])

    if len(filters.environments) > 0:
        query_filters.append(Environment.name.in_(filters.environments))
        joins_needed.update(["test_execution", "environment"])

    if len(filters.test_cases) > 0:
        query_filters.append(TestCase.name.in_(filters.test_cases))
        joins_needed.add("test_case")

    if len(filters.template_ids) > 0:
        query_filters.append(TestCase.template_id.in_(filters.template_ids))
        joins_needed.add("test_case")

    if len(filters.execution_metadata) > 0:
        query_filters.append(filter_execution_metadata(filters.execution_metadata))
        joins_needed.add("test_execution")

    if filters.issues == QueryValue.ANY:
        query_filters.append(
            exists(
                select(1)
                .select_from(IssueTestResultAttachment)
                .where(IssueTestResultAttachment.test_result_id == TestResult.id)
            )
        )
    elif filters.issues == QueryValue.NONE:
        query_filters.append(
            ~exists(
                select(1)
                .select_from(IssueTestResultAttachment)
                .where(IssueTestResultAttachment.test_result_id == TestResult.id)
            )
        )
    elif len(filters.issues) > 0:
        query_filters.append(
            TestResult.id.in_(
                select(IssueTestResultAttachment.test_result_id).where(
                    IssueTestResultAttachment.issue_id.in_(filters.issues)
                )
            )
        )

    if len(filters.test_result_statuses) > 0:
        query_filters.append(TestResult.status.in_(filters.test_result_statuses))

    if len(filters.test_execution_statuses) > 0:
        query_filters.append(TestExecution.status.in_(filters.test_execution_statuses))
        joins_needed.add("test_execution")

    if filters.assignee_ids != []:
        if filters.assignee_ids == QueryValue.ANY:
            query_filters.append(Artefact.assignee_id.isnot(None))
        elif filters.assignee_ids == QueryValue.NONE:
            query_filters.append(Artefact.assignee_id.is_(None))
        elif len(filters.assignee_ids) > 0:
            query_filters.append(Artefact.assignee_id.in_(filters.assignee_ids))
        joins_needed.update(["test_execution", "artefact_build", "artefact"])

    if filters.rerun_is_requested is not None:
        joins_needed.add("test_execution")
        rerun_exists = exists(
            select(1)
            .select_from(TestExecutionRerunRequest)
            .where(
                TestExecutionRerunRequest.test_plan_id == TestExecution.test_plan_id,
                TestExecutionRerunRequest.artefact_build_id
                == TestExecution.artefact_build_id,
                TestExecutionRerunRequest.environment_id
                == TestExecution.environment_id,
            )
        )
        query_filters.append(
            rerun_exists if filters.rerun_is_requested else ~rerun_exists
        )

    if filters.execution_is_latest is not None:
        joins_needed.add("test_execution")
        newer_execution = aliased(TestExecution)
        newer_execution_exists = exists(
            select(1)
            .select_from(newer_execution)
            .where(
                TestExecution.test_plan_id == newer_execution.test_plan_id,
                TestExecution.artefact_build_id == newer_execution.artefact_build_id,
                TestExecution.environment_id == newer_execution.environment_id,
                TestExecution.id < newer_execution.id,
            )
        )
        query_filters.append(
            ~newer_execution_exists
            if filters.execution_is_latest
            else newer_execution_exists
        )

    if filters.from_date is not None:
        query_filters.append(TestResult.created_at >= filters.from_date)

    if filters.until_date is not None:
        query_filters.append(TestResult.created_at <= filters.until_date)

    return query_filters, joins_needed


def apply_joins(query: Select, joins_needed: set[str]) -> Select:
    if "test_execution" in joins_needed:
        query = query.join(TestResult.test_execution)

    if "environment" in joins_needed:
        query = query.join(TestExecution.environment)

    if "artefact_build" in joins_needed:
        query = query.join(TestExecution.artefact_build)

    if "artefact" in joins_needed:
        query = query.join(ArtefactBuild.artefact)

    if "test_case" in joins_needed:
        query = query.join(TestResult.test_case)

    return query


def filter_test_results(query: Select, filters: TestResultSearchFilters) -> Select:
    # Build filters and track which joins are needed
    query_filters, joins_needed = build_query_filters_and_joins(filters)

    # Build the main query with only necessary joins
    query = apply_joins(query, joins_needed)

    # Apply pagination
    if filters.offset is not None:
        query = query.offset(filters.offset)
    if filters.limit is not None:
        query = query.limit(filters.limit)

    # Apply all filters
    if query_filters:
        query = query.where(and_(*query_filters))

    return query

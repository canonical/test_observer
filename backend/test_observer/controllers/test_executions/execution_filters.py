# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Filter-building utilities for TestExecution queries.

Separated from search.py so they can be imported by reruns.py without
triggering route registration side-effects from search.py.
"""

from typing import Literal

from sqlalchemy import Select, and_, exists, select, true
from sqlalchemy.orm import aliased

from test_observer.common.constants import QueryValue
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.controllers.test_executions.shared_models import _TestExecutionFilterBase
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ColumnElement,
    Environment,
    TestEvent,
    TestExecution,
    TestExecutionMetadata,
    TestExecutionRerunRequest,
    User,
    test_execution_metadata_association_table,
)

JoinName = Literal["test_execution", "artefact_build", "artefact", "environment"]


def filter_execution_metadata(
    execution_metadata: ExecutionMetadata,
) -> ColumnElement[bool]:
    conditions = []
    for category, values in execution_metadata.root.items():
        subq = select(true()).select_from(test_execution_metadata_association_table)
        subq = subq.join(
            TestExecutionMetadata,
            test_execution_metadata_association_table.c.test_execution_metadata_id == TestExecutionMetadata.id,
        )
        subq = subq.where(
            test_execution_metadata_association_table.c.test_execution_id == TestExecution.id,
            TestExecutionMetadata.category == category,
            TestExecutionMetadata.value.in_(values),
        )
        subq = subq.limit(1)
        conditions.append(exists(subq))

    return and_(*conditions)


def build_execution_filters(
    filters: _TestExecutionFilterBase,
) -> tuple[list[ColumnElement[bool]], set[JoinName]]:
    query_filters: list[ColumnElement[bool]] = []
    joins_needed: set[JoinName] = set()

    if filters.families:
        query_filters.append(Artefact.family.in_(filters.families))
        joins_needed.update(["artefact_build", "artefact"])

    if filters.artefacts:
        query_filters.append(Artefact.name.in_(filters.artefacts))
        joins_needed.update(["artefact_build", "artefact"])

    if filters.artefact_is_archived is not None:
        query_filters.append(Artefact.archived == filters.artefact_is_archived)
        joins_needed.update(["artefact_build", "artefact"])

    if filters.environments:
        query_filters.append(Environment.name.in_(filters.environments))
        joins_needed.add("environment")

    if filters.execution_metadata and len(filters.execution_metadata) > 0:
        query_filters.append(filter_execution_metadata(filters.execution_metadata))

    if filters.test_execution_statuses:
        query_filters.append(TestExecution.status.in_(filters.test_execution_statuses))

    if filters.reviewer_ids != []:
        if filters.reviewer_ids == QueryValue.ANY:
            query_filters.append(Artefact.reviewers.any())
        elif filters.reviewer_ids == QueryValue.NONE:
            query_filters.append(~Artefact.reviewers.any())
        elif isinstance(filters.reviewer_ids, list) and filters.reviewer_ids:
            query_filters.append(Artefact.reviewers.any(User.id.in_(filters.reviewer_ids)))
        joins_needed.update(["artefact_build", "artefact"])

    if filters.rerun_is_requested is not None:
        rerun_exists = exists(
            select(1)
            .select_from(TestExecutionRerunRequest)
            .where(
                TestExecutionRerunRequest.test_plan_id == TestExecution.test_plan_id,
                TestExecutionRerunRequest.artefact_build_id == TestExecution.artefact_build_id,
                TestExecutionRerunRequest.environment_id == TestExecution.environment_id,
            )
        )
        query_filters.append(rerun_exists if filters.rerun_is_requested else ~rerun_exists)

    if filters.execution_is_latest is not None:
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
        query_filters.append(~newer_execution_exists if filters.execution_is_latest else newer_execution_exists)

    event_names = getattr(filters, "event_names", [])
    if event_names != []:
        event_exists = exists(select(1).select_from(TestEvent).where(TestEvent.test_execution_id == TestExecution.id))
        if event_names == QueryValue.ANY:
            query_filters.append(event_exists)
        elif event_names == QueryValue.NONE:
            query_filters.append(~event_exists)
        elif isinstance(event_names, list) and event_names:
            query_filters.append(
                exists(
                    select(1)
                    .select_from(TestEvent)
                    .where(
                        TestEvent.test_execution_id == TestExecution.id,
                        TestEvent.event_name.in_(event_names),
                    )
                )
            )

    if filters.from_date is not None:
        query_filters.append(TestExecution.updated_at >= filters.from_date)

    if filters.until_date is not None:
        query_filters.append(TestExecution.updated_at <= filters.until_date)

    return query_filters, joins_needed


def apply_te_joins(query: Select, joins_needed: set[JoinName]) -> Select:
    if "artefact_build" in joins_needed:
        query = query.join(TestExecution.artefact_build)
    if "artefact" in joins_needed:
        query = query.join(ArtefactBuild.artefact)
    if "environment" in joins_needed:
        query = query.join(TestExecution.environment)
    return query

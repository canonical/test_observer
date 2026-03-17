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

"""
Initialize Prometheus metrics from database on application startup.

This module populates all metrics with historical data so the /metrics endpoint
immediately reflects the current state rather than starting from zero.
"""

import logging
from datetime import datetime, timedelta
from os import environ

from sqlalchemy import func
from sqlalchemy.orm import Session

from test_observer.common.metrics import (
    test_results,
    test_results_metadata,
    test_results_triaged,
)
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Environment,
    Issue,
    IssueTestResultAttachment,
    TestCase,
    TestExecution,
    TestExecutionMetadata,
    TestPlan,
    TestResult,
    test_execution_metadata_association_table,
)

logger = logging.getLogger(__name__)

# Configuration from environment
METRICS_INIT_ENABLED = environ.get("METRICS_INIT_ENABLED", "true").lower() == "true"
METRICS_INIT_DAYS = int(environ.get("METRICS_INIT_DAYS", "30"))


def initialize_all_metrics(db: Session) -> None:
    """
    Initialize all Prometheus metrics from database.

    Queries the database for existing test results and populates metrics
    to reflect historical data for ALL families.

    Args:
        db: Database session
    """
    if not METRICS_INIT_ENABLED:
        logger.info("Metrics initialization disabled (METRICS_INIT_ENABLED=false)")
        return

    logger.info(f"Initializing Prometheus metrics from database (last {METRICS_INIT_DAYS} days)...")

    try:
        count_basic = _initialize_test_results_metric(db)
        count_triaged = _initialize_triaged_metrics(db)
        count_metadata = _initialize_metadata_metrics(db)

        logger.info(f"Initialized {count_basic} basic test result metrics")
        logger.info(f"Initialized {count_triaged} triaged result metrics")
        logger.info(f"Initialized {count_metadata} metadata metrics")
        logger.info("Metrics initialization complete")

    except Exception as e:
        logger.exception(f"Failed to initialize metrics: {e}")
        # Don't re-raise - allow application to start


def _get_cutoff_date() -> datetime | None:
    """Get the cutoff date for metrics initialization based on config."""
    if METRICS_INIT_DAYS == 0:
        return None  # No time limit
    return datetime.utcnow() - timedelta(days=METRICS_INIT_DAYS)


def _initialize_test_results_metric(db: Session) -> int:
    """
    Initialize test_results metric for ALL families.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query test results grouped by all label fields
    query = (
        db.query(
            Artefact.family,
            Artefact.name.label("artefact_name"),
            Artefact.stage.label("artefact_stage"),
            Artefact.track,
            Artefact.series,
            Artefact.os,
            Environment.name.label("environment_name"),
            TestPlan.name.label("test_plan"),
            TestCase.name.label("test_name"),
            TestResult.status,
            func.count().label("cnt"),
        )
        .select_from(TestResult)
        .join(TestExecution, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(Environment, TestExecution.environment_id == Environment.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.family,
        Artefact.name,
        Artefact.stage,
        Artefact.track,
        Artefact.series,
        Artefact.os,
        Environment.name,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
    )

    count = 0
    for row in query.all():
        test_results.labels(
            family=row.family.value,
            artefact_name=row.artefact_name,
            artefact_stage=row.artefact_stage,
            track=row.track or "",
            series=row.series or "",
            os=row.os or "",
            environment_name=row.environment_name,
            test_plan=row.test_plan,
            test_name=row.test_name,
            status=row.status.value,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count


def _initialize_triaged_metrics(db: Session) -> int:
    """
    Initialize test_results_triaged metric for ALL families.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query test results with issue attachments
    query = (
        db.query(
            Artefact.family,
            Artefact.name.label("artefact_name"),
            Artefact.stage.label("artefact_stage"),
            Artefact.track,
            Artefact.series,
            Artefact.os,
            Environment.name.label("environment_name"),
            TestPlan.name.label("test_plan"),
            TestCase.name.label("test_name"),
            TestResult.status,
            Issue.source,
            Issue.project,
            Issue.key,
            func.count().label("cnt"),
        )
        .select_from(TestResult)
        .join(
            IssueTestResultAttachment,
            TestResult.id == IssueTestResultAttachment.test_result_id,
        )
        .join(Issue, IssueTestResultAttachment.issue_id == Issue.id)
        .join(TestExecution, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(Environment, TestExecution.environment_id == Environment.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.family,
        Artefact.name,
        Artefact.stage,
        Artefact.track,
        Artefact.series,
        Artefact.os,
        Environment.name,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
        Issue.source,
        Issue.project,
        Issue.key,
    )

    count = 0
    for row in query.all():
        test_results_triaged.labels(
            family=row.family.value,
            artefact_name=row.artefact_name,
            artefact_stage=row.artefact_stage,
            track=row.track or "",
            series=row.series or "",
            os=row.os or "",
            environment_name=row.environment_name,
            test_plan=row.test_plan,
            test_name=row.test_name,
            status=row.status.value,
            issue_source=row.source.value,
            issue_project=row.project,
            issue_key=row.key,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count


def _initialize_metadata_metrics(db: Session) -> int:
    """
    Initialize test_results_metadata metric for ALL families.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query all execution metadata
    query = (
        db.query(
            Artefact.family,
            Artefact.name.label("artefact_name"),
            Artefact.stage.label("artefact_stage"),
            Artefact.track.label("artefact_track"),
            Artefact.series.label("artefact_series"),
            Artefact.os.label("artefact_os"),
            Environment.name.label("environment_name"),
            TestPlan.name.label("test_plan"),
            TestCase.name.label("test_name"),
            TestResult.status,
            TestExecutionMetadata.category,
            TestExecutionMetadata.value,
            func.count().label("cnt"),
        )
        .select_from(TestExecution)
        .join(
            test_execution_metadata_association_table,
            TestExecution.id == test_execution_metadata_association_table.c.test_execution_id,
        )
        .join(
            TestExecutionMetadata,
            test_execution_metadata_association_table.c.test_execution_metadata_id == TestExecutionMetadata.id,
        )
        .join(TestResult, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(Environment, TestExecution.environment_id == Environment.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.family,
        Artefact.name,
        Artefact.stage,
        Artefact.track,
        Artefact.series,
        Artefact.os,
        Environment.name,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
        TestExecutionMetadata.category,
        TestExecutionMetadata.value,
    )

    count = 0
    for row in query.all():
        test_results_metadata.labels(
            family=row.family.value,
            artefact_name=row.artefact_name,
            artefact_stage=row.artefact_stage,
            track=row.artefact_track or "",
            series=row.artefact_series or "",
            os=row.artefact_os or "",
            environment_name=row.environment_name,
            test_plan=row.test_plan,
            test_name=row.test_name,
            status=row.status.value,
            metadata_category=row.category,
            metadata_value=row.value,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count

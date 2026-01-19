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

"""
Initialize Prometheus metrics from database on application startup.

This module populates all metrics with historical data so the /metrics endpoint
immediately reflects the current state rather than starting from zero.
"""

import logging
from datetime import datetime, timedelta
from os import environ

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from test_observer.common.metrics import (
    test_executions_results,
    test_executions_results_triaged,
    test_execution_results_metadata_charm_revision,
    test_execution_results_metadata_charm_failure,
    test_executions_results_metadata_charm_cli,
    test_executions_results_metadata_simple,
)
from test_observer.common.metrics_helpers import extract_endpoint_info
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    Issue,
    IssueTestResultAttachment,
    TestCase,
    TestExecution,
    TestExecutionMetadata,
    TestPlan,
    TestResult,
    test_execution_metadata_association_table,
)
from test_observer.data_access.models_enums import FamilyName

logger = logging.getLogger(__name__)

# Configuration from environment
METRICS_INIT_ENABLED = environ.get("METRICS_INIT_ENABLED", "true").lower() == "true"
METRICS_INIT_DAYS = int(environ.get("METRICS_INIT_DAYS", "30"))


def initialize_all_metrics(db: Session) -> None:
    """
    Initialize all Prometheus metrics from database.

    Queries the database for existing test results and populates metrics
    to reflect historical data. Only processes charm family artefacts.

    Args:
        db: Database session
    """
    if not METRICS_INIT_ENABLED:
        logger.info("Metrics initialization disabled (METRICS_INIT_ENABLED=false)")
        return

    logger.info(
        f"Initializing Prometheus metrics from database "
        f"(last {METRICS_INIT_DAYS} days)..."
    )

    try:
        count_basic = _initialize_test_results_metric(db)
        count_triaged = _initialize_triaged_metrics(db)
        count_revision = _initialize_charm_revision_metrics(db)
        count_failure = _initialize_charm_failure_metrics(db)
        count_cli = _initialize_cli_metrics(db)
        count_simple = _initialize_simple_metadata_metrics(db)

        logger.info(f"Initialized {count_basic} basic test result metrics")
        logger.info(f"Initialized {count_triaged} triaged result metrics")
        logger.info(
            f"Initialized {count_revision + count_failure + count_cli + count_simple} "
            f"metadata metrics ({count_revision} revision, {count_failure} failure, "
            f"{count_cli} CLI, {count_simple} simple)"
        )
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
    Initialize t_obs_results metric with historical data.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query test results grouped by all label fields
    query = (
        db.query(
            Artefact.name.label("target_asset"),
            Artefact.track.label("target_track"),
            Artefact.stage.label("target_risk"),
            TestPlan.name.label("test_plan_name"),
            TestCase.name.label("test_name"),
            TestResult.status,
            func.count().label("cnt"),
        )
        .select_from(TestResult)
        .join(TestExecution, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .filter(Artefact.family == FamilyName.charm)
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.name,
        Artefact.track,
        Artefact.stage,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
    )

    count = 0
    for row in query.all():
        # Extract endpoint info from test plan
        provider_endpoint, interface, requirer_endpoint, neighbor_asset = (
            extract_endpoint_info(row.test_plan_name, row.target_asset)
        )

        if not all([provider_endpoint, interface, requirer_endpoint, neighbor_asset]):
            continue

        # Set metric value to count
        test_executions_results.labels(
            target_asset=row.target_asset,
            target_track=row.target_track or "",
            target_risk=row.target_risk,
            provider_endpoint=provider_endpoint,
            interface=interface,
            requirer_endpoint=requirer_endpoint,
            neighbor_asset=neighbor_asset,
            test_name=row.test_name,
            status=row.status.value,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count


def _initialize_triaged_metrics(db: Session) -> int:
    """
    Initialize t_obs_results_triaged metric with historical data.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query test results with issue attachments
    query = (
        db.query(
            Artefact.name.label("target_asset"),
            Artefact.track.label("target_track"),
            Artefact.stage.label("target_risk"),
            TestPlan.name.label("test_plan_name"),
            TestCase.name.label("test_name"),
            TestResult.status,
            Issue.source,
            Issue.project,
            Issue.key,
            Issue.url,
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
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .filter(Artefact.family == FamilyName.charm)
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.name,
        Artefact.track,
        Artefact.stage,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
        Issue.source,
        Issue.project,
        Issue.key,
        Issue.url,
    )

    count = 0
    for row in query.all():
        provider_endpoint, interface, requirer_endpoint, neighbor_asset = (
            extract_endpoint_info(row.test_plan_name, row.target_asset)
        )

        if not all([provider_endpoint, interface, requirer_endpoint, neighbor_asset]):
            continue

        test_executions_results_triaged.labels(
            target_asset=row.target_asset,
            target_track=row.target_track or "",
            target_risk=row.target_risk,
            provider_endpoint=provider_endpoint,
            interface=interface,
            requirer_endpoint=requirer_endpoint,
            neighbor_asset=neighbor_asset,
            test_name=row.test_name,
            status=row.status.value,
            issue_source=row.source.value,
            issue_project=row.project,
            issue_key=row.key,
            issue_url=row.url,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count


def _initialize_charm_revision_metrics(db: Session) -> int:
    """
    Initialize t_obs_results_metadata_charm_revision metric.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query metadata with charm_qa:charm:*:revision pattern
    query = (
        db.query(
            Artefact.name.label("target_asset"),
            Artefact.track.label("target_track"),
            Artefact.stage.label("target_risk"),
            TestPlan.name.label("test_plan_name"),
            TestCase.name.label("test_name"),
            TestResult.status,
            TestExecutionMetadata.category,
            TestExecutionMetadata.value,
            func.count().label("cnt"),
        )
        .select_from(TestExecution)
        .join(
            test_execution_metadata_association_table,
            TestExecution.id
            == test_execution_metadata_association_table.c.test_execution_id,
        )
        .join(
            TestExecutionMetadata,
            test_execution_metadata_association_table.c.test_execution_metadata_id
            == TestExecutionMetadata.id,
        )
        .join(TestResult, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .filter(
            and_(
                Artefact.family == FamilyName.charm,
                TestExecutionMetadata.category.like("charm_qa:charm:%:revision"),
            )
        )
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.name,
        Artefact.track,
        Artefact.stage,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
        TestExecutionMetadata.category,
        TestExecutionMetadata.value,
    )

    count = 0
    for row in query.all():
        provider_endpoint, interface, requirer_endpoint, neighbor_asset = (
            extract_endpoint_info(row.test_plan_name, row.target_asset)
        )

        if not all([provider_endpoint, interface, requirer_endpoint, neighbor_asset]):
            continue

        # Extract charm name from category (charm_qa:charm:CHARM_NAME:revision)
        parts = row.category.split(":")
        if len(parts) == 4:
            charm_name = parts[2]
            test_execution_results_metadata_charm_revision.labels(
                target_asset=row.target_asset,
                target_track=row.target_track or "",
                target_risk=row.target_risk,
                provider_endpoint=provider_endpoint,
                interface=interface,
                requirer_endpoint=requirer_endpoint,
                neighbor_asset=neighbor_asset,
                test_name=row.test_name,
                status=row.status.value,
                charm_name=charm_name,
                charm_revision=row.value,
            ).set(int(row.cnt))  # type: ignore[arg-type]
            count += 1

    return count


def _initialize_charm_failure_metrics(db: Session) -> int:
    """
    Initialize t_obs_results_metadata_charm_failure metric.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query metadata with charm_qa:failure:charm:*:status pattern
    query = (
        db.query(
            Artefact.name.label("target_asset"),
            Artefact.track.label("target_track"),
            Artefact.stage.label("target_risk"),
            TestPlan.name.label("test_plan_name"),
            TestCase.name.label("test_name"),
            TestResult.status,
            TestExecutionMetadata.category,
            TestExecutionMetadata.value,
            func.count().label("cnt"),
        )
        .select_from(TestExecution)
        .join(
            test_execution_metadata_association_table,
            TestExecution.id
            == test_execution_metadata_association_table.c.test_execution_id,
        )
        .join(
            TestExecutionMetadata,
            test_execution_metadata_association_table.c.test_execution_metadata_id
            == TestExecutionMetadata.id,
        )
        .join(TestResult, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .filter(
            and_(
                Artefact.family == FamilyName.charm,
                TestExecutionMetadata.category.like("charm_qa:failure:charm:%:status"),
            )
        )
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.name,
        Artefact.track,
        Artefact.stage,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
        TestExecutionMetadata.category,
        TestExecutionMetadata.value,
    )

    count = 0
    for row in query.all():
        provider_endpoint, interface, requirer_endpoint, neighbor_asset = (
            extract_endpoint_info(row.test_plan_name, row.target_asset)
        )

        if not all([provider_endpoint, interface, requirer_endpoint, neighbor_asset]):
            continue

        # Extract charm name from category (charm_qa:failure:charm:CHARM_NAME:status)
        cat_parts = row.category.split(":")
        if len(cat_parts) != 5:
            continue

        charm_name = cat_parts[3]

        # Parse value (entity_type:charm_status:status_message)
        value_parts = row.value.split(":", 2)
        if len(value_parts) < 2:
            continue

        entity_type = value_parts[0]
        charm_status = value_parts[1]
        status_message = value_parts[2] if len(value_parts) > 2 else ""

        test_execution_results_metadata_charm_failure.labels(
            target_asset=row.target_asset,
            target_track=row.target_track or "",
            target_risk=row.target_risk,
            provider_endpoint=provider_endpoint,
            interface=interface,
            requirer_endpoint=requirer_endpoint,
            neighbor_asset=neighbor_asset,
            test_name=row.test_name,
            status=row.status.value,
            charm_name=charm_name,
            entity_type=entity_type,
            charm_status=charm_status,
            status_message=status_message,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count


def _initialize_cli_metrics(db: Session) -> int:
    """
    Initialize t_obs_results_metadata_failure_cli metric.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query metadata with charm_qa:failure:cli:cmd or charm_qa:failure:cli:stderr
    query = (
        db.query(
            Artefact.name.label("target_asset"),
            Artefact.track.label("target_track"),
            Artefact.stage.label("target_risk"),
            TestPlan.name.label("test_plan_name"),
            TestCase.name.label("test_name"),
            TestResult.status,
            TestExecutionMetadata.category,
            TestExecutionMetadata.value,
            func.count().label("cnt"),
        )
        .select_from(TestExecution)
        .join(
            test_execution_metadata_association_table,
            TestExecution.id
            == test_execution_metadata_association_table.c.test_execution_id,
        )
        .join(
            TestExecutionMetadata,
            test_execution_metadata_association_table.c.test_execution_metadata_id
            == TestExecutionMetadata.id,
        )
        .join(TestResult, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .filter(
            and_(
                Artefact.family == FamilyName.charm,
                TestExecutionMetadata.category.in_(
                    ["charm_qa:failure:cli:cmd", "charm_qa:failure:cli:stderr"]
                ),
            )
        )
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.name,
        Artefact.track,
        Artefact.stage,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
        TestExecutionMetadata.category,
        TestExecutionMetadata.value,
    )

    count = 0
    for row in query.all():
        provider_endpoint, interface, requirer_endpoint, neighbor_asset = (
            extract_endpoint_info(row.test_plan_name, row.target_asset)
        )

        if not all([provider_endpoint, interface, requirer_endpoint, neighbor_asset]):
            continue

        # Determine which label to set based on category
        if row.category == "charm_qa:failure:cli:cmd":
            cmd_value = row.value
            stderr_value = ""
        else:  # charm_qa:failure:cli:stderr
            cmd_value = ""
            stderr_value = row.value

        test_executions_results_metadata_charm_cli.labels(
            target_asset=row.target_asset,
            target_track=row.target_track or "",
            target_risk=row.target_risk,
            provider_endpoint=provider_endpoint,
            interface=interface,
            requirer_endpoint=requirer_endpoint,
            neighbor_asset=neighbor_asset,
            test_name=row.test_name,
            status=row.status.value,
            cmd=cmd_value,
            stderr=stderr_value,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count


def _initialize_simple_metadata_metrics(db: Session) -> int:
    """
    Initialize t_obs_results_metadata_simple metric.

    Returns:
        Number of metric combinations initialized
    """
    cutoff_date = _get_cutoff_date()

    # Query all charm_qa metadata not covered by other specific metrics
    query = (
        db.query(
            Artefact.name.label("target_asset"),
            Artefact.track.label("target_track"),
            Artefact.stage.label("target_risk"),
            TestPlan.name.label("test_plan_name"),
            TestCase.name.label("test_name"),
            TestResult.status,
            TestExecutionMetadata.category,
            TestExecutionMetadata.value,
            func.count().label("cnt"),
        )
        .select_from(TestExecution)
        .join(
            test_execution_metadata_association_table,
            TestExecution.id
            == test_execution_metadata_association_table.c.test_execution_id,
        )
        .join(
            TestExecutionMetadata,
            test_execution_metadata_association_table.c.test_execution_metadata_id
            == TestExecutionMetadata.id,
        )
        .join(TestResult, TestResult.test_execution_id == TestExecution.id)
        .join(TestCase, TestResult.test_case_id == TestCase.id)
        .join(TestPlan, TestExecution.test_plan_id == TestPlan.id)
        .join(ArtefactBuild, TestExecution.artefact_build_id == ArtefactBuild.id)
        .join(Artefact, ArtefactBuild.artefact_id == Artefact.id)
        .filter(
            and_(
                Artefact.family == FamilyName.charm,
                TestExecutionMetadata.category.like("charm_qa:%"),
            )
        )
    )

    if cutoff_date:
        query = query.filter(TestResult.created_at > cutoff_date)

    query = query.group_by(
        Artefact.name,
        Artefact.track,
        Artefact.stage,
        TestPlan.name,
        TestCase.name,
        TestResult.status,
        TestExecutionMetadata.category,
        TestExecutionMetadata.value,
    )

    count = 0
    for row in query.all():
        provider_endpoint, interface, requirer_endpoint, neighbor_asset = (
            extract_endpoint_info(row.test_plan_name, row.target_asset)
        )

        if not all([provider_endpoint, interface, requirer_endpoint, neighbor_asset]):
            continue

        test_executions_results_metadata_simple.labels(
            target_asset=row.target_asset,
            target_track=row.target_track or "",
            target_risk=row.target_risk,
            provider_endpoint=provider_endpoint,
            interface=interface,
            requirer_endpoint=requirer_endpoint,
            neighbor_asset=neighbor_asset,
            test_name=row.test_name,
            status=row.status.value,
            metadata_key=row.category,
            metadata_value=row.value,
        ).set(int(row.cnt))  # type: ignore[arg-type]
        count += 1

    return count

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

from dataclasses import replace

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from scripts.seed_performance_data import PROFILES, AlreadySeededError, SeedSummary, seed_performance_data
from test_observer.data_access.models import (
    Artefact,
    ArtefactBuildEnvironmentReview,
    IssueTestResultAttachment,
    IssueTestResultAttachmentRule,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import StageName, TestExecutionStatus, TestResultStatus
from tests.data_generator import DataGenerator


def _seed(db_session: Session, seed: int = 0) -> SeedSummary:
    return seed_performance_data(db_session.connection(), PROFILES["small"], seed=seed)


def test_seeds_the_profile_counts(db_session: Session):
    profile = PROFILES["small"]
    summary = _seed(db_session)

    assert summary.artefacts == profile.artefacts == db_session.scalar(select(func.count(Artefact.id)))
    assert summary.executions == profile.executions == db_session.scalar(select(func.count(TestExecution.id)))
    assert summary.results == profile.results == db_session.scalar(select(func.count(TestResult.id)))
    assert summary.io_log_bytes == db_session.scalar(select(func.sum(func.length(TestResult.io_log))))


def test_execution_status_follows_its_results(db_session: Session):
    _seed(db_session)

    failed_executions = set(
        db_session.scalars(
            select(TestResult.test_execution_id).where(TestResult.status == TestResultStatus.FAILED).distinct()
        )
    )
    statuses = {row.id: row.status for row in db_session.execute(select(TestExecution.id, TestExecution.status))}

    assert failed_executions
    for execution_id, status in statuses.items():
        expected = TestExecutionStatus.FAILED if execution_id in failed_executions else TestExecutionStatus.PASSED
        assert status == expected


def test_failed_results_report_the_failure_in_their_io_log(db_session: Session):
    _seed(db_session)

    logs = db_session.scalars(select(TestResult.io_log).where(TestResult.status == TestResultStatus.FAILED)).all()

    assert logs
    assert all("FAIL:" in log for log in logs)


def test_has_undecided_reviews_archived_artefacts_and_version_history(db_session: Session):
    _seed(db_session)

    undecided = db_session.scalar(
        select(func.count(ArtefactBuildEnvironmentReview.id)).where(
            func.cardinality(ArtefactBuildEnvironmentReview.review_decision) == 0
        )
    )
    archived = db_session.scalar(select(func.count(Artefact.id)).where(Artefact.archived))
    names_with_history = db_session.scalar(
        select(func.count()).select_from(
            select(Artefact.name).group_by(Artefact.name).having(func.count() > 1).subquery()
        )
    )

    assert undecided
    assert archived
    assert names_with_history == PROFILES["small"].artefacts // PROFILES["small"].versions


def test_same_seed_gives_the_same_data(db_session: Session):
    first = _seed(db_session, seed=5)
    logs = db_session.scalars(select(TestResult.io_log).order_by(TestResult.id)).all()
    db_session.rollback()

    second = _seed(db_session, seed=5)
    assert replace(second, seconds=0) == replace(first, seconds=0)
    assert db_session.scalars(select(TestResult.io_log).order_by(TestResult.id)).all() == logs


def test_refuses_to_seed_a_database_it_has_already_seeded(db_session: Session):
    _seed(db_session)

    with pytest.raises(AlreadySeededError, match="--truncate"):
        _seed(db_session)


def test_attaches_issues_to_failed_results_through_rules_with_metadata(db_session: Session):
    summary = _seed(db_session)

    attachments = db_session.scalars(select(IssueTestResultAttachment)).all()
    rules = db_session.scalars(select(IssueTestResultAttachmentRule)).all()

    assert summary.attachments == len(attachments) > 0
    assert len(rules) == PROFILES["small"].issues
    assert all(rule.execution_metadata for rule in rules)
    for attachment in attachments:
        assert attachment.test_result.status == TestResultStatus.FAILED
        # The rule that attached the issue matches its execution's metadata.
        rule_metadata = {(m.category, m.value) for m in attachment.attachment_rule.execution_metadata}
        execution_metadata = {(m.category, m.value) for m in attachment.test_result.test_execution.execution_metadata}
        assert rule_metadata and rule_metadata <= execution_metadata


def test_leaves_failed_results_it_did_not_create_alone(db_session: Session, generator: DataGenerator):
    build = generator.gen_artefact_build(generator.gen_artefact(StageName.beta))
    execution = generator.gen_test_execution(build, generator.gen_environment())
    existing = generator.gen_test_result(generator.gen_test_case(), execution, status=TestResultStatus.FAILED)

    _seed(db_session)

    attached = db_session.scalars(select(IssueTestResultAttachment.test_result_id)).all()
    assert attached
    assert existing.id not in attached

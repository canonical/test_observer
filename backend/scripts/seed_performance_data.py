#!/usr/bin/env python

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

"""Seed a database with synthetic data shaped for performance testing.

Unlike seed_data.py, which creates a handful of hand-written records through
the API for manual exploration, this script bulk-inserts a large, deterministic
data set straight into the tables, so the cost of an endpoint can be measured
at a realistic scale. It creates:

- reviewers assigned to artefacts, with environment reviews some of which are
  undecided,
- several versions of each artefact name, so previous-result lookups have
  history to walk,
- several executions per environment, so reruns and "latest execution"
  filters have something to exclude,
- many results per execution with io logs whose sizes follow a long tail,
  because the size of the io logs dominates the size of result payloads,
- issues attached to some of the failed results through attachment rules
  that match on execution metadata, which result responses also include.

Every artefact gets the same identity fields and a unique name, which satisfies
each family's uniqueness constraint without any family-specific logic.

The same profile and seed always produce the same rows. The database must be
migrated to head. Rows the script did not create are left alone, but it
refuses to run on a database it has already seeded: pass --truncate to empty
every table first.

Usage:
    python scripts/seed_performance_data.py [--profile small|medium|large]
        [--seed N] [--truncate]
"""

import argparse
import random
import sys
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from itertools import batched
from typing import Any

from sqlalchemy import Connection, Table, func, insert, select, text

from test_observer.data_access.models import (
    Artefact,
    ArtefactBuild,
    ArtefactBuildEnvironmentReview,
    Base,
    Environment,
    Issue,
    IssueTestResultAttachment,
    IssueTestResultAttachmentRule,
    IssueTestResultAttachmentRuleExecutionMetadata,
    TestCase,
    TestExecution,
    TestExecutionMetadata,
    TestPlan,
    TestResult,
    User,
    artefact_reviewers_association,
    environment_review_reviewers_association,
    test_execution_metadata_association_table,
)
from test_observer.data_access.models_enums import (
    ArtefactBuildEnvironmentReviewDecision,
    ArtefactStatus,
    FamilyName,
    IssueSource,
    IssueStatus,
    TestExecutionStatus,
    TestResultStatus,
)

# Rows are fixed in time so the data set does not depend on when it was seeded.
ANCHOR = datetime(2026, 1, 1, 12, 0, 0)
NAME_PREFIX = "perf"
INSERT_BATCH_SIZE = 2_000


@dataclass(frozen=True)
class PerformanceProfile:
    reviewers: int
    # Distinct artefact names per family. Each gets `versions` artefacts.
    names_per_family: int
    versions: int
    architectures: int
    # Environments per architecture. Every build is tested on each of them.
    environments: int
    # Executions per build and environment. All but the last are reruns.
    runs: int
    results_per_execution: int
    failure_rate: float
    # io log sizes: most are near the median, `large_log_rate` of them are large.
    median_log_bytes: int
    large_log_bytes: int
    large_log_rate: float
    reviewers_per_artefact: int
    # Issues, each with an attachment rule, and the share of failed results
    # attached to one of them.
    issues: int
    attached_failure_rate: float
    undecided_rate: float
    archived_rate: float

    @property
    def artefacts(self) -> int:
        return len(FamilyName) * self.names_per_family * self.versions

    @property
    def executions(self) -> int:
        return self.artefacts * self.architectures * self.environments * self.runs

    @property
    def results(self) -> int:
        return self.executions * self.results_per_execution


PROFILES = {
    # Seeds in a second or two, for tests of the tooling itself.
    "small": PerformanceProfile(
        reviewers=3,
        names_per_family=2,
        versions=2,
        architectures=2,
        environments=3,
        runs=2,
        results_per_execution=10,
        failure_rate=0.1,
        median_log_bytes=500,
        large_log_bytes=5_000,
        large_log_rate=0.05,
        reviewers_per_artefact=1,
        issues=3,
        attached_failure_rate=0.5,
        undecided_rate=0.5,
        archived_rate=0.1,
    ),
    # 115,200 results and about 375 MB of io logs.
    "medium": PerformanceProfile(
        reviewers=10,
        names_per_family=4,
        versions=3,
        architectures=2,
        environments=8,
        runs=2,
        results_per_execution=60,
        failure_rate=0.05,
        median_log_bytes=2_000,
        large_log_bytes=64_000,
        large_log_rate=0.02,
        reviewers_per_artefact=2,
        issues=20,
        attached_failure_rate=0.3,
        undecided_rate=0.3,
        archived_rate=0.1,
    ),
}
# About a million results and 3.3 GB of io logs.
PROFILES["large"] = replace(
    PROFILES["medium"], reviewers=15, names_per_family=8, environments=16, results_per_execution=130
)


@dataclass
class SeedSummary:
    reviewers: int
    artefacts: int
    builds: int
    environments: int
    executions: int
    results: int
    attachments: int
    io_log_bytes: int
    seconds: float


def _insert_returning_ids(connection: Connection, model: type[Base], rows: Sequence[dict[str, Any]]) -> list[int]:
    ids: list[int] = []
    for batch in batched(rows, INSERT_BATCH_SIZE):
        result = connection.execute(insert(model).returning(model.id, sort_by_parameter_order=True), list(batch))
        ids.extend(row[0] for row in result)
    return ids


def _insert(
    connection: Connection, target: type[Base] | Table, rows: Iterator[dict[str, Any]] | Sequence[dict[str, Any]]
) -> None:
    # One multi-row INSERT per batch: without RETURNING, pg8000's executemany
    # sends every row in its own round trip.
    for batch in batched(rows, INSERT_BATCH_SIZE):
        connection.execute(insert(target).values(list(batch)))


def _timestamps(moment: datetime) -> dict[str, datetime]:
    return {"created_at": moment, "updated_at": moment}


class _LogFactory:
    """Cuts io logs of a chosen size out of one precomputed block of log lines."""

    def __init__(self, rng: random.Random, profile: PerformanceProfile):
        self.rng = rng
        self.profile = profile
        lines = [f"[{index:04d}] step completed: value={rng.randrange(10**8):08d} status=ok" for index in range(512)]
        pool = "\n".join(lines) + "\n"
        # Long enough for a slice of the largest log starting anywhere in the pool.
        self.block = pool * (2 + profile.large_log_bytes // len(pool))
        self.pool_size = len(pool)

    def _size(self) -> int:
        if self.rng.random() < self.profile.large_log_rate:
            return self.profile.large_log_bytes
        spread = self.profile.median_log_bytes // 2
        return max(1, self.profile.median_log_bytes + self.rng.randint(-spread, spread))

    def log(self, case_name: str, status: TestResultStatus) -> str:
        size = self._size()
        start = self.rng.randrange(self.pool_size)
        text_ = f"Running {case_name}\n" + self.block[start : start + size]
        if status == TestResultStatus.FAILED:
            text_ += f"\nFAIL: {case_name} exited with status {self.rng.choice((1, 2, 124))}"
        return text_ + "\n"


class AlreadySeededError(RuntimeError):
    """The database already holds rows from an earlier run of this script."""


def seed_performance_data(connection: Connection, profile: PerformanceProfile, *, seed: int = 0) -> SeedSummary:
    """Insert the synthetic data set on an open connection. The caller commits."""
    # The rows have fixed names, so a second run would fail on the first
    # unique constraint it meets.
    if connection.scalar(select(func.count()).select_from(User).where(User.email.startswith(f"{NAME_PREFIX}-"))):
        raise AlreadySeededError("this database has already been seeded, pass --truncate to start from empty tables")
    started = time.monotonic()
    rng = random.Random(seed)
    logs = _LogFactory(rng, profile)

    reviewer_ids = _insert_returning_ids(
        connection,
        User,
        [
            {
                "email": f"{NAME_PREFIX}-reviewer-{index}@example.com",
                "launchpad_handle": f"{NAME_PREFIX}-reviewer-{index}",
                "name": f"Performance Reviewer {index}",
                "is_admin": False,
                **_timestamps(ANCHOR),
            }
            for index in range(profile.reviewers)
        ],
    )

    [test_plan_id] = _insert_returning_ids(
        connection, TestPlan, [{"name": f"{NAME_PREFIX}::full", **_timestamps(ANCHOR)}]
    )

    architectures = [f"arch{index}" for index in range(profile.architectures)]
    environment_rows: list[dict[str, Any]] = [
        {
            "name": f"{NAME_PREFIX}-{architecture}-machine-{index:03d}",
            "architecture": architecture,
            **_timestamps(ANCHOR),
        }
        for architecture in architectures
        for index in range(profile.environments)
    ]
    environment_ids = _insert_returning_ids(connection, Environment, environment_rows)
    environments_by_architecture: dict[str, list[int]] = {architecture: [] for architecture in architectures}
    for row, environment_id in zip(environment_rows, environment_ids, strict=True):
        environments_by_architecture[row["architecture"]].append(environment_id)

    case_names = [
        f"{NAME_PREFIX}/suite-{index % 12:02d}/case-{index:04d}" for index in range(profile.results_per_execution)
    ]
    case_ids = _insert_returning_ids(
        connection,
        TestCase,
        [
            {"name": name, "category": name.split("/")[1], "template_id": "", **_timestamps(ANCHOR)}
            for name in case_names
        ],
    )

    artefact_rows: list[dict[str, Any]] = []
    for family in FamilyName:
        for name_index in range(profile.names_per_family):
            for version in range(profile.versions):
                serial = len(artefact_rows)
                created = ANCHOR + timedelta(days=7 * version, minutes=serial)
                artefact_rows.append(
                    {
                        "name": f"{NAME_PREFIX}-{family}-{name_index:03d}",
                        "version": f"1.{version}",
                        "family": family,
                        "stage": "candidate",
                        "track": "latest",
                        "store": "",
                        "branch": "",
                        "series": "",
                        "repo": "",
                        "source": "",
                        "os": "",
                        "release": "",
                        "owner": "",
                        "image_url": "",
                        "comment": "",
                        "sha256": f"{serial:064x}",
                        "status": ArtefactStatus.UNDECIDED,
                        "archived": rng.random() < profile.archived_rate,
                        **_timestamps(created),
                    }
                )
    artefact_ids = _insert_returning_ids(connection, Artefact, artefact_rows)

    _insert(
        connection,
        artefact_reviewers_association,
        [
            {"artefact_id": artefact_id, "user_id": reviewer_id}
            for artefact_id in artefact_ids
            for reviewer_id in rng.sample(reviewer_ids, min(profile.reviewers_per_artefact, len(reviewer_ids)))
        ],
    )

    build_rows: list[dict[str, Any]] = [
        {
            "artefact_id": artefact_id,
            "architecture": architecture,
            "revision": 1,
            **_timestamps(artefact_row["created_at"]),
        }
        for artefact_id, artefact_row in zip(artefact_ids, artefact_rows, strict=True)
        for architecture in architectures
    ]
    build_ids = _insert_returning_ids(connection, ArtefactBuild, build_rows)

    review_rows: list[dict[str, Any]] = []
    execution_rows: list[dict[str, Any]] = []
    for build_id, build_row in zip(build_ids, build_rows, strict=True):
        for environment_position, environment_id in enumerate(environments_by_architecture[build_row["architecture"]]):
            undecided = rng.random() < profile.undecided_rate
            review_rows.append(
                {
                    "artefact_build_id": build_id,
                    "environment_id": environment_id,
                    "review_decision": []
                    if undecided
                    else [ArtefactBuildEnvironmentReviewDecision.APPROVED_ALL_TESTS_PASS],
                    "review_comment": "",
                    **_timestamps(build_row["created_at"]),
                }
            )
            for run in range(profile.runs):
                started_at = build_row["created_at"] + timedelta(hours=1 + environment_position, minutes=15 * run)
                execution_rows.append(
                    {
                        "artefact_build_id": build_id,
                        "environment_id": environment_id,
                        "test_plan_id": test_plan_id,
                        "status": TestExecutionStatus.PASSED,
                        "ci_link": None,
                        "c3_link": None,
                        "resource_url": "",
                        "created_at": started_at,
                        "updated_at": started_at + timedelta(minutes=10),
                    }
                )
    review_ids = _insert_returning_ids(connection, ArtefactBuildEnvironmentReview, review_rows)
    _insert(
        connection,
        environment_review_reviewers_association,
        [{"environment_review_id": review_id, "user_id": rng.choice(reviewer_ids)} for review_id in review_ids],
    )

    # Decide every result's status first so each execution's status matches its results.
    statuses_per_execution = [
        [TestResultStatus.FAILED if rng.random() < profile.failure_rate else TestResultStatus.PASSED for _ in case_ids]
        for _ in execution_rows
    ]
    for row, statuses in zip(execution_rows, statuses_per_execution, strict=True):
        if TestResultStatus.FAILED in statuses:
            row["status"] = TestExecutionStatus.FAILED
    execution_ids = _insert_returning_ids(connection, TestExecution, execution_rows)

    log_bytes = 0

    def result_rows() -> Iterator[dict[str, Any]]:
        nonlocal log_bytes
        for execution_id, execution_row, statuses in zip(
            execution_ids, execution_rows, statuses_per_execution, strict=True
        ):
            for case_id, case_name, status in zip(case_ids, case_names, statuses, strict=True):
                io_log = logs.log(case_name, status)
                log_bytes += len(io_log)
                yield {
                    "test_execution_id": execution_id,
                    "test_case_id": case_id,
                    "status": status,
                    "comment": "",
                    "io_log": io_log,
                    **_timestamps(execution_row["created_at"]),
                }

    _insert(connection, TestResult, result_rows())

    attachments = _attach_issues(connection, profile, rng, execution_ids)

    return SeedSummary(
        reviewers=len(reviewer_ids),
        artefacts=len(artefact_ids),
        builds=len(build_ids),
        environments=len(environment_ids),
        executions=len(execution_ids),
        results=len(execution_ids) * len(case_ids),
        attachments=attachments,
        io_log_bytes=log_bytes,
        seconds=round(time.monotonic() - started, 1),
    )


def _attach_issues(
    connection: Connection, profile: PerformanceProfile, rng: random.Random, execution_ids: Sequence[int]
) -> int:
    """Attach issues to a share of this seed's failed results, each through a rule.

    Each issue has a rule that matches on one execution metadata value, and
    every seeded execution carries one of those values. A failed result is
    only ever attached through the rule its execution matches, and only the
    executions in `execution_ids` are considered.
    """
    if not profile.issues or not execution_ids:
        return 0
    values = [f"{NAME_PREFIX}-rule-{index}" for index in range(profile.issues)]
    issue_ids = _insert_returning_ids(
        connection,
        Issue,
        [
            {
                "source": IssueSource.JIRA,
                "project": NAME_PREFIX.upper(),
                "key": f"{NAME_PREFIX.upper()}-{index + 1}",
                "title": f"Synthetic failure {index + 1}",
                "status": IssueStatus.OPEN,
                **_timestamps(ANCHOR),
            }
            for index in range(profile.issues)
        ],
    )
    rule_ids = _insert_returning_ids(
        connection,
        IssueTestResultAttachmentRule,
        [{"issue_id": issue_id, "enabled": True, **_timestamps(ANCHOR)} for issue_id in issue_ids],
    )
    _insert(
        connection,
        IssueTestResultAttachmentRuleExecutionMetadata,
        [
            {"attachment_rule_id": rule_id, "category": NAME_PREFIX, "value": value, **_timestamps(ANCHOR)}
            for rule_id, value in zip(rule_ids, values, strict=True)
        ],
    )
    metadata_ids = _insert_returning_ids(
        connection,
        TestExecutionMetadata,
        [{"category": NAME_PREFIX, "value": value, **_timestamps(ANCHOR)} for value in values],
    )
    rule_of_execution = {execution_id: rng.randrange(profile.issues) for execution_id in execution_ids}
    _insert(
        connection,
        test_execution_metadata_association_table,
        [
            {"test_execution_id": execution_id, "test_execution_metadata_id": metadata_ids[rule]}
            for execution_id, rule in rule_of_execution.items()
        ],
    )

    # The range narrows the scan; the membership check keeps only this seed's
    # executions even if another writer interleaved IDs.
    failed = connection.execute(
        select(TestResult.id, TestResult.test_execution_id)
        .where(
            TestResult.status == TestResultStatus.FAILED,
            TestResult.test_execution_id.between(min(execution_ids), max(execution_ids)),
        )
        .order_by(TestResult.id)
    ).all()
    rows = [
        {
            "issue_id": issue_ids[rule_of_execution[execution_id]],
            "attachment_rule_id": rule_ids[rule_of_execution[execution_id]],
            "test_result_id": result_id,
            **_timestamps(ANCHOR),
        }
        for result_id, execution_id in failed
        if execution_id in rule_of_execution and rng.random() < profile.attached_failure_rate
    ]
    _insert(connection, IssueTestResultAttachment, rows)
    return len(rows)


def truncate_all(connection: Connection) -> None:
    """Remove every row from every application table, keeping the schema."""
    tables = connection.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version'")
    ).scalars()
    names = ", ".join(f'"{name}"' for name in tables)
    if names:
        connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profile", choices=sorted(PROFILES), default="medium")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--truncate", action="store_true", help="empty every table first")
    args = parser.parse_args(argv)
    profile = PROFILES[args.profile]

    from test_observer.data_access.setup import engine

    sys.stdout.write(
        f"Seeding {profile.artefacts} artefacts, {profile.executions} executions "
        f"and {profile.results} results ({args.profile} profile, seed {args.seed})\n"
    )
    with engine.connect() as connection:
        if args.truncate:
            truncate_all(connection)
        try:
            summary = seed_performance_data(connection, profile, seed=args.seed)
        except AlreadySeededError as error:
            raise SystemExit(f"error: {error}") from error
        connection.commit()
    sys.stdout.write(
        f"Seeded {summary.results} results with {summary.io_log_bytes / 1e6:.1f} MB of io logs in {summary.seconds} s\n"
    )


if __name__ == "__main__":
    main()

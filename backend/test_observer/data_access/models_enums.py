# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from enum import StrEnum


class FamilyName(StrEnum):
    snap = "snap"
    deb = "deb"
    charm = "charm"
    image = "image"
    solution = "solution"


class TestExecutionStatus(StrEnum):
    __test__ = False

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_TESTED = "NOT_TESTED"
    ENDED_PREMATURELY = "ENDED_PREMATURELY"


class ArtefactBuildEnvironmentReviewDecision(StrEnum):
    REJECTED = "REJECTED"
    APPROVED_INCONSISTENT_TEST = "APPROVED_INCONSISTENT_TEST"
    APPROVED_UNSTABLE_PHYSICAL_INFRA = "APPROVED_UNSTABLE_PHYSICAL_INFRA"
    APPROVED_CUSTOMER_PREREQUISITE_FAIL = "APPROVED_CUSTOMER_PREREQUISITE_FAIL"
    APPROVED_FAULTY_HARDWARE = "APPROVED_FAULTY_HARDWARE"
    APPROVED_ALL_TESTS_PASS = "APPROVED_ALL_TESTS_PASS"


class ArtefactStatus(StrEnum):
    APPROVED = "APPROVED"
    MARKED_AS_FAILED = "MARKED_AS_FAILED"
    UNDECIDED = "UNDECIDED"


class TestResultStatus(StrEnum):
    __test__ = False

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class IssueSource(StrEnum):
    JIRA = "jira"
    GITHUB = "github"
    LAUNCHPAD = "launchpad"


class IssueStatus(StrEnum):
    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"


class NotificationType(StrEnum):
    USER_ASSIGNED_ARTEFACT_REVIEW = "USER_ASSIGNED_ARTEFACT_REVIEW"
    USER_ASSIGNED_ENVIRONMENT_REVIEW = "USER_ASSIGNED_ENVIRONMENT_REVIEW"

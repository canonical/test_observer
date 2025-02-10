# Copyright (C) 2023-2025 Canonical Ltd.
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


from enum import Enum


class FamilyName(str, Enum):
    snap = "snap"
    deb = "deb"
    charm = "charm"
    image = "image"


class StageName(str, Enum):
    proposed = "proposed"
    updates = "updates"
    edge = "edge"
    beta = "beta"
    candidate = "candidate"
    stable = "stable"
    pending = "pending"
    current = "current"

    def _compare(self, other: str) -> int:
        stages = list(StageName.__members__.values())
        return stages.index(self) - stages.index(StageName(other))

    def __lt__(self, other: str) -> bool:
        return self._compare(other) < 0

    def __le__(self, other: str) -> bool:
        return self._compare(other) <= 0

    def __gt__(self, other: str) -> bool:
        return self._compare(other) > 1

    def __ge__(self, other: str) -> bool:
        return self._compare(other) >= 0


class TestExecutionStatus(str, Enum):
    __test__ = False

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_TESTED = "NOT_TESTED"
    ENDED_PREMATURELY = "ENDED_PREMATURELY"


class ArtefactBuildEnvironmentReviewDecision(str, Enum):
    REJECTED = "REJECTED"
    APPROVED_INCONSISTENT_TEST = "APPROVED_INCONSISTENT_TEST"
    APPROVED_UNSTABLE_PHYSICAL_INFRA = "APPROVED_UNSTABLE_PHYSICAL_INFRA"
    APPROVED_CUSTOMER_PREREQUISITE_FAIL = "APPROVED_CUSTOMER_PREREQUISITE_FAIL"
    APPROVED_FAULTY_HARDWARE = "APPROVED_FAULTY_HARDWARE"
    APPROVED_ALL_TESTS_PASS = "APPROVED_ALL_TESTS_PASS"


class ArtefactStatus(str, Enum):
    APPROVED = "APPROVED"
    MARKED_AS_FAILED = "MARKED_AS_FAILED"
    UNDECIDED = "UNDECIDED"


class TestResultStatus(str, Enum):
    __test__ = False

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

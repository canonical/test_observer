# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
#        Omar Selo <omar.selo@canonical.com>


from enum import Enum


class FamilyName(str, Enum):
    snap = "snap"
    deb = "deb"
    charm = "charm"


class StageName(str, Enum):
    proposed = "proposed"
    updates = "updates"
    edge = "edge"
    beta = "beta"
    candidate = "candidate"
    stable = "stable"


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

# Copyright 2026 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import patch

import ops
import ops.testing
from validators.base import (
    BaseValidator,
    ValidationLevel,
    ValidationResult,
    ValidationResultStatus,
)
from validators.update_status_check import UpdateStatusCheckResults

from charm import TestObserverBackendCharm


def _results(*statuses: ValidationResultStatus) -> UpdateStatusCheckResults:
    return UpdateStatusCheckResults(
        results=[
            ValidationResult(
                status=status,
                endpoint="database",
                interface="postgresql_client",
                role="requires",
                level="simple",
                relation_id=1,
                error="boom" if status == "ERROR" else None,
            )
            for status in statuses
        ]
    )


def _make_stub_validator(
    status: ValidationResultStatus, error: str | None = None
) -> type[BaseValidator]:
    """Build a BaseValidator subclass whose `validate()` returns a fixed result.

    Used to control ValidatorRunner's output deterministically in the
    `validate` action tests without depending on a real database connection.
    """

    class _StubValidator(BaseValidator):
        def validate(self, level: ValidationLevel = "simple") -> ValidationResult:
            return ValidationResult(
                status=status,
                endpoint=self.endpoint,
                interface="postgresql_client",
                role=self.role,
                level=level,
                relation_id=self.relation_id,
                error=error,
            )

    return _StubValidator


class TestIntegrationValidation(unittest.TestCase):
    def setUp(self):
        self.harness = ops.testing.Harness(TestObserverBackendCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_update_status_sets_blocked_on_failing_check(self):
        with patch("charm.run_simple_check", return_value=_results("FAIL")):
            self.harness.charm.on.update_status.emit()

        self.harness.evaluate_status()
        self.assertIsInstance(self.harness.model.unit.status, ops.BlockedStatus)
        self.assertIn("database", self.harness.model.unit.status.message)

    def test_update_status_sets_error_on_erroring_check(self):
        with patch("charm.run_simple_check", return_value=_results("ERROR")):
            self.harness.charm.on.update_status.emit()

        self.harness.evaluate_status()
        self.assertIsInstance(self.harness.model.unit.status, ops.BlockedStatus)

    def test_update_status_clears_previous_failure_once_passing(self):
        with patch("charm.run_simple_check", return_value=_results("FAIL")):
            self.harness.charm.on.update_status.emit()

        with patch("charm.run_simple_check", return_value=_results("PASS")):
            self.harness.charm.on.update_status.emit()

        self.harness.evaluate_status()
        self.assertNotIsInstance(self.harness.model.unit.status, ops.BlockedStatus)

    def test_validate_action_returns_results_and_defaults_to_simple(self):
        self.harness.add_relation("database", "postgresql")

        with patch(
            "validators.validate_action.validate_action._load_validators",
            return_value={"postgresql_client": [_make_stub_validator("PASS")]},
        ):
            output = self.harness.run_action("validate")

        self.assertIn("results", output.results)
        self.assertIn('"level":"simple"', output.results["results"])

    def test_validate_action_respects_level_param(self):
        self.harness.add_relation("database", "postgresql")

        with patch(
            "validators.validate_action.validate_action._load_validators",
            return_value={"postgresql_client": [_make_stub_validator("PASS")]},
        ):
            output = self.harness.run_action("validate", {"level": "deep"})

        self.assertIn('"level":"deep"', output.results["results"])

    def test_validate_action_fails_on_error_result(self):
        self.harness.add_relation("database", "postgresql")

        with patch(
            "validators.validate_action.validate_action._load_validators",
            return_value={"postgresql_client": [_make_stub_validator("ERROR", error="boom")]},
        ):
            with self.assertRaises(ops.testing.ActionFailed) as ctx:
                self.harness.run_action("validate")

        self.assertIn("boom", ctx.exception.message)
        self.assertIn("results", ctx.exception.output.results)

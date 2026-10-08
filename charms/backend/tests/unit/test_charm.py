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

    Used to control the engine's output deterministically in the `validate`
    action tests without depending on a real database connection.
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
        self.harness.set_leader(True)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def _add_ready_database_relation(self):
        """Add a database relation with endpoint data so the check is not skipped."""
        relation_id = self.harness.add_relation("database", "postgresql")
        self.harness.update_relation_data(
            relation_id,
            "postgresql",
            {
                "endpoints": "postgresql:5432",
                "username": "test_observer",
                "password": "test_password",
                "database": "test_observer_db",
            },
        )
        # Relation hooks wait for Pebble in the harness; these tests exercise
        # validation status, not workload startup.
        self.harness.model.unit.status = ops.ActiveStatus()
        return relation_id

    def _run_update_status(self):
        with patch.object(self.harness.charm, "_migrations_ready", return_value=True):
            self.harness.charm.on.update_status.emit()
        self.harness.evaluate_status()

    def test_update_status_sets_blocked_on_failing_check(self):
        self._add_ready_database_relation()
        with patch("charm.run_simple_check", return_value=_results("FAIL")):
            self._run_update_status()
        self.assertIsInstance(self.harness.model.unit.status, ops.BlockedStatus)
        self.assertIn("database", self.harness.model.unit.status.message)

    def test_update_status_sets_blocked_on_erroring_check(self):
        self._add_ready_database_relation()
        with patch("charm.run_simple_check", return_value=_results("ERROR")):
            self._run_update_status()
        self.assertIsInstance(self.harness.model.unit.status, ops.BlockedStatus)

    def test_update_status_clears_previous_failure_once_passing(self):
        self._add_ready_database_relation()
        with patch("charm.run_simple_check", return_value=_results("FAIL")):
            self._run_update_status()

        with patch("charm.run_simple_check", return_value=_results("PASS")):
            self._run_update_status()
        self.assertIsInstance(self.harness.model.unit.status, ops.ActiveStatus)

    def test_update_status_preserves_other_blocked_status(self):
        self._add_ready_database_relation()
        with patch("charm.run_simple_check", return_value=_results("FAIL")):
            self._run_update_status()

        self.harness.model.unit.status = ops.BlockedStatus("Unrelated failure")
        with patch("charm.run_simple_check", return_value=_results("PASS")):
            self._run_update_status()

        self.assertEqual(self.harness.model.unit.status, ops.BlockedStatus("Unrelated failure"))

    def test_collect_status_preserves_waiting_status_over_validation_failure(self):
        self._add_ready_database_relation()
        with patch("charm.run_simple_check", return_value=_results("FAIL")):
            self._run_update_status()

        self.harness.model.unit.status = ops.WaitingStatus("Waiting for database migration")
        self.harness.evaluate_status()

        self.assertEqual(
            self.harness.model.unit.status,
            ops.WaitingStatus("Waiting for database migration"),
        )

    def test_update_status_skips_check_until_database_relation_ready(self):
        # GIVEN no database relation at all
        self.harness.model.unit.status = ops.ActiveStatus()

        # WHEN update-status runs
        with patch("charm.run_simple_check", return_value=_results("ERROR")) as run_check:
            self._run_update_status()

        # THEN the validator engine is skipped and the unit waits for the relation
        run_check.assert_not_called()
        self.assertEqual(
            self.harness.model.unit.status,
            ops.WaitingStatus("Waiting for database relation"),
        )

    def test_update_status_waits_for_complete_database_relation_data(self):
        # GIVEN a relation with endpoints but no credentials
        relation_id = self.harness.add_relation("database", "postgresql")
        self.harness.update_relation_data(
            relation_id, "postgresql", {"endpoints": "postgresql:5432"}
        )
        self.harness.model.unit.status = ops.ActiveStatus()

        # WHEN update-status runs
        with patch("charm.run_simple_check") as run_check:
            self._run_update_status()

        # THEN validation is skipped until all required connection data is present
        run_check.assert_not_called()
        self.assertEqual(
            self.harness.model.unit.status,
            ops.WaitingStatus("Waiting for database relation"),
        )

    def test_update_status_waits_when_database_data_disappears_after_failure(self):
        # GIVEN a previously failing validation with a ready relation
        relation_id = self._add_ready_database_relation()
        with patch("charm.run_simple_check", return_value=_results("FAIL")):
            self._run_update_status()
        self.assertIsInstance(self.harness.model.unit.status, ops.BlockedStatus)

        # WHEN the database stops publishing connection data
        self.harness.update_relation_data(relation_id, "postgresql", {"endpoints": ""})
        with patch("charm.run_simple_check") as run_check:
            self._run_update_status()

        # THEN the stale validator failure is cleared but the unit does not appear healthy
        run_check.assert_not_called()
        self.assertEqual(
            self.harness.model.unit.status,
            ops.WaitingStatus("Waiting for database relation"),
        )

    def test_update_status_recovers_when_database_data_returns(self):
        # GIVEN a relation without usable connection data
        relation_id = self.harness.add_relation("database", "postgresql")
        self.harness.model.unit.status = ops.ActiveStatus()
        self._run_update_status()
        self.assertEqual(
            self.harness.model.unit.status,
            ops.WaitingStatus("Waiting for database relation"),
        )

        # WHEN the relation publishes complete connection data
        self.harness.update_relation_data(
            relation_id,
            "postgresql",
            {
                "endpoints": "postgresql:5432",
                "username": "test_observer",
                "password": "test_password",
            },
        )
        self.harness.model.unit.status = ops.WaitingStatus("Waiting for database relation")
        with patch("charm.run_simple_check", return_value=_results("PASS")) as run_check:
            self._run_update_status()

        # THEN validation resumes and clears the relation wait
        run_check.assert_called_once()
        self.assertIsInstance(self.harness.model.unit.status, ops.ActiveStatus)

    def test_validate_action_returns_results_and_defaults_to_simple(self):
        self._add_ready_database_relation()

        with patch(
            "validators.engine.engine.load_validators",
            return_value={"postgresql_client": [_make_stub_validator("PASS")]},
        ):
            output = self.harness.run_action("validate")

        self.assertIn("results", output.results)
        self.assertIn('"status": "PASS"', output.results["results"])
        self.assertIn('"level": "simple"', output.results["results"])

    def test_validate_action_respects_level_param(self):
        self._add_ready_database_relation()

        with patch(
            "validators.engine.engine.load_validators",
            return_value={"postgresql_client": [_make_stub_validator("PASS")]},
        ):
            output = self.harness.run_action("validate", {"level": "deep"})

        self.assertIn('"level": "deep"', output.results["results"])

    def test_validate_action_fails_on_error_result(self):
        self._add_ready_database_relation()

        with patch(
            "validators.engine.engine.load_validators",
            return_value={"postgresql_client": [_make_stub_validator("ERROR", error="boom")]},
        ):
            with self.assertRaises(ops.testing.ActionFailed) as ctx:
                self.harness.run_action("validate")

        self.assertIn("boom", ctx.exception.message)
        self.assertIn("results", ctx.exception.output.results)

    def test_validate_action_fails_when_no_validators_are_discovered(self):
        self._add_ready_database_relation()

        with patch("validators.engine.engine.load_validators", return_value={}):
            with self.assertRaises(ops.testing.ActionFailed) as ctx:
                self.harness.run_action("validate")

        self.assertIn("No validators produced validation results", ctx.exception.message)

    def test_validate_action_reports_skipped_when_relation_not_ready(self):
        # GIVEN a database relation with no data published yet (e.g. right
        # after `juju integrate`, before the two ends negotiate)
        relation_id = self.harness.add_relation("database", "postgresql")
        self.harness.update_relation_data(
            relation_id, self.harness.model.app.name, {"database": ""}
        )
        relation = self.harness.model.relations["database"][0]
        self.assertEqual(dict(relation.data[self.harness.model.app]), {})
        self.assertEqual(dict(relation.data[relation.app]), {})

        # WHEN the validate action runs
        with patch(
            "validators.engine.engine.load_validators",
            return_value={"postgresql_client": [_make_stub_validator("PASS")]},
        ):
            output = self.harness.run_action("validate")

        # THEN the engine reports SKIPPED rather than running (and failing)
        # the validator against an incomplete databag
        self.assertIn('"status": "SKIPPED"', output.results["results"])

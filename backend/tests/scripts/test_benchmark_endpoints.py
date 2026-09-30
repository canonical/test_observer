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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scripts.benchmark_endpoints import format_table, run_benchmark
from scripts.seed_performance_data import PROFILES, seed_performance_data
from test_observer.common.enums import Permission
from tests.conftest import override_permissions


@pytest.fixture
def seeded(db_session: Session) -> Session:
    seed_performance_data(db_session.connection(), PROFILES["small"])
    return db_session


def test_measures_every_scenario_on_seeded_data(seeded: Session, test_client: TestClient):
    with override_permissions(*Permission):
        targets, measurements = run_benchmark(test_client, seeded.connection(), 1)

    assert all(value is not None for value in targets.values())
    assert [m.status for m in measurements] == [200] * len(measurements)
    by_name = {m.scenario: m for m in measurements}
    assert by_name["execution-search-50"].items == 50
    assert by_name["execution-search-count"].items == 0
    assert by_name["execution-results"].items == PROFILES["small"].results_per_execution
    assert all(m.sql_statements > 0 and m.response_bytes > 0 for m in measurements)
    assert format_table(measurements).count("\n") == len(measurements) + 1


def test_runs_only_the_selected_scenarios(seeded: Session, test_client: TestClient):
    with override_permissions(*Permission):
        _, measurements = run_benchmark(test_client, seeded.connection(), 1, ["artefact-builds"])

    assert [m.scenario for m in measurements] == ["artefact-builds"]


def test_rejects_an_unknown_scenario(seeded: Session, test_client: TestClient):
    with pytest.raises(ValueError, match="no-such-scenario"):
        run_benchmark(test_client, seeded.connection(), 1, ["no-such-scenario"])

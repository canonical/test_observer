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

from test_observer.common.enums import Permission
from test_observer.data_access.models import IssueTestResultAttachment
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


@pytest.mark.parametrize(
    "endpoint,permission,result_key",
    [
        ("/v1/artefacts/search", Permission.view_artefact, "artefacts"),
        ("/v1/environments", Permission.view_test, "environments"),
        ("/v1/test-plans", Permission.view_test, "test_plans"),
        ("/v1/test-cases", Permission.view_test, "test_cases"),
        ("/v1/test-results", Permission.view_test, "test_results"),
        ("/v1/test-executions", Permission.view_test, "test_executions"),
        ("/v1/issues", Permission.view_issue, "issues"),
    ],
)
@pytest.mark.parametrize(
    "families",
    [
        ["unregistered"],
        [""],
        ["unregistered", ""],
        ["unregistered", "custom", ""],
    ],
)
def test_list_family_filters(
    test_client: TestClient,
    generator: DataGenerator,
    db_session: Session,
    endpoint: str,
    permission: Permission,
    result_key: str,
    families: list[str],
) -> None:
    for family in ("custom", "other"):
        generator.gen_family(family)
        artefact = generator.gen_artefact(family=family, name=family)
        execution = generator.gen_test_execution(
            generator.gen_artefact_build(artefact),
            generator.gen_environment(name=family),
            test_plan=family,
        )
        result = generator.gen_test_result(generator.gen_test_case(name=family), execution)
        issue = generator.gen_issue(key=family)
        db_session.add(IssueTestResultAttachment(issue=issue, test_result=result))
    db_session.commit()

    baseline = make_authenticated_request(
        lambda: test_client.get(endpoint, params={"families": "custom"}),
        permission,
    )
    assert baseline.status_code == 200
    assert len(baseline.json()[result_key]) == 1

    response = make_authenticated_request(
        lambda: test_client.get(endpoint, params=[("families", family) for family in families]),
        permission,
    )

    assert response.status_code == 200
    expected = baseline.json()[result_key] if "custom" in families else []
    assert response.json()[result_key] == expected
    if "count" in response.json():
        assert response.json()["count"] == len(expected)

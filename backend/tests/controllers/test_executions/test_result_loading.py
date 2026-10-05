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

"""How many queries the test execution endpoints make, and what they read.

Results carry their full io_log, so a response that reads them more often
than it uses them, or loads related rows one at a time, costs memory and
time in proportion to the page. These tests pin the number of queries and
how often io logs are read, independent of the data's size.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.data_access.models import (
    IssueTestResultAttachment,
    IssueTestResultAttachmentRule,
    IssueTestResultAttachmentRuleExecutionMetadata,
)
from test_observer.data_access.models_enums import TestResultStatus
from tests.conftest import override_permissions
from tests.data_generator import DataGenerator


@contextmanager
def _statements(db_session: Session) -> Iterator[list[str]]:
    """Collect the SQL statements run on the test session's connection."""
    statements: list[str] = []
    connection = db_session.connection()

    def record(_conn: object, _cursor: object, statement: str, *_: object) -> None:
        statements.append(statement)

    event.listen(connection, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(connection, "before_cursor_execute", record)


def _seed(generator: DataGenerator, db_session: Session, executions: int) -> str:
    """One artefact with `executions` executions, each with a passed result and a
    failed one attached to an issue through its own rule with metadata."""
    name = f"loading_{uuid.uuid4().hex[:8]}"
    build = generator.gen_artefact_build(generator.gen_artefact(name=name))
    environment = generator.gen_environment(name=f"{name}_env")
    passed = generator.gen_test_case(name=f"{name}_passed")
    failed = generator.gen_test_case(name=f"{name}_failed")
    for index in range(executions):
        execution = generator.gen_test_execution(build, environment, ci_link=f"https://ci.example.com/{name}/{index}")
        generator.gen_test_result(passed, execution, io_log="ok\n" * 10)
        result = generator.gen_test_result(failed, execution, TestResultStatus.FAILED, io_log="FAIL\n" * 10)
        issue = generator.gen_issue(key=f"{name}-{index}")
        rule = IssueTestResultAttachmentRule(
            issue=issue,
            execution_metadata=[
                IssueTestResultAttachmentRuleExecutionMetadata(category="loading", value=f"{name}-{index}")
            ],
        )
        db_session.add_all([rule, IssueTestResultAttachment(issue=issue, test_result=result, attachment_rule=rule)])
    db_session.flush()
    return name


def _search(test_client: TestClient, db_session: Session, artefact: str) -> tuple[list[str], dict]:
    # Start from an empty identity map, so nothing the test created is reused
    # and every search makes the queries a fresh request would.
    db_session.expunge_all()
    with override_permissions(Permission.view_test), _statements(db_session) as statements:
        response = test_client.get("/v1/test-executions", params={"artefacts": artefact, "limit": 50})
    assert response.status_code == 200
    return statements, response.json()


def test_search_reads_each_io_log_once(test_client: TestClient, generator: DataGenerator, db_session: Session):
    artefact = _seed(generator, db_session, executions=3)

    statements, body = _search(test_client, db_session, artefact)

    assert len(body["test_executions"]) == 3
    assert all(len(execution["test_results"]) == 2 for execution in body["test_executions"])
    assert sum(".io_log" in statement for statement in statements) == 1


def test_search_queries_do_not_grow_with_the_page(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    small, _ = _search(test_client, db_session, _seed(generator, db_session, executions=2))
    large, body = _search(test_client, db_session, _seed(generator, db_session, executions=6))

    assert len(body["test_executions"]) == 6
    attachments = [
        issue
        for execution in body["test_executions"]
        for result in execution["test_results"]
        for issue in result["issues"]
    ]
    assert len(attachments) == 6
    assert all(attachment["attachment_rule"]["execution_metadata"] for attachment in attachments)
    assert len(large) == len(small)


def test_get_test_execution_does_not_read_results(
    test_client: TestClient, generator: DataGenerator, db_session: Session
):
    build = generator.gen_artefact_build(generator.gen_artefact(name=f"loading_{uuid.uuid4().hex[:8]}"))
    execution = generator.gen_test_execution(build, generator.gen_environment())
    generator.gen_test_result(generator.gen_test_case(), execution, io_log="log\n" * 10)
    execution_id = execution.id
    db_session.expunge_all()

    with override_permissions(Permission.view_test), _statements(db_session) as statements:
        response = test_client.get(f"/v1/test-executions/{execution_id}")

    assert response.status_code == 200
    assert not any(".io_log" in statement for statement in statements)

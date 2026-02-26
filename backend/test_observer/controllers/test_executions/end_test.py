# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import (
    ArtefactBuild,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.models_enums import (
    TestExecutionStatus,
    TestResultStatus,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db
from test_observer.controllers.issues.attachment_rules_logic import (
    apply_test_result_attachment_rules,
)

from .logic import delete_previous_results
from .models import C3TestResult, C3TestResultStatus, EndTestExecutionRequest

router = APIRouter()


@router.put(
    "/end-test",
    dependencies=[Security(permission_checker, scopes=[Permission.change_test])],
)
def end_test_execution(request: EndTestExecutionRequest, db: Session = Depends(get_db)):
    test_execution = _find_related_test_execution(request, db)

    if test_execution is None:
        raise HTTPException(status_code=404, detail="Related TestExecution not found")

    delete_previous_results(db, test_execution)
    _store_c3_test_results(db, request.test_results, test_execution)

    has_failures = test_execution.has_failures

    test_execution.status = (
        TestExecutionStatus.FAILED if has_failures else TestExecutionStatus.PASSED
    )

    if request.c3_link is not None:
        test_execution.c3_link = request.c3_link

    test_execution.checkbox_version = request.checkbox_version

    db.commit()


def _find_related_test_execution(
    request: EndTestExecutionRequest, db: Session
) -> TestExecution | None:
    stmt = (
        select(TestExecution)
        .where(TestExecution.ci_link == request.ci_link)
        .options(
            joinedload(TestExecution.artefact_build).joinedload(ArtefactBuild.artefact),
            joinedload(TestExecution.test_results).joinedload(TestResult.test_case),
        )
    )

    return db.execute(stmt).unique().scalar_one_or_none()


def _store_c3_test_results(
    db: Session,
    c3_test_results: list[C3TestResult],
    test_execution: TestExecution,
) -> None:
    for r in c3_test_results:
        test_case = get_or_create(
            db,
            TestCase,
            filter_kwargs={"name": r.name},
            creation_kwargs={"category": r.category},
        )

        if r.template_id:
            test_case.template_id = r.template_id

        test_result = TestResult(
            test_case=test_case,
            test_execution=test_execution,
            status=_parse_c3_test_result_status(r.status),
            comment=r.comment,
            io_log=r.io_log,
        )

        db.add(test_result)
        db.flush()
        apply_test_result_attachment_rules(db, test_result)

    db.commit()


def _parse_c3_test_result_status(status: C3TestResultStatus) -> TestResultStatus:
    match status:
        case C3TestResultStatus.PASS:
            return TestResultStatus.PASSED
        case C3TestResultStatus.FAIL:
            return TestResultStatus.FAILED
        case C3TestResultStatus.SKIP:
            return TestResultStatus.SKIPPED

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
from sqlalchemy import delete
from sqlalchemy.orm import Session, selectinload

from test_observer.common.permissions import Permission, permission_checker

from test_observer.common.metric_collectors import (
    update_test_results_metric,
)
from test_observer.controllers.test_executions.models import TestResultRequest
from test_observer.controllers.issues.attachment_rules_logic import (
    apply_test_result_attachment_rules,
)
from test_observer.data_access.models import (
    ArtefactBuild,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

router = APIRouter(tags=["test-results"])


@router.post(
    "/{id}/test-results",
    dependencies=[Security(permission_checker, scopes=[Permission.change_test])],
)
def post_results(
    id: int,
    request: list[TestResultRequest],
    db: Session = Depends(get_db),
):
    test_execution = db.get(
        TestExecution,
        id,
        options=[
            selectinload(TestExecution.artefact_build).selectinload(
                ArtefactBuild.artefact
            ),
            selectinload(TestExecution.environment),
            selectinload(TestExecution.execution_metadata),
        ],
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    for result in request:
        test_case = get_or_create(
            db,
            TestCase,
            filter_kwargs={"name": result.name},
            creation_kwargs={
                "category": result.category,
                "template_id": result.template_id,
            },
        )

        db.execute(
            delete(TestResult).where(
                TestResult.test_execution_id == test_execution.id,
                TestResult.test_case_id == test_case.id,
            )
        )

        test_result = TestResult(
            test_execution=test_execution,
            test_case=test_case,
            status=result.status,
            comment=result.comment,
            io_log=result.io_log,
        )

        db.add(test_result)
        db.flush()
        apply_test_result_attachment_rules(db, test_result)

        update_test_results_metric(test_execution, test_case, result)

    db.commit()

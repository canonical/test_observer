# Copyright (C) 2023 Canonical Ltd.
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

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import reported_issues
from .models import TestCasesResponse

from test_observer.data_access.models import TestCase
from test_observer.data_access.setup import get_db

router = APIRouter(tags=["test-cases"])
router.include_router(reported_issues.router)


@router.get("", response_model=TestCasesResponse)
def get_test_cases(db: Session = Depends(get_db)) -> TestCasesResponse:
    """
    Returns test cases as a flat list with their template IDs.

    Template ID represents the generic test (e.g., "disk/stats_name")
    Test case name is the specific instance (e.g., "disk/stats_nvme0n1")
    Multiple test cases can share the same template ID but have different names.
    """
    query = (
        select(
            TestCase.name.label("test_case"),
            TestCase.template_id,
        )
        .distinct()
        .order_by(TestCase.name, TestCase.template_id)
    )

    rows = db.execute(query).mappings().all()
    return TestCasesResponse.from_rows(rows)

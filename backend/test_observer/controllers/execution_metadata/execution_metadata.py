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


from fastapi import APIRouter, Depends, Security
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.common.permissions import Permission, permission_checker
from test_observer.data_access.models import TestExecutionMetadata
from test_observer.data_access.setup import get_db

from .models import ExecutionMetadataGetResponse, ExecutionMetadata


from . import execution_metadata

router = APIRouter(tags=["execution-metadata"])
router.include_router(execution_metadata.router)


@router.get(
    "",
    response_model=ExecutionMetadataGetResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_execution_metadata(db: Session = Depends(get_db)):
    return ExecutionMetadataGetResponse(
        execution_metadata=ExecutionMetadata.from_rows(
            db.execute(select(TestExecutionMetadata)).scalars().all()
        ),
    )

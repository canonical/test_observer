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


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from test_observer.data_access.setup import get_db
from test_observer.data_access.models import TestExecution
from test_observer.data_access.repository import (
    create_test_execution_relevant_link,
    get_test_execution_relevant_links,
)
from test_observer.controllers.artefacts.models import (
    TestExecutionRelevantLinkCreate,
    TestExecutionRelevantLinkResponse,
)

router = APIRouter(tags=["test-execution-relevant-links"])


@router.post("/{id}/links", response_model=TestExecutionRelevantLinkResponse)
def post_link(
    id: int, request: TestExecutionRelevantLinkCreate, db: Session = Depends(get_db)
):
    test_execution = db.get(TestExecution, id)
    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")
    return create_test_execution_relevant_link(db, id, request.label, request.url)


@router.get("/{id}/links", response_model=list[TestExecutionRelevantLinkResponse])
def list_links(id: int, db: Session = Depends(get_db)):
    return get_test_execution_relevant_links(db, id)


@router.delete("/{id}/links/{link_id}", status_code=204)
def delete_link(id: int, link_id: int, db: Session = Depends(get_db)):
    test_execution = db.get(TestExecution, id)
    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    link = next(
        (
            link
            for link in test_execution.relevant_links
            if link.id == link_id
        ),
        None,
    )
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(link)
    db.commit()


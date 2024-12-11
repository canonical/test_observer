# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from test_observer.data_access.models import (
    TestEvent,
    TestExecution,
)
from test_observer.data_access.models_enums import TestExecutionStatus
from test_observer.data_access.setup import get_db

from .logic import delete_previous_test_events
from .models import StatusUpdateRequest, TestEventDTO
from .testflinger_event_parser import TestflingerEventParser

router = APIRouter()


@router.put("/{id}/status_update")
def put_status_update(
    id: int, request: StatusUpdateRequest, db: Session = Depends(get_db)
):
    test_execution = db.get(
        TestExecution,
        id,
        options=[joinedload(TestExecution.test_events)],
    )
    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    delete_previous_test_events(db, test_execution)

    for event in request.events:
        test_event = TestEvent(
            event_name=event.event_name,
            timestamp=event.timestamp,
            detail=event.detail,
        )
        db.add(test_event)
        test_execution.test_events.append(test_event)
    event_parser = TestflingerEventParser()
    event_parser.process_events(test_execution.test_events)
    if event_parser.resource_url is not None:
        test_execution.resource_url = event_parser.resource_url
    if (
        event_parser.is_ended_prematurely
        and test_execution.status is not TestExecutionStatus.FAILED
        and test_execution.status is not TestExecutionStatus.PASSED
    ):
        test_execution.status = TestExecutionStatus.ENDED_PREMATURELY
    db.commit()


@router.get("/{id}/status_update", response_model=list[TestEventDTO])
def get_status_update(id: int, db: Session = Depends(get_db)):
    test_execution = db.get(
        TestExecution,
        id,
        options=[joinedload(TestExecution.test_events)],
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    return test_execution.test_events

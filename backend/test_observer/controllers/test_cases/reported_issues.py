from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import TestCaseIssue
from test_observer.data_access.setup import get_db

from .models import CreateReportedIssue, ReportedIssue

router = APIRouter()


endpoint = "/reported-issues"


@router.get(endpoint, response_model=list[ReportedIssue])
def get_reported_issues(template_id: str | None = None, db: Session = Depends(get_db)):
    stmt = select(TestCaseIssue)
    if template_id:
        stmt = stmt.where(TestCaseIssue.template_id == template_id)
    return db.execute(stmt).scalars()


@router.post(endpoint, response_model=ReportedIssue)
def create_reported_issue(request: CreateReportedIssue, db: Session = Depends(get_db)):
    issue = TestCaseIssue(
        template_id=request.template_id,
        url=request.url,
        description=request.description,
    )
    db.add(issue)
    db.commit()

    return issue

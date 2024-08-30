from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import TestCaseIssue
from test_observer.data_access.setup import get_db

from .models import ReportedIssueRequest, ReportedIssueResponse

router = APIRouter()


endpoint = "/reported-issues"


@router.get(endpoint, response_model=list[ReportedIssueResponse])
def get_reported_issues(
    template_id: str | None = None,
    case_name: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(TestCaseIssue)
    if template_id:
        stmt = stmt.where(TestCaseIssue.template_id == template_id)
    if case_name:
        stmt = stmt.where(TestCaseIssue.case_name == case_name)
    return db.execute(stmt).scalars()


@router.post(endpoint, response_model=ReportedIssueResponse)
def create_reported_issue(request: ReportedIssueRequest, db: Session = Depends(get_db)):
    issue = TestCaseIssue(
        template_id=request.template_id,
        url=request.url,
        description=request.description,
        case_name=request.case_name,
    )
    db.add(issue)
    db.commit()

    return issue


@router.put(endpoint + "/{issue_id}", response_model=ReportedIssueResponse)
def update_reported_issue(
    issue_id: int, request: ReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = db.get(TestCaseIssue, issue_id)
    for field in request.model_fields:
        setattr(issue, field, getattr(request, field))
    db.commit()
    return issue


@router.delete(endpoint + "/{issue_id}")
def delete_reported_issue(issue_id: int, db: Session = Depends(get_db)):
    db.delete(db.get(TestCaseIssue, issue_id))
    db.commit()

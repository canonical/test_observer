from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_observer.data_access.models import EnvironmentIssue
from test_observer.data_access.setup import get_db

from .models import ReportedIssueRequest, ReportedIssueResponse

router = APIRouter()

endpoint = "/reported-issues"


@router.get(endpoint, response_model=list[ReportedIssueResponse])
def get_reported_issues(db: Session = Depends(get_db)):
    return db.execute(select(EnvironmentIssue)).scalars()


@router.post(endpoint, response_model=ReportedIssueResponse)
def create_reported_issue(request: ReportedIssueRequest, db: Session = Depends(get_db)):
    issue = EnvironmentIssue(
        environment_name=request.environment_name,
        url=request.url,
        description=request.description,
    )
    db.add(issue)
    db.commit()

    return issue


@router.put(endpoint + "/{issue_id}", response_model=ReportedIssueResponse)
def update_reported_issue(
    issue_id: int, request: ReportedIssueRequest, db: Session = Depends(get_db)
):
    issue = db.get(EnvironmentIssue, issue_id)
    for field in request.model_fields:
        setattr(issue, field, getattr(request, field))
    db.commit()
    return issue


@router.delete(endpoint + "/{issue_id}")
def delete_reported_issue(issue_id: int, db: Session = Depends(get_db)):
    db.delete(db.get(EnvironmentIssue, issue_id))
    db.commit()

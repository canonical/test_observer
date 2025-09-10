from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_observer.data_access.models import Application
from test_observer.data_access.setup import get_db


def get_current_application(
    request: Request, db: Session = Depends(get_db)
) -> Application | None:
    match request.headers.get("Authorization", "").split():
        case ["Bearer", token]:
            return db.scalar(select(Application).where(Application.api_key == token))
        case _:
            return None

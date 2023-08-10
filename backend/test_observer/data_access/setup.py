from os import environ
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .models import Artefact
from .validators import validate_artefact

DEFAULT_DB_URL = "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres"
DB_URL = environ.get("DB_URL", DEFAULT_DB_URL)

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


event.listen(Artefact, "before_insert", validate_artefact)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

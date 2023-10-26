from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# We need to import this to enable event listeners
import test_observer.data_access.validators  # noqa: F401


DEFAULT_DB_URL = "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres"
DB_URL = environ.get("DB_URL", DEFAULT_DB_URL)

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

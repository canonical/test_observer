from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sys import environ

db_url = environ.get("DB_URL")
if db_url is None:
    db_url = "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres"

engine = create_engine(db_url, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

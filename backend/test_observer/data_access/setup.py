from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_URL = "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres"
DB_URL = environ.get("DB_URL", DEFAULT_DB_URL)

engine = create_engine(DB_URL, pool_size=45, max_overflow=45)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

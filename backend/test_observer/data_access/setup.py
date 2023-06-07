from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DB_URL = environ.get(
    "DB_URL", "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres"
)

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

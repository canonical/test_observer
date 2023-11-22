from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import redis

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

# Redis dependency
def get_redis():
    return redis.Redis(host='test-observer-redis', port=6379, decode_responses=True)
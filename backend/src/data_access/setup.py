from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine(
    "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres", echo=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

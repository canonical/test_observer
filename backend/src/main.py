from fastapi import FastAPI
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres", echo=True
)

app = FastAPI()


@app.get("/")
def root():
    with engine.connect() as conn:
        conn.execute(text("select 'test db connection'"))
    return {"message": "Hello World"}

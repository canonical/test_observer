# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Omar Abou Selo <omar.selo@canonical.com>
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>


import logging

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.data_access import models
from src.controllers import snap_manager_controller


engine = create_engine(
    "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres", echo=True
)
models.Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

logger = logging.getLogger("test-observer-backend")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    with engine.connect() as conn:
        conn.execute(text("select 'test db connection'"))
    return {"message": "Hello World"}


@app.put("/snapmanager")
async def snap_manager(db: Session = Depends(get_db)):
    try:
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with session() as sess:
            processed_artefacts = snap_manager_controller(sess)
            logger.info("INFO: Processed artefacts %s", processed_artefacts)
        if False in processed_artefacts.values():
            return JSONResponse(
                status_code=500,
                content={
                    "detail": (
                        "Got some errors while processing the next artefacts: "
                        ", ".join(
                            [k for k, v in processed_artefacts.items() if v is False]
                        )
                    )
                },
            )
        return JSONResponse(
            status_code=200,
            content={"detail": "All the artefacts have been processed successfully"},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

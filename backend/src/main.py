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


from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import yaml
import logging

from .services import get_stages_by_family_name
from .controllers.snap_manager import run_snap_manager

engine = create_engine(
    "postgresql+pg8000://postgres:password@test-observer-db:5432/postgres", echo=True
)

app = FastAPI()

logger = logging.getLogger("test-observer-backend")


@app.get("/")
def root():
    with engine.connect() as conn:
        conn.execute(text("select 'test db connection'"))
    return {"message": "Hello World"}


@app.post("/snapmanager")
async def snap_manager(file: UploadFile):
    try:
        content = await file.read()
        data = yaml.safe_load(content)
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with session() as sess:
            stages = get_stages_by_family_name(sess, "snap")
            processed_artefacts = {}
            for stage in stages:
                for artefact in stage.artefacts:
                    if artefact.is_archived:
                        continue
                    try:
                        processed_artefacts[
                            f"{artefact.name} - {artefact.version}"
                        ] = True
                        run_snap_manager(sess, artefact, data)
                    except Exception as exc:
                        processed_artefacts[
                            f"{artefact.name} - {artefact.version}"
                        ] = False
                        logger.warning("WARNING: %s", str(exc), exc_info=True)
            logger.info("INFO: Processed artefacts %s", processed_artefacts)
        if False in processed_artefacts.values():
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"Got some errors while processing the next artefacts: {', '.join(map(str, [k for k, v in processed_artefacts.items() if v is False]))}"
                },
            )
        return JSONResponse(
            status_code=200,
            content={"detail": "All the artefacts are processed successfully"},
        )

    except (yaml.parser.ParserError, yaml.scanner.ScannerError):
        return JSONResponse(
            status_code=400, content={"detail": "Error while parsing config"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

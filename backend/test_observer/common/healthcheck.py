# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import logging
from threading import Thread

import uvicorn
from fastapi import APIRouter, FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from test_observer.data_access.setup import get_db

logger = logging.getLogger("test-observer-backend")

router = APIRouter(prefix="/healthcheck", tags=["health"])

def create_app() -> FastAPI:
    """Create a minimal FastAPI app for healthcheck endpoints."""
    app = FastAPI(
        title="Test Observer Healthcheck",
        description="Healthcheck endpoints for container orchestration",
        docs_url=None,
        openapi_url=None,
        redoc_url=None,
    )
    app.include_router(router)
    return app


def start_http_server(port: int) -> Thread:
    """Start healthcheck server in a background thread."""
    app = create_app()
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    
    thread = Thread(daemon=True, target=server.run)
    thread.start()
    return thread


@router.get("/live")
async def live() -> dict[str, str]:
    """
    Liveness probe.
    
    Returns 200 OK if the application process is running and responding to requests.
    Does not check external dependencies like the database.
    
    Use this probe with container orchestration to determine if the process should be restarted.
    """
    return {"status": "live"}


@router.get("/ready")
async def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Readiness probe.
    
    Returns 200 OK if the application is ready to serve traffic, including database connectivity.
    Performs a simple database query to verify the connection is valid.
    
    Use this probe with container orchestration to determine if traffic should be routed to this pod.
    Returns 503 if the database is unavailable.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise

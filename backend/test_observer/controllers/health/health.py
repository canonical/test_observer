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

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from test_observer.data_access.setup import get_db

logger = logging.getLogger("test-observer-backend")

router = APIRouter()


@router.get("/live")
async def live(request: Request) -> dict[str, str]:
    """
    Liveness probe.

    Returns 200 OK if the application process is running and responding to requests.
    Does not check external dependencies like the database.

    Use this probe with container orchestration to determine if the process should be restarted.
    Note that this should only be accessible internally (e.g. from the host container)
    and not accessible over the public API.
    """
    _ensure_local_client(request)
    return {"status": "live"}


@router.get("/ready")
async def ready(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Readiness probe.

    Returns 200 OK if the application is ready to serve traffic, including database connectivity.
    Performs a simple database query to verify the connection is valid.

    Use this probe with container orchestration to determine if traffic should be routed to this pod.
    Note that this should only be accessible internally (e.g. from the host container)
    and not accessible over the public API.
    Returns 503 if the database is unavailable.
    """
    _ensure_local_client(request)
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed") from e


def _ensure_local_client(request: Request) -> None:
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        logger.warning(
            f"Received health check from unexpected client: {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(status_code=403, detail="Forbidden")

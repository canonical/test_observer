# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import logging
from contextlib import asynccontextmanager

import sentry_sdk
from anyio import to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import start_http_server
from starlette.middleware.sessions import SessionMiddleware

from test_observer.common.config import (
    ADDITIONAL_CORS_ORIGINS,
    FRONTEND_URL,
    METRICS_PORT,
    SENTRY_DSN,
    SESSIONS_HTTPS_ONLY,
    SESSIONS_SECRET,
)
from test_observer.common.metrics import instrumentator
from test_observer.common.metrics_initializer import initialize_all_metrics
from test_observer.controllers.router import router
from test_observer.data_access.setup import SessionLocal

if SENTRY_DSN:
    sentry_sdk.init(SENTRY_DSN)  # type: ignore

logger = logging.getLogger("test-observer-backend")
logging.basicConfig(level=logging.INFO)


def _initialize_all_metrics() -> None:
    with SessionLocal() as db:
        initialize_all_metrics(db)


async def _initialize_all_metrics_in_thread() -> None:
    """
    Initialize all Prometheus metrics from the database using a separate thread
    so the main event loop is not blocked.
    """
    try:
        # abandon_on_cancel=True ensures shutdown won't block waiting for this
        # potentially long-running DB initialization to finish; the worker thread
        # may continue running in the background until process exit.
        await to_thread.run_sync(_initialize_all_metrics, abandon_on_cancel=True)
    except Exception:
        logger.exception("Error during metrics initialization in thread")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    On startup, starts the metrics server and initializes Prometheus metrics
    from the database.
    """
    # Startup: Start metrics HTTP server on separate port
    try:
        start_http_server(METRICS_PORT)
        logger.info(f"Metrics server started on port {METRICS_PORT}")
    except Exception:
        # Continue startup even if metrics server fails
        logger.exception("Failed to start metrics server")
    # Run metrics initialization in the background without blocking the main event loop
    metrics_task = asyncio.create_task(_initialize_all_metrics_in_thread())

    yield  # Application runs

    # Shutdown: cleanup if needed
    if not metrics_task.done():
        logger.info("Metrics initialization still running; cancelling task for shutdown...")
        metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        logger.info("Background metrics task detached")
    except Exception:
        logger.exception("Unexpected error while awaiting metrics task in shutdown")


app = FastAPI(
    lifespan=lifespan,
    # Redirecting slashes can return a http schemed host when the request is https.
    # A browser may block such a request means that the frontend loads without data.
    # See https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content/How_to_fix_website_with_mixed_content
    # By stopping redirects, the api will get a 404 if it doesn't use the exact path.
    # This is useful to remind developers to use the exact path during development.
    # To be a standard all paths should not end with a trailing slash.
    redirect_slashes=False,
    title="Test Observer",
    description="Test Observer API (see https://github.com/canonical/test_observer)",
    license_info={
        "name": "GNU Affero General Public License v3",
        "url": "https://raw.githubusercontent.com/canonical/test_observer/refs/heads/main/backend/LICENSE",
    },
    docs_url=None,  # Disable default docs to add custom ones
    openapi_url=None,  # Disable default openapi.json to add custom one
    redoc_url="/redocs",  # But keep the default redocs
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] + ADDITIONAL_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSIONS_SECRET,
    https_only=SESSIONS_HTTPS_ONLY,
)

# Instrument the app with Prometheus metrics
# (exposed on separate port via start_http_server)
instrumentator.instrument(app)

app.include_router(router)

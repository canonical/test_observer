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

import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CollectorRegistry, make_wsgi_app
from prometheus_client.multiprocess import MultiProcessCollector
from starlette.middleware.sessions import SessionMiddleware

from test_observer.common.config import (
    FRONTEND_URL,
    METRICS_PORT,
    PROMETHEUS_MULTIPROC_DIR,
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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    On startup, starts the metrics server and initializes Prometheus metrics
    from the database.
    """
    # Startup: Start metrics HTTP server on separate port.
    # In multiprocess mode only one worker binds the port; others get OSError, which is expected.
    Path(PROMETHEUS_MULTIPROC_DIR).mkdir(parents=True, exist_ok=True)
    try:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)

        class _SilentHandler(WSGIRequestHandler):
            def log_message(self, *args: object) -> None:  # suppress per-request logs
                pass

        httpd = make_server("", METRICS_PORT, make_wsgi_app(registry), handler_class=_SilentHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Metrics server started on port {METRICS_PORT}")
    except OSError:
        logger.info(f"Metrics port {METRICS_PORT} already bound by another worker — skipping")
    except Exception:
        logger.exception("Failed to start metrics server")

    # Initialize metrics from database
    db = SessionLocal()
    try:
        initialize_all_metrics(db)
    except Exception as e:
        logger.exception(f"Error during metrics initialization: {e}")
        # Continue startup even if metrics init fails
    finally:
        db.close()

    yield  # Application runs


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
    allow_origins=[FRONTEND_URL],
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

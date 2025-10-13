# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import logging
import sentry_sdk
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from test_observer.common.config import (
    FRONTEND_URL,
    SENTRY_DSN,
    SESSIONS_SECRET,
    SESSIONS_HTTPS_ONLY,
)
from test_observer.controllers.router import router

if SENTRY_DSN:
    sentry_sdk.init(SENTRY_DSN)  # type: ignore

logger = logging.getLogger("test-observer-backend")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
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


app.include_router(router)

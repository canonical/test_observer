# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import os

SENTRY_DSN = os.getenv("SENTRY_DSN")
SAML_SP_BASE_URL = os.getenv("SAML_SP_BASE_URL", "http://localhost:30000")
SAML_IDP_METADATA_URL = os.getenv(
    "SAML_IDP_METADATA_URL",
    "http://localhost:8080/simplesaml/saml2/idp/metadata.php",
)
SAML_SP_X509_CERT = os.getenv("SAML_SP_X509_CERT", "")
SAML_SP_KEY = os.getenv("SAML_SP_KEY", "")
ADDITIONAL_CORS_ORIGINS = [
    origin.strip() for origin in os.getenv("ADDITIONAL_CORS_ORIGINS", "").split(",") if origin.strip()
]
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:30001")
SESSIONS_SECRET = os.getenv("SESSIONS_SECRET", "secret")
SESSIONS_HTTPS_ONLY = os.getenv("SESSIONS_HTTPS_ONLY", "true").lower() == "true"
IGNORE_PERMISSIONS = {
    permission.strip() for permission in os.getenv("IGNORE_PERMISSIONS", "").lower().split(",") if permission.strip()
}
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
__METRICS_INIT_DAYS__ = int(os.getenv("METRICS_INIT_DAYS", "30"))
METRICS_INIT_DAYS = __METRICS_INIT_DAYS__ if __METRICS_INIT_DAYS__ > 0 else 0
METRICS_INIT_ENABLED = os.getenv("METRICS_INIT_ENABLED", "true").lower() == "true"
REQUIRE_AUTHENTICATION = os.getenv("REQUIRE_AUTHENTICATION", "false").lower() == "true"


def int_from_env(name: str, default: int, *, minimum: int = 1) -> int:
    """Read an integer setting, failing at startup if it is below `minimum`."""
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer of at least {minimum}, got {raw!r}") from error
    if value < minimum:
        raise ValueError(f"{name} must be an integer of at least {minimum}, got {raw!r}")
    return value


# The largest `limit` each kind of paginated endpoint accepts. A request above
# it gets a 422 response. Each page is built in memory, so these caps bound how
# much memory one request can take, and the kinds differ in cost per item:
# - an execution in the execution search carries all of its results and io logs,
# - a result in the result search carries its own io log,
# - a listing item (artefact name, environment, test case, user, ...) is small.
# None may go below the largest default page size, 50, or a request that
# leaves out `limit` would get more than the cap.
MIN_PAGE_LIMIT = 50
MAX_EXECUTION_PAGE_LIMIT = int_from_env("MAX_EXECUTION_PAGE_LIMIT", 50, minimum=MIN_PAGE_LIMIT)
MAX_RESULT_PAGE_LIMIT = int_from_env("MAX_RESULT_PAGE_LIMIT", 1000, minimum=MIN_PAGE_LIMIT)
MAX_LISTING_PAGE_LIMIT = int_from_env("MAX_LISTING_PAGE_LIMIT", 1000, minimum=MIN_PAGE_LIMIT)

# When enabled, SAML logins skip the Launchpad user lookup. Intended for local
# development against a local IdP where SAML users do not exist in Launchpad.
# Defaults to false so production never skips the lookup unless opted in.
USE_LOCAL_LOGIN = os.getenv("USE_LOCAL_LOGIN", "false").lower() == "true"

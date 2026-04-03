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

VERSION = os.getenv("VERSION", "0.0.0")
SENTRY_DSN = os.getenv("SENTRY_DSN")
SAML_SP_BASE_URL = os.getenv("SAML_SP_BASE_URL", "http://localhost:30000")
SAML_IDP_METADATA_URL = os.getenv(
    "SAML_IDP_METADATA_URL",
    "http://localhost:8080/simplesaml/saml2/idp/metadata.php",
)
SAML_SP_X509_CERT = os.getenv("SAML_SP_X509_CERT", "")
SAML_SP_KEY = os.getenv("SAML_SP_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:30001")
SESSIONS_SECRET = os.getenv("SESSIONS_SECRET", "secret")
SESSIONS_HTTPS_ONLY = os.getenv("SESSIONS_HTTPS_ONLY", "true").lower() == "true"
IGNORE_PERMISSIONS = {
    permission.strip() for permission in os.getenv("IGNORE_PERMISSIONS", "").lower().split(",") if permission.strip()
}
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))

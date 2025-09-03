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

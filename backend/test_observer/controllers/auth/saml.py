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
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
import os


router = APIRouter(prefix="/saml", tags=["authentication"])


logger = logging.getLogger("test-observer-backend")


def _get_saml_settings() -> dict[str, Any] | None:
    # Only initialize SAML if IDP metadata URL is provided
    idp_metadata_url = os.getenv("SAML_IDP_METADATA_URL")
    if not idp_metadata_url:
        logger.info("SAML not configured - no IDP metadata URL provided")
        return None

    sp_base_url = os.getenv("SAML_SP_BASE_URL", "http://localhost:30000")

    try:
        idp_settings = OneLogin_Saml2_IdPMetadataParser.parse_remote(idp_metadata_url)[
            "idp"
        ]
    except Exception as e:
        logger.warning(
            f"Failed to fetch SAML IDP metadata from {idp_metadata_url}: {e}"
        )
        return None

    return {
        "strict": True,
        "debug": True,
        "sp": {
            "entityId": f"{sp_base_url}",
            "assertionConsumerService": {
                "url": f"{sp_base_url}/v1/auth/saml/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": f"{sp_base_url}/v1/auth/saml/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": os.getenv("SAML_SP_X509_CERT", ""),
            "privateKey": os.getenv("SAML_SP_KEY", ""),
        },
        "idp": idp_settings,
    }


# Sentinel value for uninitialized cache
_UNINITIALIZED = object()

# Cache for lazy initialization
_saml_settings_cache: Any = _UNINITIALIZED


def get_saml_settings() -> dict[str, Any] | None:
    """Get SAML settings with lazy initialization."""
    global _saml_settings_cache
    if _saml_settings_cache is _UNINITIALIZED:
        _saml_settings_cache = _get_saml_settings()
    return _saml_settings_cache


@router.get("/login")
async def saml_login(request: Request):
    settings = get_saml_settings()
    if settings is None:
        raise HTTPException(
            status_code=503, detail="SAML authentication is not configured"
        )
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, settings)
    return RedirectResponse(url=auth.login())


@router.get("/logout")
async def saml_logout(request: Request):
    settings = get_saml_settings()
    if settings is None:
        raise HTTPException(
            status_code=503, detail="SAML authentication is not configured"
        )
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, settings)
    return RedirectResponse(url=auth.logout())


@router.post("/acs")
async def saml_login_callback(request: Request):
    settings = get_saml_settings()
    if settings is None:
        raise HTTPException(
            status_code=503, detail="SAML authentication is not configured"
        )
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, settings)
    auth.process_response()
    errors = auth.get_errors()

    if errors:
        logger.warning(
            "Error when processing SAML ACS Response: {} {}".format(
                ", ".join(errors), auth.get_last_error_reason()
            )
        )
        raise HTTPException(500, "Authentication failed")

    if not auth.is_authenticated():
        raise HTTPException(403, "Authentication failed")

    return {
        "name_id_format": auth.get_nameid_format(),
        "name_id": auth.get_nameid(),
        "session_index": auth.get_session_index(),
        "attributes": auth.get_attributes(),
    }


@router.post("/sls")
@router.get("/sls")
async def saml_logout_callback(request: Request):
    settings = get_saml_settings()
    if settings is None:
        raise HTTPException(
            status_code=503, detail="SAML authentication is not configured"
        )
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, settings)
    auth.process_slo()
    errors = auth.get_errors()

    if errors:
        logger.warning(
            "Error when processing SAML SLS Response: {} {}".format(
                ", ".join(errors), auth.get_last_error_reason()
            )
        )
        raise HTTPException(500, "Logout failed")


async def _prepare_from_fastapi_request(request: Request) -> dict[str, Any]:
    form_data = await request.form()
    result: dict[str, Any] = {
        "http_host": request.url.hostname,
        "server_port": request.url.port,
        "script_name": request.url.path,
        "post_data": {},
        "get_data": {},
    }
    if request.query_params:
        result["get_data"] = (request.query_params,)
    if "SAMLResponse" in form_data:
        saml_response = form_data["SAMLResponse"]
        result["post_data"]["SAMLResponse"] = saml_response
    if "RelayState" in form_data:
        relay_state = form_data["RelayState"]
        result["post_data"]["RelayState"] = relay_state
    return result

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

from datetime import datetime, timedelta
from functools import cache
import logging
from typing import Any
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
from sqlalchemy.orm import Session

from test_observer.common.config import (
    SAML_IDP_METADATA_URL,
    SAML_SP_BASE_URL,
    SAML_SP_KEY,
    SAML_SP_X509_CERT,
)
from test_observer.controllers.artefacts.models import UserResponse
from test_observer.data_access.models import User, UserSession
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db
from test_observer.external_apis.launchpad.launchpad_api import LaunchpadAPI
from test_observer.main import FRONTEND_URL


router = APIRouter(prefix="/saml")


logger = logging.getLogger("test-observer-backend")


@cache
def _get_saml_settings() -> dict[str, Any]:
    return {
        "strict": True,
        "debug": True,
        "sp": {
            "entityId": f"{SAML_SP_BASE_URL}",
            "assertionConsumerService": {
                "url": f"{SAML_SP_BASE_URL}/v1/auth/saml/acs",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "singleLogoutService": {
                "url": f"{SAML_SP_BASE_URL}/v1/auth/saml/sls",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "x509cert": SAML_SP_X509_CERT,
            "privateKey": SAML_SP_KEY,
        },
        "idp": OneLogin_Saml2_IdPMetadataParser.parse_remote(SAML_IDP_METADATA_URL)[
            "idp"
        ],
    }


@router.get("/login")
async def saml_login(request: Request, return_to: str | None = None):
    settings = _get_saml_settings()
    if settings is None:
        raise HTTPException(
            status_code=503, detail="SAML authentication is not configured"
        )
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, settings)
    return RedirectResponse(url=auth.login(return_to=return_to))


@router.get("/logout")
async def saml_logout(request: Request):
    settings = _get_saml_settings()
    if settings is None:
        raise HTTPException(
            status_code=503, detail="SAML authentication is not configured"
        )
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, settings)
    return RedirectResponse(url=auth.logout())


@router.post("/acs", response_model=UserResponse)
async def saml_login_callback(request: Request, db: Session = Depends(get_db)):
    settings = _get_saml_settings()
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

    user = _create_user(db, auth)
    session = UserSession(
        user_id=user.id, expires_at=datetime.now() + timedelta(days=14)
    )
    db.add(session)
    db.commit()

    request.session["id"] = session.id

    if return_to := req["post_data"].get("RelayState"):
        frontend_url = urlparse(FRONTEND_URL)
        return_url = urlparse(return_to)
        # Check if it's safe to redirect user to this URL
        if frontend_url.netloc == return_url.netloc:
            response = RedirectResponse(
                url=return_to, status_code=status.HTTP_302_FOUND
            )
            return response
        else:
            # Note by default python3-saml returns to API url
            logger.warning(f"Received invalid return url {return_to}")

    return user


def _create_user(db: Session, auth: OneLogin_Saml2_Auth) -> User:
    email = auth.get_nameid()
    lp_user = LaunchpadAPI().get_user_by_email(email)
    user = get_or_create(
        db,
        User,
        {"email": email},
        {
            "name": auth.get_attributes()["fullname"][0],
            "launchpad_handle": lp_user.handle if lp_user else None,
        },
    )
    return user


@router.post("/sls")
@router.get("/sls")
async def saml_logout_callback(request: Request):
    settings = _get_saml_settings()
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

    logger.info("Received a login request with the following parameters:")
    logger.info(f"request.headers {request.headers.items()}")
    logger.info(f"request.url.scheme {request.url.scheme}")
    logger.info(f"result['server_port'] {result['server_port']}")

    if request.url.scheme == "https" or result["server_port"] == 443:
        result["https"] = "on"
    if request.query_params:
        result["get_data"] = (request.query_params,)
    if "SAMLResponse" in form_data:
        saml_response = form_data["SAMLResponse"]
        result["post_data"]["SAMLResponse"] = saml_response
    if "RelayState" in form_data:
        relay_state = form_data["RelayState"]
        result["post_data"]["RelayState"] = relay_state
    return result

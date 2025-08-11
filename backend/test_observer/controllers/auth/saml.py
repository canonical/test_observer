from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
import os


router = APIRouter(prefix="/saml", tags=["authentication"])


def _get_saml_settings() -> dict[str, Any]:
    sp_base_url = os.getenv("SAML_SP_BASE_URL")
    idp_metadata_url = os.getenv("SAML_IDP_METADATA_URL")

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
        "idp": OneLogin_Saml2_IdPMetadataParser.parse_remote(idp_metadata_url)["idp"],
    }


saml_settings = _get_saml_settings()


@router.get("/login")
async def saml_login(request: Request):
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    sso_url = auth.login()
    return RedirectResponse(url=sso_url)


@router.post("/acs")
async def saml_login_callback(request: Request):
    req = await _prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, saml_settings)
    auth.process_response()
    errors = auth.get_errors()
    if len(errors) == 0:
        if auth.is_authenticated():
            return "User authenticated"
        else:
            return "User not authenticated"
    else:
        print(
            "Error when processing SAML Response: {} {}".format(
                ", ".join(errors), auth.get_last_error_reason()
            )
        )
        return "Error in callback"


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

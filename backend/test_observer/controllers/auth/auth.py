from authlib.integrations.starlette_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749.grants import ClientCredentialsGrant
from fastapi import APIRouter, HTTPException, Request, Depends, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from models import OAuth2Client
from database import get_db
from passlib.context import CryptContext

from os import getenv

SECRET_KEY = getenv("TOKEN_SIGNING_SECRET")
ALGORITHM = getenv("TOKEN_SIGNING_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRY = int(getenv("TOKEN_EXPIRY", "15"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(client_id: str, scope: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY)
    payload = {"sub": client_id, "scope": scope, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_client_secret(provided_secret: str):
    """Verify the provided client secret against the stored hash."""
    return pwd_context.verify(provided_secret, pwd_context.hash(getenv("ADMIN_CLIENT_SECRET")))

class CustomClientCredentialsGrant(ClientCredentialsGrant):
    """Custom grant to validate client credentials using fixed ENV variables."""

    def authenticate_client(self, request):
        """Verify client ID and secret."""
        client_id = request.client_id
        client_secret = request.client_secret

        # Validate against fixed environment variables
        if client_id != getenv("ADMIN_CLIENT_ID") or not verify_client_secret(client_secret):
            raise HTTPException(status_code=401, detail="Invalid client credentials")

        return {"client_id": client_id, "scope": "read write"}  # Fake client object

    def create_access_token(self, client, grant_user):
        """Generate a JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRY)
        payload = {"sub": client["client_id"], "scope": client["scope"], "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

auth_server = AuthorizationServer(
    query_client=lambda client_id: None,
    save_token=lambda *args, **kwargs: None,
)


auth_server.register_grant(CustomClientCredentialsGrant)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def verify_refresh_token(refresh_token: str):
    """Verify refresh token validity."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    

router = APIRouter()

endpoint = "/auth"

@router.post("/token")
async def issue_token(request: Request):
    """OAuth2 Token Endpoint (Client Credentials using client_secret_basic)."""
    return await auth_server.create_token_response(request)

@router.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    """Protected API requiring a valid access token."""
    return {"message": "You have access!", "token": token}
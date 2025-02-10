from fastapi import APIRouter, HTTPException, Depends, HTTPBasic, status
from fastapi.security import HTTPBasicCredentials
from typing import Annotated

from os import getenv
import logging
import secrets

router = APIRouter(tags=["auth"])

security = HTTPBasic()

def has_admin_credentials(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_username = secrets.compare_digest(credentials.username, getenv("ADMIN_CLIENT_ID"))
    correct_password = secrets.compare_digest(credentials.password, getenv("ADMIN_CLIENT_SECRET"))
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},  # Ensures the client prompts for credentials
        )
    return credentials.username
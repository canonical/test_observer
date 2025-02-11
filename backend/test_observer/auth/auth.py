# Copyright (C) 2024 Canonical Ltd.
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

from fastapi import APIRouter, HTTPException, Depends, HTTPBasic, status
from fastapi.security import HTTPBasicCredentials
from typing import Annotated

from os import getenv
import secrets

router = APIRouter(tags=["auth"])

security = HTTPBasic()

def has_admin_credentials(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_username = (
        secrets.compare_digest(credentials.username, getenv("ADMIN_CLIENT_ID"))
    )
    correct_password = (
        secrets.compare_digest(credentials.password, getenv("ADMIN_CLIENT_SECRET"))
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            # Ensures the client prompts for credentials
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
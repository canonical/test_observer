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

router = APIRouter(tags=["auth"])

basic_auth = HTTPBasic()

def get_admin_credentials():
    return {
        "client_id": getenv("ADMIN_CLIENT_ID"),
        "client_secret": getenv("ADMIN_CLIENT_SECRET"),
    }

def has_admin_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(basic_auth)],
    admin_credentials: dict = Depends(get_admin_credentials)
):
    correct_username = credentials.username == admin_credentials["client_id"]
    correct_password = credentials.password == admin_credentials["client_secret"]

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
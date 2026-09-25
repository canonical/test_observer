# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Client for C3's testing-pools API (the source of truth for expected environments).

NOTE: This is a family-specific external integration (C3 only knows about deb/snap)
and is acknowledged technical debt per the project's generic-platform design principle.
"""

import requests

from test_observer.common import config

from .c3_models import TestingPool

_TIMEOUT_SECONDS = 30


class C3NotConfiguredError(Exception):
    """Raised when the C3 API credentials are not configured."""


class C3Api:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_testing_pools(self, family: str) -> list[TestingPool]:
        """Fetch C3 testing pools for a given artefact family (``deb`` or ``snap``).

        Follows pagination and returns all pools. Raises :class:`C3NotConfiguredError`
        when no credentials are configured so callers can degrade gracefully.
        """
        if not self.is_configured():
            raise C3NotConfiguredError("C3_CLIENT_ID and C3_CLIENT_SECRET are not set")

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._fetch_access_token()}",
        }
        url: str | None = f"{self.base_url}/api/v2/testing-pools/"
        params: dict[str, str] | None = {"family": family}

        pools: list[TestingPool] = []
        while url:
            response = requests.get(url, headers=headers, params=params, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()

            # C3 (DRF) paginates as {"results": [...], "next": url}; tolerate a bare list too.
            if isinstance(payload, dict):
                results = payload.get("results", [])
                url = payload.get("next")
            else:
                results = payload
                url = None
            params = None  # `next` already carries the query string

            pools.extend(TestingPool(**item) for item in results)

        return pools

    def _fetch_access_token(self) -> str:
        """C3 access tokens are short lived, so one is resolved on every call rather than cached."""
        response = requests.post(
            f"{self.base_url}/oauth2/token/",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["access_token"]


def get_c3_api() -> C3Api:
    return C3Api(config.C3_API_BASE_URL, config.C3_CLIENT_ID, config.C3_CLIENT_SECRET)

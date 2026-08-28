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

import logging

import requests

from test_observer.common import config

from .c3_models import TestingPool

logger = logging.getLogger("test-observer-backend")

_TIMEOUT_SECONDS = 30


class C3NotConfiguredError(Exception):
    """Raised when the C3 API token is not configured."""


def is_configured() -> bool:
    return bool(config.C3_API_TOKEN)


def get_testing_pools(family: str) -> list[TestingPool]:
    """Fetch C3 testing pools for a given artefact family (``deb`` or ``snap``).

    Follows pagination and returns all pools. Raises :class:`C3NotConfiguredError`
    when no API token is configured so callers can degrade gracefully.
    """
    if not is_configured():
        raise C3NotConfiguredError("C3_API_TOKEN is not set")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {config.C3_API_TOKEN}",
    }
    url: str | None = f"{config.C3_API_BASE_URL.rstrip('/')}/api/v2/testing-pools/"
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

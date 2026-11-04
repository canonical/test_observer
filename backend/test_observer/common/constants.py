# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import hashlib
from enum import StrEnum


def _lock_key() -> int:
    """Generate a 64-bit integer key for advisory locking."""
    digest = hashlib.sha256(b"test-observer-backend").digest()[:8]
    return int.from_bytes(digest, "big", signed=True)


# Shared by every process that migrates this database
# Used to ensure only one unit migrates the database at a time
MIGRATION_LOCK_ID = _lock_key()

PREVIOUS_TEST_RESULT_COUNT = 10
VALID_ISSUE_HOSTS = {"github.com", "warthogs.atlassian.net", "bugs.launchpad.net"}


class QueryValue(StrEnum):
    ANY = "any"
    NONE = "none"

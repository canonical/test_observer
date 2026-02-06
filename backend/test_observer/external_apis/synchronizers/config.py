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

"""Configuration for issue synchronization"""

from os import environ

DEFAULT_OPEN_INTERVAL_S = 3600
DEFAULT_RECENT_CLOSED_INTERVAL_S = 21600
DEFAULT_OLD_CLOSED_INTERVAL_S = 604800
DEFAULT_OLD_CLOSED_THRESHOLD_DAYS = 30
DEFAULT_BATCH_SIZE = 50
DEFAULT_BATCH_DELAY_S = 60


class SyncConfig:
    """Centralized configuration for issue synchronization intervals

    All values must be provided via environment variables:
        - SYNC_OPEN_INTERVAL: Seconds between syncs for OPEN/UNKNOWN issues
        - SYNC_RECENT_CLOSED_INTERVAL: Seconds between syncs for recently closed issues
        - SYNC_OLD_CLOSED_INTERVAL: Seconds between syncs for old closed issues
        - SYNC_OLD_CLOSED_THRESHOLD_DAYS: Days threshold for "old" closed issues
        - SYNC_BATCH_SIZE: Number of issues to process per batch
        - SYNC_BATCH_DELAY: Seconds to wait between batches
    """

    OPEN_ISSUE_INTERVAL = int(
        environ.get("SYNC_OPEN_INTERVAL_S", DEFAULT_OPEN_INTERVAL_S)
    )
    RECENT_CLOSED_INTERVAL = int(
        environ.get("SYNC_RECENT_CLOSED_INTERVAL_S", DEFAULT_RECENT_CLOSED_INTERVAL_S)
    )
    OLD_CLOSED_INTERVAL = int(
        environ.get("SYNC_OLD_CLOSED_INTERVAL_S", DEFAULT_OLD_CLOSED_INTERVAL_S)
    )
    OLD_CLOSED_THRESHOLD_DAYS = int(
        environ.get("SYNC_OLD_CLOSED_THRESHOLD_DAYS", DEFAULT_OLD_CLOSED_THRESHOLD_DAYS)
    )
    BATCH_SIZE = int(environ.get("SYNC_BATCH_SIZE", DEFAULT_BATCH_SIZE))
    BATCH_DELAY = int(environ.get("SYNC_BATCH_DELAY_S", DEFAULT_BATCH_DELAY_S))

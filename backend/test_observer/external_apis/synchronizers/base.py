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

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from test_observer.data_access.models import Issue
from dataclasses import dataclass


@dataclass
class SyncResult:
    """Result of a single issue synchronization"""

    success: bool
    title_updated: bool = False
    status_updated: bool = False
    error: str | None = None


class BaseIssueSynchronizer(ABC):
    """Base class for platform-specific issue synchronizers"""

    @abstractmethod
    def can_sync(self, issue: Issue) -> bool:
        """
        Check if this synchronizer can handle the given issue

        Args:
            issue: Issue to check

        Returns:
            True if this synchronizer can sync the issue
        """
        pass

    @abstractmethod
    def sync_issue(self, issue: Issue, db: Session) -> SyncResult:
        """
        Synchronize a single issue from the external platform

        Args:
            issue: Issue to synchronize
            db: Database session

        Returns:
            SyncResult with synchronization outcome
        """
        pass

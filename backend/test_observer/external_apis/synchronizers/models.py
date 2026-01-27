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

from dataclasses import dataclass
from test_observer.external_apis.synchronizers.base import SyncResult


@dataclass
class SyncResults:
    """Results of synchronization run"""

    total: int
    successful: int
    failed: int
    updated: int
    results: list[SyncResult]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100

    @classmethod
    def from_results(cls, results: list[SyncResult]) -> "SyncResults":
        """
        Create SyncResults from a list of individual results

        Args:
            results: List of individual sync results

        Returns:
            Aggregated SyncResults
        """
        total = len(results)
        successful = 0
        failed = 0
        updated = 0

        for result in results:
            if result.success:
                successful += 1
                if result.title_updated or result.status_updated:
                    updated += 1
            else:
                failed += 1

        return cls(
            total=total,
            successful=successful,
            failed=failed,
            updated=updated,
            results=results,
        )

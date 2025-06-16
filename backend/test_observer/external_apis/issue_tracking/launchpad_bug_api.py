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



from launchpadlib.launchpad import Launchpad  # type: ignore

from test_observer.data_access.models_enums import IssueStatus
from .models import IssueInfo


class LaunchpadBugAPI:
    """Client for Launchpad Bugs API"""
    
    def __init__(self):
        self.launchpad = Launchpad.login_anonymously(
            "test-observer-bugs", "production", version="devel"
        )
    
    def get_bug(self, bug_number: str) -> IssueInfo | None:
        """
        Get bug information from Launchpad
        
        Args:
            bug_number: Launchpad bug number
            
        Returns:
            IssueInfo object if successful, None if not found or error
        """
        try:
            bug = self.launchpad.bugs[bug_number]
            
            if not bug:
                return None
            
            # Determine bug status
            # Launchpad bug statuses: New, Incomplete, Opinion, Invalid, Won't Fix, 
            # Expired, Confirmed, Triaged, In Progress, Fix Committed, Fix Released
            status_name = str(bug.status).lower()
            if status_name in ["fix released", "fix committed", "invalid", "won't fix", "expired"]:
                status = IssueStatus.CLOSED
            elif status_name in ["new", "incomplete", "confirmed", "triaged", "in progress", "opinion"]:
                status = IssueStatus.OPEN
            else:
                status = IssueStatus.UNKNOWN
            
            # Parse last updated time
            last_updated = None
            if hasattr(bug, "date_last_updated") and bug.date_last_updated:
                last_updated = bug.date_last_updated
            
            # Get assignee
            assignee = None
            if hasattr(bug, "assignee") and bug.assignee:
                assignee = bug.assignee.display_name
            
            # Extract tags as labels
            labels = []
            if hasattr(bug, "tags"):
                labels = list(bug.tags)
            
            # Build bug URL
            bug_url = f"https://bugs.launchpad.net/bugs/{bug_number}"
            
            return IssueInfo(
                external_id=str(bug_number),
                title=str(bug.title) if hasattr(bug, "title") else "",
                status=status,
                url=bug_url,
                last_updated=last_updated,
                assignee=assignee,
                labels=labels,
                description=str(bug.description) if hasattr(bug, "description") else None
            )
            
        except Exception:
            # Log error in production, for now return None
            # Launchpad API can raise various exceptions
            return None
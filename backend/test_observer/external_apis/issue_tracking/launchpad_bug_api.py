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

import logging
import os

from launchpadlib.launchpad import Launchpad  # type: ignore
from lazr.restfulclient.errors import NotFound  # type: ignore

from test_observer.data_access.models_enums import IssueStatus
from .models import IssueInfo

logger = logging.getLogger(__name__)


class LaunchpadBugAPI:
    """Client for Launchpad Bugs API"""
    
    def __init__(self, consumer_name: str | None = None, oauth_token: str | None = None, oauth_token_secret: str | None = None):
        """
        Initialize Launchpad API client
        
        Args:
            consumer_name: Launchpad consumer name for authenticated access
            oauth_token: OAuth token for authenticated access  
            oauth_token_secret: OAuth token secret for authenticated access
            
        If no credentials provided, will use anonymous access which can't access private bugs.
        """
        # Check environment variables if credentials not provided
        consumer_name = consumer_name or os.getenv("LAUNCHPAD_CONSUMER_NAME")
        oauth_token = oauth_token or os.getenv("LAUNCHPAD_OAUTH_TOKEN")
        oauth_token_secret = oauth_token_secret or os.getenv("LAUNCHPAD_OAUTH_TOKEN_SECRET")
        
        if consumer_name and oauth_token and oauth_token_secret:
            logger.info("Initializing authenticated Launchpad connection")
            try:
                self.launchpad = Launchpad.login(
                    consumer_name=consumer_name,
                    token_string=oauth_token,
                    access_secret=oauth_token_secret,
                    service_root="production",
                    version="devel"
                )
                self._authenticated = True
                logger.info("✅ Authenticated Launchpad connection established")
            except Exception as e:
                logger.warning(f"Failed to authenticate with Launchpad: {e}")
                logger.info("Falling back to anonymous access")
                self.launchpad = Launchpad.login_anonymously(
                    "test-observer-bugs", "production", version="devel"
                )
                self._authenticated = False
        else:
            logger.info("Initializing anonymous Launchpad connection")
            self.launchpad = Launchpad.login_anonymously(
                "test-observer-bugs", "production", version="devel"
            )
            self._authenticated = False
    
    def get_bug(self, bug_number: str) -> IssueInfo | None:
        """
        Get bug information from Launchpad
        
        Args:
            bug_number: Launchpad bug number
            
        Returns:
            IssueInfo object if successful, None if not found or error
        """
        try:
            access_type = "authenticated" if self._authenticated else "anonymous"
            logger.debug(f"Fetching Launchpad bug: {bug_number} (using {access_type} access)")
            
            # Try to access the bug - this may raise KeyError or NotFound
            try:
                bug = self.launchpad.bugs[bug_number]
            except (KeyError, NotFound) as e:
                # Bug not found (404) or inaccessible - this is normal for deleted/private bugs
                access_type = "authenticated" if self._authenticated else "anonymous"
                if not self._authenticated:
                    logger.info(f"Launchpad bug {bug_number} not found or not accessible with {access_type} access: {type(e).__name__}: {e} (try providing Launchpad credentials)")
                else:
                    logger.info(f"Launchpad bug {bug_number} not found or not accessible even with {access_type} access: {type(e).__name__}: {e}")
                return None
            
            if not bug:
                logger.info(f"Launchpad bug not found: {bug_number}")
                return None
            
            try:
                # Determine bug status from bug tasks (Launchpad stores status in tasks, not directly on bug)
                # Launchpad bug statuses: New, Incomplete, Opinion, Invalid, Won't Fix, 
                # Expired, Confirmed, Triaged, In Progress, Fix Committed, Fix Released
                status = IssueStatus.UNKNOWN
                
                if hasattr(bug, "bug_tasks") and bug.bug_tasks:
                    # Get status from the first bug task (usually the primary one)
                    try:
                        first_task = bug.bug_tasks[0]
                        if hasattr(first_task, "status") and first_task.status:
                            status_name = str(first_task.status).lower()
                            if status_name in ["fix released", "fix committed", "invalid", "won't fix", "expired"]:
                                status = IssueStatus.CLOSED
                            elif status_name in ["new", "incomplete", "confirmed", "triaged", "in progress", "opinion"]:
                                status = IssueStatus.OPEN
                            else:
                                status = IssueStatus.UNKNOWN
                            logger.debug(f"Launchpad bug {bug_number} status from task: {status_name} -> {status}")
                        else:
                            logger.warning(f"Launchpad bug {bug_number} task has no status attribute")
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"Launchpad bug {bug_number} could not access bug task status: {e}")
                else:
                    # Fallback: try direct status attribute (though this usually doesn't exist)
                    if hasattr(bug, "status") and bug.status:
                        status_name = str(bug.status).lower()
                        if status_name in ["fix released", "fix committed", "invalid", "won't fix", "expired"]:
                            status = IssueStatus.CLOSED
                        elif status_name in ["new", "incomplete", "confirmed", "triaged", "in progress", "opinion"]:
                            status = IssueStatus.OPEN
                        else:
                            status = IssueStatus.UNKNOWN
                        logger.debug(f"Launchpad bug {bug_number} status from bug: {status_name} -> {status}")
                    else:
                        logger.warning(f"Launchpad bug {bug_number} has no status information available")
                
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
            except AttributeError as e:
                logger.warning(f"Launchpad bug {bug_number} missing required attributes: {e}")
                return None
        except Exception as e:
            logger.error(f"Error fetching Launchpad bug {bug_number}: {type(e).__name__}: {e}", exc_info=True)
            raise
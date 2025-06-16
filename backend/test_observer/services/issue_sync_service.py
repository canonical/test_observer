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
from datetime import datetime

from sqlalchemy.orm import Session

from test_observer.data_access.models import TestCaseIssue, EnvironmentIssue
from test_observer.data_access.models_enums import IssueSyncStatus
from test_observer.external_apis.issue_tracking import (
    GitHubAPI,
    JiraAPI,
    LaunchpadBugAPI,
    IssueURLParser,
    IssueInfo,
)

logger = logging.getLogger(__name__)


class IssueSyncService:
    """Service for synchronizing issue statuses from external APIs"""
    
    def __init__(self, 
                 github_api: GitHubAPI | None = None,
                 jira_api: JiraAPI | None = None,
                 launchpad_api: LaunchpadBugAPI | None = None):
        self.github_api = github_api or GitHubAPI()
        self.jira_api = jira_api or JiraAPI()
        self.launchpad_api = launchpad_api or LaunchpadBugAPI()
        self.url_parser = IssueURLParser()
    
    def sync_test_case_issues(self, db: Session) -> dict[str, int]:
        """
        Sync all test case issues with external APIs
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {"synced": 0, "failed": 0, "skipped": 0}
        
        # Get all test case issues that need syncing
        issues = db.query(TestCaseIssue).filter(
            TestCaseIssue.url.isnot(None)
        ).all()
        
        for issue in issues:
            try:
                result = self._sync_issue_status(issue.url)
                if result:
                    # Update issue with synced data
                    issue.external_id = result.external_id
                    issue.issue_status = result.status
                    issue.sync_status = IssueSyncStatus.SYNCED
                    issue.last_synced_at = datetime.utcnow()
                    issue.sync_error = None
                    stats["synced"] += 1
                    logger.info(f"Synced test case issue {issue.id}: {issue.url}")
                else:
                    # Failed to sync
                    issue.sync_status = IssueSyncStatus.SYNC_FAILED
                    issue.sync_error = "Failed to fetch issue data"
                    stats["failed"] += 1
                    logger.warning(f"Failed to sync test case issue {issue.id}: {issue.url}")
            except Exception as e:
                # Handle sync error
                issue.sync_status = IssueSyncStatus.SYNC_FAILED
                issue.sync_error = str(e)[:500]  # Limit error message length
                stats["failed"] += 1
                logger.error(f"Error syncing test case issue {issue.id}: {e}")
        
        db.commit()
        return stats
    
    def sync_environment_issues(self, db: Session) -> dict[str, int]:
        """
        Sync all environment issues with external APIs
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {"synced": 0, "failed": 0, "skipped": 0}
        
        # Get all environment issues that need syncing
        issues = db.query(EnvironmentIssue).filter(
            EnvironmentIssue.url.isnot(None)
        ).all()
        
        for issue in issues:
            try:
                result = self._sync_issue_status(issue.url)
                if result:
                    # Update issue with synced data
                    issue.external_id = result.external_id
                    issue.issue_status = result.status
                    issue.sync_status = IssueSyncStatus.SYNCED
                    issue.last_synced_at = datetime.utcnow()
                    issue.sync_error = None
                    stats["synced"] += 1
                    logger.info(f"Synced environment issue {issue.id}: {issue.url}")
                else:
                    # Failed to sync
                    issue.sync_status = IssueSyncStatus.SYNC_FAILED
                    issue.sync_error = "Failed to fetch issue data"
                    stats["failed"] += 1
                    logger.warning(f"Failed to sync environment issue {issue.id}: {issue.url}")
            except Exception as e:
                # Handle sync error
                issue.sync_status = IssueSyncStatus.SYNC_FAILED
                issue.sync_error = str(e)[:500]  # Limit error message length
                stats["failed"] += 1
                logger.error(f"Error syncing environment issue {issue.id}: {e}")
        
        db.commit()
        return stats
    
    def _sync_issue_status(self, url: str) -> IssueInfo | None:
        """
        Sync status for a single issue URL
        
        Args:
            url: Issue URL to sync
            
        Returns:
            IssueInfo object if successful, None if failed
        """
        if not url:
            return None
        
        parsed_url = self.url_parser.parse_url(url)
        if not parsed_url:
            logger.warning(f"Could not parse issue URL: {url}")
            return None
        
        try:
            if parsed_url.platform == "github":
                return self.github_api.get_issue(
                    parsed_url.owner, 
                    parsed_url.repo, 
                    parsed_url.external_id
                )
            elif parsed_url.platform == "jira":
                return self.jira_api.get_issue(parsed_url.external_id)
            elif parsed_url.platform == "launchpad":
                return self.launchpad_api.get_bug(parsed_url.external_id)
            else:
                logger.warning(f"Unsupported platform: {parsed_url.platform}")
                return None
        except Exception as e:
            logger.error(f"Error fetching issue data for {url}: {e}")
            return None
    
    def sync_all_issues(self, db: Session) -> dict[str, int]:
        """
        Sync all issues (test case and environment)
        
        Args:
            db: Database session
            
        Returns:
            Combined sync statistics
        """
        test_case_stats = self.sync_test_case_issues(db)
        env_stats = self.sync_environment_issues(db)
        
        return {
            "test_case_synced": test_case_stats["synced"],
            "test_case_failed": test_case_stats["failed"],
            "environment_synced": env_stats["synced"],
            "environment_failed": env_stats["failed"],
            "total_synced": test_case_stats["synced"] + env_stats["synced"],
            "total_failed": test_case_stats["failed"] + env_stats["failed"],
        }
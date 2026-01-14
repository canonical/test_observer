# Copyright (C) 2025 Canonical Ltd.
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

from __future__ import annotations

import logging
from dataclasses import dataclass
from os import environ

from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue
from test_observer.data_access.models_enums import IssueSource, IssueStatus
from test_observer.external_apis.exceptions import (
    IssueNotFoundError,
    APIError,
)
from test_observer.external_apis.github.github_client import GitHubClient
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a single issue sync"""

    issue_id: int
    source: IssueSource
    project: str
    key: str
    success: bool
    title_updated: bool = False
    status_updated: bool = False
    error: str | None = None


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


class IssueSynchronizer:
    """Synchronizes issues from external sources (GitHub, Jira, Launchpad)"""

    def __init__(self):
        """Initialize clients for each platform using environment variables"""
        # GitHub client - token is optional for public repos
        github_token = environ.get("GITHUB_TOKEN")
        self.github_client = GitHubClient(token=github_token)

        # Jira client - requires base URL, email and api_token for Cloud auth
        jira_base_url = environ.get("JIRA_BASE_URL")
        jira_email = environ.get("JIRA_EMAIL")
        jira_api_token = environ.get("JIRA_API_TOKEN")
        jira_bearer_token = ""

        self.jira_client = JiraClient(
            base_url=jira_base_url,
            email=jira_email,
            api_token=jira_api_token,
            bearer_token=jira_bearer_token,
        )

        # Launchpad client - can use anonymous or credentials file
        launchpad_anonymous = (
            environ.get("LAUNCHPAD_ANONYMOUS", "true").lower() == "true"
        )
        launchpad_credentials = environ.get("LAUNCHPAD_CREDENTIALS_FILE")

        self.launchpad_client = LaunchpadClient(
            anonymous=launchpad_anonymous,
            credentials_file=launchpad_credentials,
        )

    def sync_all_issues(self, db: Session) -> SyncResults:
        """
        Synchronize all issues in the database.

        Args:
            db: Database session

        Returns:
            SyncResults with statistics
        """
        # Fetch all issues from database
        issues = db.query(Issue).all()
        total = len(issues)

        logger.info(f"Starting synchronization of {total} issues")

        results_list: list[SyncResult] = []
        successful = 0
        failed = 0
        updated = 0

        for issue in issues:
            result = self.sync_issue(db, issue)
            results_list.append(result)

            if result.success:
                successful += 1
                if result.title_updated or result.status_updated:
                    updated += 1
            else:
                failed += 1

        sync_results = SyncResults(
            total=total,
            successful=successful,
            failed=failed,
            updated=updated,
            results=results_list,
        )

        logger.info(
            f"Synchronization complete: {successful}/{total} successful, "
            f"{updated} updated, success rate: {sync_results.success_rate:.1f}%"
        )

        return sync_results

    def sync_issue(self, db: Session, issue: Issue) -> SyncResult:
        """
        Synchronize a single issue.

        Args:
            db: Database session
            issue: Issue to sync

        Returns:
            SyncResult with outcome
        """
        try:
            # Get appropriate client for this issue source
            client = self._get_client(issue.source)

            # Fetch issue data from external API
            issue_data = client.get_issue(issue.project, issue.key)

            # Track what changed
            title_updated = False
            status_updated = False

            # Update title if changed
            if issue.title != issue_data.title:
                logger.debug(
                    f"Updating title for {issue.source} {issue.project}/{issue.key}: "
                    f"{issue.title!r} → {issue_data.title!r}"
                )
                issue.title = issue_data.title
                title_updated = True

            # Map state to status enum
            new_status = self._map_status(issue_data.state)

            # Update status if changed
            if issue.status != new_status:
                logger.debug(
                    f"Updating status for {issue.source} {issue.project}/{issue.key}: "
                    f"{issue.status} → {new_status}"
                )
                issue.status = new_status
                status_updated = True

            # Commit changes if anything updated
            if title_updated or status_updated:
                db.commit()

            return SyncResult(
                issue_id=issue.id,
                source=issue.source,
                project=issue.project,
                key=issue.key,
                success=True,
                title_updated=title_updated,
                status_updated=status_updated,
            )

        except IssueNotFoundError as e:
            logger.warning(
                f"Issue {issue.source} {issue.project}/{issue.key} not found: {e}"
            )
            return SyncResult(
                issue_id=issue.id,
                source=issue.source,
                project=issue.project,
                key=issue.key,
                success=False,
                error=str(e),
            )

        except APIError as e:
            logger.error(
                f"API error syncing {issue.source} {issue.project}/{issue.key}: {e}"
            )
            return SyncResult(
                issue_id=issue.id,
                source=issue.source,
                project=issue.project,
                key=issue.key,
                success=False,
                error=f"API error: {e}",
            )

        except Exception as e:
            logger.exception(
                f"Unexpected error syncing {issue.source} "
                f"{issue.project}/{issue.key}: {e}"
            )
            return SyncResult(
                issue_id=issue.id,
                source=issue.source,
                project=issue.project,
                key=issue.key,
                success=False,
                error=f"Unexpected error: {e}",
            )

    def _get_client(
        self, source: IssueSource
    ) -> GitHubClient | JiraClient | LaunchpadClient:
        """Get the appropriate client for the issue source"""
        if source == IssueSource.GITHUB:
            return self.github_client
        elif source == IssueSource.JIRA:
            return self.jira_client
        elif source == IssueSource.LAUNCHPAD:
            return self.launchpad_client
        else:
            raise ValueError(f"Unknown issue source: {source}")

    def _map_status(self, state: str) -> IssueStatus:
        """Map normalized state to IssueStatus enum"""
        if state == "open":
            return IssueStatus.OPEN
        elif state == "closed":
            return IssueStatus.CLOSED
        else:
            return IssueStatus.UNKNOWN

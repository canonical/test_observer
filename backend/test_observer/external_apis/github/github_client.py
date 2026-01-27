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

from github import Github, GithubIntegration
from github.Issue import Issue as GithubIssue
import logging

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub client using GitHub App authentication"""

    def __init__(self, app_id: str, private_key: str):
        """
        Initialize GitHub client with App credentials

        Args:
            app_id: GitHub App ID
            private_key: GitHub App Private Key (PEM format)

        Raises:
            ValueError: If credentials are missing or invalid
        """
        if not app_id or not private_key:
            raise ValueError("GitHub App ID and Private Key are required")

        self.app_id = app_id
        self.private_key = private_key
        self._github = self._authenticate_as_app()

    def _authenticate_as_app(self) -> Github:
        """Authenticate using GitHub App credentials"""
        try:
            # Create GitHub Integration
            integration = GithubIntegration(self.app_id, self.private_key)

            # Get all installations for this app
            installations = list(integration.get_installations())

            if not installations:
                raise ValueError("No installations found for this GitHub App")

            # Use the first installation
            installation = installations[0]

            logger.info(f"Authenticated as GitHub App installation {installation.id}")

            # Get installation access token
            token = integration.get_access_token(installation.id).token

            return Github(token)

        except Exception as e:
            logger.error(f"Failed to authenticate with GitHub App: {e}")
            raise

    def get_issue(self, project: str, key: str) -> GithubIssue:
        """
        Get issue from GitHub

        Args:
            project: Repository in format "owner/repo" (e.g., "canonical/test-observer")
            key: Issue number (e.g., "123")

        Returns:
            GitHub Issue object

        Raises:
            ValueError: If project format is invalid
            GithubException: If issue cannot be fetched
        """
        try:
            # Validate project format (should be "owner/repo")
            if "/" not in project:
                raise ValueError(
                    f"Invalid project format: {project}. Expected 'owner/repo'"
                )

            # Parse issue number
            issue_number = int(key.lstrip("#"))

            # Fetch issue
            repository = self._github.get_repo(project)
            return repository.get_issue(issue_number)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch GitHub issue {project}#{key}: {e}")
            raise

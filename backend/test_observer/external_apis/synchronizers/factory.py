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

from os import environ
from test_observer.external_apis.github import GitHubClient
from test_observer.external_apis.jira import JiraClient
from test_observer.external_apis.launchpad import LaunchpadClient
from test_observer.external_apis.synchronizers.base import BaseIssueSynchronizer
from test_observer.external_apis.synchronizers.github import GitHubIssueSynchronizer
from test_observer.external_apis.synchronizers.jira import JiraIssueSynchronizer
from test_observer.external_apis.synchronizers.launchpad import (
    LaunchpadIssueSynchronizer,
)
from test_observer.external_apis.synchronizers.service import (
    IssueSynchronizationService,
)
import logging

logger = logging.getLogger(__name__)


def create_synchronization_service() -> IssueSynchronizationService:
    """
    Factory to create synchronization service with all configured synchronizers

    Required environment variables:
        - GIT_APP_ID: GitHub App ID
        - GIT_APP_PRIVATE_KEY: GitHub App Private Key (PEM format)

    Optional environment variables:
        - JIRA_URL: Jira instance URL (default: https://warthogs.atlassian.net)
        - JIRA_API_TOKEN: Jira API token
        - LAUNCHPAD_CREDENTIALS_PATH: Path to Launchpad credentials file

    Returns:
        IssueSynchronizationService with all configured synchronizers

    Raises:
        ValueError: If required GitHub credentials are missing
    """
    synchronizers: list[BaseIssueSynchronizer] = []

    github_app_id = environ.get("GIT_APP_ID")
    github_private_key = environ.get("GIT_APP_PRIVATE_KEY")

    if not github_app_id or not github_private_key:
        logger.error("GitHub App credentials not configured")
        raise ValueError(
            "Missing GitHub App credentials. "
            "Set GIT_APP_ID and GIT_APP_PRIVATE_KEY environment variables."
        )

    try:
        github_client = GitHubClient(
            app_id=github_app_id, private_key=github_private_key
        )
        synchronizers.append(GitHubIssueSynchronizer(github_client))
        logger.info("GitHub synchronizer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize GitHub synchronizer: {e}")
        raise

    jira_base_url = environ.get("JIRA_URL", "https://warthogs.atlassian.net")
    jira_api_token = environ.get("JIRA_API_TOKEN")
    jira_email = environ.get("JIRA_EMAIL")

    if jira_api_token and jira_email:
        try:
            jira_client = JiraClient(
                base_url=jira_base_url, email=jira_email, api_token=jira_api_token
            )
            synchronizers.append(JiraIssueSynchronizer(jira_client))
            logger.info("Jira synchronizer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Jira synchronizer: {e}")
    else:
        logger.warning("JIRA_API_TOKEN not set, Jira sync disabled")

    try:
        launchpad_client = LaunchpadClient()
        synchronizers.append(LaunchpadIssueSynchronizer(launchpad_client))
        logger.info("Launchpad synchronizer initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Launchpad synchronizer: {e}")

    if not synchronizers:
        raise ValueError("No synchronizers could be initialized")

    return IssueSynchronizationService(synchronizers)

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
import logging

from test_observer.external_apis.github.github_client import GitHubClient
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.synchronizers.base import BaseIssueSynchronizer
from test_observer.external_apis.synchronizers.github import GitHubIssueSynchronizer
from test_observer.external_apis.synchronizers.jira import JiraIssueSynchronizer
from test_observer.external_apis.synchronizers.launchpad import (
    LaunchpadIssueSynchronizer,
)
from test_observer.external_apis.synchronizers.service import (
    IssueSynchronizationService,
)

logger = logging.getLogger(__name__)


def create_synchronization_service() -> IssueSynchronizationService:
    """
    Factory function to create IssueSynchronizationService with configured clients

    All synchronizers are optional - at least one must be configured for the
    service to be created successfully.

    Returns:
        IssueSynchronizationService instance with available synchronizers

    Raises:
        ValueError: If no synchronizers could be configured
    """
    synchronizers: list[BaseIssueSynchronizer] = []

    github_app_id = environ.get("GIT_APP_ID")
    github_private_key = environ.get("GIT_APP_PRIVATE_KEY")

    if github_app_id and github_private_key:
        try:
            github_client = GitHubClient(
                app_id=github_app_id, private_key=github_private_key
            )
            synchronizers.append(GitHubIssueSynchronizer(github_client))
            logger.info("GitHub synchronizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub synchronizer: {e}")
    else:
        logger.warning(
            "GitHub App credentials not configured, skipping GitHub synchronizer"
        )

    jira_base_url = environ.get("JIRA_URL")
    jira_email = environ.get("JIRA_EMAIL")
    jira_api_token = environ.get("JIRA_API_TOKEN")

    if jira_base_url and jira_email and jira_api_token:
        try:
            jira_client = JiraClient(
                base_url=jira_base_url, email=jira_email, api_token=jira_api_token
            )
            synchronizers.append(JiraIssueSynchronizer(jira_client))
            logger.info("Jira synchronizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Jira synchronizer: {e}")
    else:
        logger.warning(
            "Jira credentials not fully configured, skipping Jira synchronizer"
        )

    launchpad_app_name = environ.get("LAUNCHPAD_APP_NAME")

    if launchpad_app_name:
        try:
            launchpad_client = LaunchpadClient()
            synchronizers.append(LaunchpadIssueSynchronizer(launchpad_client))
            logger.info("Launchpad synchronizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Launchpad synchronizer: {e}")
    else:
        logger.warning(
            "Launchpad app name not configured, skipping Launchpad synchronizer"
        )

    if not synchronizers:
        raise ValueError(
            "No synchronizers configured. At least one of GitHub, Jira, or Launchpad "
            "credentials must be provided."
        )

    return IssueSynchronizationService(synchronizers)

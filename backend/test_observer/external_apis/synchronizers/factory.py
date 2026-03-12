# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import logging
from os import environ

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
            github_client = GitHubClient(app_id=github_app_id, private_key=github_private_key)
            synchronizers.append(GitHubIssueSynchronizer(github_client))
            logger.info("GitHub synchronizer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub synchronizer: {e}")
    else:
        logger.warning("GitHub App credentials not configured, skipping GitHub synchronizer")

    jira_cloud_id = environ.get("JIRA_CLOUD_ID")
    jira_email = environ.get("JIRA_EMAIL")
    jira_api_token = environ.get("JIRA_API_TOKEN")

    if jira_cloud_id and jira_email and jira_api_token:
        try:
            jira_client = JiraClient(
                cloud_id=jira_cloud_id,
                email=jira_email,
                api_token=jira_api_token,
            )
            synchronizers.append(JiraIssueSynchronizer(jira_client))
            logger.info("Jira synchronizer initialized with scoped service account")
        except Exception as e:
            logger.error(f"Failed to initialize Jira synchronizer: {e}")
    else:
        logger.warning(
            "Jira credentials not fully configured "
            "(need JIRA_CLOUD_ID, JIRA_EMAIL, JIRA_API_TOKEN), "
            "skipping Jira synchronizer"
        )

    try:
        launchpad_client = LaunchpadClient()
        synchronizers.append(LaunchpadIssueSynchronizer(launchpad_client))
        logger.info("Launchpad synchronizer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Launchpad synchronizer: {e}")

    if not synchronizers:
        raise ValueError(
            "No synchronizers configured. At least one of GitHub, Jira, or Launchpad credentials must be provided."
        )

    return IssueSynchronizationService(synchronizers)

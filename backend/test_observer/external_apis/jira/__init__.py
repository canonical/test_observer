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

from os import environ

from .jira_client import JiraClient


def get_jira_client() -> JiraClient:
    """Build a configured JiraClient from environment variables.

    Raises:
        ValueError: If any required Jira credential env vars are missing.
    """
    jira_cloud_id = environ.get("JIRA_CLOUD_ID")
    jira_email = environ.get("JIRA_EMAIL")
    jira_api_token = environ.get("JIRA_API_TOKEN")

    if not all([jira_cloud_id, jira_email, jira_api_token]):
        raise ValueError("Jira credentials not fully configured. Requires: JIRA_CLOUD_ID, JIRA_EMAIL, JIRA_API_TOKEN")

    return JiraClient(
        cloud_id=str(jira_cloud_id),
        email=str(jira_email),
        api_token=str(jira_api_token),
    )


__all__ = ["JiraClient", "get_jira_client"]

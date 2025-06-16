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


import os
from datetime import datetime
import base64

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from test_observer.data_access.models_enums import IssueStatus
from .models import IssueInfo


class JiraAPI:
    """Client for Jira REST API"""
    
    def __init__(self, base_url: str | None = None, 
                 username: str | None = None, token: str | None = None):
        self.base_url = (base_url or os.environ.get("JIRA_BASE_URL", "https://warthogs.atlassian.net")).rstrip("/")
        self.username = username or os.environ.get("JIRA_USERNAME")
        self.token = token or os.environ.get("JIRA_TOKEN")
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        # Basic auth if credentials provided
        if self.username and self.token:
            auth_string = f"{self.username}:{self.token}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {auth_bytes}"
            
        self.session.headers.update(headers)
    
    def get_issue(self, issue_key: str) -> IssueInfo | None:
        """
        Get issue information from Jira
        
        Args:
            issue_key: Jira issue key (e.g., "TEST-123")
            
        Returns:
            IssueInfo object if successful, None if not found or error
        """
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 404:
                return None
            response.raise_for_status()
            
            data = response.json()
            fields = data.get("fields", {})
            
            # Determine issue status
            status_name = fields.get("status", {}).get("name", "").lower()
            if status_name in ["done", "closed", "resolved", "complete"]:
                status = IssueStatus.CLOSED
            elif status_name in ["open", "to do", "in progress", "in review"]:
                status = IssueStatus.OPEN
            else:
                status = IssueStatus.UNKNOWN
            
            # Parse last updated time
            last_updated = None
            if fields.get("updated"):
                # Jira returns datetime in format "2023-12-01T10:30:00.000+0000"
                timestamp_str = fields["updated"]
                # Remove milliseconds and convert timezone format
                if "." in timestamp_str:
                    timestamp_str = timestamp_str.split(".")[0] + "+00:00"
                last_updated = datetime.fromisoformat(timestamp_str)
            
            # Extract labels
            labels = [label for label in fields.get("labels", [])]
            
            # Get assignee
            assignee = None
            if fields.get("assignee"):
                assignee = fields["assignee"].get("displayName") or fields["assignee"].get("name")
            
            # Build issue URL
            issue_url = f"{self.base_url}/browse/{issue_key}"
            
            return IssueInfo(
                external_id=issue_key,
                title=fields.get("summary", ""),
                status=status,
                url=issue_url,
                last_updated=last_updated,
                assignee=assignee,
                labels=labels,
                description=fields.get("description", {}).get("content") if isinstance(fields.get("description"), dict) else None
            )
            
        except (requests.RequestException, ValueError, KeyError):
            # Log error in production, for now return None
            return None
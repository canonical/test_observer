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
import logging
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from test_observer.data_access.models_enums import IssueStatus
from .models import IssueInfo

logger = logging.getLogger(__name__)


class GitHubAPI:
    """Client for GitHub Issues API"""
    
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        
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
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers.update(headers)
    
    def get_issue(self, owner: str, repo: str, issue_number: str) -> IssueInfo | None:
        """
        Get issue information from GitHub
        
        Args:
            owner: Repository owner
            repo: Repository name  
            issue_number: Issue number
            
        Returns:
            IssueInfo object if successful, None if not found or error
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
            logger.debug(f"Fetching GitHub issue from: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 404:
                logger.info(f"GitHub issue not found: {owner}/{repo}#{issue_number}")
                return None
            response.raise_for_status()
            
            data = response.json()
            
            # Determine issue status
            if data["state"] == "closed":
                status = IssueStatus.CLOSED
            elif data["state"] == "open":
                status = IssueStatus.OPEN
            else:
                status = IssueStatus.UNKNOWN
            
            # Parse last updated time
            last_updated = None
            if data.get("updated_at"):
                last_updated = datetime.fromisoformat(
                    data["updated_at"].replace("Z", "+00:00")
                )
            
            # Extract labels
            labels = [label["name"] for label in data.get("labels", [])]
            
            # Get assignee
            assignee = None
            if data.get("assignee"):
                assignee = data["assignee"]["login"]
            
            return IssueInfo(
                external_id=str(data["number"]),
                title=data["title"],
                status=status,
                url=data["html_url"],
                last_updated=last_updated,
                assignee=assignee,
                labels=labels,
                description=data.get("body")
            )
            
        except requests.RequestException as e:
            logger.error(f"HTTP error fetching GitHub issue {owner}/{repo}#{issue_number}: {type(e).__name__}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}, body: {e.response.text[:500]}")
            raise
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing GitHub API response for {owner}/{repo}#{issue_number}: {type(e).__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching GitHub issue {owner}/{repo}#{issue_number}: {type(e).__name__}: {e}")
            raise
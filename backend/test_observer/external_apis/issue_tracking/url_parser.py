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


import re
from urllib.parse import urlparse

from .models import ParsedIssueURL


class IssueURLParser:
    """Parser for extracting issue information from URLs"""
    
    # URL patterns for different issue tracking systems
    GITHUB_PATTERN = re.compile(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)")
    JIRA_PATTERN = re.compile(r"([a-zA-Z0-9.-]+)/browse/([A-Z][A-Z0-9]+-\d+)")
    LAUNCHPAD_PATTERN = re.compile(r"bugs\.launchpad\.net/.*?(?:\+bug|bugs)/(\d+)")
    
    @classmethod
    def parse_url(cls, url: str) -> ParsedIssueURL | None:
        """
        Parse an issue URL and extract relevant information
        
        Args:
            url: The URL to parse
            
        Returns:
            ParsedIssueURL object if successful, None if URL format not recognized
        """
        if not url:
            return None
            
        parsed_url = urlparse(url)
        
        # GitHub issues
        github_match = cls.GITHUB_PATTERN.search(url)
        if github_match and parsed_url.hostname == "github.com":
            owner, repo, issue_number = github_match.groups()
            return ParsedIssueURL(
                platform="github",
                host=parsed_url.hostname,
                external_id=issue_number,
                owner=owner,
                repo=repo
            )
        
        # Jira issues
        jira_match = cls.JIRA_PATTERN.search(url)
        if jira_match:
            host, issue_key = jira_match.groups()
            project_key = issue_key.split("-")[0]
            return ParsedIssueURL(
                platform="jira",
                host=host,
                external_id=issue_key,
                project=project_key
            )
        
        # Launchpad bugs  
        launchpad_match = cls.LAUNCHPAD_PATTERN.search(url)
        if launchpad_match and parsed_url.hostname == "bugs.launchpad.net":
            bug_number = launchpad_match.groups()[0]
            return ParsedIssueURL(
                platform="launchpad",
                host=parsed_url.hostname,
                external_id=bug_number
            )
        
        return None
    
    @classmethod
    def is_supported_url(cls, url: str) -> bool:
        """Check if a URL is from a supported issue tracking system"""
        return cls.parse_url(url) is not None
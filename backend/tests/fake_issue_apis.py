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


from datetime import datetime

from test_observer.data_access.models_enums import IssueStatus
from test_observer.external_apis.issue_tracking import (
    GitHubAPI,
    JiraAPI,
    LaunchpadBugAPI,
    IssueInfo,
)


class FakeGitHubAPI(GitHubAPI):
    """Fake GitHub API for testing"""
    
    def __init__(self, token: str | None = None):
        # Override superclass init to avoid HTTP setup
        pass
    
    def get_issue(self, owner: str, repo: str, issue_number: str) -> IssueInfo | None:
        """Return fake issue data based on issue number"""
        # Mock data for testing
        test_issues = {
            "1": IssueInfo(
                external_id="1",
                title="Test issue 1",
                status=IssueStatus.OPEN,
                url=f"https://github.com/{owner}/{repo}/issues/1",
                last_updated=datetime(2023, 12, 1, 10, 30),
                assignee="test-user",
                labels=["bug", "high-priority"],
                description="This is a test issue"
            ),
            "2": IssueInfo(
                external_id="2",
                title="Test issue 2",
                status=IssueStatus.CLOSED,
                url=f"https://github.com/{owner}/{repo}/issues/2",
                last_updated=datetime(2023, 12, 2, 14, 45),
                assignee=None,
                labels=["enhancement"],
                description="This is a closed test issue"
            ),
            "999": None  # Not found case
        }
        
        return test_issues.get(issue_number)


class FakeJiraAPI(JiraAPI):
    """Fake Jira API for testing"""
    
    def __init__(self, base_url: str = "https://warthogs.atlassian.net", 
                 username: str | None = None, token: str | None = None):
        # Override superclass init to avoid HTTP setup
        pass
    
    def get_issue(self, issue_key: str) -> IssueInfo | None:
        """Return fake issue data based on issue key"""
        # Mock data for testing
        test_issues = {
            "TEST-123": IssueInfo(
                external_id="TEST-123",
                title="Test Jira issue",
                status=IssueStatus.OPEN,
                url="https://warthogs.atlassian.net/browse/TEST-123",
                last_updated=datetime(2023, 12, 1, 9, 15),
                assignee="Jane Smith",
                labels=["testing", "automation"],
                description="This is a test Jira issue"
            ),
            "DONE-456": IssueInfo(
                external_id="DONE-456",
                title="Completed Jira issue",
                status=IssueStatus.CLOSED,
                url="https://warthogs.atlassian.net/browse/DONE-456",
                last_updated=datetime(2023, 11, 30, 16, 30),
                assignee="Bob Johnson",
                labels=["completed"],
                description="This is a completed Jira issue"
            ),
            "MISSING-999": None  # Not found case
        }
        
        return test_issues.get(issue_key)


class FakeLaunchpadBugAPI(LaunchpadBugAPI):
    """Fake Launchpad Bugs API for testing"""
    
    def __init__(self):
        # Override superclass init to avoid Launchpad API setup
        pass
    
    def get_bug(self, bug_number: str) -> IssueInfo | None:
        """Return fake bug data based on bug number"""
        # Mock data for testing
        test_bugs = {
            "123456": IssueInfo(
                external_id="123456",
                title="Test Launchpad bug",
                status=IssueStatus.OPEN,
                url="https://bugs.launchpad.net/bugs/123456",
                last_updated=datetime(2023, 12, 1, 8, 45),
                assignee="Alice Cooper",
                labels=["kernel", "regression"],
                description="This is a test Launchpad bug"
            ),
            "789012": IssueInfo(
                external_id="789012",
                title="Fixed Launchpad bug",
                status=IssueStatus.CLOSED,
                url="https://bugs.launchpad.net/bugs/789012",
                last_updated=datetime(2023, 11, 29, 12, 20),
                assignee=None,
                labels=["fixed"],
                description="This is a fixed Launchpad bug"
            ),
            "999999": None  # Not found case
        }
        
        return test_bugs.get(bug_number)
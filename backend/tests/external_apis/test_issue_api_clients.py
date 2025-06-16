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
from tests.fake_issue_apis import FakeGitHubAPI, FakeJiraAPI, FakeLaunchpadBugAPI


class TestFakeGitHubAPI:
    """Test suite for FakeGitHubAPI"""
    
    def test_get_existing_open_issue(self):
        """Test retrieving an existing open issue"""
        api = FakeGitHubAPI()
        result = api.get_issue("canonical", "test-observer", "1")
        
        assert result is not None
        assert result.external_id == "1"
        assert result.title == "Test issue 1"
        assert result.status == IssueStatus.OPEN
        assert result.url == "https://github.com/canonical/test-observer/issues/1"
        assert result.assignee == "test-user"
        assert result.labels == ["bug", "high-priority"]
        assert result.description == "This is a test issue"
        assert isinstance(result.last_updated, datetime)
    
    def test_get_existing_closed_issue(self):
        """Test retrieving an existing closed issue"""
        api = FakeGitHubAPI()
        result = api.get_issue("canonical", "test-observer", "2")
        
        assert result is not None
        assert result.external_id == "2"
        assert result.title == "Test issue 2" 
        assert result.status == IssueStatus.CLOSED
        assert result.assignee is None
        assert result.labels == ["enhancement"]
    
    def test_get_nonexistent_issue(self):
        """Test retrieving a non-existent issue returns None"""
        api = FakeGitHubAPI()
        result = api.get_issue("canonical", "test-observer", "999")
        
        assert result is None
    
    def test_get_unknown_issue_number(self):
        """Test retrieving an unknown issue number returns None"""
        api = FakeGitHubAPI()
        result = api.get_issue("canonical", "test-observer", "12345")
        
        assert result is None


class TestFakeJiraAPI:
    """Test suite for FakeJiraAPI"""
    
    def test_get_existing_open_issue(self):
        """Test retrieving an existing open Jira issue"""
        api = FakeJiraAPI()
        result = api.get_issue("TEST-123")
        
        assert result is not None
        assert result.external_id == "TEST-123"
        assert result.title == "Test Jira issue"
        assert result.status == IssueStatus.OPEN
        assert result.url == "https://warthogs.atlassian.net/browse/TEST-123"
        assert result.assignee == "Jane Smith"
        assert result.labels == ["testing", "automation"]
        assert result.description == "This is a test Jira issue"
        assert isinstance(result.last_updated, datetime)
    
    def test_get_existing_closed_issue(self):
        """Test retrieving an existing closed Jira issue"""
        api = FakeJiraAPI()
        result = api.get_issue("DONE-456")
        
        assert result is not None
        assert result.external_id == "DONE-456"
        assert result.title == "Completed Jira issue"
        assert result.status == IssueStatus.CLOSED
        assert result.assignee == "Bob Johnson"
        assert result.labels == ["completed"]
    
    def test_get_nonexistent_issue(self):
        """Test retrieving a non-existent Jira issue returns None"""
        api = FakeJiraAPI()
        result = api.get_issue("MISSING-999")
        
        assert result is None
    
    def test_get_unknown_issue_key(self):
        """Test retrieving an unknown issue key returns None"""
        api = FakeJiraAPI()
        result = api.get_issue("UNKNOWN-789")
        
        assert result is None


class TestFakeLaunchpadBugAPI:
    """Test suite for FakeLaunchpadBugAPI"""
    
    def test_get_existing_open_bug(self):
        """Test retrieving an existing open Launchpad bug"""
        api = FakeLaunchpadBugAPI()
        result = api.get_bug("123456")
        
        assert result is not None
        assert result.external_id == "123456"
        assert result.title == "Test Launchpad bug"
        assert result.status == IssueStatus.OPEN
        assert result.url == "https://bugs.launchpad.net/bugs/123456"
        assert result.assignee == "Alice Cooper"
        assert result.labels == ["kernel", "regression"]
        assert result.description == "This is a test Launchpad bug"
        assert isinstance(result.last_updated, datetime)
    
    def test_get_existing_closed_bug(self):
        """Test retrieving an existing closed Launchpad bug"""
        api = FakeLaunchpadBugAPI()
        result = api.get_bug("789012")
        
        assert result is not None
        assert result.external_id == "789012"
        assert result.title == "Fixed Launchpad bug"
        assert result.status == IssueStatus.CLOSED
        assert result.assignee is None
        assert result.labels == ["fixed"]
    
    def test_get_nonexistent_bug(self):
        """Test retrieving a non-existent Launchpad bug returns None"""
        api = FakeLaunchpadBugAPI()
        result = api.get_bug("999999")
        
        assert result is None
    
    def test_get_unknown_bug_number(self):
        """Test retrieving an unknown bug number returns None"""
        api = FakeLaunchpadBugAPI()
        result = api.get_bug("111111")
        
        assert result is None


class TestAPIClientInitialization:
    """Test API client initialization without real connections"""
    
    def test_fake_github_api_initialization(self):
        """Test FakeGitHubAPI initializes without network calls"""
        api = FakeGitHubAPI()
        # Should not raise any errors and not make network calls
        assert api is not None
    
    def test_fake_jira_api_initialization(self):
        """Test FakeJiraAPI initializes without network calls"""
        api = FakeJiraAPI()
        # Should not raise any errors and not make network calls
        assert api is not None
    
    def test_fake_launchpad_api_initialization(self):
        """Test FakeLaunchpadBugAPI initializes without network calls"""
        api = FakeLaunchpadBugAPI()
        # Should not raise any errors and not make network calls
        assert api is not None
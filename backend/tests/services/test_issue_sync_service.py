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



from sqlalchemy.orm import Session

from test_observer.data_access.models import TestCaseIssue, EnvironmentIssue
from test_observer.data_access.models_enums import IssueStatus, IssueSyncStatus
from test_observer.services.issue_sync_service import IssueSyncService
from tests.fake_issue_apis import FakeGitHubAPI, FakeJiraAPI, FakeLaunchpadBugAPI


class TestIssueSyncService:
    """Test suite for IssueSyncService"""
    
    def test_sync_test_case_issues_github(self, db_session: Session):
        """Test syncing test case issues from GitHub"""
        # Create test data
        test_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url="https://github.com/canonical/test-observer/issues/1",
            description="Test GitHub issue"
        )
        db_session.add(test_issue)
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync issues
        stats = service.sync_test_case_issues(db_session)
        
        # Check results
        assert stats["synced"] == 1
        assert stats["failed"] == 0
        
        # Refresh from database
        db_session.refresh(test_issue)
        
        assert test_issue.external_id == "1"
        assert test_issue.issue_status == IssueStatus.OPEN
        assert test_issue.sync_status == IssueSyncStatus.SYNCED
        assert test_issue.last_synced_at is not None
        assert test_issue.sync_error is None
    
    def test_sync_test_case_issues_jira(self, db_session: Session):
        """Test syncing test case issues from Jira"""
        # Create test data
        test_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url="https://warthogs.atlassian.net/browse/TEST-123",
            description="Test Jira issue"
        )
        db_session.add(test_issue)
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync issues
        stats = service.sync_test_case_issues(db_session)
        
        # Check results
        assert stats["synced"] == 1
        assert stats["failed"] == 0
        
        # Refresh from database
        db_session.refresh(test_issue)
        
        assert test_issue.external_id == "TEST-123"
        assert test_issue.issue_status == IssueStatus.OPEN
        assert test_issue.sync_status == IssueSyncStatus.SYNCED
    
    def test_sync_test_case_issues_launchpad(self, db_session: Session):
        """Test syncing test case issues from Launchpad"""
        # Create test data
        test_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url="https://bugs.launchpad.net/ubuntu/+bug/123456",
            description="Test Launchpad bug"
        )
        db_session.add(test_issue)
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync issues
        stats = service.sync_test_case_issues(db_session)
        
        # Check results
        assert stats["synced"] == 1
        assert stats["failed"] == 0
        
        # Refresh from database
        db_session.refresh(test_issue)
        
        assert test_issue.external_id == "123456"
        assert test_issue.issue_status == IssueStatus.OPEN
        assert test_issue.sync_status == IssueSyncStatus.SYNCED
    
    def test_sync_test_case_issues_not_found(self, db_session: Session):
        """Test syncing test case issues that don't exist"""
        # Create test data with non-existent issue
        test_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url="https://github.com/canonical/test-observer/issues/999",
            description="Non-existent GitHub issue"
        )
        db_session.add(test_issue)
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync issues
        stats = service.sync_test_case_issues(db_session)
        
        # Check results
        assert stats["synced"] == 0
        assert stats["failed"] == 1
        
        # Refresh from database
        db_session.refresh(test_issue)
        
        assert test_issue.sync_status == IssueSyncStatus.SYNC_FAILED
        assert test_issue.sync_error == "Failed to fetch issue data"
    
    def test_sync_environment_issues_github(self, db_session: Session):
        """Test syncing environment issues from GitHub"""
        # Create test data
        env_issue = EnvironmentIssue(
            environment_name="test-env",
            url="https://github.com/canonical/test-observer/issues/2",
            description="Test environment issue",
            is_confirmed=True
        )
        db_session.add(env_issue)
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync issues
        stats = service.sync_environment_issues(db_session)
        
        # Check results
        assert stats["synced"] == 1
        assert stats["failed"] == 0
        
        # Refresh from database
        db_session.refresh(env_issue)
        
        assert env_issue.external_id == "2"
        assert env_issue.issue_status == IssueStatus.CLOSED
        assert env_issue.sync_status == IssueSyncStatus.SYNCED
        assert env_issue.last_synced_at is not None
    
    def test_sync_all_issues(self, db_session: Session):
        """Test syncing all issues (test case and environment)"""
        # Create test data
        test_case_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url="https://github.com/canonical/test-observer/issues/1",
            description="Test case issue"
        )
        env_issue = EnvironmentIssue(
            environment_name="test-env",
            url="https://warthogs.atlassian.net/browse/DONE-456",
            description="Environment issue",
            is_confirmed=True
        )
        db_session.add_all([test_case_issue, env_issue])
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync all issues
        stats = service.sync_all_issues(db_session)
        
        # Check results
        assert stats["test_case_synced"] == 1
        assert stats["test_case_failed"] == 0
        assert stats["environment_synced"] == 1
        assert stats["environment_failed"] == 0
        assert stats["total_synced"] == 2
        assert stats["total_failed"] == 0
        
        # Check database updates
        db_session.refresh(test_case_issue)
        db_session.refresh(env_issue)
        
        assert test_case_issue.issue_status == IssueStatus.OPEN
        assert env_issue.issue_status == IssueStatus.CLOSED
    
    def test_sync_issues_with_null_urls(self, db_session: Session):
        """Test syncing issues with null URLs are skipped"""
        # Create test data with null URL
        test_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url=None,
            description="Issue without URL"
        )
        db_session.add(test_issue)
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync issues
        stats = service.sync_test_case_issues(db_session)
        
        # Check results - should be no synced or failed issues
        assert stats["synced"] == 0
        assert stats["failed"] == 0
        
        # Refresh from database
        db_session.refresh(test_issue)
        
        # Should remain unchanged
        assert test_issue.sync_status == IssueSyncStatus.NEVER_SYNCED
        assert test_issue.external_id is None
    
    def test_sync_issues_with_unsupported_urls(self, db_session: Session):
        """Test syncing issues with unsupported URLs"""
        # Create test data with unsupported URL
        test_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url="https://unsupported.example.com/issues/123",
            description="Issue with unsupported URL"
        )
        db_session.add(test_issue)
        db_session.commit()
        
        # Create service with fake APIs
        service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        # Sync issues
        stats = service.sync_test_case_issues(db_session)
        
        # Check results
        assert stats["synced"] == 0
        assert stats["failed"] == 1
        
        # Refresh from database
        db_session.refresh(test_issue)
        
        assert test_issue.sync_status == IssueSyncStatus.SYNC_FAILED
        assert test_issue.sync_error is not None
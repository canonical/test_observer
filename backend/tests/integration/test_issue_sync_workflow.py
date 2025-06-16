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


from unittest.mock import patch

from sqlalchemy.orm import Session

from test_observer.data_access.models import TestCaseIssue, EnvironmentIssue
from test_observer.data_access.models_enums import IssueStatus, IssueSyncStatus
from test_observer.external_apis.issue_tracking import IssueURLParser
from test_observer.services.issue_sync_service import IssueSyncService
from tests.fake_issue_apis import FakeGitHubAPI, FakeJiraAPI, FakeLaunchpadBugAPI


class TestEndToEndIssueSyncWorkflow:
    """End-to-end integration tests for issue sync workflow"""
    
    def test_complete_github_issue_sync_workflow(self, db_session: Session):
        """Test complete workflow: URL parsing, API call, database update for GitHub"""
        # 1. Create test case issue with GitHub URL
        github_url = "https://github.com/canonical/test-observer/issues/1"
        test_case_issue = TestCaseIssue(
            template_id="test-template-001",
            case_name="test-gpu-driver",
            url=github_url,
            description="GPU driver test failing on new hardware"
        )
        db_session.add(test_case_issue)
        db_session.commit()
        
        # 2. Verify URL parsing works
        parsed_url = IssueURLParser.parse_url(github_url)
        assert parsed_url is not None
        assert parsed_url.platform == "github"
        assert parsed_url.owner == "canonical"
        assert parsed_url.repo == "test-observer"
        assert parsed_url.external_id == "1"
        
        # 3. Execute sync service with fake APIs
        sync_service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        stats = sync_service.sync_test_case_issues(db_session)
        
        # 4. Verify sync statistics
        assert stats["synced"] == 1
        assert stats["failed"] == 0
        
        # 5. Verify database was updated correctly
        db_session.refresh(test_case_issue)
        
        assert test_case_issue.external_id == "1"
        assert test_case_issue.issue_status == IssueStatus.OPEN
        assert test_case_issue.sync_status == IssueSyncStatus.SYNCED
        assert test_case_issue.last_synced_at is not None
        assert test_case_issue.sync_error is None
        
        # Original fields should remain unchanged
        assert test_case_issue.template_id == "test-template-001"
        assert test_case_issue.case_name == "test-gpu-driver"
        assert test_case_issue.url == github_url
        assert test_case_issue.description == "GPU driver test failing on new hardware"
    
    def test_complete_jira_issue_sync_workflow(self, db_session: Session):
        """Test complete workflow for Jira issue"""
        # 1. Create environment issue with Jira URL
        jira_url = "https://warthogs.atlassian.net/browse/TEST-123"
        env_issue = EnvironmentIssue(
            environment_name="rpi4-edge-device",
            url=jira_url,
            description="Device connectivity issues",
            is_confirmed=True
        )
        db_session.add(env_issue)
        db_session.commit()
        
        # 2. Verify URL parsing
        parsed_url = IssueURLParser.parse_url(jira_url)
        assert parsed_url is not None
        assert parsed_url.platform == "jira"
        assert parsed_url.external_id == "TEST-123"
        
        # 3. Execute sync
        sync_service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        stats = sync_service.sync_environment_issues(db_session)
        
        # 4. Verify results
        assert stats["synced"] == 1
        assert stats["failed"] == 0
        
        # 5. Verify database update
        db_session.refresh(env_issue)
        
        assert env_issue.external_id == "TEST-123"
        assert env_issue.issue_status == IssueStatus.OPEN
        assert env_issue.sync_status == IssueSyncStatus.SYNCED
    
    def test_complete_launchpad_issue_sync_workflow(self, db_session: Session):
        """Test complete workflow for Launchpad bug"""
        # 1. Create test case issue with Launchpad URL
        launchpad_url = "https://bugs.launchpad.net/ubuntu/+bug/789012"
        test_case_issue = TestCaseIssue(
            template_id="kernel-test-001",
            case_name="network-stress-test",
            url=launchpad_url,
            description="Network stress test regression"
        )
        db_session.add(test_case_issue)
        db_session.commit()
        
        # 2. Verify URL parsing
        parsed_url = IssueURLParser.parse_url(launchpad_url)
        assert parsed_url is not None
        assert parsed_url.platform == "launchpad"
        assert parsed_url.external_id == "789012"
        
        # 3. Execute sync
        sync_service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        stats = sync_service.sync_test_case_issues(db_session)
        
        # 4. Verify results
        assert stats["synced"] == 1
        assert stats["failed"] == 0
        
        # 5. Verify database update - this should be a closed bug
        db_session.refresh(test_case_issue)
        
        assert test_case_issue.external_id == "789012"
        assert test_case_issue.issue_status == IssueStatus.CLOSED
        assert test_case_issue.sync_status == IssueSyncStatus.SYNCED
    
    def test_mixed_platform_sync_workflow(self, db_session: Session):
        """Test syncing issues from different platforms in one operation"""
        # Create issues from different platforms
        github_issue = TestCaseIssue(
            template_id="web-test",
            case_name="login-test",
            url="https://github.com/canonical/test-observer/issues/2",
            description="Login test issue"
        )
        
        jira_issue = EnvironmentIssue(
            environment_name="staging-server",
            url="https://warthogs.atlassian.net/browse/DONE-456",
            description="Staging server configuration",
            is_confirmed=False
        )
        
        launchpad_issue = TestCaseIssue(
            template_id="kernel-test",
            case_name="boot-test",
            url="https://bugs.launchpad.net/ubuntu/+bug/123456",
            description="Boot test failing"
        )
        
        db_session.add_all([github_issue, jira_issue, launchpad_issue])
        db_session.commit()
        
        # Execute sync for all issues
        sync_service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        stats = sync_service.sync_all_issues(db_session)
        
        # Verify overall statistics
        assert stats["total_synced"] == 3
        assert stats["total_failed"] == 0
        assert stats["test_case_synced"] == 2  # github_issue + launchpad_issue
        assert stats["environment_synced"] == 1  # jira_issue
        
        # Verify each issue was updated correctly
        db_session.refresh(github_issue)
        db_session.refresh(jira_issue)
        db_session.refresh(launchpad_issue)
        
        # GitHub issue (closed based on fake API)
        assert github_issue.issue_status == IssueStatus.CLOSED
        assert github_issue.external_id == "2"
        
        # Jira issue (closed based on fake API)
        assert jira_issue.issue_status == IssueStatus.CLOSED
        assert jira_issue.external_id == "DONE-456"
        
        # Launchpad issue (open based on fake API)
        assert launchpad_issue.issue_status == IssueStatus.OPEN
        assert launchpad_issue.external_id == "123456"
    
    def test_sync_workflow_with_failures(self, db_session: Session):
        """Test workflow when some issues fail to sync"""
        # Create mix of valid and invalid issues
        valid_issue = TestCaseIssue(
            template_id="valid-test",
            case_name="valid-case",
            url="https://github.com/canonical/test-observer/issues/1",
            description="Valid GitHub issue"
        )
        
        invalid_issue = TestCaseIssue(
            template_id="invalid-test",
            case_name="invalid-case",
            url="https://github.com/canonical/test-observer/issues/999",  # Non-existent
            description="Invalid GitHub issue"
        )
        
        unsupported_issue = EnvironmentIssue(
            environment_name="test-env",
            url="https://unsupported.example.com/issues/123",
            description="Unsupported platform",
            is_confirmed=True
        )
        
        db_session.add_all([valid_issue, invalid_issue, unsupported_issue])
        db_session.commit()
        
        # Execute sync
        sync_service = IssueSyncService(
            github_api=FakeGitHubAPI(),
            jira_api=FakeJiraAPI(),
            launchpad_api=FakeLaunchpadBugAPI()
        )
        
        stats = sync_service.sync_all_issues(db_session)
        
        # Verify mixed results
        assert stats["total_synced"] == 1  # Only valid_issue
        assert stats["total_failed"] == 2  # invalid_issue + unsupported_issue
        
        # Verify individual issue states
        db_session.refresh(valid_issue)
        db_session.refresh(invalid_issue)
        db_session.refresh(unsupported_issue)
        
        # Valid issue should be synced
        assert valid_issue.sync_status == IssueSyncStatus.SYNCED
        assert valid_issue.issue_status == IssueStatus.OPEN
        
        # Invalid and unsupported issues should have failed
        assert invalid_issue.sync_status == IssueSyncStatus.SYNC_FAILED
        assert unsupported_issue.sync_status == IssueSyncStatus.SYNC_FAILED
        
        # Both should have error messages
        assert invalid_issue.sync_error is not None
        assert unsupported_issue.sync_error is not None
    
    def test_celery_task_integration(self, db_session: Session):
        """Test full Celery task integration with database"""
        # Create test data
        test_issue = TestCaseIssue(
            template_id="celery-test",
            case_name="async-test",
            url="https://github.com/canonical/test-observer/issues/1",
            description="Celery integration test"
        )
        db_session.add(test_issue)
        db_session.commit()
        
        # Mock the Celery task dependencies
        with patch(
            'test_observer.services.issue_sync_service.IssueSyncService'
        ) as mock_service_class:
            # Use real service with fake APIs
            real_service = IssueSyncService(
                github_api=FakeGitHubAPI(),
                jira_api=FakeJiraAPI(),
                launchpad_api=FakeLaunchpadBugAPI()
            )
            mock_service_class.return_value = real_service
            
            # Import and execute the Celery task
            from tasks.celery import sync_issue_statuses
            
            with patch('tasks.celery.SessionLocal', return_value=db_session):
                result = sync_issue_statuses()
            
            # Verify task result
            assert result["total_synced"] == 1
            assert result["total_failed"] == 0
            
            # Verify database was updated
            db_session.refresh(test_issue)
            assert test_issue.sync_status == IssueSyncStatus.SYNCED
            assert test_issue.issue_status == IssueStatus.OPEN
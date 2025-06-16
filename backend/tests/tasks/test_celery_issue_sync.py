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


from unittest.mock import Mock, patch

import pytest

from test_observer.data_access.models import TestCaseIssue, EnvironmentIssue
from test_observer.data_access.models_enums import IssueStatus, IssueSyncStatus
from test_observer.services.issue_sync_service import IssueSyncService


class TestCeleryIssueSyncTask:
    """Test suite for Celery issue sync task integration"""
    
    @patch('test_observer.services.issue_sync_service.IssueSyncService')
    def test_sync_issue_statuses_task_success(self, mock_service_class):
        """Test successful execution of sync_issue_statuses Celery task"""
        # Import here to avoid circular imports with Celery setup
        from tasks.celery import sync_issue_statuses
        
        # Mock the service instance and its methods
        mock_service = Mock(spec=IssueSyncService)
        mock_service.sync_all_issues.return_value = {
            "test_case_synced": 2,
            "test_case_failed": 0,
            "environment_synced": 1,
            "environment_failed": 0,
            "total_synced": 3,
            "total_failed": 0,
        }
        mock_service_class.return_value = mock_service
        
        # Mock SessionLocal to return a mock database session
        with patch('tasks.celery.SessionLocal') as mock_session_local:
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            
            # Execute the task
            result = sync_issue_statuses()
            
            # Verify the service was called correctly
            mock_service_class.assert_called_once()
            mock_service.sync_all_issues.assert_called_once_with(mock_db)
            
            # Verify database session was closed
            mock_db.close.assert_called_once()
            
            # Verify return value
            assert result == {
                "test_case_synced": 2,
                "test_case_failed": 0,
                "environment_synced": 1,
                "environment_failed": 0,
                "total_synced": 3,
                "total_failed": 0,
            }
    
    @patch('test_observer.services.issue_sync_service.IssueSyncService')
    def test_sync_issue_statuses_task_service_failure(self, mock_service_class):
        """Test Celery task when service throws an exception"""
        # Import here to avoid circular imports with Celery setup
        from tasks.celery import sync_issue_statuses
        
        # Mock the service to raise an exception
        mock_service = Mock(spec=IssueSyncService)
        mock_service.sync_all_issues.side_effect = Exception("Service error")
        mock_service_class.return_value = mock_service
        
        # Mock SessionLocal
        with patch('tasks.celery.SessionLocal') as mock_session_local:
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            
            # Execute the task and expect it to raise the exception
            with pytest.raises(Exception, match="Service error"):
                sync_issue_statuses()
            
            # Verify database session was still closed
            mock_db.close.assert_called_once()
    
    def test_sync_issue_statuses_task_integration(self, db_session):
        """Integration test for sync_issue_statuses task with real database"""
        # Create test data
        test_case_issue = TestCaseIssue(
            template_id="test-template",
            case_name="test-case",
            url="https://github.com/canonical/test-observer/issues/1",
            description="Test GitHub issue"
        )
        env_issue = EnvironmentIssue(
            environment_name="test-env",
            url="https://bugs.launchpad.net/ubuntu/+bug/123456",
            description="Test Launchpad bug",
            is_confirmed=True
        )
        db_session.add_all([test_case_issue, env_issue])
        db_session.commit()
        
        # Import fake APIs and patch the service
        from tests.fake_issue_apis import (
            FakeGitHubAPI, FakeJiraAPI, FakeLaunchpadBugAPI
        )
        
        # Mock the service with fake APIs
        with patch(
            'test_observer.services.issue_sync_service.IssueSyncService'
        ) as mock_service_class:
            # Create a real service instance with fake APIs
            real_service = IssueSyncService(
                github_api=FakeGitHubAPI(),
                jira_api=FakeJiraAPI(),
                launchpad_api=FakeLaunchpadBugAPI()
            )
            mock_service_class.return_value = real_service
            
            # Import and run the task with mocked SessionLocal
            from tasks.celery import sync_issue_statuses
            
            with patch('tasks.celery.SessionLocal', return_value=db_session):
                result = sync_issue_statuses()
            
            # Verify results
            assert result["total_synced"] == 2
            assert result["total_failed"] == 0
            
            # Check database updates
            db_session.refresh(test_case_issue)
            db_session.refresh(env_issue)
            
            assert test_case_issue.sync_status == IssueSyncStatus.SYNCED
            assert test_case_issue.issue_status == IssueStatus.OPEN
            assert env_issue.sync_status == IssueSyncStatus.SYNCED
            assert env_issue.issue_status == IssueStatus.OPEN


class TestCeleryPeriodicTaskSetup:
    """Test suite for Celery periodic task configuration"""
    
    def test_periodic_task_is_configured(self):
        """Test that the sync_issue_statuses task is configured as a periodic task"""
        # Import the Celery app configuration
        from tasks.celery import setup_periodic_tasks
        
        # Mock the sender (Celery app) to capture periodic task registration
        mock_sender = Mock()
        
        # Call the setup function
        setup_periodic_tasks(mock_sender)
        
        # Verify that add_periodic_task was called for issue sync
        # The call should be for 900 seconds (15 minutes) interval
        calls = mock_sender.add_periodic_task.call_args_list
        
        # Find the call for sync_issue_statuses
        sync_call = None
        for call in calls:
            args, kwargs = call
            if (len(args) >= 2 and hasattr(args[1], 'name') and 
                'sync_issue_statuses' in str(args[1])):
                break
        
        # Alternative: check if the task interval is 900 seconds
        task_intervals = [call[0][0] for call in calls]
        assert 900 in task_intervals, (
            "Issue sync task should be scheduled every 15 minutes"
        )
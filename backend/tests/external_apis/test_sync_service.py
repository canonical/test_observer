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

from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue, IssueSource, IssueStatus
from test_observer.external_apis.synchronizers.base import (
    BaseIssueSynchronizer,
    SyncResult,
)
from test_observer.external_apis.synchronizers.service import (
    IssueSynchronizationService,
)


def test_service_initialization_requires_synchronizers():
    """Test that service requires at least one synchronizer"""
    with pytest.raises(ValueError, match="At least one synchronizer is required"):
        IssueSynchronizationService([])


def test_service_routes_to_correct_synchronizer(db_session: Session):
    """Test that service routes issues to the correct synchronizer"""
    # Create mock synchronizers
    github_sync = Mock(spec=BaseIssueSynchronizer)
    github_sync.can_sync.return_value = False

    jira_sync = Mock(spec=BaseIssueSynchronizer)
    jira_sync.can_sync.return_value = True
    jira_sync.sync_issue.return_value = SyncResult(success=True)

    # Create service
    service = IssueSynchronizationService([github_sync, jira_sync])

    # Create test issue (Jira)
    issue = Issue(
        source=IssueSource.JIRA,
        project="TEST",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Sync issue
    result = service.sync_issue(issue, db_session)

    # Verify correct synchronizer was used
    assert github_sync.can_sync.called
    assert jira_sync.can_sync.called
    assert jira_sync.sync_issue.called
    assert result.success is True


def test_service_handles_no_matching_synchronizer(db_session: Session):
    """Test handling when no synchronizer can handle the issue"""
    # Create mock synchronizer that rejects the issue
    mock_sync = Mock(spec=BaseIssueSynchronizer)
    mock_sync.can_sync.return_value = False

    # Create service
    service = IssueSynchronizationService([mock_sync])

    # Create test issue with GitHub source (but mock will reject it)
    issue = Issue(
        source=IssueSource.GITHUB,
        project="test/repo",
        key="123",
        title="Test Issue",
        status=IssueStatus.OPEN,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # Sync issue
    result = service.sync_issue(issue, db_session)

    # Verify error result
    assert result.success is False
    assert result.error is not None
    assert "No synchronizer available" in result.error


def test_sync_all_issues(db_session: Session):
    """Test syncing all issues in database"""
    # Create mock synchronizer
    mock_sync = Mock(spec=BaseIssueSynchronizer)
    mock_sync.can_sync.return_value = True
    mock_sync.sync_issue.return_value = SyncResult(success=True, title_updated=True)

    # Create service
    service = IssueSynchronizationService([mock_sync])

    # Create test issues
    issue1 = Issue(
        source=IssueSource.GITHUB,
        project="test/repo",
        key="1",
        title="Issue 1",
        status=IssueStatus.OPEN,
    )
    issue2 = Issue(
        source=IssueSource.GITHUB,
        project="test/repo",
        key="2",
        title="Issue 2",
        status=IssueStatus.OPEN,
    )
    db_session.add_all([issue1, issue2])
    db_session.commit()

    # Sync all issues
    results = service.sync_all_issues(db_session)

    # Verify results
    assert results.total == 2
    assert results.successful == 2
    assert results.failed == 0
    assert results.updated == 2
    assert results.success_rate == 100.0

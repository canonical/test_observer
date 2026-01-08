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


import logging
from os import environ

from celery import Celery
from sqlalchemy import select

from test_observer.data_access.setup import SessionLocal
from test_observer.data_access.models import Issue
from test_observer.kernel_swm_integration.swm_integrator import (
    update_artefacts_with_tracker_info,
)
from test_observer.kernel_swm_integration.swm_reader import get_artefacts_swm_info
from test_observer.promotion.promoter import promote_artefacts
from test_observer.users.delete_expired_user_sessions import (
    delete_expired_user_sessions,
)
from test_observer.external_apis.github.github_client import GitHubClient
from test_observer.external_apis.jira.jira_client import JiraClient
from test_observer.external_apis.launchpad.launchpad_client import LaunchpadClient
from test_observer.external_apis.synchronizer import IssueSynchronizer

DEVELOPMENT_BROKER_URL = "redis://test-observer-redis"
broker_url = environ.get("CELERY_BROKER_URL", DEVELOPMENT_BROKER_URL)

app = Celery("tasks", broker=broker_url)

logger = logging.getLogger(__name__)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):  # noqa
    # Skip periodic tasks optionally for envs like docker-compose on github
    if environ.get("DISABLE_PERIODIC_TASKS", "false").lower() == "true":
        logger.info("Periodic tasks disabled via DISABLE_PERIODIC_TASKS env vars")
        return

    sender.add_periodic_task(300, integrate_with_kernel_swm.s())
    sender.add_periodic_task(600, run_promote_artefacts.s())
    sender.add_periodic_task(600, clean_user_sessions.s())
    sender.add_periodic_task(3600, sync_all_issues.s())  # Every hour


@app.task
def integrate_with_kernel_swm():
    db = SessionLocal()
    swm_info = get_artefacts_swm_info()
    update_artefacts_with_tracker_info(db, swm_info)


@app.task
def run_promote_artefacts():
    promote_artefacts(SessionLocal())


@app.task
def clean_user_sessions():
    delete_expired_user_sessions(SessionLocal())


@app.task
def sync_all_issues():
    """Synchronize all issues with their remote sources every hour"""
    session = SessionLocal()
    try:
        logger.info("Starting periodic issue synchronization...")

        # Initialize clients with environment variables
        github_client = (
            GitHubClient(token=environ.get("GITHUB_TOKEN"))
            if environ.get("GITHUB_TOKEN")
            else None
        )

        jira_client = None
        if environ.get("JIRA_BASE_URL"):
            jira_client = JiraClient(
                base_url=environ.get("JIRA_BASE_URL"),
                email=environ.get("JIRA_EMAIL"),
                api_token=environ.get("JIRA_API_TOKEN"),
            )

        launchpad_client = LaunchpadClient(
            credentials_file=environ.get("LAUNCHPAD_CREDENTIALS_FILE"),
            anonymous=environ.get("LAUNCHPAD_CREDENTIALS_FILE") is None,
        )

        # Initialize synchronizer
        synchronizer = IssueSynchronizer(
            db=session,
            github_client=github_client,
            jira_client=jira_client,
            launchpad_client=launchpad_client,
        )

        # Sync all issues
        results = synchronizer.sync_all_issues(batch_size=50)

        # Summary statistics
        total = len(results)
        successful = sum(1 for r in results if r.success)
        updated = sum(1 for r in results if r.updated)
        failed = sum(1 for r in results if not r.success)

        logger.info(
            f"Issue synchronization completed: "
            f"total={total}, successful={successful}, updated={updated}, failed={failed}"
        )

    except Exception as e:
        logger.exception(f"Error during issue synchronization: {e}")
    finally:
        session.close()


@app.task
def sync_issue_by_id(issue_id: int):
    """Sync a single issue by ID"""
    session = SessionLocal()
    try:
        logger.info(f"Syncing issue {issue_id}...")

        # Get the issue
        stmt = select(Issue).where(Issue.id == issue_id)
        issue = session.scalar(stmt)

        if not issue:
            logger.warning(f"Issue {issue_id} not found in database")
            return

        # Initialize clients with environment variables
        github_client = (
            GitHubClient(token=environ.get("GITHUB_TOKEN"))
            if environ.get("GITHUB_TOKEN")
            else None
        )

        jira_client = None
        if environ.get("JIRA_BASE_URL"):
            jira_client = JiraClient(
                base_url=environ.get("JIRA_BASE_URL"),
                email=environ.get("JIRA_EMAIL"),
                api_token=environ.get("JIRA_API_TOKEN"),
            )

        launchpad_client = LaunchpadClient(
            credentials_file=environ.get("LAUNCHPAD_CREDENTIALS_FILE"),
            anonymous=environ.get("LAUNCHPAD_CREDENTIALS_FILE") is None,
        )

        # Initialize synchronizer
        synchronizer = IssueSynchronizer(
            db=session,
            github_client=github_client,
            jira_client=jira_client,
            launchpad_client=launchpad_client,
        )

        # Sync the issue
        result = synchronizer.sync_issue(issue)

        if result.success:
            logger.info(
                f"Issue {issue_id} synced successfully. Updated: {result.updated}"
            )
        else:
            logger.warning(f"Failed to sync issue {issue_id}: {result.error}")

    except Exception as e:
        logger.exception(f"Error syncing issue {issue_id}: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    app.start()

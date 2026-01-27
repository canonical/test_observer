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

from celery import Celery, Task

from test_observer.data_access.setup import SessionLocal
from test_observer.external_apis.synchronizers.factory import (
    create_synchronization_service,
)
from test_observer.data_access.models import Issue
from test_observer.kernel_swm_integration.swm_integrator import (
    update_artefacts_with_tracker_info,
)
from test_observer.kernel_swm_integration.swm_reader import get_artefacts_swm_info
from test_observer.promotion.promoter import promote_artefacts
from test_observer.users.delete_expired_user_sessions import (
    delete_expired_user_sessions,
)

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
    sender.add_periodic_task(3600, sync_all_issues.s())


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
def sync_all_issues() -> dict:
    """Sync all issues from external platforms (runs periodically)"""
    db = SessionLocal()
    try:
        service = create_synchronization_service()
        results = service.sync_all_issues(db)

        return {
            "total": results.total,
            "successful": results.successful,
            "failed": results.failed,
            "updated": results.updated,
            "success_rate": results.success_rate,
        }
    except Exception as e:
        logger.error(f"Failed to sync all issues: {e}")
        return {"error": str(e), "total": 0, "successful": 0, "failed": 0}
    finally:
        db.close()


@app.task(bind=True, max_retries=2)
def sync_issue_by_id(self: Task, issue_id: int) -> dict:
    """Manually synchronize a specific issue by ID (called on-demand)"""
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return {"success": False, "error": "Issue not found"}

        service = create_synchronization_service()
        result = service.sync_issue(issue, db)

        return {
            "success": result.success,
            "title_updated": result.title_updated,
            "status_updated": result.status_updated,
            "error": result.error,
        }
    except Exception as e:
        logger.error(f"Failed to sync issue {issue_id}: {e}")
        raise self.retry(exc=e, countdown=60 * (2**self.request.retries)) from e
    finally:
        db.close()


if __name__ == "__main__":
    app.start()

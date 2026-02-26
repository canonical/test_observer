# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import logging
from os import environ

from celery import Celery

from test_observer.data_access.setup import SessionLocal
from test_observer.external_apis.synchronizers.factory import (
    create_synchronization_service,
)
from test_observer.external_apis.synchronizers.sync_strategy import SyncStrategy
from test_observer.data_access.models import Issue
from test_observer.kernel_swm_integration.swm_integrator import (
    update_artefacts_with_tracker_info,
)
from test_observer.kernel_swm_integration.swm_reader import get_artefacts_swm_info
from test_observer.promotion.promoter import promote_artefacts
from test_observer.users.delete_expired_user_sessions import (
    delete_expired_user_sessions,
)
from test_observer.external_apis.synchronizers.config import SyncConfig

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

    # Staggered sync tasks
    if environ.get("ENABLE_ISSUE_SYNC", "false").lower() == "true":
        sender.add_periodic_task(
            SyncConfig.OPEN_ISSUE_INTERVAL, sync_high_priority_issues.s()
        )
        sender.add_periodic_task(
            SyncConfig.RECENT_CLOSED_INTERVAL, sync_medium_priority_issues.s()
        )
        sender.add_periodic_task(
            SyncConfig.OLD_CLOSED_INTERVAL, sync_low_priority_issues.s()
        )


@app.task
def integrate_with_kernel_swm():
    with SessionLocal() as db:
        swm_info = get_artefacts_swm_info()
        # update_artefacts_with_tracker_info calls db.commit()
        update_artefacts_with_tracker_info(db, swm_info)


@app.task
def run_promote_artefacts():
    with SessionLocal() as db:
        # The underlying functions called in promoote_artefacts call db.commit()
        promote_artefacts(db)


@app.task
def clean_user_sessions():
    with SessionLocal() as db:
        # delete_expired_user_sessions calls db.commit()
        delete_expired_user_sessions(db)


@app.task
def sync_high_priority_issues() -> dict:
    """Sync open and unknown issues (high priority)"""
    return _sync_issues_by_priority("high")


@app.task
def sync_medium_priority_issues() -> dict:
    """Sync recently closed issues (medium priority)"""
    return _sync_issues_by_priority("medium")


@app.task
def sync_low_priority_issues() -> dict:
    """Sync old closed issues (low priority)"""
    return _sync_issues_by_priority("low")


def _sync_issues_by_priority(priority: str) -> dict:
    """Sync issues of a given priority in batches"""
    db = SessionLocal()
    try:
        service = create_synchronization_service()

        total_synced = 0
        total_updated = 0
        total_failed = 0
        batch_count = 0

        while True:
            issues = SyncStrategy.get_issues_due_for_sync(
                db, batch_size=SyncConfig.BATCH_SIZE, priority=priority
            )

            if not issues:
                break

            batch_count += 1
            logger.info(
                f"Processing {priority} priority batch "
                f"{batch_count} ({len(issues)} issues)"
            )

            # Sync the batch
            results = service.sync_issues_batch(issues, db)

            total_synced += results.total
            total_updated += results.updated
            total_failed += results.failed

            if len(issues) < SyncConfig.BATCH_SIZE:
                break

        stats = SyncStrategy.get_sync_stats(db)

        return {
            "priority": priority,
            "batches_processed": batch_count,
            "total_synced": total_synced,
            "total_updated": total_updated,
            "total_failed": total_failed,
            "sync_stats": stats,
        }

    except Exception as e:
        logger.error(f"Failed to sync {priority} priority issues: {e}")
        return {"priority": priority, "error": str(e), "total_synced": 0}
    finally:
        db.close()


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

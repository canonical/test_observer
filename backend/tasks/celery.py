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

from test_observer.data_access.setup import SessionLocal
from test_observer.kernel_swm_integration.swm_integrator import (
    update_artefacts_with_tracker_info,
)
from test_observer.kernel_swm_integration.swm_reader import get_artefacts_swm_info
from test_observer.promotion.promoter import promote_artefacts
from test_observer.services.issue_sync_service import IssueSyncService
from test_observer.logging_config import setup_logging

# Setup logging for Celery tasks
setup_logging()

DEVELOPMENT_BROKER_URL = "redis://test-observer-redis"
broker_url = environ.get("CELERY_BROKER_URL", DEVELOPMENT_BROKER_URL)

app = Celery("tasks", broker=broker_url)

logger = logging.getLogger(__name__)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):  # noqa
    sender.add_periodic_task(300, integrate_with_kernel_swm.s())
    sender.add_periodic_task(600, run_promote_artefacts.s())
    # Sync issue statuses every 120 seconds
    sender.add_periodic_task(120, sync_issue_statuses.s())


@app.task
def integrate_with_kernel_swm():
    db = SessionLocal()
    swm_info = get_artefacts_swm_info()
    update_artefacts_with_tracker_info(db, swm_info)


@app.task
def run_promote_artefacts():
    promote_artefacts(SessionLocal())


@app.task
def sync_issue_statuses():
    """Celery task to sync issue statuses from external APIs"""
    db = SessionLocal()
    logger.info("Starting issue sync task")
    try:
        sync_service = IssueSyncService()
        stats = sync_service.sync_all_issues(db)
        logger.info(f"Issue sync completed successfully: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Issue sync task failed: {type(e).__name__}: {e}", exc_info=True)
        raise
    finally:
        db.close()
        logger.debug("Issue sync task finished, database connection closed")


if __name__ == "__main__":
    app.start()

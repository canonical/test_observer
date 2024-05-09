import logging
from os import environ

from celery import Celery

from test_observer.data_access.setup import SessionLocal
from test_observer.kernel_swm_integration.swm_integrator import (
    update_artefacts_with_tracker_info,
)
from test_observer.kernel_swm_integration.swm_reader import get_artefacts_swm_info
from test_observer.promotion.promoter import promote_artefacts

DEVELOPMENT_BROKER_URL = "redis://test-observer-redis"
broker_url = environ.get("CELERY_BROKER_URL", DEVELOPMENT_BROKER_URL)

app = Celery("tasks", broker=broker_url)

logger = logging.getLogger(__name__)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):  # noqa
    sender.add_periodic_task(300, integrate_with_kernel_swm.s())
    sender.add_periodic_task(600, run_promote_artefacts.s())


@app.task
def integrate_with_kernel_swm():
    db = SessionLocal()
    swm_info = get_artefacts_swm_info(db)
    update_artefacts_with_tracker_info(db, swm_info)


@app.task
def run_promote_artefacts():
    promote_artefacts(SessionLocal())


if __name__ == "__main__":
    app.start()

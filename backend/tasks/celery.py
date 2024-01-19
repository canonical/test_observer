from os import environ

from celery import Celery

DEVELOPMENT_BROKER_URL = "redis://test-observer-redis"
broker_url = environ.get("CELERY_BROKER_URL", DEVELOPMENT_BROKER_URL)

app = Celery("tasks", broker=broker_url)

if __name__ == "__main__":
    app.start()

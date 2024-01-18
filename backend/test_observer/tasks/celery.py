from celery import Celery

app = Celery("tasks", broker="redis://test-observer-redis")

if __name__ == "__main__":
    app.start()

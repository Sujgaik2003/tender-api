from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Use Redis as broker and backend
# Default to localhost if not set in env (dev mode)
BROKER_URL = "redis://localhost:6379/0"
BACKEND_URL = "redis://localhost:6379/0"

celery_app = Celery(
    "tender_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=["app.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Rate limits for stability
    task_default_rate_limit="10/s",
)

if __name__ == "__main__":
    celery_app.start()

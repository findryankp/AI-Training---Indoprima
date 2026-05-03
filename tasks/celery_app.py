import os
from celery import Celery

# Mengambil URL Redis dari environment variable atau default ke localhost
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Inisialisasi Celery App
celery_app = Celery(
    "crewai_flow",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.celery_tasks"]  # Memasukkan file task yang akan dibuat
)

# Konfigurasi tambahan Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,       # Maksimal 30 menit
    task_soft_time_limit=25 * 60,  # Warning di 25 menit
    worker_prefetch_multiplier=1,  # Distribusi tugas yang adil
)

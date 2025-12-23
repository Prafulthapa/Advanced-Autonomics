from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Configure task routes
celery_app.conf.task_routes = {
    "generate_and_send_email_task": {"queue": "emails"},
    "send_email_task": {"queue": "emails"},
    "agent_cycle_task": {"queue": "agent"},
    "agent_health_check": {"queue": "agent"},
}

# ============================================
# CELERY BEAT SCHEDULE - AGENT AUTOMATION
# ============================================

celery_app.conf.beat_schedule = {
    # Main agent cycle - runs every 5 minutes
    'agent-cycle': {
        'task': 'agent_cycle_task',
        'schedule': 300.0,  # 5 minutes in seconds
    },

    # Health check - every 1 minute
    'agent-health-check': {
        'task': 'agent_health_check',
        'schedule': 60.0,  # 1 minute
    },
}

celery_app.conf.timezone = 'UTC'

print("✅ Celery app configured with correct task routes")

# CRITICAL: Import tasks module to register all @celery_app.task decorators
# This MUST come after celery_app is configured
from app.worker import tasks  # noqa: F401

print(f"✅ Tasks imported and registered: {len([k for k in celery_app.tasks.keys() if not k.startswith('celery.')])}")
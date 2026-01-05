from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# ============================================
# TASK ROUTES
# ============================================

celery_app.conf.task_routes = {
    "generate_and_send_email_task": {"queue": "emails"},
    "send_email_task": {"queue": "emails"},
    "agent_cycle_task": {"queue": "agent"},
    "agent_health_check": {"queue": "agent"},
    "fetch_and_process_replies": {"queue": "replies"},  # ✅ NEW: IMAP route
}

# ============================================
# CELERY BEAT SCHEDULE
# ============================================

celery_app.conf.beat_schedule = {
    # Main agent cycle - every 5 minutes
    "agent-cycle": {
        "task": "agent_cycle_task",
        "schedule": 300.0,
    },

    # Health check - every 1 minute
    "agent-health-check": {
        "task": "agent_health_check",
        "schedule": 60.0,
    },

    # ✅ NEW: Fetch email replies every 15 minutes
    "fetch-email-replies": {
        "task": "fetch_and_process_replies",
        "schedule": 900.0,  # 15 minutes
    },
}

celery_app.conf.beat_schedule = {
    # Main agent cycle - every 5 minutes
    "agent-cycle": {
        "task": "agent_cycle_task",
        "schedule": 300.0,
    },

    # Health check - every 1 minute
    "agent-health-check": {
        "task": "agent_health_check",
        "schedule": 60.0,
    },

    # Fetch email replies every 15 minutes
    "fetch-email-replies": {
        "task": "fetch_and_process_replies",
        "schedule": 900.0,
    },

    # ✅ NEW: Cleanup old logs - daily at midnight
    "cleanup-old-logs": {
        "task": "cleanup_old_logs",
        "schedule": crontab(hour=0, minute=0),
    },

    # ✅ NEW: Recalculate lead scores - daily at 2 AM
    "recalculate-lead-scores": {
        "task": "recalculate_lead_scores",
        "schedule": crontab(hour=2, minute=0),
    },

    # ✅ NEW: Daily report - every day at 9 AM
    "daily-report": {
        "task": "generate_daily_report",
        "schedule": crontab(hour=9, minute=0),
    },
}

celery_app.conf.timezone = "UTC"

print("✅ Celery app configured with correct task routes")

# ============================================
# 🔴 CRITICAL: TASK REGISTRATION
# ============================================

# Import ALL task modules so Celery registers them
import app.worker.tasks         # noqa: F401
import app.worker.agent_tasks   # 👈 ✅ THE FIX (REQUIRED)
import app.worker.imap_tasks    # ✅ NEW: Register IMAP tasks

print(
    f"✅ Tasks registered: "
    f"{len([k for k in celery_app.tasks.keys() if not k.startswith('celery.')])}"
)
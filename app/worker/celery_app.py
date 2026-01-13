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
# WORKER CONFIGURATION
# ============================================
from app.worker.celery_config import (
    WORKER_CONCURRENCY,
    MAX_TASKS_PER_CHILD,
    TASK_SOFT_TIME_LIMIT,
    TASK_HARD_TIME_LIMIT,
    TASK_ACKS_LATE,
    WORKER_PREFETCH_MULTIPLIER
)

celery_app.conf.update(
    worker_concurrency=WORKER_CONCURRENCY,
    worker_max_tasks_per_child=MAX_TASKS_PER_CHILD,
    task_soft_time_limit=TASK_SOFT_TIME_LIMIT,
    task_time_limit=TASK_HARD_TIME_LIMIT,
    task_acks_late=TASK_ACKS_LATE,
    worker_prefetch_multiplier=WORKER_PREFETCH_MULTIPLIER,
)

# ============================================
# TASK ROUTES
# ============================================

celery_app.conf.task_routes = {
    "generate_and_send_email_task": {"queue": "emails"},
    "send_email_task": {"queue": "emails"},
    "agent_cycle_task": {"queue": "agent"},
    "agent_health_check": {"queue": "agent"},
    "fetch_and_process_replies": {"queue": "replies"},
    "process_scraped_lead": {"queue": "emails"},
    "run_linkedin_scraper": {"queue": "scraper"},
}

# ============================================
# CELERY BEAT SCHEDULE
# ============================================

celery_app.conf.beat_schedule = {
    # MAIN AGENT CYCLE - EVERY 5 MINUTES
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

    # Cleanup old logs - daily at midnight
    "cleanup-old-logs": {
        "task": "cleanup_old_logs",
        "schedule": crontab(hour=0, minute=0),
    },

    # Recalculate lead scores - daily at 2 AM
    "recalculate-lead-scores": {
        "task": "recalculate_lead_scores",
        "schedule": crontab(hour=2, minute=0),
    },

    # Daily report - every day at 9 AM
    "daily-report": {
        "task": "generate_daily_report",
        "schedule": crontab(hour=9, minute=0),
    },

    # Run scraper every 6 hours
    "scrape-new-leads": {
        "task": "run_linkedin_scraper",
        "schedule": crontab(hour="*/6"),
    },
    
        "auto-scrape-leads": {
        "task": "run_automated_lead_pipeline",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
}

celery_app.conf.timezone = "UTC"

print("✅ Celery app configured with correct task routes")
print(f"📅 Beat schedule configured with {len(celery_app.conf.beat_schedule)} tasks")

# ============================================
# ⚠️ IMPORT TASKS AT THE END (AFTER celery_app IS DEFINED)
# ============================================

# This MUST come after celery_app is created
import app.worker.tasks       # noqa: F401
import app.worker.agent_tasks # noqa: F401
import app.worker.imap_tasks  # noqa: F401
import app.worker.lead_tasks  # noqa: F401, E402
import app.worker.scraper_scheduler  # noqa: F401, E402

print(
    f"✅ Tasks registered: "
    f"{len([k for k in celery_app.tasks.keys() if not k.startswith('celery.')])}"
)

if 'agent-cycle' in celery_app.conf.beat_schedule:
    print("✅ VERIFIED: agent-cycle task is scheduled")
else:
    print("❌ WARNING: agent-cycle task NOT in schedule!")
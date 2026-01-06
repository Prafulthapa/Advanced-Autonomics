"""
Celery Worker Configuration
Control concurrency and task execution
"""
import os

# ============================================
# WORKER CONCURRENCY SETTINGS
# ============================================

# Number of concurrent worker processes
WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "1"))

# Max tasks per worker before restart (memory management)
MAX_TASKS_PER_CHILD = int(os.getenv("CELERY_MAX_TASKS_PER_CHILD", "100"))

# Task time limits
TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "300"))  # 5 minutes
TASK_HARD_TIME_LIMIT = int(os.getenv("CELERY_TASK_HARD_TIME_LIMIT", "600"))  # 10 minutes

# Task execution settings
TASK_ACKS_LATE = True  # Only ack after task completes
WORKER_PREFETCH_MULTIPLIER = 1  # Only fetch 1 task at a time per worker

print(f"⚙️ Celery Config:")
print(f"   Concurrency: {WORKER_CONCURRENCY}")
print(f"   Prefetch: {WORKER_PREFETCH_MULTIPLIER}")
print(f"   Task Timeout: {TASK_SOFT_TIME_LIMIT}s")
# Should have something like:
from app.worker import tasks
from app.worker import lead_tasks  # ← This line is critical!
from app.worker import agent_tasks
from app.worker import imap_tasks
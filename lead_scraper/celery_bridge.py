"""
Celery Bridge - Connect scraper to email worker
Pushes scraped leads directly into email queue
"""

from celery import Celery
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to your existing Redis/Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "lead_scraper_bridge",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configure to use your existing queues
celery_app.conf.update(
    task_routes={
        "process_scraped_lead": {"queue": "emails"},
        "enrich_and_queue_lead": {"queue": "emails"}
    }
)


def push_lead_to_email_queue(lead_data):
    """
    Push a scraped lead directly into email processing queue.
    
    Args:
        lead_data: Dict with lead info from LinkedIn
    """
    try:
        # Send to your existing email task
        task = celery_app.send_task(
            "process_scraped_lead",  # This task we'll create in worker
            args=[lead_data],
            queue="emails",
            countdown=5  # Delay 5 seconds to avoid spam
        )
        
        logger.info(f"✅ Queued lead: {lead_data.get('name')} → Task ID: {task.id}")
        return task.id
        
    except Exception as e:
        logger.error(f"❌ Failed to queue lead: {str(e)}")
        return None


def push_leads_batch(leads_list):
    """
    Push multiple leads in batch.
    
    Args:
        leads_list: List of lead dicts
    """
    logger.info(f"📤 Pushing {len(leads_list)} leads to email queue...")
    
    queued_count = 0
    
    for lead in leads_list:
        task_id = push_lead_to_email_queue(lead)
        if task_id:
            queued_count += 1
    
    logger.info(f"✅ Successfully queued {queued_count}/{len(leads_list)} leads")
    return queued_count
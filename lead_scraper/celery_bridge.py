"""
Celery Bridge - Push scraped carpentry leads to email queue
UPDATED for carpentry lead format
"""

from celery import Celery
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "lead_scraper_bridge",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_routes={
        "process_carpentry_lead": {"queue": "emails"},
        "import_carpentry_lead": {"queue": "emails"}
    }
)


def push_lead_to_email_queue(lead_data):
    """
    Push a carpentry lead to email queue.
    
    Args:
        lead_data: Dict with carpentry lead info
            {
                'company_name': str,
                'executive_name': str,
                'email': str,
                'phone': str,
                'website': str,
                'address': str,
                'state': str,
                'source': str
            }
    """
    try:
        # Validate required fields
        if not lead_data.get('email'):
            logger.warning(f"⚠️ Skipping {lead_data.get('company_name')} - no email")
            return None
        
        if '@' not in lead_data.get('email', ''):
            logger.warning(f"⚠️ Skipping {lead_data.get('company_name')} - invalid email")
            return None
        
        # Format for email system
        email_task_data = {
            'email': lead_data.get('email'),
            'company': lead_data.get('company_name'),
            'name': lead_data.get('executive_name', 'Manager'),
            'phone': lead_data.get('phone', ''),
            'website': lead_data.get('website', ''),
            'location': lead_data.get('state', 'Australia'),
            'source': lead_data.get('source', 'Web Scraping'),
            'industry': 'Carpentry/Woodworking'
        }
        
        # Send to email worker
        task = celery_app.send_task(
            "app.worker.tasks.process_new_lead",  # Your existing email task
            args=[email_task_data],
            queue="emails",
            countdown=5
        )
        
        logger.info(f"✅ Queued: {lead_data.get('company_name')} → {task.id}")
        return task.id
        
    except Exception as e:
        logger.error(f"❌ Failed to queue {lead_data.get('company_name')}: {e}")
        return None


def push_leads_batch(leads_list):
    """
    Push multiple carpentry leads in batch.
    
    Args:
        leads_list: List of lead dicts
    
    Returns:
        int: Number of leads successfully queued
    """
    logger.info(f"📤 Pushing {len(leads_list)} carpentry leads to email queue...")
    
    queued_count = 0
    failed_count = 0
    
    for lead in leads_list:
        task_id = push_lead_to_email_queue(lead)
        if task_id:
            queued_count += 1
        else:
            failed_count += 1
    
    logger.info(f"✅ Queued: {queued_count}/{len(leads_list)} leads")
    if failed_count > 0:
        logger.warning(f"⚠️ Failed: {failed_count} leads")
    
    return queued_count
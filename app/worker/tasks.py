from sqlalchemy.orm import Session
from datetime import datetime
import logging
import asyncio
from celery.exceptions import MaxRetriesExceededError

from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.lead import Lead
from app.models.email_log import EmailLog
from app.models.email_queue import EmailQueue
from app.models.agent_config import AgentConfig

from app.services.email_service import EmailService
from app.services.ollama_service import OllamaService

from app.services.email_templates import (
    get_template_for_industry,
    get_subject_for_industry
)

logger = logging.getLogger(__name__)


@celery_app.task(
    name="generate_and_send_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=3600,
    retry_jitter=True
)
def generate_and_send_email_task(self, lead_id: int, queue_id: int = None):
    """
    ✅ FIXED: Proper queue status tracking + NO duplicate counter increments
    """
    db: Session = SessionLocal()
    queue_record = None

    try:
        logger.info(f"🚀 Starting generate+send task for lead_id={lead_id} (attempt {self.request.retries + 1}/4)")

        # ✅ FIX 1: Load and mark as processing IMMEDIATELY
        if queue_id:
            queue_record = db.query(EmailQueue).filter(EmailQueue.id == queue_id).first()
            if queue_record:
                queue_record.status = "processing"
                queue_record.task_id = self.request.id
                queue_record.retry_count = self.request.retries
                db.commit()  # ✅ Commit immediately so UI sees it
                logger.info(f"✅ Queue {queue_id} marked as processing")

        # Fetch lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.error(f"❌ Lead {lead_id} not found")
            if queue_record:
                queue_record.status = "failed"
                queue_record.last_error = "Lead not found"
                queue_record.failed_at = datetime.utcnow()
                db.commit()
            return {"success": False, "error": "Lead not found"}

        # Prepare lead data
        first_name = (
            lead.first_name
            if lead.first_name and lead.first_name not in ["UNKNOWN", "None"]
            else ""
        )
        last_name = (
            lead.last_name
            if lead.last_name and lead.last_name not in ["UNKNOWN", "None"]
            else ""
        )
        company = lead.company or "your company"

        # Generate HTML email
        from app.services.html_email_templates_professional import get_full_professional_template

        html_body, images = get_full_professional_template(
            first_name=first_name,
            company=company,
            email=lead.email,
            lead=lead
        )

        # Generate plain-text fallback using AI
        template = get_template_for_industry(lead.industry)
        prompt = template.format(
            first_name=first_name or "there",
            last_name=last_name,
            company=company,
            email=lead.email
        )

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        plain_text_body = loop.run_until_complete(
            OllamaService.generate_email(prompt)
        )

        # Subject line
        subject = get_subject_for_industry(lead.industry, lead.company)

        # Inject unsubscribe link
        unsubscribe_link = (
            f"http://localhost:8000/unsubscribe?email={lead.email}"
        )
        html_body = html_body.replace(
            "{{{{UNSUBSCRIBE_LINK}}}}",
            unsubscribe_link
        )

        # Send email
        to_name = f"{first_name} {last_name}".strip() or None

        success, error = EmailService.send_email(
            to_email=lead.email,
            subject=subject,
            body=plain_text_body,
            to_name=to_name,
            html_body=html_body,
            images=None
        )

        # Log email
        email_log = EmailLog(
            lead_id=lead_id,
            subject=subject,
            body=plain_text_body,
            status="sent" if success else "failed",
            error_message=error,
            sent_at=datetime.utcnow()
        )
        db.add(email_log)

        # ============================================
        # ✅ FIX: NO COUNTER INCREMENT HERE
        # Counters are incremented in agent_runner.py
        # ============================================
        if success:
            lead.last_email_sent_at = datetime.utcnow()
            lead.status = "contacted" if lead.sequence_step == 0 else "follow_up"
            lead.sequence_step += 1

            if queue_record:
                queue_record.status = "sent"
                queue_record.sent_at = datetime.utcnow()
                logger.info(f"✅ Queue {queue_id} marked as sent")

            # Rate limits are incremented by agent_runner.py when queuing
            logger.info(f"✅ Email sent successfully to {lead.email}")

        else:
            if queue_record:
                queue_record.status = "failed"
                queue_record.last_error = error
                queue_record.failed_at = datetime.utcnow()
                logger.warning(f"❌ Email failed for {lead.email}: {error}")

        db.commit()

        logger.info(
            f"✅ Email task completed for lead_id={lead_id}, success={success}"
        )

        return {
            "success": success,
            "error": error,
            "lead_id": lead_id,
            "email_log_id": email_log.id,
            "email_type": "professional_html",
            "retry_count": self.request.retries,
            "queue_id": queue_id,
            "queue_status": queue_record.status if queue_record else None
        }

    except Exception as e:
        logger.error(
            f"❌ Error in generate_and_send_email_task (attempt {self.request.retries + 1}): {str(e)}",
            exc_info=True
        )

        if queue_record:
            queue_record.status = "failed"  # ✅ Mark as failed
            queue_record.last_error = str(e)
            queue_record.retry_count = self.request.retries + 1
            db.commit()

        db.rollback()

        try:
            retry_delay = 300 * (2 ** self.request.retries)

            logger.warning(
                f"⚠️ Retrying in {retry_delay}s (attempt {self.request.retries + 2}/4)"
            )

            raise self.retry(exc=e, countdown=retry_delay)

        except MaxRetriesExceededError:
            logger.error(f"🚨 Max retries exceeded for lead_id={lead_id}")

            if queue_record:
                queue_record.status = "failed"
                queue_record.last_error = f"Max retries exceeded: {str(e)}"
                queue_record.failed_at = datetime.utcnow()
                db.commit()

            return {"success": False, "error": "Max retries exceeded", "exception": str(e)}

    finally:
        db.close()


@celery_app.task(
    name="send_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=3600,
    retry_jitter=True
)
def send_email_task(
    self,
    lead_id: int,
    subject: str,
    body: str,
    html_body: str = None,
    queue_id: int = None
):
    """
    ✅ FIXED: NO duplicate counter increments + proper queue status tracking
    """
    db: Session = SessionLocal()
    queue_record = None

    try:
        logger.info(f"🚀 Starting email task for lead_id={lead_id} (attempt {self.request.retries + 1}/4)")

        # ✅ FIX: Mark as processing immediately
        if queue_id:
            queue_record = db.query(EmailQueue).filter(EmailQueue.id == queue_id).first()
            if queue_record:
                queue_record.status = "processing"
                queue_record.task_id = self.request.id
                queue_record.retry_count = self.request.retries
                db.commit()  # ✅ Commit so UI sees "processing"
                logger.info(f"✅ Queue {queue_id} marked as processing")

        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.error(f"❌ Lead {lead_id} not found")
            if queue_record:
                queue_record.status = "failed"
                queue_record.last_error = "Lead not found"
                queue_record.failed_at = datetime.utcnow()
                db.commit()
            return {"success": False, "error": "Lead not found"}

        to_name = f"{lead.first_name} {lead.last_name}".strip()
        if not to_name or to_name in ["UNKNOWN None", "None None"]:
            to_name = None

        images = None
        if html_body:
            images = {
                "company_logo": "app/static/images/logo.png"
            }

        success, error = EmailService.send_email(
            to_email=lead.email,
            subject=subject,
            body=body,
            to_name=to_name,
            html_body=html_body,
            images=images
        )

        email_log = EmailLog(
            lead_id=lead_id,
            subject=subject,
            body=body,
            status="sent" if success else "failed",
            error_message=error,
            sent_at=datetime.utcnow()
        )
        db.add(email_log)

        # ✅ NO COUNTER INCREMENT - handled by agent_runner.py
        if success:
            lead.last_email_sent_at = datetime.utcnow()
            lead.status = "contacted"
            lead.sequence_step += 1

            if queue_record:
                queue_record.status = "sent"
                queue_record.sent_at = datetime.utcnow()
                logger.info(f"✅ Queue {queue_id} marked as sent")

            # Rate limits incremented by agent_runner.py
            logger.info(f"✅ Email sent successfully")

        else:
            if queue_record:
                queue_record.status = "failed"
                queue_record.last_error = error
                queue_record.failed_at = datetime.utcnow()
                logger.warning(f"❌ Queue {queue_id} marked as failed: {error}")

        db.commit()

        logger.info(
            f"✅ Email task completed for lead_id={lead_id}, success={success}"
        )

        return {
            "success": success,
            "error": error,
            "lead_id": lead_id,
            "email_log_id": email_log.id,
            "queue_id": queue_id,
            "status": "sent" if success else "failed",
            "retry_count": self.request.retries
        }

    except Exception as e:
        logger.error(
            f"❌ Error in send_email_task: {str(e)}",
            exc_info=True
        )

        if queue_record:
            queue_record.status = "failed"  # ✅ Mark as failed
            queue_record.last_error = str(e)
            queue_record.retry_count = self.request.retries + 1
            db.commit()

        db.rollback()

        try:
            retry_delay = 300 * (2 ** self.request.retries)
            logger.warning(f"⚠️ Retrying in {retry_delay}s")
            raise self.retry(exc=e, countdown=retry_delay)

        except MaxRetriesExceededError:
            logger.error(f"🚨 Max retries exceeded for lead_id={lead_id}")

            if queue_record:
                queue_record.status = "failed"  # ✅ Permanently failed
                queue_record.last_error = f"Max retries exceeded: {str(e)}"
                queue_record.failed_at = datetime.utcnow()
                db.commit()

            return {"success": False, "error": "Max retries exceeded"}

    finally:
        db.close()
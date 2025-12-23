from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json
import asyncio

# CRITICAL FIX: Import the celery_app from celery_app.py instead of creating a new one
from app.worker.celery_app import celery_app

from app.database import SessionLocal
from app.models.lead import Lead
from app.models.email_log import EmailLog
from app.services.email_service import EmailService
from app.services.ollama_service import OllamaService
from app.services.email_templates import get_template_for_industry, get_subject_for_industry

logger = logging.getLogger(__name__)

# NO LONGER CREATE A NEW CELERY APP HERE!
# The celery_app is imported from celery_app.py


@celery_app.task(name="send_email_task")
def send_email_task(lead_id: int, subject: str, body: str):
    """Celery task to send an email asynchronously."""
    db: Session = SessionLocal()

    try:
        logger.info(f"Starting email task for lead_id={lead_id}")

        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return {"success": False, "error": "Lead not found"}

        # Send email
        to_name = f"{lead.first_name} {lead.last_name}".strip()
        if not to_name or to_name == "UNKNOWN None":
            to_name = None

        success, error = EmailService.send_email(
            to_email=lead.email,
            subject=subject,
            body=body,
            to_name=to_name
        )

        # Log email to database
        email_log = EmailLog(
            lead_id=lead_id,
            subject=subject,
            body=body,
            status="sent" if success else "failed",
            error_message=error,
            sent_at=datetime.utcnow()
        )
        db.add(email_log)

        # Update lead
        if success:
            lead.last_email_sent_at = datetime.utcnow()
            lead.status = "contacted"
            lead.sequence_step += 1

        db.commit()

        logger.info(f"Email task completed for lead_id={lead_id}, success={success}")

        return {
            "success": success,
            "error": error,
            "lead_id": lead_id,
            "email_log_id": email_log.id
        }

    except Exception as e:
        logger.error(f"Error in send_email_task: {str(e)}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="generate_and_send_email_task")
def generate_and_send_email_task(lead_id: int):
    """Celery task to generate email with AI using industry templates and send it."""
    db: Session = SessionLocal()

    try:
        logger.info(f"Starting generate+send task for lead_id={lead_id}")

        # Get lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return {"success": False, "error": "Lead not found"}

        # Get industry-specific template
        template = get_template_for_industry(lead.industry)

        # Handle UNKNOWN or missing names
        first_name = lead.first_name if lead.first_name and lead.first_name != "UNKNOWN" else ""
        last_name = lead.last_name if lead.last_name and lead.last_name != "None" else ""

        # Format the template with lead data
        prompt = template.format(
            first_name=first_name or "there",
            last_name=last_name,
            company=lead.company or "your company",
            email=lead.email
        )

        # Generate email with AI
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        email_body = loop.run_until_complete(OllamaService.generate_email(prompt))

        # Get industry-specific subject line
        subject = get_subject_for_industry(lead.industry, lead.company)

        # Send email
        to_name = f"{first_name} {last_name}".strip()
        if not to_name:
            to_name = None

        success, error = EmailService.send_email(
            to_email=lead.email,
            subject=subject,
            body=email_body,
            to_name=to_name
        )

        # Log email
        email_log = EmailLog(
            lead_id=lead_id,
            subject=subject,
            body=email_body,
            status="sent" if success else "failed",
            error_message=error,
            sent_at=datetime.utcnow()
        )
        db.add(email_log)

        # Update lead
        if success:
            lead.last_email_sent_at = datetime.utcnow()
            lead.status = "contacted"
            lead.sequence_step = 1

        db.commit()

        logger.info(f"Generate+send task completed for lead_id={lead_id}, success={success}")

        return {
            "success": success,
            "error": error,
            "lead_id": lead_id,
            "email_log_id": email_log.id,
            "generated_email": email_body
        }

    except Exception as e:
        logger.error(f"Error in generate_and_send_email_task: {str(e)}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}

    finally:
        db.close()


# ============================================
# AGENT AUTOMATION TASKS
# ============================================

@celery_app.task(name="agent_cycle_task")
def agent_cycle_task():
    """
    Main agent cycle - processes leads and sends emails.
    Runs every 5 minutes via Celery Beat.
    """
    from app.models.agent_config import AgentConfig
    from app.models.agent_action_log import AgentActionLog

    db = SessionLocal()
    try:
        logger.info("🤖 Starting agent cycle...")

        # Get agent config
        config = db.query(AgentConfig).first()
        if not config:
            logger.error("❌ No agent config found")
            return {"status": "error", "message": "No agent config"}

        # Check if agent is running
        if not config.is_running:
            logger.info("⏸️ Agent is not running")
            return {"status": "skipped", "message": "Agent not running"}

        if config.is_paused:
            logger.info("⏸️ Agent is paused")
            return {"status": "skipped", "message": "Agent paused"}

        # Log cycle start
        action_log = AgentActionLog(
            action_type="cycle_start",
            action_result="started",
            decision_reason="Agent cycle initiated",
            agent_run_id="cycle",
            emails_sent_before=config.emails_sent_today
        )
        db.add(action_log)
        db.commit()

        # Get leads that need contact (new or interested)
        leads_to_contact = db.query(Lead).filter(
            Lead.status.in_(['new', 'replied', 'interested'])
        ).limit(10).all()

        queued = 0
        errors = 0

        for lead in leads_to_contact:
            try:
                # Check rate limits
                if config.emails_sent_this_hour >= config.hourly_email_limit:
                    logger.info(f"⏸️ Hourly limit reached: {config.emails_sent_this_hour}/{config.hourly_email_limit}")
                    break

                if config.emails_sent_today >= config.daily_email_limit:
                    logger.info(f"⏸️ Daily limit reached: {config.emails_sent_today}/{config.daily_email_limit}")
                    break

                # Queue email task
                logger.info(f"📧 Queuing email for lead {lead.id}: {lead.email}")
                generate_and_send_email_task.delay(lead.id)
                queued += 1

            except Exception as e:
                logger.error(f"❌ Error queuing lead {lead.id}: {e}")
                errors += 1

        # Update agent status
        config.last_agent_run_at = datetime.utcnow()
        db.commit()

        # Log cycle complete
        result = {
            "status": "success",
            "queued": queued,
            "errors": errors,
            "skipped": len(leads_to_contact) - queued - errors
        }

        action_log = AgentActionLog(
            action_type="cycle_complete",
            action_result="success",
            decision_reason=f"Cycle completed: {queued} emails queued",
            action_metadata=json.dumps(result),
            agent_run_id="cycle",
            emails_sent_before=config.emails_sent_today
        )
        db.add(action_log)
        db.commit()

        logger.info(f"✅ Agent cycle complete: {result}")
        return result

    except Exception as e:
        error_msg = f"Agent cycle error: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)

        # Log error
        try:
            action_log = AgentActionLog(
                action_type="cycle_error",
                action_result="error",
                error_message=error_msg,
                agent_run_id="cycle",
                emails_sent_before=0
            )
            db.add(action_log)
            db.commit()
        except:
            pass

        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="agent_health_check")
def agent_health_check():
    """
    Health check task - monitors agent status.
    Runs every minute via Celery Beat.
    """
    from app.models.agent_config import AgentConfig

    db = SessionLocal()
    try:
        config = db.query(AgentConfig).first()
        if not config:
            return {"status": "error", "message": "No config"}

        # Reset hourly counter if needed
        now = datetime.utcnow()
        if config.last_hour_reset:
            hours_diff = (now - config.last_hour_reset).total_seconds() / 3600
            if hours_diff >= 1:
                logger.info(f"🔄 Resetting hourly counter (was {config.emails_sent_this_hour})")
                config.emails_sent_this_hour = 0
                config.last_hour_reset = now
                db.commit()

        # Reset daily counter if needed
        if config.last_reset_date:
            try:
                last_reset = datetime.strptime(config.last_reset_date, "%Y-%m-%d").date()
                if now.date() > last_reset:
                    logger.info(f"🔄 Resetting daily counter (was {config.emails_sent_today})")
                    config.emails_sent_today = 0
                    config.last_reset_date = now.strftime("%Y-%m-%d")
                    db.commit()
            except:
                pass

        health_status = {
            "status": "healthy",
            "is_running": config.is_running,
            "is_paused": config.is_paused,
            "emails_sent_today": config.emails_sent_today,
            "emails_sent_this_hour": config.emails_sent_this_hour,
            "daily_limit": config.daily_email_limit,
            "hourly_limit": config.hourly_email_limit,
        }

        logger.info(f"💓 Health check: {health_status}")
        return health_status

    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


logger.info("✅ All Celery tasks registered with main celery_app")
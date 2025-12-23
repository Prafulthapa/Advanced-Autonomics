from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import asyncio

from app.database import SessionLocal
from app.models.lead import Lead
from app.models.email_reply import EmailReply
from app.services.imap_service import IMAPService
from app.services.reply_matcher import ReplyMatcher
from app.services.ollama_service import OllamaService
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="fetch_and_process_replies")
def fetch_and_process_replies():
    """
    Celery task to:
    1. Fetch unread emails via IMAP
    2. Match them to leads
    3. Classify with AI
    4. Update lead status
    """
    db: Session = SessionLocal()

    try:
        logger.info("Starting IMAP fetch and process task")

        # Fetch unread emails
        emails = IMAPService.fetch_unread_emails(limit=50)
        logger.info(f"Fetched {len(emails)} unread emails")

        if not emails:
            logger.info("No new emails to process")
            return {"processed": 0, "matched": 0, "classified": 0}

        processed_count = 0
        matched_count = 0
        classified_count = 0

        for email_data in emails:
            try:
                from_email = email_data.get("from_email")
                subject = email_data.get("subject", "")
                body = email_data.get("body", "")

                logger.info(f"Processing email from {from_email}")

                # Skip out-of-office and bounce messages
                if ReplyMatcher.is_out_of_office(body, subject):
                    logger.info("Skipping out-of-office message")
                    continue

                if ReplyMatcher.is_bounce(body, subject, from_email):
                    logger.info("Skipping bounce message")
                    continue

                # Try to match to a lead
                lead_id = ReplyMatcher.match_reply_to_lead(db, email_data)
                matched = lead_id is not None

                if matched:
                    matched_count += 1

                # Classify reply with AI
                classification = None
                classification_confidence = None
                classification_reason = None

                if body and len(body) > 10:
                    try:
                        # Run async classification
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        classification_result = loop.run_until_complete(
                            OllamaService.classify_reply(body)
                        )
                        loop.close()

                        # Parse classification (simple version)
                        classification = classification_result.strip().lower()

                        # Normalize classification
                        if "interest" in classification and "not" not in classification:
                            classification = "interested"
                        elif "not" in classification or "no" in classification:
                            classification = "not_interested"
                        elif "unsubscribe" in classification or "remove" in classification:
                            classification = "unsubscribe"
                        else:
                            classification = "unclear"

                        classified_count += 1
                        logger.info(f"Classified as: {classification}")

                    except Exception as e:
                        logger.error(f"Classification failed: {str(e)}")
                        classification = "unclear"

                # Store email reply in database
                email_reply = EmailReply(
                    lead_id=lead_id,
                    from_email=from_email,
                    to_email=email_data.get("to_email"),
                    subject=subject,
                    body=body,
                    message_id=email_data.get("message_id"),
                    in_reply_to=email_data.get("in_reply_to"),
                    references=email_data.get("references"),
                    classification=classification,
                    classification_confidence=classification_confidence,
                    classification_reason=classification_reason,
                    processed=True,
                    matched=matched,
                    received_at=email_data.get("received_at"),
                    processed_at=datetime.utcnow(),
                    raw_headers=email_data.get("raw_headers")
                )
                db.add(email_reply)

                # Update lead if matched
                if lead_id and classification:
                    lead = db.query(Lead).filter(Lead.id == lead_id).first()
                    if lead:
                        lead.replied = "yes"
                        lead.reply_received_at = datetime.utcnow()

                        # Update status based on classification
                        if classification == "interested":
                            lead.status = "interested"
                        elif classification == "not_interested":
                            lead.status = "not_interested"
                        elif classification == "unsubscribe":
                            lead.status = "unsubscribed"
                        else:
                            lead.status = "replied"

                        logger.info(f"Updated lead {lead_id} status to {lead.status}")

                processed_count += 1
                db.commit()

            except Exception as e:
                logger.error(f"Error processing individual email: {str(e)}", exc_info=True)
                db.rollback()
                continue

        logger.info(f"IMAP task completed: {processed_count} processed, {matched_count} matched, {classified_count} classified")

        return {
            "success": True,
            "processed": processed_count,
            "matched": matched_count,
            "classified": classified_count
        }

    except Exception as e:
        logger.error(f"Error in fetch_and_process_replies: {str(e)}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}

    finally:
        db.close()
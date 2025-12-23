from sqlalchemy.orm import Session
from typing import Optional, Dict
import logging

from app.models.lead import Lead
from app.models.email_log import EmailLog

logger = logging.getLogger(__name__)


class ReplyMatcher:
    """Service for matching inbound email replies to leads."""

    @staticmethod
    def match_reply_to_lead(db: Session, email_data: Dict) -> Optional[int]:
        """Match an inbound email reply to a lead."""
        from_email = email_data.get("from_email", "").lower().strip()

        logger.info(f"Attempting to match reply from {from_email}")

        # Direct email match (most reliable)
        lead = db.query(Lead).filter(
            Lead.email == from_email,
            Lead.status.in_(["contacted", "replied", "interested", "not_interested"])
        ).first()

        if lead:
            logger.info(f"✓ Matched via email address to lead {lead.id}")
            return lead.id

        logger.warning(f"✗ Could not match reply from {from_email}")
        return None

    @staticmethod
    def is_out_of_office(body: str, subject: str) -> bool:
        """Detect out-of-office messages."""
        body_lower = body.lower()
        subject_lower = subject.lower()

        ooo_keywords = [
            "out of office",
            "automatic reply",
            "auto-reply",
            "away from my desk",
            "on vacation",
        ]

        for keyword in ooo_keywords:
            if keyword in body_lower or keyword in subject_lower:
                return True

        return False

    @staticmethod
    def is_bounce(body: str, subject: str, from_email: str) -> bool:
        """Detect bounce messages."""
        body_lower = body.lower()
        from_lower = from_email.lower()

        if "mailer-daemon" in from_lower or "postmaster" in from_lower:
            return True

        bounce_indicators = ["delivery failed", "undelivered", "user unknown"]

        for indicator in bounce_indicators:
            if indicator in body_lower:
                return True

        return False
"""
Rate limiting logic for agent safety
"""

from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session

from app.models.agent_config import AgentConfig
from app.utils.time_utils import TimeUtils


class RateLimiter:
    """Enforce rate limits to prevent spam."""
    
    @staticmethod
    def check_daily_limit(db: Session) -> Tuple[bool, str]:
        """
        Check if daily email limit has been reached.
        
        Returns:
            (allowed: bool, reason: str)
        """
        config = db.query(AgentConfig).first()
        if not config:
            return False, "Agent config not found"
        
        # Reset daily counter if new day
        current_date = TimeUtils.get_current_date_str()
        if config.last_reset_date != current_date:
            config.emails_sent_today = 0
            config.last_reset_date = current_date
            db.commit()
        
        # Check limit
        if config.emails_sent_today >= config.daily_email_limit:
            return False, f"Daily limit reached ({config.daily_email_limit})"
        
        return True, f"OK ({config.emails_sent_today}/{config.daily_email_limit})"
    
    @staticmethod
    def check_hourly_limit(db: Session) -> Tuple[bool, str]:
        """
        Check if hourly email limit has been reached.
        
        Returns:
            (allowed: bool, reason: str)
        """
        config = db.query(AgentConfig).first()
        if not config:
            return False, "Agent config not found"
        
        # Reset hourly counter if new hour
        now = datetime.utcnow()
        if config.last_hour_reset is None or \
           (now - config.last_hour_reset) >= timedelta(hours=1):
            config.emails_sent_this_hour = 0
            config.last_hour_reset = now
            db.commit()
        
        # Check limit
        if config.emails_sent_this_hour >= config.hourly_email_limit:
            return False, f"Hourly limit reached ({config.hourly_email_limit})"
        
        return True, f"OK ({config.emails_sent_this_hour}/{config.hourly_email_limit})"
    
    @staticmethod
    def increment_counters(db: Session):
        """Increment email sent counters after successful send."""
        config = db.query(AgentConfig).first()
        if config:
            config.emails_sent_today += 1
            config.emails_sent_this_hour += 1
            config.total_emails_sent += 1
            db.commit()
    
    @staticmethod
    def can_send_email(db: Session) -> Tuple[bool, str]:
        """
        Master check: Can we send an email right now?
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Check daily limit
        daily_ok, daily_reason = RateLimiter.check_daily_limit(db)
        if not daily_ok:
            return False, daily_reason
        
        # Check hourly limit
        hourly_ok, hourly_reason = RateLimiter.check_hourly_limit(db)
        if not hourly_ok:
            return False, hourly_reason
        
        return True, "All limits OK"
    
    @staticmethod
    def get_remaining_capacity(db: Session) -> dict:
        """Get current rate limit status."""
        config = db.query(AgentConfig).first()
        if not config:
            return {"error": "Config not found"}
        
        return {
            "daily": {
                "sent": config.emails_sent_today,
                "limit": config.daily_email_limit,
                "remaining": config.daily_email_limit - config.emails_sent_today
            },
            "hourly": {
                "sent": config.emails_sent_this_hour,
                "limit": config.hourly_email_limit,
                "remaining": config.hourly_email_limit - config.emails_sent_this_hour
            }
        }
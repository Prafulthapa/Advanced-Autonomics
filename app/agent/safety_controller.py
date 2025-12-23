"""
Safety controls for agent operations
"""

from sqlalchemy.orm import Session
from typing import Tuple
import logging

from app.models.lead import Lead
from app.models.agent_config import AgentConfig
from app.utils.rate_limiter import RateLimiter
from app.utils.time_utils import TimeUtils
from app.config import agent_config

logger = logging.getLogger(__name__)


class SafetyController:
    """Enforce safety rules before agent takes actions."""
    
    @staticmethod
    def can_contact_lead(lead: Lead, db: Session) -> Tuple[bool, str]:
        """
        Check if it's safe to contact this lead.
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Check 1: Lead must be enabled for agent
        if not lead.agent_enabled:
            return False, "Lead has agent disabled"
        
        # Check 2: Lead must not be paused
        if lead.agent_paused:
            return False, "Lead is manually paused"
        
        # Check 3: Check status
        blocked_statuses = ['unsubscribed', 'bounced', 'replied', 'interested', 'not_interested']
        if lead.status in blocked_statuses:
            return False, f"Lead status is '{lead.status}'"
        
        # Check 4: Max follow-ups reached?
        if lead.follow_up_count >= lead.max_follow_ups:
            return False, f"Max follow-ups reached ({lead.max_follow_ups})"
        
        # Check 5: Too many errors?
        if lead.error_count >= 3:
            return False, f"Too many errors ({lead.error_count})"
        
        # Check 6: Too many bounces?
        if lead.bounce_count >= 2:
            return False, "Lead email bounced multiple times"
        
        # Check 7: Is it time to contact?
        if lead.next_agent_check_at and not TimeUtils.is_ready_for_action(lead.next_agent_check_at):
            return False, "Not yet time to contact"
        
        return True, "Lead is eligible"
    
    @staticmethod
    def can_send_now(db: Session) -> Tuple[bool, str]:
        """
        Check if agent can send emails right now.
        
        Returns:
            (allowed: bool, reason: str)
        """
        config = db.query(AgentConfig).first()
        if not config:
            return False, "Agent config not found"
        
        # Check 1: Agent must be running
        if not config.is_running:
            return False, "Agent is not running"
        
        # Check 2: Agent must not be paused
        if config.is_paused:
            return False, "Agent is paused"
        
        # Check 3: Business hours
        if config.respect_business_hours:
            if not TimeUtils.is_business_hours(
                timezone_str=config.timezone,
                start_time=config.business_hours_start,
                end_time=config.business_hours_end,
                active_days=agent_config.get('timing.active_days', [1, 2, 3, 4, 5])
            ):
                return False, "Outside business hours"
        
        # Check 4: Rate limits
        rate_ok, rate_reason = RateLimiter.can_send_email(db)
        if not rate_ok:
            return False, rate_reason
        
        return True, "Safe to send"
    
    @staticmethod
    def check_error_rate(db: Session) -> Tuple[bool, float]:
        """
        Check if error rate is too high.
        
        Returns:
            (safe: bool, error_rate: float)
        """
        config = db.query(AgentConfig).first()
        if not config:
            return False, 0.0
        
        if config.total_emails_sent == 0:
            return True, 0.0
        
        error_rate = (config.total_errors / config.total_emails_sent) * 100
        
        if config.pause_on_high_error_rate:
            if error_rate > config.error_rate_threshold:
                return False, error_rate
        
        return True, error_rate
    
    @staticmethod
    def emergency_stop(db: Session, reason: str):
        """Emergency stop agent operations."""
        logger.critical(f"🚨 EMERGENCY STOP: {reason}")
        
        config = db.query(AgentConfig).first()
        if config:
            config.is_running = False
            config.is_paused = True
            db.commit()
            
        logger.critical("🛑 Agent has been stopped")
    
    @staticmethod
    def validate_lead_email(email: str) -> Tuple[bool, str]:
        """Basic email validation."""
        if not email or '@' not in email:
            return False, "Invalid email format"
        
        # Check for common test/invalid domains
        blocked_domains = ['example.com', 'test.com', 'localhost']
        domain = email.split('@')[1].lower()
        
        if domain in blocked_domains:
            return False, f"Blocked domain: {domain}"
        
        return True, "Email valid"
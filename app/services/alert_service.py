"""
Alert System
Send notifications when critical issues occur
"""

import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.models.agent_config import AgentConfig

logger = logging.getLogger(__name__)


class AlertLevel:
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertService:
    """Send alerts for critical system events."""
    
    @staticmethod
    def send_alert(
        level: str,
        title: str,
        message: str,
        notify_email: str = None
    ):
        """
        Send alert notification.
        
        Args:
            level: AlertLevel (info, warning, critical)
            title: Alert title
            message: Alert message
            notify_email: Email to notify (optional)
        """
        
        # Log alert
        log_func = logger.info if level == AlertLevel.INFO else \
                   logger.warning if level == AlertLevel.WARNING else \
                   logger.critical
        
        log_func(f"[{level.upper()}] {title}: {message}")
        
        # TODO: Send email notification if notify_email provided
        # TODO: Send Slack notification
        # TODO: Send SMS via Twilio
        
        # For now, just log
        if notify_email:
            logger.info(f"Would notify {notify_email}: {title}")
    
    @staticmethod
    def check_and_alert(db: Session):
        """Check system health and send alerts if needed."""
        
        config = db.query(AgentConfig).first()
        if not config:
            return
        
        # Alert 1: High error rate
        if config.total_emails_sent > 20:
            error_rate = (config.total_errors / config.total_emails_sent) * 100
            if error_rate > 15:
                AlertService.send_alert(
                    AlertLevel.CRITICAL,
                    "High Error Rate",
                    f"Email error rate is {error_rate:.1f}% (threshold: 15%)"
                )
        
        # Alert 2: Agent stopped unexpectedly
        if config.is_running:
            time_since_run = (datetime.utcnow() - config.last_agent_run_at).total_seconds() / 60
            if time_since_run > 30:
                AlertService.send_alert(
                    AlertLevel.WARNING,
                    "Agent Inactive",
                    f"Agent hasn't run in {time_since_run:.0f} minutes"
                )
        
        # Alert 3: Rate limit approaching
        daily_pct = (config.emails_sent_today / config.daily_email_limit) * 100
        if daily_pct > 90:
            AlertService.send_alert(
                AlertLevel.WARNING,
                "Daily Limit Approaching",
                f"Used {daily_pct:.0f}% of daily email limit"
            )
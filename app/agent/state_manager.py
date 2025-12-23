"""
Lead state machine and transitions
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.lead import Lead
from app.utils.time_utils import TimeUtils

logger = logging.getLogger(__name__)


class LeadState:
    """Lead status constants."""
    NEW = "new"
    CONTACTED = "contacted"
    FOLLOW_UP = "follow_up"
    REPLIED = "replied"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    PAUSED = "paused"
    CLOSED = "closed"


class StateManager:
    """Manage lead state transitions."""
    
    @staticmethod
    def transition_to_contacted(lead: Lead, db: Session):
        """Move lead to 'contacted' state after first email."""
        lead.status = LeadState.CONTACTED
        lead.sequence_step = 1
        lead.follow_up_count += 1
        lead.last_email_sent_at = datetime.utcnow()
        lead.last_agent_action_at = datetime.utcnow()
        
        # Schedule next follow-up
        next_check = TimeUtils.calculate_next_followup(
            lead.last_email_sent_at,
            lead.days_between_followups
        )
        lead.next_agent_check_at = next_check
        
        db.commit()
        logger.info(f"Lead {lead.id} transitioned to CONTACTED, next check: {next_check}")
    
    @staticmethod
    def transition_to_follow_up(lead: Lead, db: Session):
        """Move lead to follow-up state."""
        lead.status = LeadState.FOLLOW_UP
        lead.sequence_step += 1
        lead.follow_up_count += 1
        lead.last_email_sent_at = datetime.utcnow()
        lead.last_agent_action_at = datetime.utcnow()
        
        # Schedule next check
        next_check = TimeUtils.calculate_next_followup(
            lead.last_email_sent_at,
            lead.days_between_followups
        )
        lead.next_agent_check_at = next_check
        
        db.commit()
        logger.info(f"Lead {lead.id} moved to follow-up #{lead.sequence_step}")
    
    @staticmethod
    def transition_to_replied(lead: Lead, db: Session):
        """Mark lead as replied."""
        lead.status = LeadState.REPLIED
        lead.replied = "yes"
        lead.reply_received_at = datetime.utcnow()
        lead.agent_enabled = False  # Stop agent from contacting
        lead.next_agent_check_at = None
        
        db.commit()
        logger.info(f"Lead {lead.id} replied - agent disabled")
    
    @staticmethod
    def transition_to_interested(lead: Lead, db: Session):
        """Mark lead as interested."""
        lead.status = LeadState.INTERESTED
        lead.replied = "yes"
        lead.priority_score = 10.0  # Highest priority
        lead.agent_enabled = False  # Human takes over
        lead.next_agent_check_at = None
        
        db.commit()
        logger.info(f"Lead {lead.id} marked INTERESTED")
    
    @staticmethod
    def transition_to_not_interested(lead: Lead, db: Session):
        """Mark lead as not interested."""
        lead.status = LeadState.NOT_INTERESTED
        lead.replied = "yes"
        lead.agent_enabled = False
        lead.next_agent_check_at = None
        
        db.commit()
        logger.info(f"Lead {lead.id} marked NOT INTERESTED")
    
    @staticmethod
    def transition_to_unsubscribed(lead: Lead, db: Session):
        """Mark lead as unsubscribed."""
        lead.status = LeadState.UNSUBSCRIBED
        lead.agent_enabled = False
        lead.agent_paused = True
        lead.next_agent_check_at = None
        
        db.commit()
        logger.info(f"Lead {lead.id} UNSUBSCRIBED")
    
    @staticmethod
    def transition_to_bounced(lead: Lead, db: Session):
        """Mark lead email as bounced."""
        lead.bounce_count += 1
        
        if lead.bounce_count >= 2:
            lead.status = LeadState.BOUNCED
            lead.agent_enabled = False
            lead.next_agent_check_at = None
            logger.warning(f"Lead {lead.id} BOUNCED after {lead.bounce_count} attempts")
        else:
            # Retry later
            lead.next_agent_check_at = datetime.utcnow() + timedelta(days=1)
            logger.warning(f"Lead {lead.id} bounced (attempt {lead.bounce_count}), will retry")
        
        db.commit()
    
    @staticmethod
    def handle_error(lead: Lead, error_message: str, db: Session):
        """Handle error during lead processing."""
        lead.error_count += 1
        lead.last_error_message = error_message
        lead.last_agent_action_at = datetime.utcnow()
        
        if lead.error_count >= 3:
            lead.agent_enabled = False
            lead.next_agent_check_at = None
            logger.error(f"Lead {lead.id} disabled after {lead.error_count} errors")
        else:
            # Retry in 1 hour
            lead.next_agent_check_at = datetime.utcnow() + timedelta(hours=1)
            logger.warning(f"Lead {lead.id} error #{lead.error_count}, will retry")
        
        db.commit()
    
    @staticmethod
    def pause_lead(lead: Lead, db: Session):
        """Manually pause a lead."""
        lead.agent_paused = True
        lead.agent_notes = f"Paused manually at {datetime.utcnow()}"
        db.commit()
        logger.info(f"Lead {lead.id} paused manually")
    
    @staticmethod
    def resume_lead(lead: Lead, db: Session):
        """Resume a paused lead."""
        lead.agent_paused = False
        lead.next_agent_check_at = datetime.utcnow()  # Check immediately
        lead.agent_notes = f"Resumed manually at {datetime.utcnow()}"
        db.commit()
        logger.info(f"Lead {lead.id} resumed")
    
    @staticmethod
    def close_lead(lead: Lead, reason: str, db: Session):
        """Close a lead (stop all contact)."""
        lead.status = LeadState.CLOSED
        lead.agent_enabled = False
        lead.next_agent_check_at = None
        lead.agent_notes = f"Closed: {reason}"
        db.commit()
        logger.info(f"Lead {lead.id} closed: {reason}")
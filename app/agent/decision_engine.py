"""
AI Agent Decision Making Engine
Decides what actions to take on each lead
"""

from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from datetime import datetime
import logging

from app.models.lead import Lead
from app.agent.safety_controller import SafetyController
from app.utils.time_utils import TimeUtils

logger = logging.getLogger(__name__)


class DecisionType:
    """Types of decisions agent can make."""
    SEND_INITIAL = "send_initial_email"
    SEND_FOLLOWUP = "send_followup_email"
    SKIP = "skip"
    WAIT = "wait"
    PAUSE = "pause"
    CLOSE = "close"


class Decision:
    """Represents an agent decision."""
    
    def __init__(self, lead: Lead, action: str, reason: str, priority: float = 5.0):
        self.lead = lead
        self.action = action
        self.reason = reason
        self.priority = priority
        self.timestamp = datetime.utcnow()
    
    def __repr__(self):
        return f"Decision(lead={self.lead.id}, action={self.action}, priority={self.priority})"


class DecisionEngine:
    """Makes intelligent decisions about lead actions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_lead(self, lead: Lead) -> Decision:
        """
        Evaluate a single lead and decide what to do.
        
        Returns:
            Decision object with action and reason
        """
        # Safety check first
        can_contact, safety_reason = SafetyController.can_contact_lead(lead, self.db)
        
        if not can_contact:
            return Decision(
                lead=lead,
                action=DecisionType.SKIP,
                reason=safety_reason,
                priority=0.0
            )
        
        # Determine action based on lead state
        if lead.status == "new" and lead.sequence_step == 0:
            # New lead - send initial email
            return Decision(
                lead=lead,
                action=DecisionType.SEND_INITIAL,
                reason="New lead ready for initial contact",
                priority=self._calculate_priority(lead)
            )
        
        elif lead.status in ["contacted", "follow_up"]:
            # Check if it's time for follow-up
            if lead.next_agent_check_at and TimeUtils.is_ready_for_action(lead.next_agent_check_at):
                # Check if we haven't exceeded max follow-ups
                if lead.follow_up_count < lead.max_follow_ups:
                    return Decision(
                        lead=lead,
                        action=DecisionType.SEND_FOLLOWUP,
                        reason=f"Follow-up #{lead.follow_up_count + 1} due",
                        priority=self._calculate_priority(lead)
                    )
                else:
                    return Decision(
                        lead=lead,
                        action=DecisionType.CLOSE,
                        reason="Max follow-ups reached, no response",
                        priority=1.0
                    )
            else:
                return Decision(
                    lead=lead,
                    action=DecisionType.WAIT,
                    reason="Not yet time for next contact",
                    priority=0.0
                )
        
        else:
            # Unknown or invalid state
            return Decision(
                lead=lead,
                action=DecisionType.SKIP,
                reason=f"Lead in non-actionable state: {lead.status}",
                priority=0.0
            )
    
    def _calculate_priority(self, lead: Lead) -> float:
        """
        Calculate priority score for a lead (1-10).
        Higher = more urgent.
        """
        score = lead.priority_score  # Start with existing score
        
        # Boost for new leads
        if lead.status == "new":
            score += 2.0
        
        # Boost for higher sequence steps (follow-ups are important)
        score += (lead.sequence_step * 0.5)
        
        # Penalty for errors
        score -= (lead.error_count * 1.0)
        
        # Clamp between 1-10
        return max(1.0, min(10.0, score))
    
    def get_actionable_leads(self, limit: int = 100) -> List[Lead]:
        """
        Get all leads that might need action.
        
        Returns:
            List of leads to evaluate
        """
        return self.db.query(Lead).filter(
            Lead.agent_enabled == True,
            Lead.agent_paused == False,
            Lead.status.in_(["new", "contacted", "follow_up"])
        ).order_by(
            Lead.priority_score.desc(),
            Lead.next_agent_check_at.asc()
        ).limit(limit).all()
    
    def make_decisions(self, max_actions: int = 50) -> List[Decision]:
        """
        Evaluate all leads and return list of decisions.
        
        Args:
            max_actions: Maximum number of actions to recommend
        
        Returns:
            List of Decision objects, sorted by priority
        """
        logger.info("🧠 Decision engine starting evaluation...")
        
        # Get leads to evaluate
        leads = self.get_actionable_leads(limit=200)
        logger.info(f"Found {len(leads)} leads to evaluate")
        
        # Evaluate each lead
        decisions = []
        for lead in leads:
            decision = self.evaluate_lead(lead)
            decisions.append(decision)
        
        # Filter to actionable decisions
        actionable = [
            d for d in decisions 
            if d.action in [DecisionType.SEND_INITIAL, DecisionType.SEND_FOLLOWUP]
        ]
        
        # Sort by priority (highest first)
        actionable.sort(key=lambda d: d.priority, reverse=True)
        
        # Limit to max_actions
        final_decisions = actionable[:max_actions]
        
        logger.info(f"📊 Decision summary:")
        logger.info(f"  - Total evaluated: {len(decisions)}")
        logger.info(f"  - Actionable: {len(actionable)}")
        logger.info(f"  - Recommended: {len(final_decisions)}")
        
        return final_decisions
    
    def explain_decision(self, decision: Decision) -> str:
        """Generate human-readable explanation of decision."""
        lead = decision.lead
        
        explanation = f"""
Decision for Lead #{lead.id} ({lead.email}):
  Action: {decision.action}
  Reason: {decision.reason}
  Priority: {decision.priority}/10
  Status: {lead.status}
  Sequence Step: {lead.sequence_step}
  Follow-ups: {lead.follow_up_count}/{lead.max_follow_ups}
  Last Contact: {lead.last_email_sent_at or 'Never'}
  Next Check: {lead.next_agent_check_at or 'Not scheduled'}
"""
        return explanation.strip()
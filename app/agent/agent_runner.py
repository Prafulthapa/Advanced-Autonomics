"""
Main AI Agent Runner - WOOD ONLY VERSION
Template override logic completely removed
"""

from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
import time

from app.database import SessionLocal
from app.models.agent_config import AgentConfig
from app.models.agent_action_log import AgentActionLog
from app.models.email_queue import EmailQueue
from app.agent.decision_engine import DecisionEngine, DecisionType
from app.agent.safety_controller import SafetyController
from app.agent.state_manager import StateManager
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class AgentRunner:
    """Main autonomous agent controller - WOOD ONLY"""

    def __init__(self):
        self.run_id = str(uuid.uuid4())[:8]
        self.db: Session = SessionLocal()
        self.decision_engine = DecisionEngine(self.db)

        logger.info(f"🤖 Agent initialized [run_id: {self.run_id}] - WOOD ONLY MODE")

    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'db'):
            self.db.close()

    def is_agent_enabled(self) -> bool:
        """Check if agent should be running."""
        config = self.db.query(AgentConfig).first()
        if not config:
            logger.error("❌ Agent config not found")
            return False

        return config.is_running and not config.is_paused

    def run_cycle(self) -> dict:
        """
        Run one complete agent cycle - WOOD ONLY.
        
        🔥 REMOVED: template_override parameter - always wood now
        """
        start_time = time.time()
        self.run_id = str(uuid.uuid4())[:8]

        logger.info(f"🚀 Agent cycle starting [run_id: {self.run_id}] - WOOD ONLY")

        results = {
            "run_id": self.run_id,
            "started_at": datetime.utcnow().isoformat(),
            "template": "wood",  # Always wood
            "decisions_made": 0,
            "emails_queued": 0,
            "leads_skipped": 0,
            "errors": 0,
            "status": "running"
        }

        try:
            if not self.is_agent_enabled():
                logger.warning("⏸️ Agent is disabled, skipping cycle")
                results["status"] = "disabled"
                return results

            can_send, safety_reason = SafetyController.can_send_now(self.db)
            if not can_send:
                logger.warning(f"⚠️ Safety check failed: {safety_reason}")
                results["status"] = "blocked"
                results["block_reason"] = safety_reason
                return results

            capacity = RateLimiter.get_remaining_capacity(self.db)
            max_sends = min(
                capacity['daily']['remaining'],
                capacity['hourly']['remaining'],
                20
            )

            logger.info(f"📊 Rate limits: {capacity['daily']['sent']}/{capacity['daily']['limit']} daily, "
                       f"{capacity['hourly']['sent']}/{capacity['hourly']['limit']} hourly")

            if max_sends <= 0:
                logger.info("⏸️ Rate limits reached, waiting...")
                results["status"] = "rate_limited"
                return results

            logger.info(f"🧠 Consulting decision engine (max actions: {max_sends})...")
            decisions = self.decision_engine.make_decisions(max_actions=max_sends)
            results["decisions_made"] = len(decisions)

            if not decisions:
                logger.info("✅ No actions needed this cycle")
                results["status"] = "idle"
                return results

            logger.info(f"⚡ Executing {len(decisions)} decisions...")
            for decision in decisions:
                try:
                    if decision.action == DecisionType.SEND_INITIAL:
                        # 🔥 WOOD ONLY: No template override needed
                        self._execute_send_initial(decision)
                        results["emails_queued"] += 1

                    elif decision.action == DecisionType.SEND_FOLLOWUP:
                        # 🔥 WOOD ONLY: No template override
                        self._execute_send_followup(decision)
                        results["emails_queued"] += 1

                    elif decision.action == DecisionType.SKIP:
                        results["leads_skipped"] += 1

                    self._log_action(decision, "success")

                except Exception as e:
                    logger.error(f"❌ Error executing decision for lead {decision.lead.id}: {str(e)}")
                    results["errors"] += 1
                    self._log_action(decision, "error", str(e))
                    StateManager.handle_error(decision.lead, str(e), self.db)

            config = self.db.query(AgentConfig).first()
            if config:
                config.last_agent_run_at = datetime.utcnow()
                self.db.commit()

            results["status"] = "completed"

        except Exception as e:
            logger.error(f"💥 Agent cycle failed: {str(e)}", exc_info=True)
            results["status"] = "failed"
            results["error"] = str(e)

        finally:
            execution_time = (time.time() - start_time) * 1000
            results["execution_time_ms"] = int(execution_time)
            results["completed_at"] = datetime.utcnow().isoformat()

            logger.info(f"✅ Agent cycle completed in {execution_time:.0f}ms [run_id: {self.run_id}]")
            logger.info(f"📈 Results: {results['emails_queued']} queued, "
                       f"{results['leads_skipped']} skipped, {results['errors']} errors")

        return results

    def _execute_send_initial(self, decision):
        """
        Execute initial email send - WOOD ONLY.
        
        🔥 REMOVED: template_override parameter
        """
        from app.worker.tasks import generate_and_send_email_task
        from app.services.email_templates import get_subject_for_industry

        lead = decision.lead

        # 🔥 WOOD ONLY: Force wood template
        logger.info(f"🪵 Applying WOOD template to lead {lead.id}")
        lead.agent_notes = "template:wood"
        lead.industry = "Wood"
        self.db.commit()

        logger.info(f"📧 Queuing initial email for lead {lead.id} ({lead.email})")

        # Save to queue table
        queue_record = EmailQueue(
            lead_id=lead.id,
            subject=get_subject_for_industry(lead.industry, lead.company),
            body="AI-generated email (pending)",
            status="pending",
            scheduled_at=datetime.utcnow(),
            max_retries=3
        )
        self.db.add(queue_record)
        self.db.commit()
        self.db.refresh(queue_record)

        # Queue email task
        task = generate_and_send_email_task.delay(lead.id, queue_id=queue_record.id)

        # Update queue with task ID
        queue_record.task_id = task.id
        self.db.commit()

        # Update lead state
        StateManager.transition_to_contacted(lead, self.db)

        logger.info(f"✅ Initial email queued [task_id: {task.id}, queue_id: {queue_record.id}]")

    def _execute_send_followup(self, decision):
        """
        Execute follow-up email send - WOOD ONLY.
        """
        from app.worker.tasks import generate_and_send_email_task
        from app.services.email_templates import get_subject_for_industry

        lead = decision.lead

        logger.info(f"📧 Queuing follow-up #{lead.follow_up_count + 1} for lead {lead.id}")

        # 🔥 WOOD ONLY: Ensure wood template
        if "template:wood" not in (lead.agent_notes or ""):
            lead.agent_notes = "template:wood"
            lead.industry = "Wood"
            self.db.commit()

        # Save to queue
        queue_record = EmailQueue(
            lead_id=lead.id,
            subject=f"Follow-up: {get_subject_for_industry(lead.industry, lead.company)}",
            body="AI-generated follow-up (pending)",
            status="pending",
            scheduled_at=datetime.utcnow(),
            max_retries=3
        )
        self.db.add(queue_record)
        self.db.commit()
        self.db.refresh(queue_record)

        # Queue task
        task = generate_and_send_email_task.delay(lead.id, queue_id=queue_record.id)

        queue_record.task_id = task.id
        self.db.commit()

        # Update lead state
        StateManager.transition_to_follow_up(lead, self.db)

        logger.info(f"✅ Follow-up queued [task_id: {task.id}, queue_id: {queue_record.id}]")

    def _log_action(self, decision, result: str, error: str = None):
        """Log agent action to database."""
        try:
            config = self.db.query(AgentConfig).first()

            log = AgentActionLog(
                action_type=decision.action,
                action_result=result,
                lead_id=decision.lead.id,
                lead_email=decision.lead.email,
                decision_reason=decision.reason,
                error_message=error,
                agent_run_id=self.run_id,
                emails_sent_before=config.emails_sent_today if config else 0
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log action: {str(e)}")

    def get_status(self) -> dict:
        """Get current agent status."""
        config = self.db.query(AgentConfig).first()

        if not config:
            return {"error": "Config not found"}

        capacity = RateLimiter.get_remaining_capacity(self.db)

        return {
            "is_running": config.is_running,
            "is_paused": config.is_paused,
            "template": "wood",  # Always wood
            "last_run": config.last_agent_run_at.isoformat() if config.last_agent_run_at else None,
            "emails_today": capacity['daily']['sent'],
            "daily_limit": capacity['daily']['limit'],
            "emails_this_hour": capacity['hourly']['sent'],
            "hourly_limit": capacity['hourly']['limit'],
            "total_emails": config.total_emails_sent,
            "total_errors": config.total_errors
        }


# Singleton instance
_agent_instance = None

def get_agent() -> AgentRunner:
    """Get or create agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AgentRunner()
    return _agent_instance
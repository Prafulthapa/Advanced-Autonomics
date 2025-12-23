"""
Celery Tasks for Agent Automation
Scheduled periodic tasks for agent operations
"""

from celery import Celery
import logging
from datetime import datetime

from app.database import SessionLocal
from app.models.agent_config import AgentConfig
from app.agent.agent_runner import get_agent
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="agent_cycle_task")
def agent_cycle_task():
    """
    Periodic task: Run one agent cycle.
    This is called by Celery Beat every N minutes.
    """
    db = SessionLocal()
    
    try:
        logger.info("⏰ Scheduled agent cycle starting...")
        
        # Check if agent is enabled
        config = db.query(AgentConfig).first()
        
        if not config:
            logger.error("❌ Agent config not found")
            return {"error": "Config not found"}
        
        if not config.is_running:
            logger.info("⏸️  Agent is not running, skipping cycle")
            return {"status": "disabled"}
        
        if config.is_paused:
            logger.info("⏸️  Agent is paused, skipping cycle")
            return {"status": "paused"}
        
        # Update next run time
        config.next_agent_run_at = datetime.utcnow()
        db.commit()
        
        # Run agent cycle
        agent = get_agent()
        results = agent.run_cycle()
        
        logger.info(f"✅ Scheduled agent cycle completed: {results['emails_queued']} emails queued")
        
        return results
        
    except Exception as e:
        logger.error(f"💥 Agent cycle task failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="agent_health_check")
def agent_health_check():
    """
    Periodic task: Check agent health and alert if issues.
    Runs every 15 minutes.
    """
    db = SessionLocal()
    
    try:
        config = db.query(AgentConfig).first()
        
        if not config:
            logger.error("❌ Agent config not found in health check")
            return {"error": "Config not found"}
        
        alerts = []
        
        # Alert 1: Agent supposed to be running but isn't
        if config.is_running and config.last_agent_run_at:
            time_since_run = (datetime.utcnow() - config.last_agent_run_at).total_seconds() / 60
            if time_since_run > 30:  # No run in 30 minutes
                alerts.append({
                    "type": "no_activity",
                    "message": f"Agent hasn't run in {time_since_run:.0f} minutes",
                    "severity": "warning"
                })
        
        # Alert 2: High error rate
        if config.total_emails_sent > 10:
            error_rate = (config.total_errors / config.total_emails_sent) * 100
            if error_rate > 10:
                alerts.append({
                    "type": "high_error_rate",
                    "message": f"Error rate at {error_rate:.1f}%",
                    "severity": "critical"
                })
        
        # Alert 3: No emails sent today (during business hours)
        if config.is_running and config.emails_sent_today == 0:
            alerts.append({
                "type": "zero_sends",
                "message": "No emails sent today",
                "severity": "info"
            })
        
        if alerts:
            logger.warning(f"⚠️  Agent health alerts: {len(alerts)} issues found")
            for alert in alerts:
                logger.warning(f"   - [{alert['severity'].upper()}] {alert['message']}")
        else:
            logger.info("✅ Agent health check passed")
        
        return {
            "status": "healthy" if not alerts else "unhealthy",
            "alerts": alerts,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="cleanup_old_logs")
def cleanup_old_logs():
    """
    Periodic task: Clean up old agent action logs.
    Runs daily at midnight.
    """
    from app.models.agent_action_log import AgentActionLog
    from datetime import timedelta
    
    db = SessionLocal()
    
    try:
        # Delete logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        deleted_count = db.query(AgentActionLog).filter(
            AgentActionLog.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"🗑️  Cleaned up {deleted_count} old agent logs")
        
        return {
            "deleted": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Log cleanup failed: {str(e)}", exc_info=True)
        db.rollback()
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="sync_agent_config")
def sync_agent_config():
    """
    Periodic task: Sync agent config from YAML file.
    Runs every hour.
    """
    from app.config import agent_config
    
    db = SessionLocal()
    
    try:
        # Reload config from file
        agent_config.reload()
        
        # Update database config
        config = db.query(AgentConfig).first()
        
        if config:
            # Sync limits from file
            config.daily_email_limit = agent_config.get('limits.max_emails_per_day', 50)
            config.hourly_email_limit = agent_config.get('limits.max_emails_per_hour', 10)
            config.agent_check_interval = agent_config.get('agent.check_interval', 5)
            config.inbox_check_interval = agent_config.get('agent.inbox_check_interval', 15)
            
            # Sync timing
            config.business_hours_start = agent_config.get('timing.business_hours_start', '09:00')
            config.business_hours_end = agent_config.get('timing.business_hours_end', '17:00')
            config.timezone = agent_config.get('timing.timezone', 'America/New_York')
            
            # Sync safety
            config.respect_business_hours = agent_config.get('safety.respect_business_hours', True)
            config.respect_unsubscribes = agent_config.get('safety.respect_unsubscribes', True)
            
            db.commit()
            
            logger.info("✅ Agent config synced from YAML file")
            return {"status": "synced"}
        else:
            logger.warning("⚠️  No agent config in database to sync")
            return {"status": "no_config"}
        
    except Exception as e:
        logger.error(f"Config sync failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
    
    finally:
        db.close()
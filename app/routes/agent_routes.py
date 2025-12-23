"""
Agent Control API Routes
Endpoints to start, stop, monitor the AI agent
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import SessionLocal
from app.models.agent_config import AgentConfig
from app.models.agent_action_log import AgentActionLog
from app.models.lead import Lead
from app.agent.agent_runner import get_agent
from app.utils.rate_limiter import RateLimiter
from pydantic import BaseModel

router = APIRouter(prefix="/agent", tags=["Agent"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AgentStartRequest(BaseModel):
    """Request to start agent."""
    force: bool = False


class AgentConfigUpdate(BaseModel):
    """Update agent configuration."""
    daily_email_limit: int = None
    hourly_email_limit: int = None
    business_hours_start: str = None
    business_hours_end: str = None
    respect_business_hours: bool = None


@router.get("/status")
async def get_agent_status(db: Session = Depends(get_db)):
    """Get current agent status and statistics."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    # Get rate limit info
    capacity = RateLimiter.get_remaining_capacity(db)
    
    # Count leads by status
    lead_stats = {
        "total": db.query(Lead).count(),
        "new": db.query(Lead).filter(Lead.status == "new").count(),
        "contacted": db.query(Lead).filter(Lead.status == "contacted").count(),
        "replied": db.query(Lead).filter(Lead.replied == "yes").count(),
        "agent_enabled": db.query(Lead).filter(Lead.agent_enabled == True).count(),
        "agent_paused": db.query(Lead).filter(Lead.agent_paused == True).count(),
    }
    
    # Recent actions count
    recent_actions = db.query(AgentActionLog).filter(
        AgentActionLog.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).count()
    
    return {
        "agent": {
            "is_running": config.is_running,
            "is_paused": config.is_paused,
            "last_run": config.last_agent_run_at.isoformat() if config.last_agent_run_at else None,
            "next_run": config.next_agent_run_at.isoformat() if config.next_agent_run_at else None,
        },
        "limits": {
            "daily": {
                "sent": capacity['daily']['sent'],
                "limit": capacity['daily']['limit'],
                "remaining": capacity['daily']['remaining']
            },
            "hourly": {
                "sent": capacity['hourly']['sent'],
                "limit": capacity['hourly']['limit'],
                "remaining": capacity['hourly']['remaining']
            }
        },
        "statistics": {
            "total_emails_sent": config.total_emails_sent,
            "total_replies": config.total_replies_received,
            "total_errors": config.total_errors,
            "actions_today": recent_actions
        },
        "leads": lead_stats,
        "config": {
            "business_hours_start": config.business_hours_start,
            "business_hours_end": config.business_hours_end,
            "timezone": config.timezone,
            "respect_business_hours": config.respect_business_hours,
            "check_interval": config.agent_check_interval
        }
    }


@router.post("/start")
async def start_agent(request: AgentStartRequest = None, db: Session = Depends(get_db)):
    """Start the AI agent."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    if config.is_running and not request.force:
        raise HTTPException(status_code=400, detail="Agent is already running")
    
    # Start agent
    config.is_running = True
    config.is_paused = False
    config.agent_started_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Agent started successfully",
        "started_at": config.agent_started_at.isoformat()
    }


@router.post("/stop")
async def stop_agent(db: Session = Depends(get_db)):
    """Stop the AI agent."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    if not config.is_running:
        raise HTTPException(status_code=400, detail="Agent is not running")
    
    # Stop agent
    config.is_running = False
    config.agent_stopped_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Agent stopped successfully",
        "stopped_at": config.agent_stopped_at.isoformat()
    }


@router.post("/pause")
async def pause_agent(db: Session = Depends(get_db)):
    """Pause the agent temporarily."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    config.is_paused = True
    db.commit()
    
    return {
        "success": True,
        "message": "Agent paused"
    }


@router.post("/resume")
async def resume_agent(db: Session = Depends(get_db)):
    """Resume a paused agent."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    config.is_paused = False
    db.commit()
    
    return {
        "success": True,
        "message": "Agent resumed"
    }


@router.post("/run-now")
async def run_agent_cycle_now(db: Session = Depends(get_db)):
    """Manually trigger one agent cycle immediately."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    if not config.is_running:
        raise HTTPException(
            status_code=400, 
            detail="Agent must be started first. Use POST /agent/start"
        )
    
    # Run agent cycle
    agent = get_agent()
    results = agent.run_cycle()
    
    return {
        "success": True,
        "message": "Agent cycle completed",
        "results": results
    }


@router.patch("/config")
async def update_agent_config(
    updates: AgentConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update agent configuration."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    # Apply updates
    if updates.daily_email_limit is not None:
        config.daily_email_limit = updates.daily_email_limit
    
    if updates.hourly_email_limit is not None:
        config.hourly_email_limit = updates.hourly_email_limit
    
    if updates.business_hours_start is not None:
        config.business_hours_start = updates.business_hours_start
    
    if updates.business_hours_end is not None:
        config.business_hours_end = updates.business_hours_end
    
    if updates.respect_business_hours is not None:
        config.respect_business_hours = updates.respect_business_hours
    
    config.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Configuration updated",
        "config": {
            "daily_email_limit": config.daily_email_limit,
            "hourly_email_limit": config.hourly_email_limit,
            "business_hours_start": config.business_hours_start,
            "business_hours_end": config.business_hours_end,
            "respect_business_hours": config.respect_business_hours
        }
    }


@router.get("/logs")
async def get_agent_logs(
    limit: int = 50,
    action_type: str = None,
    db: Session = Depends(get_db)
):
    """Get recent agent action logs."""
    query = db.query(AgentActionLog).order_by(AgentActionLog.timestamp.desc())
    
    if action_type:
        query = query.filter(AgentActionLog.action_type == action_type)
    
    logs = query.limit(limit).all()
    
    return {
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "action_type": log.action_type,
                "action_result": log.action_result,
                "lead_id": log.lead_id,
                "lead_email": log.lead_email,
                "decision_reason": log.decision_reason,
                "error_message": log.error_message,
                "timestamp": log.timestamp.isoformat(),
                "execution_time_ms": log.execution_time_ms
            }
            for log in logs
        ]
    }


@router.get("/statistics")
async def get_agent_statistics(db: Session = Depends(get_db)):
    """Get detailed agent statistics."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    # Action statistics
    total_actions = db.query(AgentActionLog).count()
    
    actions_by_type = db.query(
        AgentActionLog.action_type,
        db.func.count(AgentActionLog.id)
    ).group_by(AgentActionLog.action_type).all()
    
    actions_by_result = db.query(
        AgentActionLog.action_result,
        db.func.count(AgentActionLog.id)
    ).group_by(AgentActionLog.action_result).all()
    
    # Lead statistics
    leads_by_status = db.query(
        Lead.status,
        db.func.count(Lead.id)
    ).group_by(Lead.status).all()
    
    return {
        "total_actions": total_actions,
        "actions_by_type": {action_type: count for action_type, count in actions_by_type},
        "actions_by_result": {result: count for result, count in actions_by_result},
        "leads_by_status": {status: count for status, count in leads_by_status},
        "emails_sent": config.total_emails_sent,
        "replies_received": config.total_replies_received,
        "errors": config.total_errors,
        "success_rate": (
            (config.total_emails_sent - config.total_errors) / config.total_emails_sent * 100
            if config.total_emails_sent > 0 else 0
        )
    }


@router.post("/reset-counters")
async def reset_daily_counters(db: Session = Depends(get_db)):
    """Manually reset daily email counters (for testing)."""
    config = db.query(AgentConfig).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    config.emails_sent_today = 0
    config.emails_sent_this_hour = 0
    config.last_reset_date = datetime.utcnow().strftime("%Y-%m-%d")
    config.last_hour_reset = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Counters reset successfully"
    }
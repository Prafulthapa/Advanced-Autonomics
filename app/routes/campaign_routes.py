"""
Campaign Management Routes - WOOD ONLY VERSION
Simplified: Agent handles all sending automatically
Manual campaign buttons removed - use Agent Control Panel instead
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.lead import Lead

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stats")
async def get_campaign_stats(db: Session = Depends(get_db)):
    """
    Get campaign statistics (read-only).
    
    This endpoint provides overview metrics without manual intervention.
    The agent handles all email sending automatically.
    """
    
    total = db.query(Lead).count()
    
    contacted = db.query(Lead).filter(
        Lead.status.in_(["contacted", "follow_up"])
    ).count()
    
    replied = db.query(Lead).filter(Lead.replied == "yes").count()
    
    interested = db.query(Lead).filter(Lead.status == "interested").count()
    
    new_leads = db.query(Lead).filter(Lead.status == "new").count()
    
    agent_enabled = db.query(Lead).filter(Lead.agent_enabled == True).count()
    
    return {
        "total_leads": total,
        "new_leads": new_leads,
        "contacted": contacted,
        "replied": replied,
        "interested": interested,
        "agent_enabled": agent_enabled,
        "template": "wood",
        "note": "Agent handles all sending automatically. Use Agent Control Panel to start/stop."
    }


@router.get("/template-distribution")
async def get_template_distribution(db: Session = Depends(get_db)):
    """
    Show template distribution (always 100% wood).
    
    Useful for debugging and confirming wood-only configuration.
    """
    
    leads = db.query(Lead).all()
    
    return {
        "total_leads": len(leads),
        "wood_template": len(leads),  # All wood
        "glass_template": 0,  # None (removed)
        "distribution": {
            "wood_percentage": 100.0,
            "glass_percentage": 0.0
        },
        "note": "Wood-only system - all leads receive carpentry/woodworking template"
    }


@router.get("/health")
async def get_campaign_health(db: Session = Depends(get_db)):
    """
    Get campaign health metrics.
    
    Provides quick overview of campaign status for monitoring.
    """
    
    from app.models.email_log import EmailLog
    from app.models.email_queue import EmailQueue
    from datetime import datetime, timedelta
    
    # Today's metrics
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    emails_sent_today = db.query(EmailLog).filter(
        EmailLog.sent_at >= today_start,
        EmailLog.status == "sent"
    ).count()
    
    emails_failed_today = db.query(EmailLog).filter(
        EmailLog.sent_at >= today_start,
        EmailLog.status == "failed"
    ).count()
    
    # Queue status
    queue_pending = db.query(EmailQueue).filter(
        EmailQueue.status == "pending"
    ).count()
    
    queue_processing = db.query(EmailQueue).filter(
        EmailQueue.status == "processing"
    ).count()
    
    queue_failed = db.query(EmailQueue).filter(
        EmailQueue.status == "failed",
        EmailQueue.retry_count < EmailQueue.max_retries
    ).count()
    
    # Lead status
    leads_ready = db.query(Lead).filter(
        Lead.agent_enabled == True,
        Lead.agent_paused == False,
        Lead.status.in_(["new", "contacted", "follow_up"])
    ).count()
    
    # Calculate success rate
    total_today = emails_sent_today + emails_failed_today
    success_rate = (emails_sent_today / total_today * 100) if total_today > 0 else 0
    
    return {
        "today": {
            "emails_sent": emails_sent_today,
            "emails_failed": emails_failed_today,
            "success_rate": round(success_rate, 2)
        },
        "queue": {
            "pending": queue_pending,
            "processing": queue_processing,
            "failed_retryable": queue_failed
        },
        "leads": {
            "ready_for_contact": leads_ready
        },
        "template": "wood",
        "timestamp": datetime.utcnow().isoformat()
    }
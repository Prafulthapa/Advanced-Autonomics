"""
Analytics & Reporting
Track campaign performance over time
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Optional

from app.database import SessionLocal
from app.models.lead import Lead
from app.models.email_log import EmailLog
from app.models.email_reply import EmailReply
from app.models.email_queue import EmailQueue
from app.models.agent_action_log import AgentActionLog

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/overview")
async def get_analytics_overview(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics overview.
    
    Args:
        days: Number of days to analyze (default: 30)
    """
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # ============================================
    # LEAD STATISTICS
    # ============================================
    total_leads = db.query(Lead).count()
    
    leads_by_status = db.query(
        Lead.status,
        func.count(Lead.id).label('count')
    ).group_by(Lead.status).all()
    
    # ============================================
    # EMAIL STATISTICS
    # ============================================
    total_emails_sent = db.query(EmailLog).filter(
        EmailLog.status == "sent",
        EmailLog.sent_at >= cutoff_date
    ).count()
    
    total_emails_failed = db.query(EmailLog).filter(
        EmailLog.status == "failed",
        EmailLog.sent_at >= cutoff_date
    ).count()
    
    # ============================================
    # REPLY STATISTICS
    # ============================================
    total_replies = db.query(EmailReply).filter(
        EmailReply.received_at >= cutoff_date
    ).count()
    
    replies_by_classification = db.query(
        EmailReply.classification,
        func.count(EmailReply.id).label('count')
    ).filter(
        EmailReply.received_at >= cutoff_date
    ).group_by(EmailReply.classification).all()
    
    # ============================================
    # RESPONSE RATE
    # ============================================
    contacted_leads = db.query(Lead).filter(
        Lead.status.in_(["contacted", "follow_up", "replied"])
    ).count()
    
    replied_leads = db.query(Lead).filter(
        Lead.replied == "yes"
    ).count()
    
    response_rate = (replied_leads / contacted_leads * 100) if contacted_leads > 0 else 0
    
    # ============================================
    # INTERESTED LEADS
    # ============================================
    interested_leads = db.query(Lead).filter(
        Lead.status == "interested"
    ).count()
    
    interested_rate = (interested_leads / contacted_leads * 100) if contacted_leads > 0 else 0
    
    # ============================================
    # CONVERSION FUNNEL
    # ============================================
    funnel = {
        "total_leads": total_leads,
        "contacted": contacted_leads,
        "replied": replied_leads,
        "interested": interested_leads,
        "conversion_rate": interested_rate
    }
    
    # ============================================
    # DAILY BREAKDOWN (Last 7 days)
    # ============================================
    daily_stats = []
    for i in range(7):
        day_start = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)
        
        emails_sent = db.query(EmailLog).filter(
            EmailLog.status == "sent",
            EmailLog.sent_at >= day_start,
            EmailLog.sent_at < day_end
        ).count()
        
        replies = db.query(EmailReply).filter(
            EmailReply.received_at >= day_start,
            EmailReply.received_at < day_end
        ).count()
        
        daily_stats.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "emails_sent": emails_sent,
            "replies": replies
        })
    
    return {
        "time_period_days": days,
        "overview": {
            "total_leads": total_leads,
            "contacted_leads": contacted_leads,
            "replied_leads": replied_leads,
            "interested_leads": interested_leads,
            "response_rate": round(response_rate, 2),
            "interested_rate": round(interested_rate, 2)
        },
        "leads_by_status": {status: count for status, count in leads_by_status},
        "emails": {
            "sent": total_emails_sent,
            "failed": total_emails_failed,
            "success_rate": round((total_emails_sent / (total_emails_sent + total_emails_failed) * 100), 2) if (total_emails_sent + total_emails_failed) > 0 else 0
        },
        "replies": {
            "total": total_replies,
            "by_classification": {cls: count for cls, count in replies_by_classification}
        },
        "funnel": funnel,
        "daily_breakdown": list(reversed(daily_stats))
    }


@router.get("/performance")
async def get_performance_metrics(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get recent performance metrics.
    
    Args:
        hours: Number of hours to analyze (default: 24)
    """
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Agent actions
    agent_actions = db.query(AgentActionLog).filter(
        AgentActionLog.timestamp >= cutoff
    ).count()
    
    successful_actions = db.query(AgentActionLog).filter(
        AgentActionLog.timestamp >= cutoff,
        AgentActionLog.action_result == "success"
    ).count()
    
    # Queue performance
    queue_stats = db.query(
        func.avg(EmailQueue.retry_count).label('avg_retries'),
        func.count(EmailQueue.id).label('total_processed')
    ).filter(
        and_(
            EmailQueue.status.in_(["sent", "failed"]),
            EmailQueue.created_at >= cutoff
        )
    ).first()
    
    # Average time to send
    avg_processing_time = db.query(
        func.avg(
            func.julianday(EmailQueue.sent_at) - func.julianday(EmailQueue.scheduled_at)
        ) * 24 * 60  # Convert to minutes
    ).filter(
        EmailQueue.status == "sent",
        EmailQueue.sent_at >= cutoff
    ).scalar()
    
    return {
        "time_period_hours": hours,
        "agent": {
            "total_actions": agent_actions,
            "successful_actions": successful_actions,
            "success_rate": round((successful_actions / agent_actions * 100), 2) if agent_actions > 0 else 0
        },
        "queue": {
            "total_processed": queue_stats.total_processed if queue_stats else 0,
            "avg_retries": round(queue_stats.avg_retries, 2) if queue_stats and queue_stats.avg_retries else 0,
            "avg_processing_time_minutes": round(avg_processing_time, 2) if avg_processing_time else 0
        }
    }


@router.get("/top-performing-leads")
async def get_top_performing_leads(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get leads with highest engagement (replied or interested)."""
    
    top_leads = db.query(Lead).filter(
        Lead.status.in_(["replied", "interested"])
    ).order_by(
        Lead.priority_score.desc(),
        Lead.engagement_score.desc()
    ).limit(limit).all()
    
    return {
        "total": len(top_leads),
        "leads": [
            {
                "id": lead.id,
                "email": lead.email,
                "company": lead.company,
                "status": lead.status,
                "priority_score": lead.priority_score,
                "engagement_score": lead.engagement_score,
                "follow_up_count": lead.follow_up_count,
                "last_email_sent": lead.last_email_sent_at.isoformat() if lead.last_email_sent_at else None
            }
            for lead in top_leads
        ]
    }


@router.get("/campaign-summary")
async def get_campaign_summary(db: Session = Depends(get_db)):
    """
    Get high-level campaign summary for quick overview.
    Perfect for dashboard display.
    """
    
    # Today's stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    
    emails_today = db.query(EmailLog).filter(
        EmailLog.sent_at >= today_start,
        EmailLog.status == "sent"
    ).count()
    
    replies_today = db.query(EmailReply).filter(
        EmailReply.received_at >= today_start
    ).count()
    
    # Overall campaign health
    total_leads = db.query(Lead).count()
    active_leads = db.query(Lead).filter(
        Lead.agent_enabled == True,
        Lead.agent_paused == False
    ).count()
    
    # Next scheduled actions
    next_actions = db.query(Lead).filter(
        Lead.agent_enabled == True,
        Lead.next_agent_check_at.isnot(None)
    ).order_by(Lead.next_agent_check_at.asc()).limit(5).all()
    
    return {
        "today": {
            "emails_sent": emails_today,
            "replies_received": replies_today
        },
        "campaign_health": {
            "total_leads": total_leads,
            "active_leads": active_leads,
            "paused_leads": total_leads - active_leads
        },
        "next_scheduled_actions": [
            {
                "lead_id": lead.id,
                "email": lead.email,
                "company": lead.company,
                "scheduled_at": lead.next_agent_check_at.isoformat() if lead.next_agent_check_at else None,
                "action_type": "follow_up" if lead.sequence_step > 0 else "initial"
            }
            for lead in next_actions
        ]
    }


@router.get("/export/csv")
async def export_analytics_csv(db: Session = Depends(get_db)):
    """
    Export campaign data as CSV.
    Useful for external analysis or reporting to stakeholders.
    """
    
    leads = db.query(Lead).all()
    
    csv_rows = [
        "Email,First Name,Last Name,Company,Industry,Status,Follow-ups,Priority Score,Last Contacted,Replied,Classification"
    ]
    
    for lead in leads:
        # Get latest reply classification
        latest_reply = db.query(EmailReply).filter(
            EmailReply.lead_id == lead.id
        ).order_by(EmailReply.received_at.desc()).first()
        
        classification = latest_reply.classification if latest_reply else ""
        
        csv_rows.append(
            f"{lead.email},"
            f"{lead.first_name or ''},"
            f"{lead.last_name or ''},"
            f"{lead.company or ''},"
            f"{lead.industry or ''},"
            f"{lead.status},"
            f"{lead.follow_up_count},"
            f"{lead.priority_score},"
            f"{lead.last_email_sent_at.strftime('%Y-%m-%d') if lead.last_email_sent_at else ''},"
            f"{lead.replied},"
            f"{classification}"
        )
    
    csv_content = "\n".join(csv_rows)
    
    from fastapi.responses import Response
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=campaign_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )
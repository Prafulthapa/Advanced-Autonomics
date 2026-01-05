"""
Email Queue Monitoring Routes
Monitor queued, failed, and retry status of emails
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models.email_queue import EmailQueue
from app.models.lead import Lead

router = APIRouter(prefix="/queue", tags=["Email Queue"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/status")
async def get_queue_status(db: Session = Depends(get_db)):
    """Get overall email queue statistics."""
    
    # Count by status
    pending = db.query(EmailQueue).filter(EmailQueue.status == "pending").count()
    processing = db.query(EmailQueue).filter(EmailQueue.status == "processing").count()
    sent = db.query(EmailQueue).filter(EmailQueue.status == "sent").count()
    failed = db.query(EmailQueue).filter(EmailQueue.status == "failed").count()
    
    # Failed with retries remaining
    retry_candidates = db.query(EmailQueue).filter(
        EmailQueue.status == "failed",
        EmailQueue.retry_count < EmailQueue.max_retries
    ).count()
    
    # Permanently failed (max retries exceeded)
    permanently_failed = db.query(EmailQueue).filter(
        EmailQueue.status == "failed",
        EmailQueue.retry_count >= EmailQueue.max_retries
    ).count()
    
    # Oldest pending
    oldest_pending = db.query(EmailQueue).filter(
        EmailQueue.status == "pending"
    ).order_by(EmailQueue.scheduled_at.asc()).first()
    
    return {
        "total": pending + processing + sent + failed,
        "by_status": {
            "pending": pending,
            "processing": processing,
            "sent": sent,
            "failed": failed
        },
        "failed_breakdown": {
            "can_retry": retry_candidates,
            "permanently_failed": permanently_failed
        },
        "oldest_pending": {
            "id": oldest_pending.id if oldest_pending else None,
            "scheduled_at": oldest_pending.scheduled_at if oldest_pending else None,
            "lead_id": oldest_pending.lead_id if oldest_pending else None
        }
    }


@router.get("/pending")
async def get_pending_emails(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all pending emails in queue."""
    
    queue_items = db.query(EmailQueue).filter(
        EmailQueue.status == "pending"
    ).order_by(EmailQueue.scheduled_at.asc()).limit(limit).all()
    
    return {
        "total": len(queue_items),
        "items": [
            {
                "id": item.id,
                "lead_id": item.lead_id,
                "subject": item.subject,
                "status": item.status,
                "retry_count": item.retry_count,
                "scheduled_at": item.scheduled_at,
                "task_id": item.task_id
            }
            for item in queue_items
        ]
    }


@router.get("/failed")
async def get_failed_emails(
    include_retryable: bool = True,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all failed emails."""
    
    query = db.query(EmailQueue).filter(EmailQueue.status == "failed")
    
    if not include_retryable:
        # Only permanently failed (max retries exceeded)
        query = query.filter(EmailQueue.retry_count >= EmailQueue.max_retries)
    
    failed_items = query.order_by(EmailQueue.failed_at.desc()).limit(limit).all()
    
    return {
        "total": len(failed_items),
        "items": [
            {
                "id": item.id,
                "lead_id": item.lead_id,
                "subject": item.subject,
                "status": item.status,
                "retry_count": item.retry_count,
                "max_retries": item.max_retries,
                "last_error": item.last_error,
                "failed_at": item.failed_at,
                "can_retry": item.retry_count < item.max_retries
            }
            for item in failed_items
        ]
    }


@router.post("/retry/{queue_id}")
async def retry_failed_email(
    queue_id: int,
    db: Session = Depends(get_db)
):
    """Manually retry a failed email."""
    
    queue_item = db.query(EmailQueue).filter(EmailQueue.id == queue_id).first()
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    if queue_item.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed emails can be retried")
    
    if queue_item.retry_count >= queue_item.max_retries:
        raise HTTPException(status_code=400, detail="Max retries exceeded")
    
    # Reset to pending
    queue_item.status = "pending"
    queue_item.scheduled_at = datetime.utcnow()
    queue_item.last_error = None
    db.commit()
    
    # Re-queue the task
    from app.worker.tasks import generate_and_send_email_task
    task = generate_and_send_email_task.delay(queue_item.lead_id, queue_id=queue_item.id)
    
    queue_item.task_id = task.id
    db.commit()
    
    return {
        "success": True,
        "message": "Email re-queued for retry",
        "queue_id": queue_id,
        "task_id": task.id
    }


@router.delete("/failed")
async def clear_failed_emails(
    only_permanent: bool = True,
    db: Session = Depends(get_db)
):
    """Clear failed emails from queue."""
    
    query = db.query(EmailQueue).filter(EmailQueue.status == "failed")
    
    if only_permanent:
        # Only delete permanently failed
        query = query.filter(EmailQueue.retry_count >= EmailQueue.max_retries)
    
    deleted_count = query.delete()
    db.commit()
    
    return {
        "success": True,
        "deleted": deleted_count,
        "message": f"Cleared {deleted_count} failed emails"
    }


@router.get("/stats")
async def get_queue_stats(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get queue statistics for the last N hours."""
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Count emails by status in time window
    recent_sent = db.query(EmailQueue).filter(
        EmailQueue.status == "sent",
        EmailQueue.sent_at >= cutoff
    ).count()
    
    recent_failed = db.query(EmailQueue).filter(
        EmailQueue.status == "failed",
        EmailQueue.failed_at >= cutoff
    ).count()
    
    # Average retry count for sent emails
    from sqlalchemy import func
    avg_retries = db.query(func.avg(EmailQueue.retry_count)).filter(
        EmailQueue.status == "sent",
        EmailQueue.sent_at >= cutoff
    ).scalar() or 0
    
    # Success rate
    total_attempts = recent_sent + recent_failed
    success_rate = (recent_sent / total_attempts * 100) if total_attempts > 0 else 0
    
    return {
        "time_window_hours": hours,
        "sent": recent_sent,
        "failed": recent_failed,
        "total_attempts": total_attempts,
        "success_rate": round(success_rate, 2),
        "avg_retries_before_success": round(avg_retries, 2)
    }
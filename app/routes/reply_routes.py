from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import SessionLocal
from app.models.email_reply import EmailReply
from app.models.lead import Lead
from app.worker.imap_tasks import fetch_and_process_replies

router = APIRouter(prefix="/replies", tags=["Replies"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def get_all_replies(
    skip: int = 0,
    limit: int = 50,
    matched_only: bool = False,
    classification: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all email replies with optional filters."""
    query = db.query(EmailReply)

    if matched_only:
        query = query.filter(EmailReply.matched == True)

    if classification:
        query = query.filter(EmailReply.classification == classification)

    replies = query.order_by(EmailReply.received_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": query.count(),
        "replies": [
            {
                "id": r.id,
                "lead_id": r.lead_id,
                "from_email": r.from_email,
                "subject": r.subject,
                "body": r.body[:200] + "..." if len(r.body) > 200 else r.body,
                "classification": r.classification,
                "matched": r.matched,
                "received_at": r.received_at,
                "processed_at": r.processed_at
            }
            for r in replies
        ]
    }


@router.get("/{reply_id}")
async def get_reply(reply_id: int, db: Session = Depends(get_db)):
    """Get a specific reply with full details."""
    reply = db.query(EmailReply).filter(EmailReply.id == reply_id).first()

    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")

    # Get lead info if matched
    lead_info = None
    if reply.lead_id:
        lead = db.query(Lead).filter(Lead.id == reply.lead_id).first()
        if lead:
            lead_info = {
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "status": lead.status
            }

    return {
        "id": reply.id,
        "lead_id": reply.lead_id,
        "lead": lead_info,
        "from_email": reply.from_email,
        "to_email": reply.to_email,
        "subject": reply.subject,
        "body": reply.body,
        "classification": reply.classification,
        "classification_reason": reply.classification_reason,
        "matched": reply.matched,
        "processed": reply.processed,
        "received_at": reply.received_at,
        "processed_at": reply.processed_at,
        "message_id": reply.message_id,
        "in_reply_to": reply.in_reply_to
    }


@router.get("/lead/{lead_id}")
async def get_replies_for_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get all replies for a specific lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    replies = db.query(EmailReply).filter(
        EmailReply.lead_id == lead_id
    ).order_by(EmailReply.received_at.desc()).all()

    return {
        "lead_id": lead_id,
        "lead_email": lead.email,
        "lead_name": f"{lead.first_name} {lead.last_name}",
        "total_replies": len(replies),
        "replies": [
            {
                "id": r.id,
                "subject": r.subject,
                "body": r.body,
                "classification": r.classification,
                "received_at": r.received_at
            }
            for r in replies
        ]
    }


@router.post("/fetch")
async def trigger_fetch_replies():
    """Manually trigger IMAP fetch and process task."""
    task = fetch_and_process_replies.delay()

    return {
        "message": "Reply fetching queued",
        "task_id": task.id
    }


@router.get("/stats/summary")
async def get_reply_stats(db: Session = Depends(get_db)):
    """Get summary statistics for replies."""
    total = db.query(EmailReply).count()
    matched = db.query(EmailReply).filter(EmailReply.matched == True).count()
    unmatched = total - matched

    interested = db.query(EmailReply).filter(
        EmailReply.classification == "interested"
    ).count()

    not_interested = db.query(EmailReply).filter(
        EmailReply.classification == "not_interested"
    ).count()

    unsubscribe = db.query(EmailReply).filter(
        EmailReply.classification == "unsubscribe"
    ).count()

    unclear = db.query(EmailReply).filter(
        EmailReply.classification == "unclear"
    ).count()

    return {
        "total_replies": total,
        "matched": matched,
        "unmatched": unmatched,
        "classifications": {
            "interested": interested,
            "not_interested": not_interested,
            "unsubscribe": unsubscribe,
            "unclear": unclear
        }
    }
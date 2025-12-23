from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.lead import Lead
from app.models.email_log import EmailLog
from app.worker.tasks import send_email_task, generate_and_send_email_task

router = APIRouter(prefix="/emails", tags=["Emails"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SendEmailRequest(BaseModel):
    subject: str
    body: str


@router.post("/send/{lead_id}")
async def send_email_to_lead(
    lead_id: int,
    request: SendEmailRequest,
    db: Session = Depends(get_db)
):
    """Send a custom email to a lead (async via Celery)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    task = send_email_task.delay(lead_id, request.subject, request.body)

    return {
        "message": "Email queued for sending",
        "lead_id": lead_id,
        "task_id": task.id
    }


@router.post("/generate-and-send/{lead_id}")
async def generate_and_send_email(lead_id: int, db: Session = Depends(get_db)):
    """Generate an AI email and send it to a lead (async via Celery)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    task = generate_and_send_email_task.delay(lead_id)

    return {
        "message": "Email generation and sending queued",
        "lead_id": lead_id,
        "lead_name": f"{lead.first_name} {lead.last_name}",
        "task_id": task.id
    }


@router.get("/logs/{lead_id}")
async def get_email_logs(lead_id: int, db: Session = Depends(get_db)):
    """Get all email logs for a specific lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    logs = db.query(EmailLog).filter(EmailLog.lead_id == lead_id).all()

    return {
        "lead_id": lead_id,
        "email_logs": [
            {
                "id": log.id,
                "subject": log.subject,
                "body": log.body,
                "status": log.status,
                "sent_at": log.sent_at,
                "error_message": log.error_message
            }
            for log in logs
        ]
    }
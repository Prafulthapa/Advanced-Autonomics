from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.lead import Lead
from app.services.ollama_service import OllamaService

router = APIRouter(prefix="/ai", tags=["AI"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ReplyClassificationRequest(BaseModel):
    reply: str


@router.post("/generate-email/{lead_id}")
async def generate_email_for_lead(lead_id: int, db: Session = Depends(get_db)):
    """Generate a personalized cold email for a specific lead using AI."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    prompt = f"""
Write a short, personalized cold email (under 120 words) for this lead:

Name: {lead.first_name} {lead.last_name}
Email: {lead.email}
Company: {lead.company}

The email should:
- Be professional but friendly
- Introduce our email outreach automation service
- Mention a benefit relevant to their company
- Include a clear call-to-action
- NOT include placeholder text like [Company Name]

Write only the email body, no subject line.
"""

    try:
        email_body = await OllamaService.generate_email(prompt)
        return {
            "lead_id": lead_id,
            "lead_name": f"{lead.first_name} {lead.last_name}",
            "lead_email": lead.email,
            "generated_email": email_body
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/generate-email")
async def generate_email_from_data(lead: dict):
    """Generate a personalized cold email from provided lead data."""
    prompt = f"""
Write a short, personalized cold email (under 120 words) for this lead:

Lead Info: {lead}

The email should be professional, friendly, and include a clear call-to-action.
Write only the email body, no subject line.
"""

    try:
        email_text = await OllamaService.generate_email(prompt)
        return {"email": email_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/classify-reply")
async def classify_reply_endpoint(data: ReplyClassificationRequest):
    """Classify an email reply as: interested, not interested, unsubscribe, or unclear."""
    try:
        result = await OllamaService.classify_reply(data.reply)
        return {"classification": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
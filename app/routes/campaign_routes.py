"""
Campaign Management Routes
Manual control over which template to use for campaigns
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import SessionLocal
from app.models.lead import Lead
from app.worker.tasks import generate_and_send_email_task

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SendCampaignRequest(BaseModel):
    lead_id: int
    template_type: str  # "glass" or "wood"


@router.post("/send-with-template")
async def send_email_with_template(
    request: SendCampaignRequest,
    db: Session = Depends(get_db)
):
    """
    Send email to a specific lead with chosen template.
    Stores template type in lead.agent_notes for future follow-ups.
    """
    
    # Validate template type
    if request.template_type not in ["glass", "wood"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid template type. Must be 'glass' or 'wood'"
        )
    
    # Get lead
    lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # 🔥 CRITICAL: Store template type in lead for follow-ups
    lead.agent_notes = f"template:{request.template_type}"
    
    # Update industry to match template (helps with future logic)
    if request.template_type == "glass":
        lead.industry = "Glass"
    elif request.template_type == "wood":
        lead.industry = "Wood"
    
     # 🔥 FIX: Update status and sequence BEFORE sending
    lead.status = "contacted"  # Mark as contacted NOW
    lead.sequence_step = 1     # Increment sequence
    lead.last_email_sent_at = datetime.utcnow()  # Set timestamp

    db.commit()
    db.refresh(lead)
    
    # Queue email task
    task = generate_and_send_email_task.delay(lead.id)
    
    return {
        "success": True,
        "lead_id": lead.id,
        "template_type": request.template_type,
        "task_id": task.id,
        "message": f"Email queued with {request.template_type} template"
    }

@router.post("/send-followups")
async def send_followups_with_original_templates(db: Session = Depends(get_db)):
    """
    Send follow-ups to contacted leads using their ORIGINAL template.
    🔥 RESPECTS TIMING RULES - only sends when it's time
    """
    from datetime import timedelta
    
    # Get leads ready for follow-up
    leads = db.query(Lead).filter(
        Lead.status.in_(["contacted", "follow_up"]),
        Lead.agent_enabled == True,
        Lead.follow_up_count < Lead.max_follow_ups,
        Lead.replied == "no"  # 🔥 Only if no reply
    ).all()
    
    if not leads:
        return {
            "success": True,
            "total": 0,
            "message": "No leads ready for follow-up"
        }
    
    glass_count = 0
    wood_count = 0
    skipped_count = 0
    
    # Follow-up schedule (from your YAML)
    followup_schedule = {
        1: 3,   # First follow-up after 3 days
        2: 7,   # Second follow-up after 7 days from previous
        3: 14   # Third follow-up after 14 days from previous
    }
    
    for lead in leads:
        # 🔥 CHECK 1: Has enough time passed?
        if lead.last_email_sent_at:
            days_to_wait = followup_schedule.get(lead.follow_up_count, 3)
            time_since_last = datetime.utcnow() - lead.last_email_sent_at
            
            if time_since_last < timedelta(days=days_to_wait):
                skipped_count += 1
                continue  # Skip - not enough time passed
        
        # 🔥 CHECK 2: Has the lead replied?
        if lead.replied == "yes":
            skipped_count += 1
            continue  # Skip - already replied
        
        # Extract template from agent_notes
        if lead.agent_notes and "template:" in lead.agent_notes:
            template_type = lead.agent_notes.split("template:")[1].split()[0]
        else:
            # Fallback: determine from industry
            if lead.industry and "wood" in lead.industry.lower():
                template_type = "wood"
            else:
                template_type = "glass"
        
        # Update lead state BEFORE queuing
        lead.status = "follow_up"
        lead.follow_up_count += 1
        lead.sequence_step += 1
        lead.last_email_sent_at = datetime.utcnow()
        
        # Queue follow-up
        task = generate_and_send_email_task.delay(lead.id)
        
        if template_type == "glass":
            glass_count += 1
        else:
            wood_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "total": len(leads),
        "sent": glass_count + wood_count,
        "skipped": skipped_count,
        "glass_count": glass_count,
        "wood_count": wood_count,
        "message": f"Follow-ups sent: {glass_count + wood_count}, skipped (timing/replied): {skipped_count}"
    }


@router.get("/template-distribution")
async def get_template_distribution(db: Session = Depends(get_db)):
    """
    Show how many leads are using each template.
    Useful for monitoring.
    """
    
    leads = db.query(Lead).all()
    
    glass_leads = 0
    wood_leads = 0
    unknown_leads = 0
    
    for lead in leads:
        if lead.agent_notes and "template:glass" in lead.agent_notes:
            glass_leads += 1
        elif lead.agent_notes and "template:wood" in lead.agent_notes:
            wood_leads += 1
        else:
            # Try to determine from industry
            if lead.industry and "wood" in lead.industry.lower():
                wood_leads += 1
            elif lead.industry and "glass" in lead.industry.lower():
                glass_leads += 1
            else:
                unknown_leads += 1
    
    return {
        "total_leads": len(leads),
        "glass_template": glass_leads,
        "wood_template": wood_leads,
        "unknown_template": unknown_leads,
        "distribution": {
            "glass_percentage": round((glass_leads / len(leads) * 100), 1) if leads else 0,
            "wood_percentage": round((wood_leads / len(leads) * 100), 1) if leads else 0
        }
    }


@router.post("/fix-template-assignments")
async def fix_template_assignments(db: Session = Depends(get_db)):
    """
    Emergency fix: Assign templates based on industry field.
    Run this to fix existing leads that don't have template info.
    """
    
    leads = db.query(Lead).filter(
        Lead.status != "new"  # Only fix contacted leads
    ).all()
    
    fixed_count = 0
    
    for lead in leads:
        # Skip if already has template assignment
        if lead.agent_notes and "template:" in lead.agent_notes:
            continue
        
        # Assign based on industry
        if lead.industry:
            industry_lower = lead.industry.lower()
            
            if any(word in industry_lower for word in ["wood", "carpentry", "timber", "furniture"]):
                template_type = "wood"
            else:
                template_type = "glass"
            
            # Update agent_notes
            if lead.agent_notes:
                lead.agent_notes += f" | template:{template_type}"
            else:
                lead.agent_notes = f"template:{template_type}"
            
            fixed_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "fixed_leads": fixed_count,
        "message": f"Fixed template assignments for {fixed_count} leads"
    }
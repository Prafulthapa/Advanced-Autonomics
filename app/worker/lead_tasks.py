"""
Lead Processing Tasks
"""

import logging
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime

from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.lead import Lead
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)


@celery_app.task(name="process_scraped_lead")
def process_scraped_lead(lead_data: dict):
    """Process a scraped lead (LinkedIn OR Carpentry/Google Maps)."""
    
    # ✅ LAZY IMPORT - only import when task actually runs
    from app.worker.tasks import generate_and_send_email_task
    
    db: Session = SessionLocal()

    try:
        email = lead_data.get('email')
        
        if not email:
            logger.warning("⚠️ No email in lead data, skipping")
            return {"success": False, "reason": "no_email"}

        # Get company name for logging
        company = lead_data.get('company') or lead_data.get('company_name', 'Unknown')
        logger.info(f"📥 Processing scraped lead: {company} ({email})")

        # Check if already exists
        existing = db.query(Lead).filter(Lead.email == email).first()

        if existing:
            logger.info(f"⚠️ Lead already exists: {email}")
            return {"success": False, "reason": "duplicate"}

        # Parse name (handle both LinkedIn and carpentry formats)
        name = lead_data.get('name', '')
        executive_name = lead_data.get('executive_name', '')
        
        # Use executive_name if available (carpentry), otherwise use name (LinkedIn)
        full_name = executive_name if executive_name else name
        
        name_parts = full_name.split() if full_name else []
        first_name = name_parts[0] if len(name_parts) > 0 else lead_data.get('first_name', '')
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else lead_data.get('last_name', '')

        # Handle carpentry-specific fields
        company_name = lead_data.get('company_name') or lead_data.get('company', '')
        
        # Create lead (compatible with both LinkedIn and Carpentry data)
        lead = Lead(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company_name,
            industry=lead_data.get('industry', 'Carpentry'),  # ✅ Default to Carpentry
            location=lead_data.get('location') or lead_data.get('address', 'USA'),
            phone=lead_data.get('phone', ''),  # ✅ Carpentry has phone
            website=lead_data.get('website', ''),  # ✅ Carpentry has website
            linkedin_url=lead_data.get('linkedin_url', ''),
            source=lead_data.get('source', 'Web Scraping'),  # ✅ Track source
            status="new",
            sequence_step=0,
            agent_enabled=True,
            priority_score=7.0
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        logger.info(f"✅ Lead created: ID={lead.id}, {company_name} ({email})")

        # Queue email generation (quick 5 second delay for scraped leads)
        task = generate_and_send_email_task.apply_async(
            args=[lead.id],
            countdown=5  # ✅ Quick delay
        )

        logger.info(f"📧 Email queued for lead {lead.id} → task {task.id}")

        return {
            "success": True,
            "lead_id": lead.id,
            "email": email,
            "company": company_name,
            "task_id": task.id
        }

    except Exception as e:
        logger.error(f"❌ Error processing lead: {str(e)}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="bulk_import_scraped_leads")
def bulk_import_scraped_leads(leads_list: list):
    """Import multiple scraped leads at once."""
    logger.info(f"📦 Bulk importing {len(leads_list)} leads...")

    results = {
        "total": len(leads_list),
        "imported": 0,
        "duplicates": 0,
        "errors": 0
    }

    for lead_data in leads_list:
        try:
            result = process_scraped_lead(lead_data)

            if result.get("success"):
                results["imported"] += 1
            elif result.get("reason") == "duplicate":
                results["duplicates"] += 1
            else:
                results["errors"] += 1

        except Exception as e:
            logger.error(f"Error in bulk import: {str(e)}")
            results["errors"] += 1

    logger.info(f"✅ Bulk import complete: {results}")
    return results
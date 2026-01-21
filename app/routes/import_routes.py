from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime

from app.database import SessionLocal
from app.models.lead import Lead

router = APIRouter(prefix="/import", tags=["Import"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_name(full_name: str) -> tuple:
    """Parse full name into first and last name."""
    if not full_name or full_name == 'N/A':
        return None, None

    parts = full_name.strip().split()
    if len(parts) == 0:
        return None, None
    elif len(parts) == 1:
        return parts[0], None
    else:
        return parts[0], ' '.join(parts[1:])


@router.post("/csv")
async def import_leads_from_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import leads from CSV file.

    Supports two formats:
    1. Advanced Autonomics: State,Name,Address,Phone,Email,Website,CEO/Owner
    2. Standard: email,first_name,last_name,company,industry,location
    """

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    contents = await file.read()
    csv_data = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_data))

    imported = 0
    skipped = 0
    errors = []
    seen_emails = set()

    print(f"\n=== STARTING CSV IMPORT ===")

    for row_num, row in enumerate(csv_reader, start=2):
        try:
            print(f"\n--- Processing Row {row_num} ---")
            print(f"Row data: {dict(row)}")

            # Try Advanced Autonomics format first
            if 'CEO/Owner' in row:
                print("Detected: Advanced Autonomics format")
                email = row.get('Email', '').strip()
                if not email or email == 'N/A' or '@' not in email:
                    print(f"SKIPPED: Invalid email '{email}'")
                    skipped += 1
                    errors.append(f"Row {row_num}: Invalid email")
                    continue

                # Check for duplicates in this batch
                if email in seen_emails:
                    print(f"SKIPPED: Duplicate in batch '{email}'")
                    skipped += 1
                    continue
                seen_emails.add(email)

                # Check if exists in database
                existing = db.query(Lead).filter(Lead.email == email).first()
                if existing:
                    print(f"SKIPPED: Already exists in DB '{email}'")
                    skipped += 1
                    continue

                ceo_name = row.get('CEO/Owner', '').strip()
                first_name, last_name = parse_name(ceo_name)

                lead = Lead(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    company=row.get('Name', '').strip() or None,
                    industry="Wood",  # ✅ CHANGED from "Glassworks"
                    location=row.get('State', '').strip() or "USA",
                    phone=row.get('Phone', '').strip() if row.get('Phone') != 'N/A' else None,
                    status="new",
                    sequence_step=0,
                    agent_enabled=True,  # ✅ ADDED
                    agent_paused=False,  # ✅ ADDED
                    priority_score=5.0,  # ✅ ADDED
                    next_agent_check_at=datetime.utcnow()  # ✅ ADDED - check immediately
                )
                print(f"SUCCESS: Created lead for '{email}'")
            else:
                # Standard format
                print("Detected: Standard format")
                email = row.get('email', '').strip()
                print(f"Extracted email: '{email}'")

                if not email or '@' not in email:
                    print(f"SKIPPED: Invalid email '{email}'")
                    skipped += 1
                    continue

                if email in seen_emails:
                    print(f"SKIPPED: Duplicate in batch '{email}'")
                    skipped += 1
                    continue
                seen_emails.add(email)
                print(f"Email passed duplicate check")

                existing = db.query(Lead).filter(Lead.email == email).first()
                print(f"Database check - existing: {existing}")

                if existing:
                    print(f"SKIPPED: Already exists in DB '{email}'")
                    skipped += 1
                    continue

                lead = Lead(
                    email=email,
                    first_name=row.get('first_name', '').strip() or None,
                    last_name=row.get('last_name', '').strip() or None,
                    company=row.get('company', '').strip() or None,
                    industry=row.get('industry', '').strip() or "Wood",  # ✅ DEFAULT to Wood
                    location=row.get('location', '').strip() or None,
                    linkedin_url=row.get('linkedin_url', '').strip() or None,
                    phone=row.get('phone', '').strip() or None,
                    status="new",
                    sequence_step=0,
                    agent_enabled=True,  # ✅ ADDED
                    agent_paused=False,  # ✅ ADDED
                    priority_score=5.0,  # ✅ ADDED
                    next_agent_check_at=datetime.utcnow()  # ✅ ADDED
                )
                print(f"SUCCESS: Created lead for '{email}'")

            db.add(lead)
            imported += 1
            print(f"Lead added to session")

        except Exception as e:
            print(f"ERROR: Exception processing row {row_num}: {str(e)}")
            skipped += 1
            errors.append(f"Row {row_num}: {str(e)}")

    print(f"\n=== COMMITTING TO DATABASE ===")
    print(f"Imported: {imported}, Skipped: {skipped}")

    try:
        db.commit()
        print("Commit successful!")
    except Exception as e:
        print(f"Commit FAILED: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "success": True,
        "imported": imported,
        "skipped": skipped,
        "total_rows": imported + skipped,
        "errors": errors[:10] if errors else None
    }


@router.get("/template")
async def get_csv_template():
    """Download a CSV template file."""
    template = """email,first_name,last_name,company,industry,location,linkedin_url,phone
john.doe@example.com,John,Doe,Example Corp,Wood,USA,https://linkedin.com/in/johndoe,+1-555-0100
jane.smith@testco.com,Jane,Smith,Test Co,Wood,USA,https://linkedin.com/in/janesmith,+1-555-0200
"""

    return {
        "template": template,
        "instructions": "Save this as a .csv file. Email is required, all other fields optional."
    }
"""
Auto-import scraped leads from JSON files into database
✅ Docker-ready version with proper error handling
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models.lead import Lead


def wait_for_database(max_retries=10):
    """Wait for database to be ready."""
    for i in range(max_retries):
        try:
            db = SessionLocal()
            # Test connection
            db.execute("SELECT 1")
            db.close()
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"⏳ Waiting for database... (attempt {i+1}/{max_retries})")
            time.sleep(2)
    
    print("❌ Database not available after retries")
    return False


def import_json_leads(json_file_path: str):
    """Import leads from a JSON file."""
    
    db = SessionLocal()
    
    try:
        # Load JSON file
        print(f"\n📂 Loading: {Path(json_file_path).name}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            leads_data = json.load(f)
        
        print(f"📊 Found {len(leads_data):,} leads in file")
        
        imported = 0
        skipped = 0
        errors = 0
        
        for lead_data in leads_data:
            try:
                email = lead_data.get('email', '').strip()
                
                # Skip if no valid email
                if not email or '@' not in email:
                    skipped += 1
                    continue
                
                # Check if already exists
                existing = db.query(Lead).filter(Lead.email == email).first()
                if existing:
                    skipped += 1
                    continue
                
                # Parse name from executive_name or company_name
                company_name = lead_data.get('company_name', '').strip()
                executive_name = lead_data.get('executive_name', '').strip()
                
                # Parse first/last name from executive_name
                name_parts = executive_name.split() if executive_name else []
                first_name = name_parts[0] if len(name_parts) > 0 else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # Create lead
                lead = Lead(
                    email=email,
                    first_name=first_name or None,
                    last_name=last_name or None,
                    company=company_name or None,
                    industry="Wood",  # Carpentry leads
                    location=lead_data.get('state', 'USA'),
                    phone=lead_data.get('phone', '').strip() or None,
                    website=lead_data.get('website', '').strip() or None,
                    source=lead_data.get('source', 'Google Maps Scraper'),
                    status="new",
                    sequence_step=0,
                    agent_enabled=True,
                    agent_paused=False,
                    priority_score=5.0,
                    next_agent_check_at=datetime.utcnow()
                )
                
                db.add(lead)
                imported += 1
                
                # Commit every 100 leads to avoid memory issues
                if imported % 100 == 0:
                    db.commit()
                    print(f"  ⚡ Progress: {imported:,}/{len(leads_data):,} ({imported/len(leads_data)*100:.1f}%)")
                
            except Exception as e:
                print(f"  ❌ Error importing {email}: {e}")
                errors += 1
                continue
        
        # Final commit
        db.commit()
        
        print(f"  ✅ File complete: {imported:,} imported, {skipped:,} skipped, {errors} errors")
        
        return imported, skipped, errors
        
    except FileNotFoundError:
        print(f"  ⚠️  File not found: {json_file_path}")
        return 0, 0, 0
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        db.rollback()
        return 0, 0, 1
        
    finally:
        db.close()


def import_all_scraped_leads():
    """Import all scraped JSON files from data folder."""
    
    data_dir = Path("/app/data")
    
    if not data_dir.exists():
        print("❌ /app/data folder not found")
        return
    
    # Find all carpentry_leads and session JSON files
    json_files = list(data_dir.glob("carpentry_leads_*.json")) + \
                 list(data_dir.glob("session_*.json"))
    
    if not json_files:
        print("ℹ️  No JSON files found in /app/data folder")
        print("   This is normal if you haven't run the scraper yet.")
        return
    
    print("=" * 70)
    print("🤖 AUTO-IMPORT SCRAPED LEADS")
    print("=" * 70)
    print(f"Found {len(json_files)} JSON files to process")
    
    # Calculate total leads
    total_leads_in_files = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_leads_in_files += len(data)
        except:
            pass
    
    print(f"Total leads across all files: {total_leads_in_files:,}")
    print(f"⚠️  Large import detected - this may take 5-10 minutes...")
    print()
    
    total_imported = 0
    total_skipped = 0
    total_errors = 0
    
    start_time = time.time()
    
    for json_file in sorted(json_files):
        imported, skipped, errors = import_json_leads(str(json_file))
        total_imported += imported
        total_skipped += skipped
        total_errors += errors
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"✅ Total imported: {total_imported:,}")
    print(f"⏭️  Total skipped (duplicates/invalid): {total_skipped:,}")
    print(f"❌ Total errors: {total_errors}")
    print(f"📁 Files processed: {len(json_files)}")
    print(f"⏱️  Time taken: {elapsed/60:.1f} minutes")
    print(f"⚡ Speed: {total_imported/(elapsed/60):.0f} leads/minute")
    
    if total_imported > 0:
        print()
        print("🎯 Next steps:")
        print("  1. Start the agent: POST http://localhost:8000/agent/start")
        print("  2. Or visit: http://localhost:8000/docs")
        print("  3. Agent will automatically email these leads")
    
    print("=" * 70)


def main():
    """Main entry point."""
    try:
        print("🚀 Auto-Import Service Starting...")
        print()
        
        # Wait for database
        if not wait_for_database():
            print("❌ Could not connect to database. Exiting.")
            sys.exit(1)
        
        # Import leads
        import_all_scraped_leads()
        
        print()
        print("✅ Auto-import service completed successfully")
        
    except KeyboardInterrupt:
        print("\n⚠️  Auto-import interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error in auto-import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
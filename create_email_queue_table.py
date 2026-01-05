#!/usr/bin/env python3
"""
Create email_queue table for task persistence
Run this once to add the new table
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def create_email_queue_table():
    """Add email_queue table to existing database."""
    
    db_path = Path("data/app.db")
    
    print("📄 Creating email_queue table...")
    print(f"📍 Database location: {db_path}")
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Create email_queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                html_body TEXT,
                task_id TEXT,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                last_error TEXT,
                scheduled_at TEXT NOT NULL,
                sent_at TEXT,
                failed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)
        print("  ✅ Table created/verified")
        
        # Create indexes
        indexes = [
            ("idx_email_queue_lead", "email_queue", "lead_id"),
            ("idx_email_queue_status", "email_queue", "status"),
            ("idx_email_queue_task", "email_queue", "task_id"),
            ("idx_email_queue_scheduled", "email_queue", "scheduled_at"),
        ]
        
        for idx_name, table_name, col_name in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col_name})")
                print(f"  ✅ Index created: {idx_name}")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e).lower():
                    print(f"  ⭐ Index already exists: {idx_name}")
                else:
                    raise
        
        # Commit all changes
        conn.commit()
        
        print("\n✅ email_queue table created successfully!")
        print("\n" + "="*60)
        print("Verification Commands:")
        print("="*60)
        print("\n1. Check table structure:")
        print('   sqlite3 data/app.db "PRAGMA table_info(email_queue);"')
        print("\n2. Check indexes:")
        print('   sqlite3 data/app.db "SELECT name FROM sqlite_master WHERE type=\'index\' AND tbl_name=\'email_queue\';"')
        print("\n3. Count queue entries:")
        print('   sqlite3 data/app.db "SELECT status, COUNT(*) FROM email_queue GROUP BY status;"')
        print("="*60)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = create_email_queue_table()
    exit(0 if success else 1)
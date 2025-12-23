#!/usr/bin/env python3
"""
Database Migration Runner - Fixed for action_metadata column
Run this to add agent fields to existing database
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def run_migration():
    """Run database migration with fixed column names."""
    
    db_path = Path("data/app.db")
    
    print("🔄 Starting database migration...")
    print(f"📁 Database location: {db_path}")
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # ============================================
        # 1. ADD COLUMNS TO LEADS TABLE
        # ============================================
        print("📝 Adding new columns to leads table...")
        
        lead_columns = {
            "agent_enabled": "INTEGER DEFAULT 1 NOT NULL",
            "agent_paused": "INTEGER DEFAULT 0 NOT NULL",
            "next_agent_check_at": "TEXT",
            "last_agent_action_at": "TEXT",
            "follow_up_count": "INTEGER DEFAULT 0 NOT NULL",
            "max_follow_ups": "INTEGER DEFAULT 3 NOT NULL",
            "days_between_followups": "INTEGER DEFAULT 3 NOT NULL",
            "priority_score": "REAL DEFAULT 5.0 NOT NULL",
            "engagement_score": "REAL DEFAULT 0.0 NOT NULL",
            "bounce_count": "INTEGER DEFAULT 0 NOT NULL",
            "error_count": "INTEGER DEFAULT 0 NOT NULL",
            "last_error_message": "TEXT",
            "agent_notes": "TEXT"
        }
        
        for col_name, col_type in lead_columns.items():
            try:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
                print(f"  ✓ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print(f"  ⏭️  Column already exists: {col_name}")
                else:
                    raise
        
        # ============================================
        # 2. CREATE AGENT_CONFIG TABLE
        # ============================================
        print("📝 Creating agent_config table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_config (
                id INTEGER PRIMARY KEY,
                is_running INTEGER DEFAULT 0 NOT NULL,
                is_paused INTEGER DEFAULT 0 NOT NULL,
                max_emails_per_day INTEGER DEFAULT 50 NOT NULL,
                max_emails_per_hour INTEGER DEFAULT 10 NOT NULL,
                emails_sent_today INTEGER DEFAULT 0 NOT NULL,
                emails_sent_this_hour INTEGER DEFAULT 0 NOT NULL,
                last_reset_date TEXT NOT NULL,
                last_run_at TEXT,
                next_run_at TEXT,
                business_hours_start TEXT DEFAULT '09:00' NOT NULL,
                business_hours_end TEXT DEFAULT '17:00' NOT NULL,
                timezone TEXT DEFAULT 'America/New_York' NOT NULL,
                min_delay_seconds INTEGER DEFAULT 300 NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """)
        print("  ✓ Table created/verified")
        
        # Insert default config if not exists
        cursor.execute("SELECT COUNT(*) FROM agent_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO agent_config (
                    is_running, is_paused, max_emails_per_day, max_emails_per_hour,
                    emails_sent_today, emails_sent_this_hour, last_reset_date,
                    business_hours_start, business_hours_end, timezone, min_delay_seconds
                ) VALUES (0, 0, 50, 10, 0, 0, ?, '09:00', '17:00', 'America/New_York', 300)
            """, (datetime.now().date().isoformat(),))
            print("  ✓ Default config inserted")
        else:
            print("  ⏭️  Config already exists")
        
        # ============================================
        # 3. CREATE AGENT_ACTION_LOGS TABLE (FIXED)
        # ============================================
        print("📝 Creating agent_action_logs table...")
        
        # Drop old table if it has wrong column name
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='agent_action_logs'
        """)
        if cursor.fetchone():
            # Check if it has the wrong column
            cursor.execute("PRAGMA table_info(agent_action_logs)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'metadata' in columns and 'action_metadata' not in columns:
                print("  🔧 Dropping old table with incorrect column name...")
                cursor.execute("DROP TABLE agent_action_logs")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                action_result TEXT NOT NULL,
                lead_id INTEGER,
                lead_email TEXT,
                decision_reason TEXT,
                action_metadata TEXT,
                error_message TEXT,
                execution_time_ms INTEGER,
                agent_run_id TEXT,
                emails_sent_before INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)
        print("  ✓ Table created/verified")
        
        # ============================================
        # 4. CREATE INDEXES
        # ============================================
        print("📝 Creating indexes...")
        
        indexes = [
            ("idx_leads_agent_enabled", "leads", "agent_enabled"),
            ("idx_leads_next_check", "leads", "next_agent_check_at"),
            ("idx_leads_status", "leads", "status"),
            ("idx_action_logs_type", "agent_action_logs", "action_type"),
            ("idx_action_logs_timestamp", "agent_action_logs", "timestamp"),
            ("idx_action_logs_lead", "agent_action_logs", "lead_id"),
            ("idx_action_logs_run_id", "agent_action_logs", "agent_run_id")
        ]
        
        for idx_name, table_name, col_name in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({col_name})")
                print(f"  ✓ Index created: {idx_name}")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e).lower():
                    print(f"  ⏭️  Index already exists: {idx_name}")
                else:
                    raise
        
        # Commit all changes
        conn.commit()
        
        print("\n✅ Migration completed successfully!")
        print("\n" + "="*60)
        print("Verification Commands:")
        print("="*60)
        print("\n1. Check tables:")
        print("   sqlite3 data/app.db \"SELECT name FROM sqlite_master WHERE type='table';\"")
        print("\n2. Check agent config:")
        print("   sqlite3 data/app.db \"SELECT * FROM agent_config;\"")
        print("\n3. Check lead columns:")
        print("   sqlite3 data/app.db \"PRAGMA table_info(leads);\"")
        print("\n4. Check action_logs columns:")
        print("   sqlite3 data/app.db \"PRAGMA table_info(agent_action_logs);\"")
        print("\n5. Start system:")
        print("   docker-compose up -d")
        print("\n6. Check agent status:")
        print("   curl http://localhost:8000/agent/status")
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
    success = run_migration()
    sys.exit(0 if success else 1)
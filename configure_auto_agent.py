#!/usr/bin/env python3
"""
Configure Agent for Fully Autonomous Operation
Enables automatic email sending without manual intervention
"""

from app.database import SessionLocal
from app.models.agent_config import AgentConfig
from datetime import datetime

def configure_autonomous_mode():
    """Set agent to fully autonomous mode."""
    
    db = SessionLocal()
    
    try:
        config = db.query(AgentConfig).first()
        
        if not config:
            print("❌ Agent config not found. Creating...")
            config = AgentConfig(
                is_running=True,
                is_paused=False,
                daily_email_limit=2000,
                hourly_email_limit=60,
                last_reset_date=datetime.utcnow().strftime("%Y-%m-%d"),
                agent_started_at=datetime.utcnow()
            )
            db.add(config)
        else:
            # Enable autonomous operation
            config.is_running = True
            config.is_paused = False
            config.agent_started_at = datetime.utcnow()
            config.next_agent_run_at = datetime.utcnow()  # Run immediately
        
        db.commit()
        
        print("✅ AUTONOMOUS MODE ENABLED!")
        print("")
        print("📊 Configuration:")
        print(f"   Status: {'🟢 RUNNING' if config.is_running else '🔴 STOPPED'}")
        print(f"   Auto-Pause: {'❌ NO' if not config.is_paused else '⏸️ YES'}")
        print(f"   Daily Limit: {config.daily_email_limit} emails")
        print(f"   Hourly Limit: {config.hourly_email_limit} emails")
        print("")
        print("🤖 Agent will now:")
        print("   ✅ Run automatically every 5 minutes")
        print("   ✅ Process leads without manual trigger")
        print("   ✅ Send emails during business hours")
        print("   ✅ Fetch replies every 15 minutes")
        print("   ✅ Continue 24/7 until stopped")
        print("")
        print("⏰ Next automatic cycle: ~5 minutes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CONFIGURING AUTONOMOUS AGENT MODE")
    print("=" * 60)
    print("")
    
    success = configure_autonomous_mode()
    
    if success:
        print("=" * 60)
        print("✅ CONFIGURATION COMPLETE")
        print("=" * 60)
        print("")
        print("Next steps:")
        print("1. Check beat logs: docker-compose logs -f beat")
        print("2. Watch for: 'Scheduler: Sending due task agent-cycle'")
        print("3. Monitor dashboard: http://localhost:8000")
        print("")
        print("⚠️  DO NOT click 'Run Now' - it will run automatically!")
    
    exit(0 if success else 1)
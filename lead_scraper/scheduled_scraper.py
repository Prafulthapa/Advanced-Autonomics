"""
Scheduled Lead Scraper Runner
Runs carpentry lead scraping at 2 AM daily (configurable)
Keeps container alive 24/7
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from lead_orchestrator import LeadOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScheduledScraper:
    """Run lead scraper on a daily schedule."""
    
    def __init__(self, run_hour=2):
        """
        Args:
            run_hour: Hour to run (0-23). Default: 2 AM
        """
        self.run_hour = run_hour
        self.last_run_date = None
        self.check_interval = 300  # Check every 5 minutes
        
        logger.info("=" * 70)
        logger.info("🤖 SCHEDULED LEAD SCRAPER INITIALIZED")
        logger.info(f"⏰ Scheduled to run daily at {self.run_hour}:00")
        logger.info(f"🔄 Check interval: {self.check_interval} seconds")
        logger.info("=" * 70)
    
    def should_run_now(self):
        """Check if scraper should run now."""
        now = datetime.now()
        
        # Check if it's the right hour (and within first 5 minutes)
        if now.hour != self.run_hour:
            return False
        
        if now.minute > 5:  # Only run in first 5 minutes of the hour
            return False
        
        # Check if already ran today
        today = now.date()
        if self.last_run_date == today:
            return False
        
        return True
    
    async def run_scraper(self):
        """Run the lead scraper."""
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"⏰ SCHEDULED RUN STARTING - {datetime.now()}")
        logger.info("=" * 70)
        
        try:
            orchestrator = LeadOrchestrator()
            await orchestrator.run_pipeline()
            
            # Mark as completed today
            self.last_run_date = datetime.now().date()
            
            logger.info("=" * 70)
            logger.info(f"✅ SCHEDULED RUN COMPLETE - {datetime.now()}")
            logger.info(f"📅 Next run: Tomorrow at {self.run_hour}:00")
            logger.info("=" * 70)
            logger.info("")
            
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ SCHEDULED RUN FAILED - {datetime.now()}")
            logger.error(f"Error: {e}", exc_info=True)
            logger.error("=" * 70)
    
    def get_time_until_next_run(self):
        """Calculate time until next scheduled run."""
        now = datetime.now()
        
        # If already ran today, next run is tomorrow
        if self.last_run_date == now.date():
            # Calculate tomorrow at run_hour
            tomorrow = now.date().replace(day=now.day + 1)
            next_run = datetime.combine(tomorrow, datetime.min.time().replace(hour=self.run_hour))
        else:
            # Next run is today at run_hour (if not passed) or tomorrow
            today_run = datetime.combine(now.date(), datetime.min.time().replace(hour=self.run_hour))
            
            if now < today_run:
                next_run = today_run
            else:
                tomorrow = now.date().replace(day=now.day + 1)
                next_run = datetime.combine(tomorrow, datetime.min.time().replace(hour=self.run_hour))
        
        delta = next_run - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        return f"{delta.days}d {hours}h {minutes}m"
    
    async def run_forever(self):
        """Keep container alive and run on schedule."""
        logger.info("🚀 Scheduler started - container will stay alive")
        logger.info(f"⏳ Next run: {self.get_time_until_next_run()}")
        logger.info("")
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                
                # Check if should run
                if self.should_run_now():
                    await self.run_scraper()
                else:
                    # Log status every 12 checks (1 hour)
                    if iteration % 12 == 0:
                        logger.info(f"💤 Status check: Waiting for scheduled run")
                        logger.info(f"   Next run: {self.get_time_until_next_run()}")
                
                # Sleep until next check
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("⚠️ Shutdown signal received")
                logger.info("👋 Stopping scheduled scraper...")
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                logger.error("⏳ Retrying in 1 minute...")
                await asyncio.sleep(60)


async def main():
    """Main entry point."""
    
    # Get configuration from environment
    run_hour = int(os.getenv("SCRAPER_RUN_HOUR", "2"))
    
    # Validate hour
    if not 0 <= run_hour <= 23:
        logger.error(f"❌ Invalid SCRAPER_RUN_HOUR: {run_hour} (must be 0-23)")
        logger.info("ℹ️  Using default: 2 AM")
        run_hour = 2
    
    # Create and run scheduler
    scheduler = ScheduledScraper(run_hour=run_hour)
    
    try:
        await scheduler.run_forever()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        logger.error("Container will restart...")


if __name__ == "__main__":
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Run the scheduler
    asyncio.run(main())
"""
Continuous Carpentry Lead Scraper
Keeps scraping 24/7 - perfect for server deployment
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from lead_orchestrator import LeadOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContinuousScraper:
    """Run scraper continuously with intelligent restart logic."""

    def __init__(self):
        self.min_delay_between_runs = 300  # 5 minutes between full cycles
        self.max_retries = 3
        self.retry_delay = 60  # 1 minute delay after failure

    async def run_forever(self):
        """Keep scraper running 24/7."""
        logger.info("=" * 70)
        logger.info("🚀 CONTINUOUS CARPENTRY LEAD SCRAPER")
        logger.info("=" * 70)
        logger.info("🌐 Running in continuous mode (24/7)")
        logger.info("⚙️  Auto-push to email queue: ENABLED")
        logger.info("♻️  Will restart automatically after completion")
        logger.info("=" * 70)
        logger.info("")

        run_number = 0
        consecutive_failures = 0

        while True:
            run_number += 1
            start_time = time.time()

            logger.info("")
            logger.info("=" * 70)
            logger.info(f"🔄 SCRAPER RUN #{run_number}")
            logger.info(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 70)

            try:
                # Run the scraper
                orchestrator = LeadOrchestrator()
                await orchestrator.run_pipeline()

                # Success - reset failure counter
                consecutive_failures = 0

                # Calculate runtime
                runtime = time.time() - start_time
                hours = int(runtime // 3600)
                minutes = int((runtime % 3600) // 60)

                logger.info("")
                logger.info("=" * 70)
                logger.info(f"✅ SCRAPER RUN #{run_number} COMPLETE")
                logger.info(f"⏱️  Runtime: {hours}h {minutes}m")
                logger.info("=" * 70)

                # Check if all searches are done
                progress_file = Path("data/scraper_progress.json")
                if progress_file.exists():
                    import json
                    with open(progress_file, 'r') as f:
                        progress = json.load(f)
                    
                    completed = len(progress.get('completed_searches', []))
                    total = 1729
                    
                    if completed >= total:
                        logger.info("")
                        logger.info("=" * 70)
                        logger.info("🎉 ALL SEARCHES COMPLETED!")
                        logger.info(f"✅ Completed {completed}/{total} searches")
                        logger.info("🔄 Will check for new searches in 1 hour...")
                        logger.info("=" * 70)
                        
                        # Wait 1 hour before checking again
                        await asyncio.sleep(3600)
                        continue

                # Wait before next run
                logger.info(f"⏳ Waiting {self.min_delay_between_runs}s before next run...")
                await asyncio.sleep(self.min_delay_between_runs)

            except KeyboardInterrupt:
                logger.info("")
                logger.info("=" * 70)
                logger.info("⚠️  SHUTDOWN SIGNAL RECEIVED")
                logger.info("=" * 70)
                logger.info("👋 Stopping continuous scraper...")
                break

            except Exception as e:
                consecutive_failures += 1

                logger.error("")
                logger.error("=" * 70)
                logger.error(f"❌ SCRAPER RUN #{run_number} FAILED")
                logger.error(f"Error: {e}")
                logger.error(f"Consecutive failures: {consecutive_failures}/{self.max_retries}")
                logger.error("=" * 70)

                if consecutive_failures >= self.max_retries:
                    logger.error("")
                    logger.error("=" * 70)
                    logger.error("🛑 MAX RETRIES REACHED")
                    logger.error("Stopping continuous scraper")
                    logger.error("Please check logs and fix issues")
                    logger.error("=" * 70)
                    break

                # Wait before retry
                wait_time = self.retry_delay * consecutive_failures
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

        logger.info("")
        logger.info("=" * 70)
        logger.info("🛑 CONTINUOUS SCRAPER STOPPED")
        logger.info("=" * 70)


async def main():
    """Main entry point."""
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Create and run continuous scraper
    scraper = ContinuousScraper()
    
    try:
        await scraper.run_forever()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        logger.error("Container will restart...")


if __name__ == "__main__":
    asyncio.run(main())
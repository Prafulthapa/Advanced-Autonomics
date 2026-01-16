"""
Lead Orchestrator - CARPENTRY VERSION
NO LinkedIn - Uses Yellow Pages, True Local, Google Maps
Pushes leads directly to email queue
"""

import asyncio
import logging
import json
import requests
from datetime import datetime
from pathlib import Path

# Import the NEW carpentry scraper (not LinkedIn!)
from carpentry_lead_scraper import CarpentryLeadScraper
from celery_bridge import push_leads_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_BASE = "http://api:8000"


class LeadOrchestrator:
    """Orchestrate carpentry lead generation pipeline."""

    def __init__(self):
        self.scraper = CarpentryLeadScraper()
        self.all_leads = []

    async def run_pipeline(self):
        """Run the complete pipeline."""
        logger.info("=" * 70)
        logger.info("🚀 CARPENTRY LEAD PIPELINE STARTING")
        logger.info("=" * 70)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Step 1: Scrape carpentry businesses
        logger.info("=" * 70)
        logger.info("STEP 1: SCRAPING CARPENTRY BUSINESSES")
        logger.info("=" * 70)

        try:
            self.scraper.run_full_scrape()
            self.all_leads = self.scraper.all_leads
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}", exc_info=True)
            return

        logger.info(f"✅ Step 1 complete: {len(self.all_leads)} leads scraped")

        if not self.all_leads:
            logger.warning("⚠️ No leads scraped, pipeline stopping")
            return

        # Step 2: Push to email queue
        logger.info("=" * 70)
        logger.info("STEP 2: PUSH TO EMAIL QUEUE - PAUSED")
        logger.info("=" * 70)

        # Filter leads with emails
        leads_with_email = [
            lead for lead in self.all_leads
            if lead.get('email') and '@' in lead.get('email', '')
        ]

        logger.info(f"📧 Leads with valid emails: {len(leads_with_email)}")

        if leads_with_email:
            queued = push_leads_batch(leads_with_email)
            logger.info(f"✅ Step 2 complete: {queued} leads queued for emailing")
        else:
            logger.warning("⚠️ No leads with emails to queue")
            queued = 0

        # Step 3: Save backup
        logger.info("=" * 70)
        logger.info("STEP 3: SAVE BACKUP")
        logger.info("=" * 70)

        backup_file = f"data/carpentry_leads_{timestamp}.json"
        self.save_backup(self.all_leads, backup_file)

        # Print summary
        self.print_summary(queued)

    def save_backup(self, leads, filename):
        """Save leads to JSON backup."""
        logger.info(f"💾 Saving backup to: {filename}")

        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Saved {len(leads)} leads to backup")

    def print_summary(self, queued_count):
        """Print pipeline summary."""
        logger.info("\n" + "=" * 70)
        logger.info("📊 PIPELINE SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total leads scraped:  {len(self.all_leads)}")
        logger.info(f"Queued for emailing:  {queued_count}")
        
        # Source breakdown
        sources = {}
        for lead in self.all_leads:
            source = lead.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        logger.info("\n📍 Sources:")
        for source, count in sources.items():
            logger.info(f"  - {source}: {count}")
        
        logger.info("=" * 70)


async def main():
    """Main execution."""
    orchestrator = LeadOrchestrator()
    await orchestrator.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
"""
Lead Orchestrator - Master script that runs everything
UPDATED: Now pushes leads directly to email queue
"""

import asyncio
import logging
import json
import csv
import requests
from datetime import datetime
from pathlib import Path

from linkedin_scraper import LinkedInScraper
from lead_enricher import LeadEnricher
from email_finder import EmailFinder
from celery_bridge import push_leads_batch, push_lead_to_email_queue  # NEW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://api:8000"


class LeadOrchestrator:
    """Orchestrate the complete lead generation pipeline."""
    
    def __init__(self):
        self.scraper = LinkedInScraper()
        self.enricher = LeadEnricher()
        self.email_finder = EmailFinder()
        
        self.raw_leads = []
        self.enriched_leads = []
        self.leads_with_emails = []
        
    async def run_pipeline(self):
        """Run the complete pipeline."""
        logger.info("🚀 Starting lead generation pipeline...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Step 1: Scrape LinkedIn
        logger.info("=" * 60)
        logger.info("STEP 1: LINKEDIN SCRAPING")
        logger.info("=" * 60)
        
        self.scraper.setup_driver()
        
        if not self.scraper.login():
            logger.error("❌ LinkedIn login failed, aborting")
            return
        
        self.raw_leads = self.scraper.run_all_searches()
        self.scraper.cleanup()
        
        logger.info(f"✅ Step 1 complete: {len(self.raw_leads)} raw leads")
        
        if not self.raw_leads:
            logger.warning("⚠️ No leads scraped, pipeline stopping")
            return
        
        # Step 2: Enrich with AI
        logger.info("=" * 60)
        logger.info("STEP 2: AI ENRICHMENT")
        logger.info("=" * 60)
        
        self.enriched_leads = await self.enricher.enrich_all_leads(self.raw_leads)
        
        logger.info(f"✅ Step 2 complete: {len(self.enriched_leads)} enriched leads")
        
        # Step 3: Find emails
        logger.info("=" * 60)
        logger.info("STEP 3: EMAIL FINDING")
        logger.info("=" * 60)
        
        for lead in self.enriched_leads:
            email, method = self.email_finder.find_email(lead)
            
            if email:
                lead['email'] = email
                lead['email_method'] = method
                self.leads_with_emails.append(lead)
        
        logger.info(f"✅ Step 3 complete: {len(self.leads_with_emails)} leads with emails")
        
        # Step 4: Push to email queue (NEW!)
        logger.info("=" * 60)
        logger.info("STEP 4: PUSH TO EMAIL QUEUE")
        logger.info("=" * 60)
        
        queued = push_leads_batch(self.leads_with_emails)
        
        logger.info(f"✅ Step 4 complete: {queued} leads queued for emailing")
        
        # Step 5: Save backup CSV
        logger.info("=" * 60)
        logger.info("STEP 5: SAVE BACKUP")
        logger.info("=" * 60)
        
        csv_file = f"data/leads_{timestamp}.csv"
        self.save_to_csv(self.leads_with_emails, csv_file)
        
        # Print summary
        self.print_summary(queued)
    
    def save_to_csv(self, leads, filename):
        """Save leads to CSV backup."""
        logger.info(f"💾 Saving backup to: {filename}")
        
        Path("data").mkdir(exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if not leads:
                return
            
            fieldnames = [
                'email', 'first_name', 'last_name', 'company', 
                'industry', 'location', 'title'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for lead in leads:
                row = {
                    'email': lead.get('email', ''),
                    'first_name': lead.get('first_name', lead.get('name', '').split()[0] if lead.get('name') else ''),
                    'last_name': lead.get('last_name', lead.get('name', '').split()[-1] if lead.get('name') and len(lead.get('name', '').split()) > 1 else ''),
                    'company': lead.get('clean_company_name', lead.get('company', '')),
                    'industry': lead.get('industry', 'Robotics/Automation'),
                    'location': lead.get('location', 'Australia'),
                    'title': lead.get('title', '')
                }
                writer.writerow(row)
        
        logger.info(f"✅ Saved {len(leads)} leads to CSV backup")
    
    def print_summary(self, queued_count):
        """Print pipeline summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 PIPELINE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Raw leads scraped:    {len(self.raw_leads)}")
        logger.info(f"Leads enriched:       {len(self.enriched_leads)}")
        logger.info(f"Emails found:         {len(self.leads_with_emails)}")
        logger.info(f"Queued for emailing:  {queued_count}")
        if self.raw_leads:
            success_rate = len(self.leads_with_emails) / len(self.raw_leads) * 100
            logger.info(f"Success rate:         {success_rate:.1f}%")
        logger.info("=" * 60)


async def main():
    """Main execution."""
    orchestrator = LeadOrchestrator()
    await orchestrator.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
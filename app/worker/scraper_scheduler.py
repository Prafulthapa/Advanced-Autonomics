"""
Scraper Scheduler Task
Triggers scraper container via docker exec
"""

import logging
import subprocess
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_linkedin_scraper")
def run_linkedin_scraper():
    """
    Trigger LinkedIn scraper in lead-scraper container.
    Called by Celery Beat every 6 hours.
    """
    logger.info("🕷️ Starting scheduled LinkedIn scraping...")

    try:
        # Run scraper in lead-scraper container
        result = subprocess.run(
            [
                "docker", "exec", "lead-scraper",
                "python", "lead_scraper/lead_orchestrator.py"
            ],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode == 0:
            logger.info("✅ Scraper completed successfully")
            logger.info(f"Output: {result.stdout[-500:]}")
            return {"success": True, "output": result.stdout[-500:]}
        else:
            logger.error(f"❌ Scraper failed with code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            return {"success": False, "error": result.stderr}

    except subprocess.TimeoutExpired:
        logger.error("❌ Scraper timeout (1 hour)")
        return {"success": False, "error": "timeout"}

    except Exception as e:
        logger.error(f"❌ Scraper error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}
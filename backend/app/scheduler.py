"""
Scheduler for daily price scraping and ingestion
Uses APScheduler to check DA website every day and ingest data
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import os

from scraper import DAPriceScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceScheduler:
    """Manages scheduled scraping and ingestion of DA price index"""
    
    def __init__(self, ingestion_pipeline=None):
        """
        Initialize scheduler and scraper
        
        Args:
            ingestion_pipeline: Optional IngestionPipeline instance for automatic ingestion
        """
        self.scheduler = BackgroundScheduler()
        self.scraper = DAPriceScraper()
        self.ingestion_pipeline = ingestion_pipeline
        self.last_run = None
        self.last_result = None
    
    def scrape_and_ingest_job(self):
        """Job function that runs the scraper and optionally ingests data"""
        logger.info("Starting scheduled scrape and ingest job...")
        try:
            # Step 1: Scrape latest PDF
            scrape_result = self.scraper.get_latest_daily_price_index()
            self.last_run = datetime.now()
            self.last_result = scrape_result
            
            if scrape_result.get("success"):
                logger.info(f"✓ Successfully scraped: {scrape_result.get('date')}")
                
                # Step 2: Automatically ingest if pipeline is configured
                if self.ingestion_pipeline:
                    logger.info("Starting automatic ingestion...")
                    try:
                        ingest_result = self.ingestion_pipeline.ingest_latest_pdf(
                            replace_if_exists=False  # Don't replace existing data
                        )
                        
                        if ingest_result.get('success'):
                            logger.info(f"✓ Ingestion successful: {ingest_result.get('entries_stored')} entries")
                            self.last_result['ingestion'] = ingest_result
                        elif 'already exists' in ingest_result.get('error', ''):
                            logger.info(f"ℹ Data already exists for {ingest_result.get('date')}, skipping ingestion")
                            self.last_result['ingestion'] = {"skipped": True, "reason": "already exists"}
                        else:
                            logger.error(f"✗ Ingestion failed: {ingest_result.get('error')}")
                            self.last_result['ingestion'] = {"error": ingest_result.get('error')}
                            
                    except Exception as e:
                        logger.error(f"✗ Ingestion error: {e}")
                        self.last_result['ingestion'] = {"error": str(e)}
                else:
                    logger.info("No ingestion pipeline configured, skipping ingestion")
            else:
                logger.error(f"✗ Scrape failed: {scrape_result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error in scrape job: {e}")
            self.last_result = {"success": False, "error": str(e)}
    
    def set_ingestion_pipeline(self, ingestion_pipeline):
        """
        Set the ingestion pipeline for automatic ingestion
        
        Args:
            ingestion_pipeline: IngestionPipeline instance
        """
        self.ingestion_pipeline = ingestion_pipeline
        logger.info("✓ Ingestion pipeline configured for automatic ingestion")
    
    def start(self, hour=8, minute=0):
        """
        Start the scheduler to run daily at specified time
        Default: 8:00 AM every day
        
        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        # Add job to run daily at specified time
        self.scheduler.add_job(
            self.scrape_and_ingest_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_price_scrape_ingest',
            name='Daily Price Index Scraper + Ingestion',
            replace_existing=True
        )
        
        self.scheduler.start()
        ingest_status = "with ingestion" if self.ingestion_pipeline else "scraping only"
        logger.info(f"✓ Scheduler started ({ingest_status}) - will run daily at {hour:02d}:{minute:02d}")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def run_now(self):
        """Manually trigger the scrape and ingest job immediately"""
        logger.info("Manual scrape triggered")
        self.scrape_and_ingest_job()
        return self.last_result
    
    def get_status(self):
        """Get scheduler status and last run info"""
        jobs = self.scheduler.get_jobs()
        
        return {
            "running": self.scheduler.running,
            "jobs": len(jobs),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
            "next_run": jobs[0].next_run_time.isoformat() if jobs else None
        }


# Global scheduler instance
scheduler = PriceScheduler()


if __name__ == "__main__":
    # Test the scheduler
    import time
    
    print("Starting scheduler test...")
    scheduler.start(hour=8, minute=0)
    
    print("Scheduler is running. Status:")
    print(scheduler.get_status())
    
    print("\nRunning manual scrape now...")
    result = scheduler.run_now()
    print(f"Result: {result}")
    
    print("\nScheduler will continue running. Press Ctrl+C to stop...")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Done!")

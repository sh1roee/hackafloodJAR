"""
Scheduler for daily price scraping
Uses APScheduler to check DA website every day
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from scraper import DAPriceScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PriceScheduler:
    """Manages scheduled scraping of DA price index"""
    
    def __init__(self):
        """Initialize scheduler and scraper"""
        self.scheduler = BackgroundScheduler()
        self.scraper = DAPriceScraper()
        self.last_run = None
        self.last_result = None
    
    def scrape_job(self):
        """Job function that runs the scraper"""
        logger.info("Starting scheduled scrape job...")
        try:
            result = self.scraper.get_latest_daily_price_index()
            self.last_run = datetime.now()
            self.last_result = result
            
            if result.get("success"):
                logger.info(f"✓ Successfully scraped: {result.get('date')}")
            else:
                logger.error(f"✗ Scrape failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error in scrape job: {e}")
            self.last_result = {"success": False, "error": str(e)}
    
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
            self.scrape_job,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_price_scrape',
            name='Daily Price Index Scraper',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"✓ Scheduler started - will run daily at {hour:02d}:{minute:02d}")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def run_now(self):
        """Manually trigger the scrape job immediately"""
        logger.info("Manual scrape triggered")
        self.scrape_job()
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

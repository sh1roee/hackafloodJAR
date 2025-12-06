from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
import os

from app.scraper import DAPriceScraper
from app.scheduler import scheduler
from app.pdf_parser import PricePDFParser

# Load environment variables
load_dotenv()

app = FastAPI(title="DA Price Monitor for Farmers")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper
scraper = DAPriceScraper()
parser = PricePDFParser()


@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the app starts"""
    # Schedule daily scraping at 8:00 AM
    scheduler.start(hour=8, minute=0)
    print("✓ Daily scheduler started - will check DA website every day at 8:00 AM")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler when the app shuts down"""
    scheduler.stop()
    print("✓ Scheduler stopped")


@app.get("/")
def root():
    return {
        "message": "DA Price Monitor API",
        "description": "SMS-based price checking for farmers in NCR",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/scrape-latest")
def scrape_latest_price_index():
    """
    Manually trigger scraping of the latest daily price index
    Returns download information
    """
    result = scraper.get_latest_daily_price_index()
    return result


@app.get("/scheduler/status")
def get_scheduler_status():
    """
    Get the status of the daily scheduler
    """
    return scheduler.get_status()


@app.post("/scheduler/run-now")
def run_scheduler_now():
    """
    Manually trigger the scheduled scrape job immediately
    """
    result = scheduler.run_now()
    return result


@app.get("/download-info")
def get_download_info():
    """
    Get information about downloaded files
    """
    download_dir = scraper.DOWNLOAD_DIR
    
    if not download_dir.exists():
        return {"files": [], "count": 0}
    
    files = []
    for pdf_file in download_dir.glob("*.pdf"):
        stat = pdf_file.stat()
        files.append({
            "filename": pdf_file.name,
            "size_kb": stat.st_size / 1024,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    # Sort by modification time, newest first
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    return {
        "files": files,
        "count": len(files),
        "directory": str(download_dir)
    }


@app.get("/parse-latest")
def parse_latest_pdf():
    """
    Parse the latest downloaded PDF and return price data as tables
    """
    tables = parser.parse_latest_pdf(show_text=False)
    
    if not tables:
        return {
            "success": False,
            "error": "No tables found in PDF"
        }
    
    # Convert DataFrames to JSON-serializable format
    result_tables = []
    for i, df in enumerate(tables):
        # Clean up the dataframe
        df_clean = df.copy()
        
        # Remove None columns
        df_clean = df_clean.loc[:, df_clean.columns.notna()]
        
        # Convert to dict
        table_data = {
            "table_number": i + 1,
            "page": df.attrs.get('page', None),
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "columns": list(df_clean.columns),
            "data": df_clean.to_dict('records')
        }
        
        result_tables.append(table_data)
    
    return {
        "success": True,
        "total_tables": len(tables),
        "tables": result_tables
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

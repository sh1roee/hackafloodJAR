from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
import os

from scraper import DAPriceScraper
from scheduler import scheduler
from pdf_parser import PricePDFParser

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMADB_API_KEY = os.getenv("CHROMADB_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required in environment")
if not CHROMADB_API_KEY:
    raise RuntimeError("CHROMADB_API_KEY is required in environment")

app = FastAPI(title="DA Price Monitor for Farmers - RAG System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
scraper = DAPriceScraper()
parser = PricePDFParser()

# Initialize RAG components
ingestion_pipeline = IngestionPipeline(
    openai_api_key=OPENAI_API_KEY,
    chromadb_api_key=CHROMADB_API_KEY
)

query_engine = QueryEngine(
    openai_api_key=OPENAI_API_KEY,
    chromadb_api_key=CHROMADB_API_KEY
)


# Request models
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class SMSQueryRequest(BaseModel):
    phone: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the app starts"""
    # Configure scheduler with ingestion pipeline
    scheduler.set_ingestion_pipeline(ingestion_pipeline)
    
    # Schedule daily scraping + ingestion at 8:00 AM
    scheduler.start(hour=8, minute=0)
    print("✓ Daily scheduler started - will check DA website and ingest data every day at 8:00 AM")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler when the app shuts down"""
    scheduler.stop()
    print("✓ Scheduler stopped")


@app.get("/")
def root():
    return {
        "message": "DA Price Monitor API - RAG System",
        "description": "SMS-based price checking for farmers in NCR using RAG",
        "version": "2.0.0",
        "features": [
            "Daily price scraping from DA website",
            "RAG-powered query system",
            "Tagalog and English support",
            "GPT-4o-mini responses",
            "ChromaDB vector storage"
        ]
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "rag_enabled": True
    }


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


# ============================================================================
# RAG ENDPOINTS
# ============================================================================

@app.post("/api/ingest")
def trigger_ingestion(replace_if_exists: bool = False):
    """
    Manually trigger ingestion of the latest PDF
    
    Args:
        replace_if_exists: If True, replace existing data for this date
    """
    try:
        result = ingestion_pipeline.ingest_latest_pdf(replace_if_exists=replace_if_exists)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Ingestion failed'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def query_prices(request: QueryRequest):
    """
    Query price information using RAG + GPT-4o-mini
    
    Supports both Tagalog and English queries.
    Examples:
    - "Magkano kamatis sa NCR?"
    - "What is the price of tomatoes?"
    - "Presyo ng manok"
    """
    try:
        result = query_engine.process_query(
            user_query=request.question,
            top_k=request.top_k,
            use_llm=True
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Query failed'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
def search_prices(commodity: str, limit: int = 5):
    """
    Semantic search for prices without LLM response
    
    Returns raw search results with metadata
    """
    try:
        result = query_engine.process_query(
            user_query=f"price of {commodity}",
            top_k=limit,
            use_llm=False
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Search failed'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query-sms")
def sms_query(request: SMSQueryRequest):
    """
    SMS-optimized query endpoint
    
    Returns short, concise responses suitable for SMS
    """
    try:
        answer = query_engine.query_sms_format(request.message)
        
        return {
            "phone": request.phone,
            "message": request.message,
            "response": answer,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chromadb-stats")
def get_chromadb_stats():
    """
    Get statistics about the ChromaDB collection
    """
    try:
        stats = ingestion_pipeline.get_chromadb_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

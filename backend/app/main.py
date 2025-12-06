from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
import os
import logging

from data_sources.scraper import DAPriceScraper
from core.scheduler import scheduler
from data_sources.pdf_parser import PricePDFParser
from processing.ingest_pipeline import IngestionPipeline
from core.query_engine import QueryEngine
from price_cache import PriceCache
from advanced_query import AdvancedQueryHandler
from sms_handler import sms_handler
from twilio_sms import twilio_sms

# Set up logging
logger = logging.getLogger(__name__)

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

# Initialize price cache (cost-efficient for simple queries)
price_cache = PriceCache(chromadb_store=query_engine.chromadb)
price_cache.refresh_cache()  # Load prices on startup

# Initialize advanced query handler (multi-product, comparison, budget, category)
advanced_query = AdvancedQueryHandler(price_cache=price_cache)
advanced_handler = advanced_query  # Alias for SMS endpoints


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
    # Configure scheduler with ingestion pipeline and price cache
    scheduler.set_ingestion_pipeline(ingestion_pipeline)
    scheduler.set_price_cache(price_cache)
    
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
def query_prices(request: QueryRequest, use_cache: bool = True):
    """
    Query price information with ADVANCED features
    
    **Supported Query Types:**
    
    1. **Single Product** (FREE, instant)
       - "Magkano kamatis sa NCR?"
       - "Price of tomato"
    
    2. **Multi-Product** (FREE, instant) ✨ NEW!
       - "Magkano kamatis, sibuyas, at bawang?"
       - "Price of tomato, onion, and garlic"
    
    3. **Comparison** (FREE, instant) ✨ NEW!
       - "Ano mas mura, manok o baboy?"
       - "Compare chicken and pork prices"
    
    4. **Budget Planning** (FREE, instant) ✨ NEW!
       - "Ano pwede bilhin ng 500 pesos?"
       - "What can I buy with 500 pesos?"
    
    5. **Category Browsing** (FREE, instant) ✨ NEW!
       - "Presyo ng lahat ng gulay"
       - "Show all vegetable prices"
       - "Lahat ng isda"
    
    **Performance:**
    - Cache mode (default): <50ms, ₱0 cost
    - RAG mode (use_cache=false): 2-3s, costs API calls
    """
    try:
        # Try advanced query handler first (handles multi, comparison, budget, category)
        if use_cache:
            advanced_result = advanced_query.process(request.question)
            if advanced_result['success']:
                logger.info(f"💡 Advanced query handled: {advanced_result.get('method', 'cache')}")
                return advanced_result
            logger.info(f"🔍 Advanced query failed, falling back to RAG...")
        
        # Fall back to expensive RAG + LLM
        result = query_engine.process_query(
            user_query=request.question,
            top_k=request.top_k,
            use_llm=True
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Query failed'))
        
        result['method'] = 'rag'  # Mark as expensive method
        result['cost'] = 'high'  # Indicate this used API calls
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


@app.post("/api/cache/refresh")
def refresh_cache_endpoint():
    """
    Manually refresh the price cache
    
    Useful after manual data ingestion or for testing
    """
    try:
        logger.info("Manual cache refresh triggered")
        price_cache.refresh_cache()
        
        cache_stats = {
            "last_updated": price_cache.last_updated.isoformat() if price_cache.last_updated else None,
            "cached_commodities": len(price_cache.cache),
            "cache_duration_hours": price_cache.cache_duration.total_seconds() / 3600
        }
        
        return {
            "success": True,
            "message": "Cache refreshed successfully",
            "stats": cache_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cache/stats")
def get_cache_stats():
    """
    Get cache statistics
    """
    try:
        return {
            "last_updated": price_cache.last_updated.isoformat() if price_cache.last_updated else None,
            "cached_commodities": len(price_cache.cache),
            "cache_duration_hours": price_cache.cache_duration.total_seconds() / 3600,
            "needs_refresh": price_cache._needs_refresh()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SMS ENDPOINTS (EngageSpark Integration)
# ============================================================================

@app.post("/api/sms/webhook")
async def engagespark_webhook(
    id: str = None,
    sender: str = None,
    message: str = None,
    **kwargs
):
    """
    EngageSpark SMS Webhook Endpoint
    
    Receives incoming SMS from farmers and sends price information back
    
    Farmers send SMS to your EngageSpark number:
    - "Magkano kamatis sa NCR"
    - "Presyo ng lahat ng gulay"
    - "Ano mas mura, manok o baboy"
    
    System responds with price information
    """
    try:
        logger.info(f"📱 Incoming SMS from {sender}: {message}")
        
        # Process the SMS query
        webhook_data = {
            "id": id,
            "from": sender or kwargs.get("from"),
            "message": message or kwargs.get("text")
        }
        
        processed = sms_handler.handle_inbound_webhook(webhook_data)
        
        if not processed['success']:
            return {"status": "error", "message": "Failed to process SMS"}
        
        user_query = processed['message']
        sender_phone = processed['sender']
        
        # Query price system (using cache for FREE queries)
        result = price_cache.query(user_query)
        
        if result['success']:
            response_text = result['answer']
        else:
            # Fallback to advanced query
            response_text = advanced_handler.handle_query(user_query)
            if not response_text or response_text.startswith("Pasensya"):
                response_text = "Pasensya po, hindi ko maintindihan ang tanong. Subukan: 'Magkano kamatis sa NCR'"
        
        # Truncate for SMS (160 char limit)
        sms_response = sms_handler.truncate_for_sms(response_text)
        
        # Send response SMS
        send_result = sms_handler.send_sms(sender_phone, sms_response)
        
        logger.info(f"📤 Sent SMS response to {sender_phone}: {sms_response[:50]}...")
        
        return {
            "status": "success",
            "query": user_query,
            "response": sms_response,
            "sms_sent": send_result.get('success', False)
        }
        
    except Exception as e:
        logger.error(f"❌ SMS webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.post("/api/sms/send")
def send_sms_manual(phone: str, message: str):
    """
    Manually send SMS (for testing)
    
    Example:
    POST /api/sms/send
    {
        "phone": "09171234567",
        "message": "Test message"
    }
    """
    try:
        result = sms_handler.send_sms(phone, message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sms/query")
def sms_query_test(phone: str, question: str):
    """
    Test SMS query flow without actual SMS
    
    Simulates what would happen when farmer sends SMS
    """
    try:
        # Query the system
        result = price_cache.query(question)
        
        if result['success']:
            response_text = result['answer']
        else:
            response_text = advanced_handler.handle_query(question)
        
        # Truncate for SMS
        sms_response = sms_handler.truncate_for_sms(response_text)
        
        return {
            "success": True,
            "phone": phone,
            "query": question,
            "full_response": response_text,
            "sms_response": sms_response,
            "length": len(sms_response),
            "method": result.get('method', 'advanced')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TWILIO SMS ENDPOINTS (Virtual SMS Testing)
# ============================================================================

@app.post("/api/sms/twilio/webhook")
async def twilio_webhook(
    MessageSid: str = "",
    From: str = "",
    To: str = "",
    Body: str = "",
):
    """
    Twilio SMS Webhook Endpoint
    
    This endpoint receives incoming SMS messages from Twilio.
    Twilio sends a POST request with form data when someone texts your Twilio number.
    
    Setup:
    1. Sign up at https://www.twilio.com/try-twilio (Free $15 credit)
    2. Get a phone number
    3. Configure webhook URL: https://your-ngrok-url.ngrok.io/api/sms/twilio/webhook
    4. Add credentials to .env file
    
    Usage:
    - Farmer texts your Twilio number: "Magkano kamatis?"
    - Twilio sends webhook to this endpoint
    - System queries price database
    - Response SMS sent back automatically
    """
    try:
        logger.info(f"📱 Twilio webhook received from {From}: {Body}")
        
        # Process the incoming SMS
        webhook_data = {
            "MessageSid": MessageSid,
            "From": From,
            "To": To,
            "Body": Body
        }
        
        processed = twilio_sms.handle_inbound_webhook(webhook_data)
        
        if not processed['success']:
            logger.error("Failed to process Twilio webhook")
            return {"status": "error", "message": "Failed to process SMS"}
        
        user_query = processed['message']
        sender_phone = processed['sender']
        
        # Query price system (using cache for FREE queries)
        result = price_cache.query(user_query)
        
        if result['success']:
            response_text = result['answer']
        else:
            # Fallback to advanced query
            response_text = advanced_handler.handle_query(user_query)
            if not response_text or response_text.startswith("Pasensya"):
                response_text = "Pasensya po, hindi ko maintindihan ang tanong. Subukan: 'Magkano kamatis sa NCR'"
        
        # Truncate for SMS (160 char limit for single SMS)
        sms_response = twilio_sms.truncate_for_sms(response_text)
        
        # Send response SMS via Twilio
        send_result = twilio_sms.send_sms(sender_phone, sms_response)
        
        logger.info(f"📤 Sent SMS response to {sender_phone}: {sms_response[:50]}...")
        
        return {
            "status": "success",
            "query": user_query,
            "response": sms_response,
            "sms_sent": send_result.get('success', False),
            "message_id": send_result.get('message_id', '')
        }
        
    except Exception as e:
        logger.error(f"❌ Twilio webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.post("/api/sms/twilio/send")
def send_twilio_sms(phone: str, message: str):
    """
    Manually send SMS via Twilio (for testing)
    
    Example:
    POST /api/sms/twilio/send
    {
        "phone": "+639171234567",
        "message": "Test message from DA Price Monitor"
    }
    """
    try:
        result = twilio_sms.send_sms(phone, message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sms/twilio/balance")
def get_twilio_balance():
    """
    Check Twilio account balance
    
    Useful to see how much credit you have left
    """
    try:
        result = twilio_sms.get_account_balance()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sms/twilio/test")
def test_twilio_query(phone: str, question: str):
    """
    Test SMS query flow with Twilio (without sending actual SMS)
    
    Simulates what would happen when farmer sends SMS via Twilio
    """
    try:
        # Query the system
        result = price_cache.query(question)
        
        if result['success']:
            response_text = result['answer']
        else:
            response_text = advanced_handler.handle_query(question)
        
        # Truncate for SMS
        sms_response = twilio_sms.truncate_for_sms(response_text)
        
        return {
            "success": True,
            "phone": phone,
            "query": question,
            "full_response": response_text,
            "sms_response": sms_response,
            "length": len(sms_response),
            "would_send": True,
            "method": result.get('method', 'advanced')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

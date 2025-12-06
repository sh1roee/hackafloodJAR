"""
Script to ingest the Laguna agricultural context file into ChromaDB
Run this after setting up the environment to add the Laguna price data
"""

import os
from dotenv import load_dotenv
from processing.ingest_pipeline import IngestionPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Ingest Laguna agricultural context into ChromaDB"""
    
    # Load environment variables
    load_dotenv()
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    chromadb_api_key = os.getenv('CHROMADB_API_KEY')
    
    if not openai_api_key or not chromadb_api_key:
        logger.error("Missing required API keys in .env file")
        return
    
    # Initialize pipeline
    logger.info("Initializing ingestion pipeline...")
    pipeline = IngestionPipeline(
        openai_api_key=openai_api_key,
        chromadb_api_key=chromadb_api_key
    )
    
    # Ingest Laguna context
    logger.info("\nIngesting Laguna agricultural context...")
    result = pipeline.ingest_laguna_context()
    
    if result['success']:
        logger.info("\n✅ SUCCESS!")
        logger.info(f"Ingested {result.get('count', 0)} context chunks")
    else:
        logger.error(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
    
    # Show collection stats
    logger.info("\nCollection statistics:")
    stats = pipeline.get_chromadb_stats()
    logger.info(f"  Total entries: {stats.get('total_entries', 0)}")
    logger.info(f"  Unique dates: {stats.get('unique_dates', 0)}")
    logger.info(f"  Categories: {stats.get('categories', {})}")


if __name__ == "__main__":
    main()

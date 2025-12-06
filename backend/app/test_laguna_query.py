"""
Test script to verify Laguna query filtering works correctly
"""

import os
from dotenv import load_dotenv
from core.query_engine import QueryEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test Laguna queries"""
    
    load_dotenv()
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    chromadb_api_key = os.getenv('CHROMADB_API_KEY')
    
    if not openai_api_key or not chromadb_api_key:
        logger.error("Missing API keys")
        return
    
    # Initialize query engine
    logger.info("Initializing query engine...")
    engine = QueryEngine(
        openai_api_key=openai_api_key,
        chromadb_api_key=chromadb_api_key
    )
    
    # Test queries
    test_queries = [
        "presyo kamatis laguna",
        "magkano bigas sa laguna",
        "price of tomato in laguna",
        "kamatis sa calamba",
    ]
    
    for query in test_queries:
        logger.info(f"\n{'='*70}")
        logger.info(f"TESTING: {query}")
        logger.info(f"{'='*70}")
        
        result = engine.process_query(query, top_k=3)
        
        if result['success']:
            logger.info(f"\nAnswer: {result['answer']}")
            logger.info(f"\nSources retrieved: {result['count']}")
            for i, source in enumerate(result['sources'][:3], 1):
                metadata = source['metadata']
                logger.info(f"  {i}. {metadata.get('commodity', 'Unknown')}: ₱{metadata.get('price', 0):.2f} "
                          f"in {metadata.get('location', 'Unknown')} ({metadata.get('tagalog', '')})")
        else:
            logger.error(f"Query failed: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()

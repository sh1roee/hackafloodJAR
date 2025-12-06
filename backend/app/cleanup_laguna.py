"""
Script to clean up old Laguna context chunks and verify new individual entries
"""

import os
from dotenv import load_dotenv
from chromadb_store import ChromaDBStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Clean up and verify Laguna data in ChromaDB"""
    
    # Load environment variables
    load_dotenv()
    
    chromadb_api_key = os.getenv('CHROMADB_API_KEY')
    chromadb_tenant = os.getenv('CHROMADB_TENANT')
    chromadb_database = os.getenv('CHROMADB_DATABASE')
    
    if not chromadb_api_key:
        logger.error("Missing CHROMADB_API_KEY in .env file")
        return
    
    # Initialize ChromaDB
    logger.info("Connecting to ChromaDB...")
    store = ChromaDBStore(
        api_key=chromadb_api_key,
        tenant=chromadb_tenant,
        database=chromadb_database,
        collection_name="da_price_index_ncr"
    )
    
    # Get all entries
    logger.info("\nFetching all entries...")
    all_data = store.collection.get()
    
    total = len(all_data['ids'])
    logger.info(f"Total entries in collection: {total}")
    
    # Find old Laguna context chunks (they have source="laguna_agricultural_data" but content_type="context")
    old_laguna_ids = []
    new_laguna_ids = []
    ncr_ids = []
    
    for i, metadata in enumerate(all_data['metadatas']):
        entry_id = all_data['ids'][i]
        
        if metadata.get('source') == 'laguna_agricultural_data' and metadata.get('content_type') == 'context':
            old_laguna_ids.append(entry_id)
        elif metadata.get('location') == 'Laguna':
            new_laguna_ids.append(entry_id)
        else:
            ncr_ids.append(entry_id)
    
    logger.info(f"\nBreakdown:")
    logger.info(f"  Old Laguna chunks (to delete): {len(old_laguna_ids)}")
    logger.info(f"  New Laguna entries: {len(new_laguna_ids)}")
    logger.info(f"  NCR entries: {len(ncr_ids)}")
    
    # Delete old Laguna chunks if any
    if old_laguna_ids:
        logger.info(f"\nDeleting {len(old_laguna_ids)} old Laguna context chunks...")
        store.collection.delete(ids=old_laguna_ids)
        logger.info("✓ Deleted old chunks")
    
    # Show sample new Laguna entries
    if new_laguna_ids:
        logger.info(f"\nSample Laguna entries:")
        sample_data = store.collection.get(ids=new_laguna_ids[:5])
        for i, metadata in enumerate(sample_data['metadatas']):
            logger.info(f"  {metadata.get('commodity', 'Unknown')}: ₱{metadata.get('price', 0):.2f} ({metadata.get('tagalog', '')})")
    else:
        logger.warning("\n⚠️ No Laguna entries found! Run ingest_laguna_context.py")
    
    # Final stats
    logger.info(f"\nFinal collection size: {store.collection.count()}")
    logger.info(f"  NCR entries: {len(ncr_ids)}")
    logger.info(f"  Laguna entries: {len(new_laguna_ids)}")


if __name__ == "__main__":
    main()

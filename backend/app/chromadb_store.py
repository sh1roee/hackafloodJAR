"""
ChromaDB storage layer for price data
Handles vector storage and retrieval
"""

import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaDBStore:
    """ChromaDB client for storing and retrieving price data"""
    
    def __init__(self, api_key: str, tenant: str = None, database: str = None, collection_name: str = "da_price_index_ncr"):
        """
        Initialize ChromaDB client
        
        Args:
            api_key: ChromaDB API key
            tenant: ChromaDB tenant ID
            database: ChromaDB database name
            collection_name: Name of the collection to use
        """
        self.api_key = api_key
        self.tenant = tenant
        self.database = database
        self.collection_name = collection_name
        
        try:
            # Prefer CloudClient if credentials are provided
            if api_key and tenant and database:
                logger.info("Connecting to ChromaDB Cloud...")
                try:
                    self.client = chromadb.CloudClient(
                        api_key=api_key,
                        tenant=tenant,
                        database=database
                    )
                    logger.info("✓ Connected to ChromaDB Cloud")
                except Exception as cloud_err:
                    logger.error(f"Cloud connection failed: {cloud_err}")
                    logger.warning("Falling back to local PersistentClient.")
                    persist_dir = os.path.join(os.path.dirname(__file__), "..", "chromadb_local")
                    self.client = chromadb.PersistentClient(path=os.path.abspath(persist_dir))
                    logger.info(f"✓ Using local ChromaDB at {os.path.abspath(persist_dir)}")
            else:
                # Fallback to local persistent client
                logger.warning("Cloud credentials missing. Falling back to local PersistentClient.")
                persist_dir = os.path.join(os.path.dirname(__file__), "..", "chromadb_local")
                self.client = chromadb.PersistentClient(path=os.path.abspath(persist_dir))
                logger.info(f"✓ Using local ChromaDB at {os.path.abspath(persist_dir)}")

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "DA Daily Price Index for NCR - Agricultural commodity prices"}
            )

            # If Cloud, optionally validate embedding dimension (OpenAI text-embedding-3-small = 1536)
            try:
                _ = self.collection.count()
            except Exception as e:
                logger.warning(f"Collection access check failed: {e}")

            logger.info(f"✓ Connected to ChromaDB collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def add_prices(self, price_data: List[Dict], embeddings: List[List[float]], texts: List[str]) -> Dict:
        """
        Add price data with embeddings to ChromaDB
        
        Args:
            price_data: List of price data dictionaries (metadata)
            embeddings: List of embedding vectors
            texts: List of text chunks
            
        Returns:
            Result dictionary with count of added items
        """
        try:
            # Generate IDs
            ids = [
                f"{data['date']}_{data['commodity']}_{data.get('specification', '')[:20]}_{idx}"
                for idx, data in enumerate(price_data)
            ]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=price_data
            )
            
            logger.info(f"✓ Added {len(price_data)} price entries to ChromaDB")
            
            return {
                "success": True,
                "count": len(price_data),
                "collection": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to add prices: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_context_chunks(self, chunks: List[str], embeddings: List[List[float]], 
                          source: str, metadata_extra: Dict = None) -> Dict:
        """
        Add context chunks (e.g., Laguna agricultural data) to ChromaDB
        
        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors
            source: Source identifier (e.g., "laguna_agricultural_data")
            metadata_extra: Additional metadata to attach to each chunk
            
        Returns:
            Result dictionary with count of added items
        """
        try:
            # Generate IDs for context chunks
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ids = [f"{source}_{timestamp}_{idx}" for idx in range(len(chunks))]
            
            # Create metadata for each chunk
            metadatas = []
            for idx, chunk in enumerate(chunks):
                metadata = {
                    "source": source,
                    "chunk_index": idx,
                    "timestamp": timestamp,
                    "content_type": "context"
                }
                if metadata_extra:
                    metadata.update(metadata_extra)
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            
            logger.info(f"✓ Added {len(chunks)} context chunks from {source} to ChromaDB")
            
            return {
                "success": True,
                "count": len(chunks),
                "source": source,
                "collection": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to add context chunks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_prices(self, query_embedding: List[float], n_results: int = 5, 
                     filter_dict: Optional[Dict] = None) -> Dict:
        """
        Search for similar price entries
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            Search results with documents, metadatas, and distances
        """
        try:
            # Build query kwargs without passing where=None (Chroma raises error)
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
            }
            if filter_dict:
                query_kwargs["where"] = filter_dict

            results = self.collection.query(**query_kwargs)
            
            return {
                "success": True,
                "results": results,
                "count": len(results['documents'][0]) if results['documents'] else 0
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_exists(self, date: str, commodity: str) -> bool:
        """
        Check if price data already exists for a specific date and commodity
        
        Args:
            date: Date string (YYYY-MM-DD)
            commodity: Commodity name
            
        Returns:
            True if exists, False otherwise
        """
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"date": date},
                        {"commodity": commodity}
                    ]
                },
                limit=1
            )
            
            return len(results['ids']) > 0
            
        except Exception as e:
            logger.error(f"Error checking existence: {e}")
            return False
    
    def delete_by_date(self, date: str) -> Dict:
        """
        Delete all entries for a specific date
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Result dictionary
        """
        try:
            # Get all IDs for this date
            results = self.collection.get(
                where={"date": date}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"✓ Deleted {len(results['ids'])} entries for date {date}")
                
                return {
                    "success": True,
                    "deleted_count": len(results['ids'])
                }
            
            return {
                "success": True,
                "deleted_count": 0
            }
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample entries to analyze
            sample = self.collection.peek(limit=100)
            
            dates = set()
            categories = {}
            
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    if metadata.get('date'):
                        dates.add(metadata['date'])
                    if metadata.get('category'):
                        cat = metadata['category']
                        categories[cat] = categories.get(cat, 0) + 1
            
            return {
                "total_entries": count,
                "unique_dates": len(dates),
                "categories": categories,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "error": str(e)
            }

"""
Ingestion pipeline for DA Price Index PDFs
Orchestrates the flow from PDF → ChromaDB
"""

import os
from typing import Dict, List
from pathlib import Path
import logging

from pdf_parser import PricePDFParser
from data_processor import PriceDataProcessor
from text_chunks import TextChunkGenerator
from chromadb_store import ChromaDBStore
from langchain_openai import OpenAIEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Pipeline to ingest PDF price data into ChromaDB"""
    
    def __init__(self, openai_api_key: str, chromadb_api_key: str):
        """
        Initialize the ingestion pipeline
        
        Args:
            openai_api_key: OpenAI API key for embeddings
            chromadb_api_key: ChromaDB API key
        """
        self.parser = PricePDFParser()
        self.processor = PriceDataProcessor()
        self.chunk_generator = TextChunkGenerator()
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=openai_api_key
        )
        
        # Initialize ChromaDB
        chromadb_tenant = os.getenv('CHROMADB_TENANT')
        chromadb_database = os.getenv('CHROMADB_DATABASE')
        self.chromadb = ChromaDBStore(
            api_key=chromadb_api_key,
            tenant=chromadb_tenant,
            database=chromadb_database,
            collection_name="da_price_index_ncr"
        )
        
        logger.info("✓ Ingestion pipeline initialized")
    
    def ingest_pdf(self, pdf_path: Path, replace_if_exists: bool = False) -> Dict:
        """
        Ingest a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            replace_if_exists: If True, replace existing data for this date
            
        Returns:
            Result dictionary with ingestion stats
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"STARTING INGESTION: {pdf_path.name}")
            logger.info(f"{'='*70}")
            
            # Step 1: Extract tables from PDF
            logger.info("Step 1/6: Extracting tables from PDF...")
            tables = self.parser.extract_tables_from_pdf(pdf_path)
            
            if not tables:
                return {
                    "success": False,
                    "error": "No tables extracted from PDF"
                }
            
            logger.info(f"✓ Extracted {len(tables)} tables")
            
            # Step 2: Process and clean data
            logger.info("Step 2/6: Processing and cleaning data...")
            price_entries = self.processor.process_all_tables(tables, pdf_path.name)
            
            if not price_entries:
                return {
                    "success": False,
                    "error": "No valid price entries found"
                }
            
            logger.info(f"✓ Processed {len(price_entries)} price entries")
            
            # Step 3: Check for existing data
            logger.info("Step 3/6: Checking for existing data...")
            if price_entries:
                date = price_entries[0]['date']
                
                if not replace_if_exists and self.chromadb.check_exists(date, price_entries[0]['commodity']):
                    logger.info(f"⚠ Data for {date} already exists. Use replace_if_exists=True to overwrite.")
                    return {
                        "success": False,
                        "error": f"Data for {date} already exists",
                        "date": date
                    }
                
                if replace_if_exists:
                    logger.info(f"Deleting existing data for {date}...")
                    self.chromadb.delete_by_date(date)
            
            # Step 4: Generate text chunks
            logger.info("Step 4/6: Generating text chunks...")
            text_chunks = self.chunk_generator.create_batch_chunks(price_entries)
            logger.info(f"✓ Generated {len(text_chunks)} text chunks")
            
            # Step 5: Generate embeddings
            logger.info("Step 5/6: Generating embeddings with OpenAI...")
            embeddings_list = []
            
            # Batch embeddings for efficiency
            batch_size = 100
            for i in range(0, len(text_chunks), batch_size):
                batch = text_chunks[i:i+batch_size]
                batch_embeddings = self.embeddings.embed_documents(batch)
                embeddings_list.extend(batch_embeddings)
                logger.info(f"  Processed {min(i+batch_size, len(text_chunks))}/{len(text_chunks)} embeddings")
            
            logger.info(f"✓ Generated {len(embeddings_list)} embeddings")
            
            # Step 6: Store in ChromaDB
            logger.info("Step 6/6: Storing in ChromaDB...")
            result = self.chromadb.add_prices(price_entries, embeddings_list, text_chunks)
            
            if result['success']:
                logger.info(f"\n{'='*70}")
                logger.info("✓ INGESTION COMPLETE")
                logger.info(f"{'='*70}")
                logger.info(f"PDF: {pdf_path.name}")
                logger.info(f"Date: {price_entries[0]['date']}")
                logger.info(f"Entries stored: {len(price_entries)}")
                logger.info(f"{'='*70}\n")
                
                # Get summary stats
                stats = self.processor.get_summary_stats(price_entries)
                
                return {
                    "success": True,
                    "pdf_file": pdf_path.name,
                    "date": price_entries[0]['date'],
                    "entries_stored": len(price_entries),
                    "stats": stats
                }
            else:
                return result
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def ingest_latest_pdf(self, replace_if_exists: bool = False) -> Dict:
        """
        Ingest the most recently downloaded PDF
        
        Args:
            replace_if_exists: If True, replace existing data for this date
            
        Returns:
            Result dictionary
        """
        latest_pdf = self.parser.get_latest_pdf()
        
        if not latest_pdf:
            return {
                "success": False,
                "error": "No PDF files found to ingest"
            }
        
        return self.ingest_pdf(latest_pdf, replace_if_exists)
    
    def get_chromadb_stats(self) -> Dict:
        """Get ChromaDB collection statistics"""
        return self.chromadb.get_collection_stats()

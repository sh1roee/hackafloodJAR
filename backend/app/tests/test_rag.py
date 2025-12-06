"""
Test script for RAG pipeline
Tests ingestion and query functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMADB_API_KEY = os.getenv("CHROMADB_API_KEY")

print("="*80)
print("DA PRICE MONITOR - RAG PIPELINE TEST")
print("="*80)

# Test 1: Import all modules
print("\nTest 1: Importing modules...")
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from processing.ingest_pipeline import IngestionPipeline
    from core.query_engine import QueryEngine
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Initialize ingestion pipeline
print("\nTest 2: Initializing ingestion pipeline...")
try:
    pipeline = IngestionPipeline(
        openai_api_key=OPENAI_API_KEY,
        chromadb_api_key=CHROMADB_API_KEY
    )
    print("✓ Ingestion pipeline initialized")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test 3: Ingest latest PDF
print("\nTest 3: Ingesting latest PDF...")
try:
    result = pipeline.ingest_latest_pdf(replace_if_exists=True)
    
    if result['success']:
        print("✓ Ingestion successful!")
        print(f"  - PDF: {result['pdf_file']}")
        print(f"  - Date: {result['date']}")
        print(f"  - Entries: {result['entries_stored']}")
        print(f"  - Stats: {result['stats']}")
    else:
        print(f"✗ Ingestion failed: {result.get('error')}")
        
except Exception as e:
    print(f"✗ Ingestion error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Get ChromaDB stats
print("\nTest 4: ChromaDB statistics...")
try:
    stats = pipeline.get_chromadb_stats()
    print("✓ ChromaDB stats:")
    print(f"  - Total entries: {stats.get('total_entries')}")
    print(f"  - Unique dates: {stats.get('unique_dates')}")
    print(f"  - Categories: {stats.get('categories')}")
except Exception as e:
    print(f"✗ Stats error: {e}")

# Test 5: Initialize query engine
print("\nTest 5: Initializing query engine...")
try:
    query_engine = QueryEngine(
        openai_api_key=OPENAI_API_KEY,
        chromadb_api_key=CHROMADB_API_KEY
    )
    print("✓ Query engine initialized")
except Exception as e:
    print(f"✗ Query engine initialization failed: {e}")
    sys.exit(1)

# Test 6: Test queries
print("\nTest 6: Running test queries...")

test_queries = [
    "Magkano kamatis sa NCR?",
    "What is the price of rice?",
    "Presyo ng manok",
    "How much is chicken?",
]

for query in test_queries:
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    try:
        result = query_engine.process_query(query, top_k=3)
        
        if result['success']:
            print(f"\nAnswer:\n{result['answer']}")
            print(f"\nSources ({len(result['sources'])}):")
            for i, source in enumerate(result['sources'][:3], 1):
                metadata = source['metadata']
                print(f"\n{i}. {metadata.get('commodity')} - ₱{metadata.get('price')}")
                print(f"   Spec: {metadata.get('specification')}")
                print(f"   Date: {metadata.get('date')}")
        else:
            print(f"✗ Query failed: {result.get('error')}")
            
    except Exception as e:
        print(f"✗ Query error: {e}")
        import traceback
        traceback.print_exc()

# Test 7: SMS format query
print(f"\n{'='*80}")
print("Test 7: SMS Format Query")
print(f"{'='*80}")

try:
    sms_response = query_engine.query_sms_format("Magkano bigas?")
    print(f"\nSMS Response ({len(sms_response)} chars):")
    print(sms_response)
except Exception as e:
    print(f"✗ SMS query error: {e}")

print(f"\n{'='*80}")
print("✓ ALL TESTS COMPLETE")
print(f"{'='*80}\n")

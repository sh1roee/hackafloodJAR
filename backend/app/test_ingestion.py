"""
Simple ingestion test to debug ChromaDB storage
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv()

print("="*80)
print("INGESTION DEBUG TEST")
print("="*80)

# Step 1: Check environment variables
print("\n[1] Environment Variables:")
print("-"*80)
openai_key = os.getenv("OPENAI_API_KEY")
chromadb_key = os.getenv("CHROMADB_API_KEY")
chromadb_tenant = os.getenv("CHROMADB_TENANT")
chromadb_database = os.getenv("CHROMADB_DATABASE")

print(f"OpenAI API Key: {'✓ SET' if openai_key else '✗ MISSING'}")
print(f"ChromaDB API Key: {'✓ SET' if chromadb_key else '✗ MISSING'}")
print(f"ChromaDB Tenant: {chromadb_tenant if chromadb_tenant else '✗ MISSING'}")
print(f"ChromaDB Database: {chromadb_database if chromadb_database else '✗ MISSING'}")

# Step 2: Test ChromaDB connection
print("\n[2] ChromaDB Connection Test:")
print("-"*80)
try:
    from chromadb_store import ChromaDBStore
    
    store = ChromaDBStore(
        api_key=chromadb_key,
        tenant=chromadb_tenant,
        database=chromadb_database,
        collection_name="da_price_index_ncr"
    )
    
    print("✓ ChromaDB connection successful")
    
    # Get initial stats
    stats = store.get_collection_stats()
    print(f"Current collection size: {stats.get('total_entries', 0)} entries")
    
except Exception as e:
    print(f"✗ ChromaDB connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test PDF parsing
print("\n[3] PDF Parsing Test:")
print("-"*80)
try:
    from data_sources.pdf_parser import PricePDFParser
    
    parser = PricePDFParser()
    latest_pdf = parser.get_latest_pdf()
    
    if latest_pdf:
        print(f"✓ Found PDF: {latest_pdf.name}")
        
        tables = parser.extract_tables_from_pdf(latest_pdf)
        print(f"✓ Extracted {len(tables)} tables from PDF")
    else:
        print("✗ No PDF files found")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ PDF parsing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test data processing
print("\n[4] Data Processing Test:")
print("-"*80)
try:
    from processing.data_processor import PriceDataProcessor
    
    processor = PriceDataProcessor()
    entries = processor.process_all_tables(tables, latest_pdf.name)
    
    print(f"✓ Processed {len(entries)} price entries")
    
    if entries:
        print(f"\nSample entry:")
        sample = entries[0]
        for key, value in sample.items():
            print(f"  {key}: {value}")
    
except Exception as e:
    print(f"✗ Data processing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Test embeddings generation
print("\n[5] Embeddings Test:")
print("-"*80)
try:
    from langchain_openai import OpenAIEmbeddings
    from processing.text_chunks import TextChunkGenerator
    
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_key
    )
    
    chunk_gen = TextChunkGenerator()
    
    # Create chunks for first 5 entries
    test_entries = entries[:5]
    chunks = [chunk_gen.create_chunk(entry) for entry in test_entries]
    
    print(f"✓ Generated {len(chunks)} text chunks")
    print(f"\nSample chunk:")
    print(f"  {chunks[0][:200]}...")
    
    # Generate embeddings
    print("\nGenerating embeddings...")
    test_embeddings = embeddings_model.embed_documents(chunks)
    
    print(f"✓ Generated {len(test_embeddings)} embeddings")
    print(f"  Embedding dimension: {len(test_embeddings[0])}")
    
except Exception as e:
    print(f"✗ Embeddings generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Test ChromaDB storage
print("\n[6] ChromaDB Storage Test:")
print("-"*80)
try:
    # Store the test entries
    result = store.add_prices(
        price_data=test_entries,
        embeddings=test_embeddings,
        texts=chunks
    )
    
    print(f"✓ Stored {result.get('added', 0)} entries in ChromaDB")
    
    # Verify storage
    stats = store.get_collection_stats()
    print(f"✓ Collection now has {stats.get('total_entries', 0)} total entries")
    
except Exception as e:
    print(f"✗ Storage failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: Test query/retrieval
print("\n[7] Query/Retrieval Test:")
print("-"*80)
try:
    # Test query
    test_query = "price of tomato"
    query_embedding = embeddings_model.embed_query(test_query)
    
    results = store.search_prices(query_embedding, n_results=3)
    
    print(f"✓ Query: '{test_query}'")
    print(f"✓ Found {len(results.get('documents', [[]])[0])} results")
    
    if results.get('documents') and results['documents'][0]:
        print(f"\nTop result:")
        print(f"  {results['documents'][0][0][:200]}...")
    
except Exception as e:
    print(f"✗ Query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✓ ALL TESTS PASSED!")
print("="*80)
print("\nYour RAG pipeline is working correctly.")
print(f"Collection '{store.collection_name}' has {stats.get('total_entries', 0)} entries")

# Optional Step 8: Ingest Laguna agricultural context
print("\n[8] Laguna Agricultural Context (OPTIONAL):")
print("-"*80)
print("Would you like to ingest the Laguna agricultural price context?")
print("This will add additional knowledge about Laguna province prices.")
ingest_laguna = input("Ingest Laguna context? (y/n): ").strip().lower()

if ingest_laguna == 'y':
    try:
        from processing.ingest_pipeline import IngestionPipeline
        
        pipeline = IngestionPipeline(
            openai_api_key=openai_key,
            chromadb_api_key=chromadb_key
        )
        
        result = pipeline.ingest_laguna_context()
        
        if result['success']:
            print(f"✓ Ingested {result.get('count', 0)} Laguna context chunks")
            
            # Show updated stats
            stats = store.get_collection_stats()
            print(f"✓ Collection now has {stats.get('total_entries', 0)} total entries")
        else:
            print(f"✗ Laguna context ingestion failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"✗ Laguna context ingestion error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Skipped Laguna context ingestion.")

print("\n" + "="*80)
print("TESTING COMPLETE")
print("="*80)

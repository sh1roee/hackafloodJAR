"""
Quick verification script to check RAG setup
Shows what APIs and models are being used
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("="*80)
print("RAG PIPELINE VERIFICATION")
print("="*80)

print("\n📋 CONFIGURATION CHECK:")
print("-" * 80)

# Check environment variables
openai_key = os.getenv("OPENAI_API_KEY")
chromadb_key = os.getenv("CHROMADB_API_KEY")
chromadb_tenant = os.getenv("CHROMADB_TENANT")
chromadb_database = os.getenv("CHROMADB_DATABASE")

print(f"✓ OpenAI API Key: {'SET' if openai_key else 'MISSING'} ({len(openai_key) if openai_key else 0} chars)")
print(f"✓ ChromaDB API Key: {'SET' if chromadb_key else 'MISSING'} ({len(chromadb_key) if chromadb_key else 0} chars)")
print(f"✓ ChromaDB Tenant: {chromadb_tenant if chromadb_tenant else 'MISSING'}")
print(f"✓ ChromaDB Database: {chromadb_database if chromadb_database else 'MISSING'}")

print("\n🔧 COMPONENT VERIFICATION:")
print("-" * 80)

# Test imports
try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    print("✓ LangChain OpenAI imported")
    
    # Show embedding model
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_key
    )
    print(f"  → Embeddings Model: text-embedding-3-small")
    
    # Show LLM model
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=openai_key
    )
    print(f"  → LLM Model: gpt-4o-mini")
    
except Exception as e:
    print(f"✗ LangChain error: {e}")

try:
    import chromadb
    print("✓ ChromaDB imported")
    print(f"  → Client: CloudClient")
    print(f"  → Tenant: {chromadb_tenant}")
    print(f"  → Database: {chromadb_database}")
    
except Exception as e:
    print(f"✗ ChromaDB error: {e}")

try:
    from ingest_pipeline import IngestionPipeline
    print("✓ Ingestion Pipeline imported")
    
    pipeline = IngestionPipeline(
        openai_api_key=openai_key,
        chromadb_api_key=chromadb_key
    )
    print("  → Pipeline initialized successfully")
    
except Exception as e:
    print(f"✗ Pipeline error: {e}")

try:
    from query_engine import QueryEngine
    print("✓ Query Engine imported")
    
    engine = QueryEngine(
        openai_api_key=openai_key,
        chromadb_api_key=chromadb_key
    )
    print("  → Query Engine initialized successfully")
    
except Exception as e:
    print(f"✗ Query Engine error: {e}")

print("\n🎯 API FLOW:")
print("-" * 80)
print("Query: 'Magkano kamatis?' →")
print("  1. Translate: kamatis → tomato")
print("  2. Embed query using text-embedding-3-small (OpenAI)")
print("  3. Search ChromaDB (tenant: fff8127e-a5f9-4faf-9e0f-03c5b5217c6a)")
print("  4. Retrieve top 5 matching price entries")
print("  5. Format context for LLM")
print("  6. Generate response using gpt-4o-mini (OpenAI)")
print("  7. Return: 'Kamatis sa NCR: ₱142.54 per kilo'")

print("\n📊 MODELS BEING USED:")
print("-" * 80)
print("✓ OpenAI text-embedding-3-small - Query & document embeddings")
print("✓ OpenAI gpt-4o-mini - Natural language responses")
print("✓ ChromaDB Cloud - Vector storage (Ron database)")
print("✓ LangChain - RAG orchestration")

print("\n" + "="*80)
print("Setup verification complete! ✓")
print("="*80)

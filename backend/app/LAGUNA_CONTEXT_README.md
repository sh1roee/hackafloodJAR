# Laguna Agricultural Price Data Integration

This module provides hardcoded agricultural price data for Laguna province and integrates it into the RAG pipeline for enhanced LLM context.

## Files Created

1. **`data_sources/laguna_agriculture_data.py`**

   - Contains hardcoded price data for Laguna province
   - Includes vegetables, fruits, root crops, and grains/legumes
   - Provides a function to generate a human-readable .txt file

2. **`downloads/price_index/laguna_agricultural_prices.txt`**

   - Auto-generated formatted text file
   - Contains all Laguna price data in a readable format
   - This file is ingested into ChromaDB for LLM context

3. **`ingest_laguna_context.py`**
   - Standalone script to ingest Laguna context into ChromaDB
   - Can be run independently or as part of the pipeline

## How to Use

### Method 1: Automatic Ingestion (Recommended)

When you initialize the `IngestionPipeline`, it automatically:

1. Checks if the Laguna context file exists
2. Generates it if missing
3. You can then call `pipeline.ingest_laguna_context()` to add it to ChromaDB

```python
from processing.ingest_pipeline import IngestionPipeline

pipeline = IngestionPipeline(
    openai_api_key="your_key",
    chromadb_api_key="your_key"
)

# Ingest Laguna agricultural context
result = pipeline.ingest_laguna_context()
print(f"Ingested {result['count']} chunks")
```

### Method 2: Run Standalone Script

```bash
cd backend
python -m app.ingest_laguna_context
```

### Method 3: During Test Ingestion

When running the test ingestion script, you'll be prompted:

```bash
python -m app.test_ingestion
```

The script will ask if you want to ingest Laguna context after the main tests pass.

## What Gets Stored

The Laguna agricultural data is:

- Split into semantic chunks (by category)
- Embedded using OpenAI embeddings
- Stored in ChromaDB with special metadata:
  - `source`: "laguna_agricultural_data"
  - `content_type`: "context"
  - `region`: "Laguna"

## LLM Integration

Once ingested, the LLM will have access to:

- 63 different agricultural commodities from Laguna
- Both English and Tagalog names
- Current price information (December 2024)
- Organized by category (vegetables, fruits, root crops, grains/legumes)

When users ask about prices in Laguna, the RAG system will retrieve this context automatically.

## Updating the Data

To update prices or add new commodities:

1. Edit `data_sources/laguna_agriculture_data.py`
2. Run the generation function:
   ```bash
   python -m app.data_sources.laguna_agriculture_data
   ```
3. Re-ingest the context:
   ```bash
   python -m app.ingest_laguna_context
   ```

## Benefits

✅ **Richer Context**: LLM has more knowledge about Laguna prices  
✅ **Better Answers**: Can provide Laguna-specific price information  
✅ **Fallback Data**: When DA MAS documents don't have data, Laguna data can help  
✅ **Regional Coverage**: Expands beyond NCR to include Laguna province  
✅ **Bilingual**: Supports both English and Tagalog queries

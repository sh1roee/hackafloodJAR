# RAG Pipeline Planning Document

## DA Price Monitor - SMS System for Farmers

### Current Status ✅

- ✅ Scraper working (downloads latest Daily Price Index from DA website)
- ✅ PDF parser extracts tables and text
- ✅ Scheduler runs daily at 8:00 AM
- ✅ Basic FastAPI endpoints

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DAILY AUTOMATIC FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DA Website → Scraper → PDF Download → Parser → Clean Data     │
│       ↓                                                         │
│  Text Chunks → OpenAI Embeddings → ChromaDB Storage            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     QUERY FLOW (SMS/API)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Farmer Query (Tagalog/English)                                │
│       ↓                                                         │
│  Translate Tagalog → English (kamatis → tomato)                │
│       ↓                                                         │
│  Query Embedding (text-embedding-3-small)                       │
│       ↓                                                         │
│  ChromaDB Search (similarity search)                            │
│       ↓                                                         │
│  Retrieve Price Context                                         │
│       ↓                                                         │
│  GPT-4o-mini (generate response)                                │
│       ↓                                                         │
│  SMS/API Response (Tagalog/English)                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase-by-Phase Implementation Plan

### **PHASE 1: Configuration & Setup** (30 min)

**Goal:** Set up ChromaDB and environment

**Tasks:**

1. Add ChromaDB API key to `.env`
2. Install packages: `chromadb-client`, `langchain-openai`, `langchain-chroma`
3. Test ChromaDB connection
4. Create collection: `da_price_index_ncr`

**Files to create/modify:**

- `.env` - Add `CHROMADB_API_KEY`
- `requirements.txt` - Add new dependencies

---

### **PHASE 2: Data Model Design** (20 min)

**Goal:** Define what data to extract and how to structure it

**Structured Data Model:**

```python
{
    "commodity": "Tomato",
    "category": "vegetables",
    "specification": "15-18 pcs/kg",
    "price": 142.54,
    "unit": "peso/kg",
    "date": "2025-12-05",
    "location": "NCR",
    "source_pdf": "daily_price_index_December_5_2025.pdf",
    "page": 6
}
```

**Text Chunk for Embedding (English):**

```
"Tomato in NCR costs 142.54 pesos per kg on December 5, 2025. Specification: 15-18 pcs/kg. Category: Highland Vegetables."
```

**Text Chunk Variation (with Tagalog):**

```
"Kamatis (Tomato) sa NCR: ₱142.54 per kilo (December 5, 2025). Size: 15-18 pieces per kg."
```

---

### **PHASE 3: Enhanced PDF Processing** (1-2 hours)

**Goal:** Extract clean, structured data from PDFs

**What to extract from each PDF:**

1. **Commodity names** - Rice, Fish, Vegetables, Meat, etc.
2. **Categories** - Group by type (IMPORTED RICE, LOCAL RICE, FISH PRODUCTS, etc.)
3. **Specifications** - Size, type, brand, quality
4. **Prices** - Convert to float, handle "n/a"
5. **Metadata** - Date, location (NCR), page number

**Data Cleaning Requirements:**

- Remove header/footer rows
- Filter out category labels (e.g., "IMPORTED COMMERCIAL RICE")
- Normalize prices: "142.54" → 142.54 (float)
- Handle missing data: "n/a" → None
- Clean commodity names: remove extra spaces
- Standardize units: "P/UNIT" → "peso"

**Files to create:**

- `data_processor.py` - Clean and structure PDF data

---

### **PHASE 4: Tagalog-English Mapping** (30 min)

**Goal:** Handle queries in Tagalog

**Essential Mappings:**

```python
COMMODITY_MAPPING = {
    # Vegetables
    "kamatis": "tomato",
    "talong": "eggplant",
    "sibuyas": "onion",
    "bawang": "garlic",
    "repolyo": "cabbage",

    # Meat
    "manok": "chicken",
    "baboy": "pork",
    "baka": "beef",

    # Fish
    "isda": "fish",
    "bangus": "milkfish",
    "tilapia": "tilapia",
    "galunggong": "mackerel scad",

    # Grains
    "bigas": "rice",
    "mais": "corn",
}
```

**Files to create:**

- `commodity_mappings.py` - Tagalog ↔ English dictionary

---

### **PHASE 5: Embedding & ChromaDB Storage** (1-2 hours)

**Goal:** Store price data as vectors in ChromaDB

**Key Components:**

1. **OpenAI Embeddings Setup:**

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
```

2. **ChromaDB Collection:**

```python
import chromadb

client = chromadb.HttpClient(
    host="api.trychroma.com",
    headers={"Authorization": f"Bearer {CHROMADB_API_KEY}"}
)

collection = client.get_or_create_collection(
    name="da_price_index_ncr",
    metadata={"description": "DA Daily Price Index for NCR"}
)
```

3. **Storage Function:**

```python
def store_price_data(price_data):
    # Generate text chunk
    text = create_text_chunk(price_data)

    # Generate embedding
    embedding = embeddings.embed_query(text)

    # Store in ChromaDB
    collection.add(
        embeddings=[embedding],
        documents=[text],
        metadatas=[price_data],
        ids=[f"{price_data['date']}_{price_data['commodity']}"]
    )
```

**Files to create:**

- `chromadb_store.py` - ChromaDB operations
- `embedding_generator.py` - Text chunk creation + embedding

---

### **PHASE 6: Ingestion Pipeline** (1 hour)

**Goal:** Automated pipeline from PDF → ChromaDB

**Pipeline Steps:**

```python
def ingest_latest_pdf():
    # 1. Get latest PDF
    pdf_path = parser.get_latest_pdf()

    # 2. Extract tables
    tables = parser.extract_tables_from_pdf(pdf_path)

    # 3. Process and clean data
    clean_data = process_tables(tables)

    # 4. Generate text chunks (English + Tagalog variations)
    chunks = create_text_chunks(clean_data)

    # 5. Generate embeddings
    embeddings = generate_embeddings(chunks)

    # 6. Store in ChromaDB
    store_in_chromadb(embeddings, clean_data)

    # 7. Log success
    return {"success": True, "items_stored": len(clean_data)}
```

**Files to create:**

- `ingest_pipeline.py` - Main ingestion logic

---

### **PHASE 7: RAG Query System** (1-2 hours)

**Goal:** Search ChromaDB and generate AI responses

**Query Processing:**

```python
def process_query(user_query: str):
    # 1. Translate Tagalog → English
    translated = translate_commodity_terms(user_query)

    # 2. Generate query embedding
    query_embedding = embeddings.embed_query(translated)

    # 3. Search ChromaDB (top 5 results)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    # 4. Format context for LLM
    context = format_search_results(results)

    # 5. Generate response with GPT-4o-mini
    response = generate_llm_response(user_query, context)

    return response
```

**LLM Prompt Template:**

```
System: You are a helpful assistant for Filipino farmers. You provide agricultural
price information from the Department of Agriculture's Daily Price Index for NCR.
Answer in a friendly, concise way. You can respond in Tagalog or English.

Context (Price Data):
{retrieved_context}

User Question: {user_query}

Instructions:
- Provide the current price based on the context
- Include the date of the price information
- If price is not available, say so politely
- Keep response short (suitable for SMS)
```

**Files to create:**

- `query_engine.py` - Query processing
- `llm_generator.py` - GPT-4o-mini integration

---

### **PHASE 8: API Integration** (1 hour)

**Goal:** FastAPI endpoints for the RAG system

**New Endpoints:**

```python
@app.post("/api/ingest")
def trigger_ingestion():
    """Manually trigger PDF ingestion"""

@app.post("/api/query")
def query_prices(query: str):
    """Query price using RAG + GPT-4o-mini"""

@app.get("/api/search")
def search_prices(commodity: str, limit: int = 5):
    """Semantic search without LLM"""

@app.post("/api/query-sms")
def sms_query(phone: str, message: str):
    """SMS-optimized query (short response)"""
```

**Files to modify:**

- `main.py` - Add new endpoints

---

### **PHASE 9: Automated Daily Updates** (30 min)

**Goal:** Auto-ingest new PDFs daily

**Scheduler Enhancement:**

```python
def daily_scrape_and_ingest():
    # 1. Scrape latest PDF
    result = scraper.get_latest_daily_price_index()

    # 2. Check if already ingested (by date)
    if not already_ingested(result['date']):
        # 3. Trigger ingestion
        ingest_result = ingest_pipeline.process_pdf(result['filepath'])

        # 4. Log results
        log_ingestion(ingest_result)
```

**Files to modify:**

- `scheduler.py` - Add ingestion to daily job

---

## Example User Interactions

### Example 1: Tagalog Query

```
User (SMS): "Magkano kamatis sa NCR?"

System Process:
1. Translate: kamatis → tomato
2. Search ChromaDB for "tomato NCR"
3. Retrieve: Tomato, ₱142.54/kg, Dec 5, 2025
4. Generate response

Response: "Kamatis sa NCR: ₱142.54 per kilo (December 5, 2025)"
```

### Example 2: English Query

```
User (API): "What's the price of chicken in NCR?"

System Process:
1. Search ChromaDB for "chicken NCR"
2. Retrieve multiple chicken entries (leg quarter, breast, whole, etc.)
3. Generate comprehensive response

Response: "Chicken prices in NCR (Dec 5, 2025):
- Leg Quarter: ₱210-235/kg
- Whole Dressed: ₱185/kg
- Breast: ₱290/kg"
```

### Example 3: Rice Price

```
User: "Magkano bigas well milled?"

Response: "Well Milled Rice sa NCR:
- Local: ₱43.50/kg
- Imported: ₱44.75/kg
(December 5, 2025)"
```

---

## Technical Stack Summary

| Component           | Technology                    | Purpose                       |
| ------------------- | ----------------------------- | ----------------------------- |
| **Scraper**         | BeautifulSoup, Requests       | Download PDFs from DA website |
| **PDF Parser**      | pdfplumber, pandas            | Extract tables from PDFs      |
| **Data Processing** | pandas, Python                | Clean and structure data      |
| **Embeddings**      | OpenAI text-embedding-3-small | Vectorize price data          |
| **Vector DB**       | ChromaDB (cloud)              | Store and search embeddings   |
| **LLM**             | GPT-4o-mini                   | Generate natural responses    |
| **Framework**       | LangChain                     | RAG orchestration             |
| **API**             | FastAPI                       | REST endpoints                |
| **Scheduler**       | APScheduler                   | Daily automation              |

---

## Dependencies to Add

```txt
# Add to requirements.txt:
chromadb-client
langchain
langchain-openai
langchain-chroma
langchain-community
```

---

## ChromaDB Setup

```python
# .env
OPENAI_API_KEY=sk-proj-...
CHROMADB_API_KEY=ck-G6DghQMpk5nKeU4SzBwX75HVtW8iuectH627Hyt2bjTb
```

---

## Success Metrics

After implementation, you should be able to:

- ✅ Automatically scrape and ingest daily price data
- ✅ Query in Tagalog: "Magkano kamatis?"
- ✅ Query in English: "Price of tomatoes?"
- ✅ Get accurate, dated responses
- ✅ Handle SMS-style queries (short, concise)
- ✅ Search across 200+ commodities
- ✅ Support farmers with real-time price info

---

## Next Steps

1. **Start with Phase 1** - Set up ChromaDB
2. **Test embedding pipeline** - Process one PDF manually
3. **Build query system** - Test with sample queries
4. **Integrate with main.py** - Create API endpoints
5. **Test end-to-end** - Full RAG flow
6. **Add SMS integration** - Connect to SMS gateway

Good luck with your hackathon! 🌾📱

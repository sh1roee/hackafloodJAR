# DA Price Monitor - Frontend

Simple chat interface for querying agricultural commodity prices.

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Make sure backend is running:**

```bash
cd ../backend/app
uvicorn main:app --reload
```

3. **Run the frontend:**

```bash
streamlit run gui.py
```

The app will open at `http://localhost:8501`

## Features

- ✅ Clean, simple chat interface
- ✅ Supports English and Tagalog queries
- ✅ Real-time price information from DA database
- ✅ Integrated with RAG backend (GPT-4o-mini + ChromaDB)

## Example Queries

- "Magkano kamatis sa NCR?"
- "What is the price of chicken?"
- "Presyo ng bigas"
- "How much is pork?"

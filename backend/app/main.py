    from typing import Any, Dict, List, Optional
import os
import time
import io
import csv
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
import numpy as np

# LangChain imports (required)
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_community.document_transformers.openai_functions import create_metadata_tagger
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import uuid
from pathlib import Path


# Load environment variables
# Load env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
DB_NAME = os.getenv("MONGO_DB", "bills_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "bills_collection")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required in environment")
if not MONGO_DB_URI:
    raise RuntimeError("MONGO_DB_URI is required in environment")

# LangChain OpenAI embeddings will pick up OPENAI_API_KEY from env; create embeddings instance
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")

# Simple MongoDB client
client = MongoClient(MONGO_DB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

app = FastAPI(title="light-streamlit-simple-backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8501", "http://127.0.0.1", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i : i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def _embed_query(text: str) -> List[float]:
    """Return an embedding vector for the given text using LangChain OpenAIEmbeddings."""
    try:
        return embeddings.embed_query(text)
    except Exception:
        # fallback to embed_documents
        return embeddings.embed_documents([text])[0]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class QueryIn(BaseModel):
    question: str
    top_k: Optional[int] = 4


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ingest_text")
def ingest_text(payload: Dict[str, Any]):
    """Ingest a plain text document (JSON {text, metadata}). Splits into chunks, embeds, and stores them."""
    try:
        text = payload.get("text")
        metadata = payload.get("metadata", {})
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        # Use LangChain-only ingestion: transform, split, embed, and store in MongoDB vectorstore
        try:
            doc = Document(page_content=text, metadata=metadata or {})
            if len(doc.page_content.split()) <= 20:
                return {"inserted_count": 0, "ids": []}

            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)

            schema = {
                "properties": {
                    "title": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "hasCode": {"type": "boolean"},
                },
                "required": ["title", "keywords", "hasCode"],
            }

            document_transformer = create_metadata_tagger(metadata_schema=schema, llm=llm)
            transformed_docs = document_transformer.transform_documents([doc])
            split_docs = splitter.split_documents(transformed_docs)

            # Use LangChain OpenAIEmbeddings and MongoDB vectorstore
            vectorstore = MongoDBAtlasVectorSearch.from_documents(split_docs, embeddings, collection=collection)
            return {"inserted_count": len(split_docs), "ids": []}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest_pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    if PyPDFLoader is None:
        raise HTTPException(status_code=500, detail="PyPDF2 not installed on server")
    try:
        contents = await file.read()
        # Use LangChain-only ingestion for PDFs
        try:
            # Save uploaded PDF into a server uploads directory and load it from there
            uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            out_name = f"ingest_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}.pdf"
            tmp_path = uploads_dir / out_name
            tmp_path.write_bytes(contents)

            # Load and process the saved PDF; ensure the uploaded file is removed afterwards
            try:
                loader = PyPDFLoader(str(tmp_path))
                pages = loader.load()

                # Combine all page text into a single document (embed whole PDF)
                full_text_parts = [p.page_content for p in pages if (p.page_content and len(p.page_content.split()) > 0)]
                full_text = "\n\n".join(full_text_parts).strip()
                if len(full_text.split()) <= 20:
                    return {"inserted_count": 0, "ids": []}

                schema = {
                    "properties": {
                        "title": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "hasCode": {"type": "boolean"},
                    },
                    "required": ["title", "keywords", "hasCode"],
                }

                document_transformer = create_metadata_tagger(metadata_schema=schema, llm=llm)

                # Create a single Document containing the whole PDF text and tag it
                whole_doc = Document(page_content=full_text, metadata={"source": file.filename})
                docs = document_transformer.transform_documents([whole_doc])

                # Store the single whole-document into MongoDB vectorstore
                vectorstore = MongoDBAtlasVectorSearch.from_documents(docs, embeddings, collection=collection)

                return {"inserted_count": len(docs), "ids": []}
            finally:
                # cleanup: remove the uploaded file from disk
                try:
                    if tmp_path and tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    # swallow cleanup errors; nothing further to do
                    pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF ingestion failed: {e}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def query(inreq: QueryIn):
    try:
        question = inreq.question
        print(question)
        top_k = int(inreq.top_k or 4)
        # Use LangChain embeddings to compute query vector
        try:
            try:
                q_emb = embeddings.embed_query(question)
            except Exception:
                q_emb = embeddings.embed_documents([question])[0]

            # fetch stored docs with embeddings from MongoDB collection
            docs = list(collection.find({}, {"text": 1, "metadata": 1, "embedding": 1}))
            scored = []
            for d in docs:
                emb = d.get("embedding")
                if not emb:
                    continue
                score = _cosine_similarity(q_emb, emb)
                scored.append((score, d))
            scored.sort(key=lambda x: x[0], reverse=True)
            top_docs = [d for _, d in scored[:top_k]]

            # Build a context with the top docs
            context = "\n\n".join([f"{idx+1}. {d.get('text')}" for idx, d in enumerate(top_docs)])

            prompt = (
                "You are a helpful assistant for bill documents. Use the provided context to answer the question.\n\n"
                f"CONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nAnswer concisely and truthfully. If not in context, say you don't know."
            )

            # Use LangChain ChatOpenAI (gpt-4o-mini) to answer
            answer = llm.invoke(prompt)
            print(answer)
            sources = [{"text": d.get("text"), "metadata": d.get("metadata", {})} for d in top_docs]
            return {"answer": answer.content, "sources": sources}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
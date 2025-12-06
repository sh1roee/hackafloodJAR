"""
RAG Query Engine
Handles query processing, embedding, retrieval, and LLM response generation
"""

import os
from typing import Dict, List
import logging

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from chromadb_store import ChromaDBStore
from core.commodity_mappings import translate_tagalog_to_english, extract_commodity_from_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryEngine:
    """RAG query engine for price information"""
    
    def __init__(self, openai_api_key: str, chromadb_api_key: str):
        """
        Initialize query engine
        
        Args:
            openai_api_key: OpenAI API key
            chromadb_api_key: ChromaDB API key
        """
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=openai_api_key
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
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
        
        logger.info("✓ Query engine initialized")
    
    def process_query(self, user_query: str, top_k: int = 5, use_llm: bool = True) -> Dict:
        """
        Process a user query and return price information
        
        Args:
            user_query: User's question (in Tagalog or English)
            top_k: Number of results to retrieve
            use_llm: Whether to use LLM for response generation
            
        Returns:
            Response dictionary with answer and sources
        """
        try:
            logger.info(f"\nQuery: {user_query}")
            
            # Step 1: Translate Tagalog to English
            translated_query = translate_tagalog_to_english(user_query)
            logger.info(f"Translated: {translated_query}")
            
            # Step 2: Generate query embedding
            query_embedding = self.embeddings.embed_query(translated_query)
            
            # Step 3: Search ChromaDB
            search_results = self.chromadb.search_prices(query_embedding, n_results=top_k)
            
            if not search_results['success']:
                return {
                    "success": False,
                    "error": "Search failed",
                    "details": search_results.get('error')
                }
            
            if search_results['count'] == 0:
                return {
                    "success": True,
                    "answer": "Sorry, I couldn't find price information for that commodity in the database.",
                    "sources": []
                }
            
            # Extract results
            results = search_results['results']
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            distances = results['distances'][0] if results['distances'] else []
            
            # Prepare sources
            sources = []
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                sources.append({
                    "text": doc,
                    "metadata": metadata,
                    "relevance_score": 1 - distance  # Convert distance to similarity
                })
            
            # If not using LLM, return raw results
            if not use_llm:
                return {
                    "success": True,
                    "query": user_query,
                    "translated_query": translated_query,
                    "sources": sources,
                    "count": len(sources)
                }
            
            # Step 4: Generate LLM response
            answer = self._generate_llm_response(user_query, sources)
            
            return {
                "success": True,
                "query": user_query,
                "answer": answer,
                "sources": sources,
                "count": len(sources)
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_llm_response(self, user_query: str, sources: List[Dict]) -> str:
        """
        Generate LLM response using retrieved context
        
        Args:
            user_query: Original user query
            sources: Retrieved price data sources
            
        Returns:
            Generated answer
        """
        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            metadata = source['metadata']
            commodity = metadata.get('commodity', 'Unknown')
            price = metadata.get('price', 0)
            spec = metadata.get('specification', '')
            date = metadata.get('date', '')
            
            context_part = f"{i}. {commodity}: ₱{price:.2f}"
            if spec:
                context_part += f" ({spec})"
            context_part += f" - {date}"
            
            context_parts.append(context_part)
        
        context = "\n".join(context_parts)
        
        # Create prompt - Complete Tagalog translation
        prompt = f"""Ikaw ay isang helpful assistant para sa mga magsasaka at mamimili sa Pilipinas. Nagbibigay ka ng impormasyon tungkol sa presyo ng mga produkto mula sa Department of Agriculture para sa NCR.

DATOS NG PRESYO:
{context}

TANONG NG USER: {user_query}

INSTRUCTIONS:
- Sagutin sa ganitong format: "Sa petsang [buwan at araw], ang presyo ng [produkto] ay ₱[presyo] [unit] sa [lokasyon]"
- HALIMBAWA NG TAMANG SAGOT:
  * Rice/kilo: "Sa petsang Disyembre 5, ang presyo ng bigas ay ₱211.00 bawat kilo sa NCR"
  * Egg/piece: "Sa petsang Disyembre 5, ang presyo ng itlog ay ₱8.25 bawat piraso sa NCR"
  * Bundle: "Sa petsang Disyembre 5, ang presyo ng talong ay ₱202.29 bawat tali sa NCR"
  * Bottle: "Sa petsang Disyembre 5, ang presyo ng mantika ay ₱90.60 bawat bote sa NCR"

- UNIT TRANSLATION (lahat Tagalog):
  * "/kg" o "pcs/kg" o "per kilogram" = "bawat kilo"
  * "/pc" o "per piece" o "grams/pc" = "bawat piraso"
  * "bundles" o "bundle" = "bawat tali"
  * "/bottle" o "ml/bottle" = "bawat bote"
  * "/liter" o "ml" = "bawat litro"
  * "/head" o "head" = "bawat ulo"
  * "pcs" = "piraso"
  * "kg" = "kilo"
  * "medium" = "katamtaman"
  * "large" = "malaki"
  * "small" = "maliit"
  * Kung walang specific unit, gamitin "bawat kilo"

- COMMODITY TRANSLATION (gawing Tagalog):
  * rice = bigas
  * tomato = kamatis
  * chicken = manok
  * pork = baboy
  * beef = baka
  * egg = itlog
  * eggplant = talong
  * fish = isda
  * cooking oil = mantika
  * onion = sibuyas
  * garlic = bawang
  * ginger = luya
  * corn = mais
  * salt = asin
  * sugar = asukal
  * cabbage = repolyo
  * carrot = karot
  * potato = patatas
  * banana = saging
  * mango = mangga
  * watermelon = pakwan
  * papaya = papaya
  * avocado = abukado
  * chili = sili
  * squash = kalabasa

- LAHAT NG SALITA SA TAGALOG:
  * "local" = "lokal"
  * "imported" = "imported" (pwedeng "angkat")
  * "fresh" = "sariwa"
  * "frozen" = "nagyelo"
  * "whole" = "buo"
  * "per" = "bawat"

- Tagalog lang ang sagot
- Maikli at tumpak
- Laging may peso symbol (₱)
- Isama ang specification kung meron pero i-translate sa Tagalog

SAGOT MO:"""
        
        # Generate response
        response = self.llm.invoke(prompt)
        
        return response.content
    
    def query_sms_format(self, user_query: str) -> str:
        """
        Generate SMS-optimized response (short and concise)
        
        Args:
            user_query: User query
            
        Returns:
            Short SMS response
        """
        result = self.process_query(user_query, top_k=3, use_llm=True)
        
        if not result['success']:
            return "Sorry, I couldn't find that information."
        
        # Get answer and truncate if too long for SMS
        answer = result.get('answer', '')
        
        # SMS limit is typically 160 characters
        # Let's aim for 150 to be safe
        if len(answer) > 150:
            # Try to truncate at a sentence boundary
            sentences = answer.split('.')
            short_answer = sentences[0] + '.'
            if len(short_answer) > 150:
                short_answer = answer[:147] + '...'
            return short_answer
        
        return answer

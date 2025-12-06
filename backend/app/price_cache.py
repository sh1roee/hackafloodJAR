"""
Price Cache System
Cost-efficient alternative to RAG for simple price lookups
Stores today's prices in memory for instant responses
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from chromadb_store import ChromaDBStore
from core.commodity_mappings import TAGALOG_TO_ENGLISH, extract_location_from_query, extract_commodity_from_query

logger = logging.getLogger(__name__)


class PriceCache:
    """
    In-memory cache for today's commodity prices
    Eliminates need for embeddings + LLM on every query
    """
    
    def __init__(self, chromadb_store: ChromaDBStore):
        self.chromadb = chromadb_store
        self.cache: Dict[str, List[Dict]] = {}
        self.last_updated: Optional[datetime] = None
        self.cache_duration = timedelta(hours=12)  # Refresh every 12 hours
        
    def _needs_refresh(self) -> bool:
        """Check if cache needs refreshing"""
        if not self.last_updated:
            return True
        return datetime.now() - self.last_updated > self.cache_duration
    
    def refresh_cache(self):
        """
        Load all today's prices from ChromaDB into memory
        This is called once per day, not on every query
        """
        try:
            logger.info("🔄 Refreshing price cache...")
            
            # Get all entries from ChromaDB
            stats = self.chromadb.get_collection_stats()
            total_entries = stats.get('total_entries', 0)
            
            if total_entries == 0:
                logger.warning("⚠️ No entries in ChromaDB")
                return
            
            # Fetch all entries (expensive but done only once)
            collection = self.chromadb.collection
            results = collection.get(
                limit=total_entries,
                include=['metadatas']
            )
            
            # Organize by commodity name
            self.cache.clear()
            
            for metadata in results['metadatas']:
                commodity = metadata.get('commodity', '').lower()
                
                # Store under both English and Tagalog names
                if commodity not in self.cache:
                    self.cache[commodity] = []
                
                self.cache[commodity].append({
                    'commodity': metadata.get('commodity'),
                    'price': metadata.get('price'),
                    'specification': metadata.get('specification', ''),
                    'unit': metadata.get('unit', 'peso'),
                    'date': metadata.get('date'),
                    'location': metadata.get('location', 'NCR'),
                    'category': metadata.get('category', '')
                })
                
                # Also index by Tagalog name if exists
                for tagalog, english in TAGALOG_TO_ENGLISH.items():
                    if english in commodity:
                        if tagalog not in self.cache:
                            self.cache[tagalog] = []
                        self.cache[tagalog].append(self.cache[commodity][-1])
            
            self.last_updated = datetime.now()
            logger.info(f"✅ Cache refreshed with {len(self.cache)} commodity variants")
            
        except Exception as e:
            logger.error(f"❌ Cache refresh failed: {e}")
    
    def simple_lookup(self, query: str) -> Optional[Dict]:
        """
        Fast lookup without LLM or embeddings
        
        Args:
            query: Simple query like "magkano kamatis" or "rice price"
            
        Returns:
            Price data or None if not found
        """
        # Refresh cache if needed
        if self._needs_refresh():
            self.refresh_cache()
        
        query_lower = query.lower()
        
        # Extract location (handles city → NCR mapping)
        # Default to 'NCR' when no explicit location found
        location = extract_location_from_query(query) or 'NCR'
        
        # Detect commodity using helper (more precise than substring)
        detected = extract_commodity_from_query(query)
        found_prices = None
        if detected:
            key = detected.lower()
            # Try exact key first
            if key in self.cache:
                found_prices = self.cache[key]
            else:
                # Fallback: search close matches
                for commodity_key, prices in self.cache.items():
                    if commodity_key == key or key in commodity_key:
                        found_prices = prices
                        break
        else:
            # Fallback to conservative substring search across cache keys
            for commodity_key, prices in self.cache.items():
                # Match whole word tokens to avoid accidental matches
                tokens = query_lower.replace(',', ' ').split()
                if commodity_key in tokens:
                    found_prices = prices
                    break
        
        if not found_prices:
            return None
        
        # If a location was specified, prefer entries matching that location
        if location:
            loc_matches = [p for p in found_prices if p.get('location', '').lower() == location.lower()]
            if loc_matches:
                # Prefer simplest specification if multiple
                loc_matches.sort(key=lambda p: (p.get('specification','').lower() not in ['per kilogram','per kilo','/kg'], p.get('price', 0)))
                return loc_matches[0]
        
        # If multiple variants, return the first entry as a simple heuristic
        # (e.g., "Regular Milled Rice" is more common than "Basmati")
        # For now, just return first one
        return found_prices[0]
    
    def format_simple_response(self, price_data: Dict, user_query: str) -> str:
        """
        Generate simple Tagalog response without LLM
        
        Args:
            price_data: Price information
            user_query: Original query
            
        Returns:
            Formatted Tagalog response
        """
        commodity = price_data.get('commodity', 'produkto')
        price = price_data.get('price', 0)
        spec = price_data.get('specification', '')
        date_str = price_data.get('date', '')
        
        # Translate commodity to Tagalog if needed
        commodity_tagalog = commodity
        for tagalog, english in TAGALOG_TO_ENGLISH.items():
            if english in commodity.lower():
                commodity_tagalog = tagalog
                break
        
        # Detect unit from specification
        unit = "bawat kilo"
        spec_lower = spec.lower()
        if "piece" in spec_lower or "/pc" in spec_lower:
            unit = "bawat piraso"
        elif "bundle" in spec_lower:
            unit = "bawat tali"
        elif "bottle" in spec_lower:
            unit = "bawat bote"
        elif "head" in spec_lower:
            unit = "bawat ulo"
        elif "liter" in spec_lower:
            unit = "bawat litro"
        
        # Format date consistently (always show explicit date)
        month_tagalog = {
            1: "Enero", 2: "Pebrero", 3: "Marso", 4: "Abril",
            5: "Mayo", 6: "Hunyo", 7: "Hulyo", 8: "Agosto",
            9: "Setyembre", 10: "Oktubre", 11: "Nobyembre", 12: "Disyembre"
        }
        date_obj = None
        try:
            if date_str:
                date_obj = datetime.fromisoformat(date_str)
        except Exception:
            date_obj = None
        if not date_obj:
            date_obj = datetime.now()
        date_formatted = f"{month_tagalog[date_obj.month]} {date_obj.day}, {date_obj.year}"
        
        # Build response
        # Respect location from the price data (Laguna, NCR, etc.)
        location = price_data.get('location', 'NCR')
        response = f"Sa petsang {date_formatted}, ang presyo ng {commodity_tagalog} ay ₱{price:.2f} {unit} sa {location}."
        
        # Add specification if important
        if spec and spec != commodity:
            spec_tagalog = spec
            if "local" in spec_lower:
                spec_tagalog = spec.replace("local", "lokal").replace("Local", "Lokal")
            if "imported" in spec_lower:
                spec_tagalog = spec.replace("imported", "imported")
            
            if spec_tagalog != spec:
                response += f" ({spec_tagalog})"
        
        return response
    
    def query(self, user_query: str) -> Dict:
        """
        Main query method - tries simple lookup first, falls back to RAG
        
        Args:
            user_query: User's question
            
        Returns:
            Response dictionary
        """
        # Try simple lookup first (FAST, FREE)
        price_data = self.simple_lookup(user_query)
        
        if price_data:
            answer = self.format_simple_response(price_data, user_query)
            return {
                "success": True,
                "query": user_query,
                "answer": answer,
                "method": "cache",  # Shows we used cache, not LLM
                "cost": 0  # No API calls!
            }
        
        # If simple lookup fails, return "not found"
        return {
            "success": False,
            "query": user_query,
            "answer": "Pasensya po, walang nakitang presyo para sa produktong iyan.",
            "method": "cache",
            "cost": 0
        }


# Global instance (initialized in main.py)
price_cache: Optional[PriceCache] = None

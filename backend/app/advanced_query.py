"""
Advanced Query Handler
Supports multi-product, comparison, budget, and category queries
"""

from typing import Dict, List, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class AdvancedQueryHandler:
    """
    Handles complex queries beyond simple price lookups
    - Multi-product: "kamatis, sibuyas, bawang"
    - Comparison: "ano mas mura, manok o baboy?"
    - Budget: "ano pwede bilhin ng 500 pesos?"
    - Category: "presyo ng lahat ng gulay"
    """
    
    def __init__(self, price_cache):
        self.price_cache = price_cache
        
        # Category keywords
        self.category_keywords = {
            'gulay': ['vegetables', 'veggie'],
            'karne': ['meat', 'beef', 'pork', 'chicken'],
            'isda': ['fish'],
            'prutas': ['fruit', 'fruits'],
            'bigas': ['rice'],
            'pampalasa': ['spices'],
        }
    
    def detect_query_type(self, query: str) -> str:
        """
        Detect what type of query this is
        
        Returns: 'multi', 'comparison', 'budget', 'category', 'cheapest', or 'single'
        """
        query_lower = query.lower()
        
        # Cheapest/Most expensive query (pinakamura, pinakamahal, cheapest, most expensive)
        if any(word in query_lower for word in ['pinakamura', 'pinakamahal', 'cheapest', 'most expensive', 'least expensive']):
            return 'cheapest'
        
        # Comparison (has "mas mura", "mas mahal", "compare", or "o" between products)
        if any(word in query_lower for word in ['mas mura', 'mas mahal', 'compare', 'alin', 'sino']):
            return 'comparison'
        
        # Budget (has peso amount)
        if re.search(r'₱?\d+|piso|peso', query_lower) and any(w in query_lower for w in ['pwede', 'bilhin', 'buy', 'budget']):
            return 'budget'
        
        # Category (has "lahat", "all")
        if any(word in query_lower for word in ['lahat', 'all', 'mga']) and not ',' in query:
            return 'category'
        
        # Multi-product (has comma or "at")
        if ',' in query or ' at ' in query_lower:
            return 'multi'
        
        return 'single'
    
    def handle_multi_product(self, query: str) -> Dict:
        """
        Handle multi-product queries like "kamatis, sibuyas, bawang"
        
        Returns list of prices for each product
        """
        # Extract product names (split by comma or "at")
        products = re.split(r',|\s+at\s+', query.lower())
        products = [p.strip() for p in products if p.strip()]
        
        # Filter out common words
        stop_words = ['magkano', 'presyo', 'ng', 'sa', 'ang', 'ncr', 'metro', 'manila']
        products = [p for p in products if p not in stop_words]
        
        if not products:
            return {
                "success": False,
                "error": "Walang nakitang produkto sa tanong"
            }
        
        results = []
        total_price = 0
        
        for product in products:
            price_data = self.price_cache.simple_lookup(product)
            
            if price_data:
                price = price_data.get('price', 0)
                commodity = price_data.get('commodity', product)
                spec = price_data.get('specification', '')
                
                # Translate commodity to Tagalog
                from core.commodity_mappings import ENGLISH_TO_TAGALOG
                commodity_tag = ENGLISH_TO_TAGALOG.get(commodity.lower(), commodity)
                
                # Detect unit
                unit = self._detect_unit(spec)
                
                results.append({
                    'product': commodity_tag,
                    'price': price,
                    'unit': unit,
                    'specification': spec
                })
                total_price += price
            else:
                results.append({
                    'product': product,
                    'price': None,
                    'error': 'Hindi nakita'
                })
        
        # Format response in Tagalog
        response_parts = []
        for item in results:
            if item.get('price'):
                response_parts.append(
                    f"• {item['product']}: ₱{item['price']:.2f} {item['unit']}"
                )
            else:
                response_parts.append(
                    f"• {item['product']}: Hindi available"
                )
        
        response = "Narito ang mga presyo sa NCR:\n\n" + "\n".join(response_parts)
        
        # Add total if multiple items found
        valid_items = [r for r in results if r.get('price')]
        if len(valid_items) > 1:
            response += f"\n\nKabuuang presyo: ₱{total_price:.2f}"
        
        return {
            "success": True,
            "answer": response,
            "method": "multi_product",
            "items": results,
            "total": total_price
        }
    
    def handle_comparison(self, query: str) -> Dict:
        """
        Handle comparison queries like "ano mas mura, manok o baboy?"
        """
        # Extract products being compared
        # Split by "o" or "or"
        parts = re.split(r'\so\s|\sor\s', query.lower())
        
        products = []
        for part in parts:
            # Remove common words
            clean = re.sub(r'(ano|mas|mura|mahal|magkano|presyo|ng|sa|ang)', '', part).strip()
            if clean:
                products.append(clean)
        
        if len(products) < 2:
            return {
                "success": False,
                "error": "Kailangan ng dalawa o higit pang produkto para sa comparison"
            }
        
        # Get prices for each product
        price_data = []
        for product in products:
            data = self.price_cache.simple_lookup(product)
            if data:
                price_data.append(data)
        
        if len(price_data) < 2:
            return {
                "success": False,
                "error": "Hindi nakita ang ilan sa mga produkto"
            }
        
        # Sort by price
        sorted_items = sorted(price_data, key=lambda x: x.get('price', 999999))
        cheapest = sorted_items[0]
        most_expensive = sorted_items[-1]
        
        # Translate to Tagalog
        from core.commodity_mappings import ENGLISH_TO_TAGALOG
        
        cheapest_name = ENGLISH_TO_TAGALOG.get(cheapest['commodity'].lower(), cheapest['commodity'])
        expensive_name = ENGLISH_TO_TAGALOG.get(most_expensive['commodity'].lower(), most_expensive['commodity'])
        
        # Build response
        response = f"**Pinakamura:** {cheapest_name} - ₱{cheapest['price']:.2f} {self._detect_unit(cheapest.get('specification', ''))}\n\n"
        response += f"**Pinakamahal:** {expensive_name} - ₱{most_expensive['price']:.2f} {self._detect_unit(most_expensive.get('specification', ''))}\n\n"
        
        # Add all items
        response += "**Buong listahan:**\n"
        for idx, item in enumerate(sorted_items, 1):
            name = ENGLISH_TO_TAGALOG.get(item['commodity'].lower(), item['commodity'])
            unit = self._detect_unit(item.get('specification', ''))
            response += f"{idx}. {name}: ₱{item['price']:.2f} {unit}\n"
        
        difference = most_expensive['price'] - cheapest['price']
        response += f"\nDifference: ₱{difference:.2f}"
        
        return {
            "success": True,
            "answer": response,
            "method": "comparison",
            "cheapest": cheapest,
            "most_expensive": most_expensive
        }
    
    def handle_budget(self, query: str) -> Dict:
        """
        Handle budget queries like "ano pwede bilhin ng 500 pesos?"
        """
        # Extract budget amount
        match = re.search(r'₱?(\d+)', query)
        if not match:
            return {
                "success": False,
                "error": "Hindi nakita ang budget amount"
            }
        
        budget = float(match.group(1))
        
        # Get all cached prices
        affordable_items = []
        
        for commodity_key, prices in self.price_cache.cache.items():
            for price_data in prices:
                price = price_data.get('price', 0)
                if price > 0 and price <= budget:
                    affordable_items.append(price_data)
        
        if not affordable_items:
            return {
                "success": True,
                "answer": f"Walang produkto na mas mababa sa ₱{budget:.2f} sa database."
            }
        
        # Sort by price (cheapest first)
        affordable_items.sort(key=lambda x: x.get('price', 0))
        
        # Take top 10
        top_items = affordable_items[:10]
        
        # Translate to Tagalog
        from core.commodity_mappings import ENGLISH_TO_TAGALOG
        
        response = f"**Pwede mong bilhin ng ₱{budget:.2f}:**\n\n"
        
        for idx, item in enumerate(top_items, 1):
            commodity = item.get('commodity', '')
            price = item.get('price', 0)
            spec = item.get('specification', '')
            
            name = ENGLISH_TO_TAGALOG.get(commodity.lower(), commodity)
            unit = self._detect_unit(spec)
            quantity = int(budget / price) if price > 0 else 0
            
            response += f"{idx}. {name}: ₱{price:.2f} {unit}"
            if quantity > 1:
                response += f" (Pwede ka bumili ng {quantity} {unit})"
            response += "\n"
        
        return {
            "success": True,
            "answer": response,
            "method": "budget",
            "budget": budget,
            "items_count": len(top_items)
        }
    
    def handle_category(self, query: str) -> Dict:
        """
        Handle category queries like "presyo ng lahat ng gulay"
        """
        query_lower = query.lower()
        
        # Detect category
        detected_category = None
        for tag_category, eng_keywords in self.category_keywords.items():
            if tag_category in query_lower or any(kw in query_lower for kw in eng_keywords):
                detected_category = tag_category
                break
        
        if not detected_category:
            # Default to showing all
            detected_category = 'lahat'
        
        # Get all items in category
        category_items = []
        
        for commodity_key, prices in self.price_cache.cache.items():
            for price_data in prices:
                category = price_data.get('category', '').lower()
                
                # Match category
                if detected_category == 'lahat':
                    category_items.append(price_data)
                elif detected_category == 'gulay' and 'vegetable' in category:
                    category_items.append(price_data)
                elif detected_category == 'karne' and any(m in category for m in ['beef', 'pork', 'chicken', 'meat']):
                    category_items.append(price_data)
                elif detected_category == 'isda' and 'fish' in category:
                    category_items.append(price_data)
                elif detected_category == 'prutas' and 'fruit' in category:
                    category_items.append(price_data)
                elif detected_category == 'bigas' and 'rice' in category:
                    category_items.append(price_data)
                elif detected_category == 'pampalasa' and 'spice' in category:
                    category_items.append(price_data)
        
        if not category_items:
            return {
                "success": True,
                "answer": f"Walang nakitang produkto sa kategoryang '{detected_category}'."
            }
        
        # Sort by price
        category_items.sort(key=lambda x: x.get('price', 0))
        
        # Limit to 15 items
        category_items = category_items[:15]
        
        # Translate category name
        category_tagalog = {
            'gulay': 'Gulay',
            'karne': 'Karne',
            'isda': 'Isda',
            'prutas': 'Prutas',
            'bigas': 'Bigas',
            'pampalasa': 'Pampalasa',
            'lahat': 'Lahat ng Produkto'
        }
        
        from core.commodity_mappings import ENGLISH_TO_TAGALOG
        
        response = f"**Presyo ng {category_tagalog.get(detected_category, detected_category)} sa NCR:**\n\n"
        
        for idx, item in enumerate(category_items, 1):
            commodity = item.get('commodity', '')
            price = item.get('price', 0)
            spec = item.get('specification', '')
            
            name = ENGLISH_TO_TAGALOG.get(commodity.lower(), commodity)
            unit = self._detect_unit(spec)
            
            response += f"{idx}. {name}: ₱{price:.2f} {unit}\n"
        
        return {
            "success": True,
            "answer": response,
            "method": "category",
            "category": detected_category,
            "items_count": len(category_items)
        }
    
    def _detect_unit(self, specification: str) -> str:
        """Detect unit from specification"""
        spec_lower = specification.lower()
        
        if "piece" in spec_lower or "/pc" in spec_lower:
            return "bawat piraso"
        elif "bundle" in spec_lower:
            return "bawat tali"
        elif "bottle" in spec_lower:
            return "bawat bote"
        elif "head" in spec_lower:
            return "bawat ulo"
        elif "liter" in spec_lower:
            return "bawat litro"
        else:
            return "bawat kilo"
    
    def handle_cheapest(self, query: str) -> Dict:
        """
        Handle "cheapest" queries like "pinakamurang bigas" or "pinakamahal na gulay"
        
        Returns the cheapest or most expensive item in a category
        """
        query_lower = query.lower()
        
        # Determine if looking for cheapest or most expensive
        is_cheapest = any(w in query_lower for w in ['pinakamura', 'cheapest', 'least expensive'])
        is_expensive = any(w in query_lower for w in ['pinakamahal', 'most expensive'])
        
        # Detect category
        detected_category = None
        for tag_category, eng_keywords in self.category_keywords.items():
            if tag_category in query_lower or any(kw in query_lower for kw in eng_keywords):
                detected_category = tag_category
                break
        
        # If no category detected, search all items
        if not detected_category:
            detected_category = 'lahat'
        
        # Get all items in category
        category_items = []
        
        for commodity_key, prices in self.price_cache.cache.items():
            for price_data in prices:
                category = price_data.get('category', '').lower()
                commodity_name = price_data.get('commodity', '').lower()
                
                # Match category or commodity name
                include = False
                
                if detected_category == 'lahat':
                    include = True
                elif detected_category == 'gulay' and 'vegetable' in category:
                    include = True
                elif detected_category == 'karne' and any(m in category for m in ['beef', 'pork', 'chicken', 'meat']):
                    include = True
                elif detected_category == 'isda' and 'fish' in category:
                    include = True
                elif detected_category == 'prutas' and 'fruit' in category:
                    include = True
                elif detected_category == 'bigas' and ('rice' in category or 'rice' in commodity_name):
                    include = True
                elif detected_category == 'pampalasa' and 'spice' in category:
                    include = True
                
                if include and price_data.get('price', 0) > 0:
                    category_items.append(price_data)
        
        if not category_items:
            return {
                "success": False,
                "answer": f"Walang nakitang produkto sa kategoryang '{detected_category}'."
            }
        
        # Sort by price
        category_items.sort(key=lambda x: x.get('price', 0))
        
        # Translate category name
        category_tagalog = {
            'gulay': 'Gulay',
            'karne': 'Karne',
            'isda': 'Isda',
            'prutas': 'Prutas',
            'bigas': 'Bigas',
            'pampalasa': 'Pampalasa',
            'lahat': 'Lahat'
        }
        
        from core.commodity_mappings import ENGLISH_TO_TAGALOG
        
        category_name = category_tagalog.get(detected_category, detected_category)
        
        if is_cheapest:
            # Show cheapest items (first 5)
            top_items = category_items[:5]
            cheapest = top_items[0]
            
            cheapest_name = ENGLISH_TO_TAGALOG.get(cheapest['commodity'].lower(), cheapest['commodity'])
            
            response = f"**🏆 Pinakamura sa {category_name}:**\n\n"
            response += f"**{cheapest_name}** - ₱{cheapest['price']:.2f} {self._detect_unit(cheapest.get('specification', ''))}\n"
            response += f"({cheapest.get('specification', '')})\n\n"
            
            if len(top_items) > 1:
                response += f"**Top 5 Pinakamura:**\n"
                for idx, item in enumerate(top_items, 1):
                    name = ENGLISH_TO_TAGALOG.get(item['commodity'].lower(), item['commodity'])
                    unit = self._detect_unit(item.get('specification', ''))
                    spec = item.get('specification', '')
                    response += f"{idx}. {name} - ₱{item['price']:.2f} {unit}\n"
                    if spec:
                        response += f"   ({spec})\n"
            
            return {
                "success": True,
                "answer": response,
                "method": "cheapest",
                "category": detected_category,
                "cheapest": cheapest,
                "items_shown": len(top_items)
            }
        
        elif is_expensive:
            # Show most expensive items (last 5)
            top_items = category_items[-5:][::-1]  # Reverse to show highest first
            most_expensive = top_items[0]
            
            expensive_name = ENGLISH_TO_TAGALOG.get(most_expensive['commodity'].lower(), most_expensive['commodity'])
            
            response = f"**🏆 Pinakamahal sa {category_name}:**\n\n"
            response += f"**{expensive_name}** - ₱{most_expensive['price']:.2f} {self._detect_unit(most_expensive.get('specification', ''))}\n"
            response += f"({most_expensive.get('specification', '')})\n\n"
            
            if len(top_items) > 1:
                response += f"**Top 5 Pinakamahal:**\n"
                for idx, item in enumerate(top_items, 1):
                    name = ENGLISH_TO_TAGALOG.get(item['commodity'].lower(), item['commodity'])
                    unit = self._detect_unit(item.get('specification', ''))
                    spec = item.get('specification', '')
                    response += f"{idx}. {name} - ₱{item['price']:.2f} {unit}\n"
                    if spec:
                        response += f"   ({spec})\n"
            
            return {
                "success": True,
                "answer": response,
                "method": "most_expensive",
                "category": detected_category,
                "most_expensive": most_expensive,
                "items_shown": len(top_items)
            }
        
        # Default: show both cheapest and most expensive
        cheapest = category_items[0]
        most_expensive = category_items[-1]
        
        cheapest_name = ENGLISH_TO_TAGALOG.get(cheapest['commodity'].lower(), cheapest['commodity'])
        expensive_name = ENGLISH_TO_TAGALOG.get(most_expensive['commodity'].lower(), most_expensive['commodity'])
        
        response = f"**{category_name} Price Range:**\n\n"
        response += f"**Pinakamura:** {cheapest_name} - ₱{cheapest['price']:.2f} {self._detect_unit(cheapest.get('specification', ''))}\n"
        response += f"**Pinakamahal:** {expensive_name} - ₱{most_expensive['price']:.2f} {self._detect_unit(most_expensive.get('specification', ''))}\n"
        
        return {
            "success": True,
            "answer": response,
            "method": "price_range",
            "category": detected_category,
            "cheapest": cheapest,
            "most_expensive": most_expensive
        }
    
    def _detect_unit(self, specification: str) -> str:
        """Detect unit from specification"""
        spec_lower = specification.lower()
        
        if "piece" in spec_lower or "/pc" in spec_lower:
            return "bawat piraso"
        elif "bundle" in spec_lower:
            return "bawat tali"
        elif "bottle" in spec_lower:
            return "bawat bote"
        elif "head" in spec_lower:
            return "bawat ulo"
        elif "liter" in spec_lower:
            return "bawat litro"
        else:
            return "bawat kilo"
    
    def process(self, query: str) -> Dict:
        """
        Main entry point - detect query type and route to handler
        """
        query_type = self.detect_query_type(query)
        
        if query_type == 'cheapest':
            return self.handle_cheapest(query)
        elif query_type == 'multi':
            return self.handle_multi_product(query)
        elif query_type == 'comparison':
            return self.handle_comparison(query)
        elif query_type == 'budget':
            return self.handle_budget(query)
        elif query_type == 'category':
            return self.handle_category(query)
        else:
            # Fall back to simple lookup
            return self.price_cache.query(query)


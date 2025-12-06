"""
Text chunk generator for RAG embeddings
Creates natural language descriptions of price data
"""

from typing import Dict, List
from commodity_mappings import ENGLISH_TO_TAGALOG


class TextChunkGenerator:
    """Generate natural language text chunks from price data"""
    
    def create_chunk(self, price_data: Dict, include_tagalog: bool = True) -> str:
        """
        Create a natural language text chunk from price data
        
        Args:
            price_data: Price data dictionary
            include_tagalog: Whether to include Tagalog translation
            
        Returns:
            Natural language text chunk
        """
        commodity = price_data['commodity']
        price = price_data['price']
        date = price_data['date']
        location = price_data['location']
        spec = price_data.get('specification', '')
        category = price_data.get('category', '')
        
        # Base English description
        text_parts = []
        
        # Main price statement
        text_parts.append(f"{commodity} in {location} costs {price:.2f} pesos")
        
        # Add specification if available
        if spec:
            text_parts.append(f"Specification: {spec}")
        
        # Add date
        text_parts.append(f"Date: {date}")
        
        # Add category
        if category:
            text_parts.append(f"Category: {category}")
        
        english_text = ". ".join(text_parts) + "."
        
        # Add Tagalog variation if requested
        if include_tagalog:
            tagalog_name = ENGLISH_TO_TAGALOG.get(commodity.lower(), commodity)
            tagalog_parts = [
                f"{tagalog_name} ({commodity}) sa {location}: ₱{price:.2f}"
            ]
            
            if spec:
                tagalog_parts.append(f"Detalye: {spec}")
            
            tagalog_parts.append(f"Petsa: {date}")
            
            tagalog_text = ". ".join(tagalog_parts) + "."
            
            # Combine both
            return f"{english_text}\n{tagalog_text}"
        
        return english_text
    
    def create_multiple_variations(self, price_data: Dict) -> List[str]:
        """
        Create multiple text variations for better retrieval
        
        Args:
            price_data: Price data dictionary
            
        Returns:
            List of text variations
        """
        commodity = price_data['commodity']
        price = price_data['price']
        date = price_data['date']
        location = price_data['location']
        spec = price_data.get('specification', '')
        category = price_data.get('category', '')
        
        variations = []
        
        # Variation 1: Full detailed description
        variations.append(self.create_chunk(price_data, include_tagalog=True))
        
        # Variation 2: Question-answer format
        tagalog_name = ENGLISH_TO_TAGALOG.get(commodity.lower(), commodity)
        qa_text = f"Question: How much is {commodity} ({tagalog_name}) in {location}? Answer: ₱{price:.2f} per unit as of {date}."
        if spec:
            qa_text += f" {spec}."
        variations.append(qa_text)
        
        # Variation 3: Short price statement
        short_text = f"{commodity} ({tagalog_name}): ₱{price:.2f}/{location}/{date}"
        variations.append(short_text)
        
        return variations
    
    def create_batch_chunks(self, price_data_list: List[Dict]) -> List[str]:
        """
        Create text chunks for a batch of price data
        
        Args:
            price_data_list: List of price data dictionaries
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        for price_data in price_data_list:
            chunk = self.create_chunk(price_data, include_tagalog=True)
            chunks.append(chunk)
        
        return chunks

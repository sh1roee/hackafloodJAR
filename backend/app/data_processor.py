"""
Data processor for DA Daily Price Index PDFs
Cleans and structures price data for RAG ingestion
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Optional


class PriceDataProcessor:
    """Process and clean price data from PDF tables"""
    
    # Categories found in DA Price Index
    CATEGORIES = {
        "IMPORTED COMMERCIAL RICE": "rice",
        "LOCAL COMMERCIAL RICE": "rice",
        "CORN PRODUCTS": "corn",
        "FISH PRODUCTS": "fish",
        "BEEF MEAT PRODUCTS": "beef",
        "PORK MEAT PRODUCTS": "pork",
        "CHICKEN MEAT PRODUCTS": "chicken",
        "LOWLAND VEGETABLES": "vegetables",
        "HIGHLAND VEGETABLES": "vegetables",
        "SPICES": "spices",
        "FRUITS": "fruits",
        "COOKING OIL": "oil",
    }
    
    def __init__(self):
        self.current_category = None
    
    def extract_date_from_filename(self, filename: str) -> str:
        """
        Extract date from PDF filename
        
        Args:
            filename: PDF filename like 'daily_price_index_December_5_2025.pdf'
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        try:
            # Try to parse date from filename
            # Format: daily_price_index_December_5_2025.pdf
            match = re.search(r'(\w+)_(\d+)_(\d{4})', filename)
            if match:
                month_name, day, year = match.groups()
                date_str = f"{month_name} {day}, {year}"
                parsed_date = datetime.strptime(date_str, "%B %d, %Y")
                return parsed_date.strftime("%Y-%m-%d")
        except:
            pass
        
        # Default to today if can't parse
        return datetime.now().strftime("%Y-%m-%d")
    
    def clean_price_value(self, price_str: str) -> Optional[float]:
        """
        Clean and convert price string to float
        
        Args:
            price_str: Price string like "142.54" or "n/a"
            
        Returns:
            Float price or None if invalid
        """
        if not price_str or price_str == 'None':
            return None
        
        price_str = str(price_str).strip()
        
        # Handle n/a, N/A, etc.
        if price_str.lower() in ['n/a', 'na', '', '-']:
            return None
        
        # Remove currency symbols and commas
        price_str = price_str.replace('₱', '').replace('P', '').replace(',', '')
        
        try:
            return float(price_str)
        except ValueError:
            return None
    
    def is_category_header(self, text: str) -> bool:
        """Check if text is a category header"""
        if not text or text == 'None':
            return False
        
        text = str(text).strip().upper()
        return any(cat in text for cat in self.CATEGORIES.keys())
    
    def get_category_from_header(self, text: str) -> Optional[str]:
        """Extract category from header text"""
        text = str(text).strip().upper()
        
        for header, category in self.CATEGORIES.items():
            if header in text:
                return category
        
        return None
    
    def clean_commodity_name(self, name: str) -> str:
        """Clean commodity name"""
        if not name or name == 'None':
            return ""
        
        name = str(name).strip()
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        return name
    
    def clean_specification(self, spec: str) -> str:
        """Clean specification text"""
        if not spec or spec == 'None':
            return ""
        
        spec = str(spec).strip()
        
        # Remove extra whitespace
        spec = ' '.join(spec.split())
        
        return spec
    
    def process_table(self, df: pd.DataFrame, page_num: int) -> List[Dict]:
        """
        Process a single table and extract structured price data
        
        Args:
            df: DataFrame from PDF table
            page_num: Page number
            
        Returns:
            List of price data dictionaries
        """
        price_entries = []
        self.current_category = None
        
        # Clean column names
        df.columns = [str(col).replace('\n', ' ').strip() if col else 'Unknown' for col in df.columns]
        
        # Find price column
        price_col = None
        for col in df.columns:
            if 'PRICE' in str(col).upper():
                price_col = col
                break
        
        if not price_col:
            return []
        
        # Find commodity and specification columns
        commodity_col = None
        spec_col = None
        
        for col in df.columns:
            col_upper = str(col).upper()
            if 'COMMODITY' in col_upper and not commodity_col:
                commodity_col = col
            elif 'SPECIFICATION' in col_upper and not spec_col:
                spec_col = col
        
        if not commodity_col:
            # Use first column as commodity
            commodity_col = df.columns[0]
        
        # Process each row
        for idx, row in df.iterrows():
            commodity = row.get(commodity_col, "")
            specification = row.get(spec_col, "") if spec_col else ""
            price = row.get(price_col, "")
            
            # Check if this is a category header
            if self.is_category_header(commodity):
                self.current_category = self.get_category_from_header(commodity)
                continue
            
            # Clean data
            commodity_clean = self.clean_commodity_name(commodity)
            spec_clean = self.clean_specification(specification)
            price_clean = self.clean_price_value(price)
            
            # Skip if no valid data
            if not commodity_clean or not price_clean:
                continue
            
            # Skip header rows
            if 'COMMODITY' in commodity_clean.upper():
                continue
            
            # Create entry
            entry = {
                "commodity": commodity_clean,
                "category": self.current_category or "other",
                "specification": spec_clean,
                "price": price_clean,
                "unit": "peso",
                "location": "NCR",
                "page": page_num
            }
            
            price_entries.append(entry)
        
        return price_entries
    
    def process_all_tables(self, tables: List[pd.DataFrame], pdf_filename: str) -> List[Dict]:
        """
        Process all tables from a PDF
        
        Args:
            tables: List of DataFrames from PDF
            pdf_filename: Name of source PDF file
            
        Returns:
            List of all price entries
        """
        all_entries = []
        date_str = self.extract_date_from_filename(pdf_filename)
        
        for table in tables:
            if table.shape[0] <= 5:  # Skip small tables (likely headers/footers)
                continue
            
            page_num = table.attrs.get('page', 0)
            entries = self.process_table(table, page_num)
            
            # Add date and source to each entry
            for entry in entries:
                entry['date'] = date_str
                entry['source_pdf'] = pdf_filename
            
            all_entries.extend(entries)
        
        return all_entries
    
    def validate_entry(self, entry: Dict) -> bool:
        """
        Validate a price entry
        
        Args:
            entry: Price data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not entry.get('commodity') or not entry.get('price'):
            return False
        
        # Check price is reasonable (positive, not too high)
        price = entry.get('price')
        if price <= 0 or price > 100000:  # Max 100k pesos seems reasonable
            return False
        
        return True
    
    def get_summary_stats(self, entries: List[Dict]) -> Dict:
        """Get summary statistics of processed data"""
        if not entries:
            return {
                "total_entries": 0,
                "categories": {},
                "price_range": {"min": 0, "max": 0, "avg": 0}
            }
        
        prices = [e['price'] for e in entries if e.get('price')]
        categories = {}
        
        for entry in entries:
            cat = entry.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_entries": len(entries),
            "categories": categories,
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "avg": sum(prices) / len(prices) if prices else 0
            }
        }

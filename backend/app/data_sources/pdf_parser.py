"""
PDF Parser for DA Daily Price Index
Extracts price data from downloaded PDFs and converts to structured format
"""

import pdfplumber
import pandas as pd
from pathlib import Path
import re


class PricePDFParser:
    """Parse DA Daily Price Index PDFs and extract price tables"""
    
    def __init__(self):
        self.download_dir = Path("downloads/price_index")
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract all text from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            str: Extracted text from all pages
        """
        try:
            print(f"\nExtracting text from: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                print(f"Total pages: {len(pdf.pages)}")
                
                all_text = []
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        all_text.append(f"--- Page {i} ---\n{text}")
                
                return "\n\n".join(all_text)
                
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None
    
    def extract_tables_from_pdf(self, pdf_path):
        """
        Extract tables from PDF and convert to DataFrames
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            list: List of pandas DataFrames
        """
        try:
            print(f"\nExtracting tables from: {pdf_path}")
            
            all_tables = []
            
            with pdfplumber.open(pdf_path) as pdf:
                print(f"Total pages: {len(pdf.pages)}")
                
                for i, page in enumerate(pdf.pages, 1):
                    print(f"\nProcessing page {i}...")
                    tables = page.extract_tables()
                    
                    if tables:
                        print(f"Found {len(tables)} table(s) on page {i}")
                        
                        for j, table in enumerate(tables, 1):
                            if table and len(table) > 0:
                                # Convert to DataFrame
                                # First row is usually headers
                                if len(table) > 1:
                                    headers = table[0]
                                    data = table[1:]
                                    df = pd.DataFrame(data, columns=headers)
                                else:
                                    df = pd.DataFrame(table)
                                
                                # Add metadata
                                df.attrs['page'] = i
                                df.attrs['table_num'] = j
                                
                                all_tables.append(df)
                                print(f"  Table {j}: {df.shape[0]} rows × {df.shape[1]} columns")
                    else:
                        print(f"No tables found on page {i}")
            
            print(f"\nTotal tables extracted: {len(all_tables)}")
            return all_tables
            
        except Exception as e:
            print(f"Error extracting tables: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_latest_pdf(self):
        """
        Get the path to the most recently downloaded PDF
        
        Returns:
            Path: Path to latest PDF or None
        """
        if not self.download_dir.exists():
            print("Download directory doesn't exist")
            return None
        
        pdf_files = list(self.download_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("No PDF files found")
            return None
        
        # Sort by modification time, newest first
        latest = max(pdf_files, key=lambda p: p.stat().st_mtime)
        return latest
    
    def parse_latest_pdf(self, show_text=False):
        """
        Parse the latest downloaded PDF
        
        Args:
            show_text: If True, also print extracted text
            
        Returns:
            list: List of DataFrames with price data
        """
        latest_pdf = self.get_latest_pdf()
        
        if not latest_pdf:
            print("No PDF to parse")
            return []
        
        print("="*70)
        print(f"PARSING: {latest_pdf.name}")
        print("="*70)
        
        # Extract text if requested
        if show_text:
            text = self.extract_text_from_pdf(latest_pdf)
            if text:
                print("\n" + "="*70)
                print("EXTRACTED TEXT")
                print("="*70)
                print(text[:2000])  # Show first 2000 characters
                if len(text) > 2000:
                    print(f"\n... (showing first 2000 of {len(text)} characters)")
        
        # Extract tables
        tables = self.extract_tables_from_pdf(latest_pdf)
        
        return tables


def test_parser():
    """Test the PDF parser"""
    parser = PricePDFParser()
    
    # Parse latest PDF and get tables
    tables = parser.parse_latest_pdf(show_text=True)
    
    print("\n" + "="*70)
    print("EXTRACTED TABLES AS DATAFRAMES")
    print("="*70)
    
    if tables:
        for i, df in enumerate(tables, 1):
            print(f"\n{'='*70}")
            print(f"TABLE {i} (Page {df.attrs.get('page', '?')})")
            print(f"{'='*70}")
            print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"\nFirst few rows:")
            print(df.head(10))
            print(f"\nColumn names: {list(df.columns)}")
            
            # Show data types
            print(f"\nData types:")
            print(df.dtypes)
    else:
        print("\nNo tables extracted")
    
    return tables


if __name__ == "__main__":
    print("Testing PDF Parser for DA Daily Price Index")
    print("="*70)
    tables = test_parser()

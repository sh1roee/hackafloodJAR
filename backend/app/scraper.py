"""
DA Price Index Scraper
Downloads the latest Daily Price Index PDF from DA website
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from pathlib import Path
import re


class DAPriceScraper:
    """Scrapes daily price index from DA Philippines website"""
    
    BASE_URL = "https://www.da.gov.ph/price-monitoring/"
    DOWNLOAD_DIR = Path("downloads/price_index")
    
    def __init__(self):
        """Initialize scraper and create download directory"""
        self.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_latest_price_index_link(self):
        """
        Scrape the DA website to find the latest Daily Price Index PDF link
        Returns: tuple of (date_str, pdf_url) or (None, None) if not found
        """
        try:
            print(f"Fetching DA price monitoring page: {self.BASE_URL}")
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all tables on the page
            tables = soup.find_all('table')
            
            # The Daily Price Index is usually the second table (index 1)
            # Let's look for it more specifically by checking table context
            for i, table in enumerate(tables):
                # Check if this table is in the Daily Price Index section
                # by looking at preceding headings
                prev_heading = None
                for sibling in table.find_previous_siblings():
                    if sibling.name in ['h2', 'h3', 'h4']:
                        prev_heading = sibling.get_text(strip=True)
                        break
                
                if prev_heading and 'Daily Price Index' in prev_heading:
                    print(f"Found Daily Price Index table (table #{i})")
                    
                    tbody = table.find('tbody')
                    if not tbody:
                        continue
                    
                    rows = tbody.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            date_cell = cells[0]
                            
                            # Find the download link
                            link = date_cell.find('a')
                            
                            if link and link.get('href'):
                                pdf_url = link['href']
                                date_text = date_cell.get_text(strip=True)
                                
                                # Make URL absolute if needed
                                if not pdf_url.startswith('http'):
                                    pdf_url = f"https://www.da.gov.ph{pdf_url}"
                                
                                print(f"Found latest daily price index: {date_text}")
                                return date_text, pdf_url
            
            print("No Daily Price Index links found")
            return None, None
            
        except Exception as e:
            print(f"Error scraping DA website: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def download_pdf(self, pdf_url, date_str):
        """
        Download the PDF from the given URL
        Returns: Path to downloaded file or None if failed
        """
        try:
            print(f"Downloading PDF from: {pdf_url}")
            response = self.session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            # Create filename from date
            safe_date = re.sub(r'[^\w\s-]', '', date_str).strip().replace(' ', '_')
            filename = f"daily_price_index_{safe_date}.pdf"
            filepath = self.DOWNLOAD_DIR / filename
            
            # Save PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(filepath) / 1024  # Size in KB
            print(f"Successfully downloaded: {filepath} ({file_size:.1f} KB)")
            
            return filepath
            
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return None
    
    def get_latest_daily_price_index(self):
        """
        Main function: Scrape and download the latest daily price index
        Returns: dict with download info or error
        """
        print("\n" + "="*60)
        print("DA DAILY PRICE INDEX SCRAPER")
        print("="*60)
        
        # Get the latest PDF link
        date_str, pdf_url = self.get_latest_price_index_link()
        
        if not pdf_url:
            return {
                "success": False,
                "error": "Could not find latest price index PDF"
            }
        
        # Download the PDF
        filepath = self.download_pdf(pdf_url, date_str)
        
        if not filepath:
            return {
                "success": False,
                "error": "Failed to download PDF"
            }
        
        result = {
            "success": True,
            "date": date_str,
            "url": pdf_url,
            "filepath": str(filepath),
            "downloaded_at": datetime.now().isoformat()
        }
        
        print("\n" + "="*60)
        print("DOWNLOAD COMPLETE")
        print(f"Date: {date_str}")
        print(f"File: {filepath}")
        print("="*60 + "\n")
        
        return result


def test_scraper():
    """Test function to run the scraper"""
    scraper = DAPriceScraper()
    result = scraper.get_latest_daily_price_index()
    print("\nResult:")
    print(result)


if __name__ == "__main__":
    test_scraper()

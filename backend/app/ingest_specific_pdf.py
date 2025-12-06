"""
Ingest a specific DA Price Index PDF by URL
Downloads the PDF and runs the existing ingestion pipeline
"""

import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv
from processing.ingest_pipeline import IngestionPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_URL = "https://www.da.gov.ph/wp-content/uploads/2025/12/December-6-2025-DPI-AFC.pdf"


def download_pdf(url: str, output_path: Path) -> Path:
    """Download a PDF from URL to output_path"""
    logger.info(f"Downloading PDF from: {url}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    output_path.write_bytes(resp.content)
    logger.info(f"Saved PDF to: {output_path}")
    return output_path


def main():
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API_KEY')
    chromadb_api_key = os.getenv('CHROMADB_API_KEY')

    if not openai_api_key or not chromadb_api_key:
        logger.error("Missing required API keys in .env file")
        sys.exit(1)

    # Prepare downloads folder
    base_dir = Path(__file__).parent
    downloads_dir = base_dir / "downloads" / "price_index"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = downloads_dir / "December-6-2025-DPI-AFC.pdf"

    try:
        download_pdf(PDF_URL, pdf_path)
    except Exception as e:
        logger.error(f"Failed to download PDF: {e}")
        sys.exit(1)

    # Initialize pipeline and ingest
    pipeline = IngestionPipeline(
        openai_api_key=openai_api_key,
        chromadb_api_key=chromadb_api_key
    )

    result = pipeline.ingest_pdf(pdf_path, replace_if_exists=True)

    if result.get('success'):
        logger.info("\n✅ Ingestion complete")
        logger.info(f"Date: {result.get('date')} | Entries: {result.get('entries_stored')}\n")
        stats = pipeline.get_chromadb_stats()
        logger.info(f"Collection '{stats.get('collection_name','')}' total entries: {stats.get('total_entries', 0)}")
    else:
        logger.error(f"\n❌ Ingestion failed: {result.get('error','Unknown error')}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

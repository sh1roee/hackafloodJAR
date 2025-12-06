# DA Price Monitor for Farmers

SMS-based agricultural price monitoring system for farmers in NCR, Philippines.

## Overview

This backend automatically scrapes the **Daily Price Index** from the [DA Philippines Price Monitoring](https://www.da.gov.ph/price-monitoring/) website every day and will provide price information to farmers via SMS.

## Features

- ✅ **Automated Daily Scraping**: Checks DA website every day at 8:00 AM
- ✅ **PDF Download**: Downloads latest daily price index PDF
- ✅ **Manual Triggers**: Can manually trigger scraping via API
- ✅ **Scheduler Status**: Monitor when last scrape ran and when next one will run
- 🚧 **PDF Parsing**: Extract price data from PDFs (coming next)
- 🚧 **SMS Integration**: Respond to farmer queries via SMS (coming next)
- 🚧 **Tagalog Support**: Handle queries in Tagalog (coming next)

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI application
│   ├── scraper.py       # DA website scraper
│   ├── scheduler.py     # Daily scheduler
│   └── downloads/       # Downloaded PDFs (auto-created)
│       └── price_index/
├── requirements.txt     # Python dependencies
└── .env                # Environment variables
```

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Server

```bash
cd backend/app
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

## API Endpoints

### Health Check

```
GET /health
```

### Scrape Latest Price Index

```
GET /scrape-latest
```

Manually download the latest daily price index PDF from DA website.

### Scheduler Status

```
GET /scheduler/status
```

Check when the scheduler last ran and when it will run next.

### Run Scheduler Now

```
POST /scheduler/run-now
```

Manually trigger the daily scrape job immediately.

### Download Info

```
GET /download-info
```

List all downloaded PDF files.

## How It Works

1. **Daily Schedule**: At 8:00 AM every day, the scheduler automatically:

   - Visits https://www.da.gov.ph/price-monitoring/
   - Finds the latest "Daily Price Index" PDF
   - Downloads it to `backend/app/downloads/price_index/`

2. **Manual Trigger**: You can also trigger scraping anytime via the API

3. **Next Steps** (coming soon):
   - Parse the PDF to extract price data
   - Store prices in a database
   - Create SMS endpoint to handle farmer queries
   - Add AI/LLM to understand Tagalog queries about plant types and locations

## Testing

### Test the Scraper Directly

```bash
cd backend/app
python scraper.py
```

This will download the latest price index PDF.

### Test via API

1. Start the server:

   ```bash
   uvicorn main:app --reload
   ```

2. Open your browser and visit:
   - `http://localhost:8000` - API info
   - `http://localhost:8000/scrape-latest` - Download latest PDF
   - `http://localhost:8000/download-info` - See downloaded files

## Development Roadmap

### Phase 1: Scraping ✅ (Current)

- [x] Scrape DA website
- [x] Download daily price index PDFs
- [x] Schedule daily automatic downloads

### Phase 2: Data Processing (Next)

- [ ] Parse PDF to extract price tables
- [ ] Store price data in database
- [ ] Create price query API

### Phase 3: SMS Integration

- [ ] SMS gateway integration
- [ ] Handle incoming SMS queries
- [ ] Send price responses via SMS

### Phase 4: AI/NLP

- [ ] Tagalog language support
- [ ] Extract plant type from query
- [ ] Extract location from query
- [ ] Generate helpful responses

## Notes for Hackathon

- Currently focused on NCR region (as per DA data)
- System should be extended to other regions in the future
- Designed for farmers to query via SMS in Tagalog
- Example query: "Magkano ang kamatis sa NCR?" (How much are tomatoes in NCR?)

## Environment Variables

Create a `.env` file in `backend/` directory:

```
# Add any API keys or configuration here
# Example:
# OPENAI_API_KEY=your_key_here
```

## License

Hackathon project - For educational purposes

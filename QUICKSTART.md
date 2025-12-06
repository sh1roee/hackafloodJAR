# DA Price Monitor - Quick Start Guide

## ✅ What's Done

Your backend is now set up and running! Here's what we've built:

### 1. **Automatic Daily Scraper**

- Checks https://www.da.gov.ph/price-monitoring/ every day at 8:00 AM
- Downloads the latest **Daily Price Index** PDF
- Currently downloaded: December 5, 2025 (343 KB)

### 2. **FastAPI Server Running**

- Server URL: http://127.0.0.1:8000
- Automatic daily scraping is active

### 3. **Available API Endpoints**

| Endpoint             | Method | Description                          |
| -------------------- | ------ | ------------------------------------ |
| `/`                  | GET    | API information                      |
| `/health`            | GET    | Health check                         |
| `/scrape-latest`     | GET    | Manually download latest price index |
| `/download-info`     | GET    | List all downloaded PDFs             |
| `/scheduler/status`  | GET    | Check scheduler status               |
| `/scheduler/run-now` | POST   | Manually trigger scrape now          |

## 🧪 Test It Now

1. **View API Info**: Open http://127.0.0.1:8000 in your browser

2. **Check Downloaded Files**: http://127.0.0.1:8000/download-info

3. **See Scheduler Status**: http://127.0.0.1:8000/scheduler/status

4. **Download Latest PDF**: http://127.0.0.1:8000/scrape-latest

## 📁 Files Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI server ✅
│   ├── scraper.py                 # DA website scraper ✅
│   ├── scheduler.py               # Daily scheduler ✅
│   └── downloads/
│       └── price_index/
│           └── daily_price_index_December_5_2025.pdf ✅
├── requirements.txt               # Dependencies ✅
├── .env                          # Environment variables ✅
└── README.md                     # Full documentation ✅
```

## 🎯 Next Steps (For You to Continue)

### Phase 2: Parse the PDF Data

You need to:

1. Install PyPDF2 or pdfplumber: `pip install pypdf2 pdfplumber`
2. Create a parser to extract price tables from the PDF
3. Structure the data (product, location, price)

Example code structure:

```python
# parser.py
def parse_price_pdf(pdf_path):
    # Extract tables from PDF
    # Return structured data: [{product, location, price}, ...]
    pass
```

### Phase 3: SMS Integration

1. Choose SMS gateway (e.g., Twilio, Semaphore)
2. Create SMS webhook endpoint
3. Handle incoming messages

### Phase 4: AI Query Processing

1. Use OpenAI/LangChain to understand Tagalog queries
2. Extract: plant type + location
3. Query your price database
4. Send response via SMS

Example query flow:

```
Farmer SMS: "Magkano kamatis NCR?"
↓
AI extracts: product="tomatoes", location="NCR"
↓
Query database for tomato prices in NCR
↓
SMS Response: "Kamatis sa NCR: ₱50-60/kg (Dec 5)"
```

## 🚀 Current Server Status

Server is running at: **http://127.0.0.1:8000**

The scheduler is active and will automatically download the latest price index every day at 8:00 AM!

## 💡 Pro Tips

- PDFs are saved in `backend/app/downloads/price_index/`
- Check logs in terminal to see scraper activity
- Use `/scheduler/run-now` to test without waiting for scheduled time
- The `.env` file is already gitignored

## 🎉 You're All Set!

The foundation is built. Now you can focus on:

1. Parsing the price data from PDFs
2. Building the SMS interface
3. Adding AI/RAG for smart query handling

Good luck with your hackathon! 🌾📱

# SMS Integration Setup Guide

## EngageSpark Configuration for Filipino Farmers

### Why EngageSpark?

- ✅ Philippines-based SMS gateway
- ✅ Supports inbound & outbound SMS
- ✅ Affordable rates for farmers
- ✅ Easy webhook integration
- ✅ Works with all PH mobile networks (Globe, Smart, Sun)

---

## Step 1: Create EngageSpark Account

1. Go to https://www.engagespark.com/
2. Sign up for an account
3. Choose "SMS" as your channel
4. Select "Philippines" as your country

---

## Step 2: Get Your SMS Number

1. In EngageSpark dashboard, go to **Numbers**
2. Purchase a Philippine SMS number (or use their test number)
3. Note down your number (e.g., `+639171234567`)

**This is the number farmers will send SMS to!**

---

## Step 3: Get API Credentials

1. Go to **Settings** → **API**
2. Copy your **API Key**
3. Copy your **Organization ID**
4. Update `.env` file:

```env
ENGAGESPARK_API_KEY=your_api_key_here
ENGAGESPARK_ORG_ID=your_org_id_here
ENGAGESPARK_SENDER_ID=DA Price
```

---

## Step 4: Configure Webhook

1. In EngageSpark dashboard, go to **Webhooks**
2. Add new webhook:

   - **URL**: `https://your-backend-url.com/api/sms/webhook`
   - **Method**: POST
   - **Events**: Select "Incoming SMS"

3. **For local testing**, use ngrok:

```bash
ngrok http 8000
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Webhook URL: https://abc123.ngrok.io/api/sms/webhook
```

---

## Step 5: Test the Integration

### Test 1: Send Test SMS

```bash
curl -X POST http://localhost:8000/api/sms/send \
  -H "Content-Type: application/json" \
  -d '{"phone":"09171234567", "message":"Test from DA Price Monitor"}'
```

### Test 2: Simulate Query

```bash
curl -X POST http://localhost:8000/api/sms/query \
  -H "Content-Type: application/json" \
  -d '{"phone":"09171234567", "question":"Magkano kamatis sa NCR"}'
```

Response:

```json
{
  "success": true,
  "phone": "09171234567",
  "query": "Magkano kamatis sa NCR",
  "sms_response": "Sa petsang Disyembre 6, ang presyo ng kamatis ay ₱142.54 bawat kilo sa NCR.",
  "length": 78,
  "method": "cache"
}
```

### Test 3: Real SMS Flow

1. Send SMS from your phone to the EngageSpark number:

   ```
   Magkano kamatis sa NCR
   ```

2. Check backend logs:

   ```
   📱 Incoming SMS from +639171234567: Magkano kamatis sa NCR
   📤 Sent SMS response to +639171234567: Sa petsang Disyembre 6...
   ```

3. You should receive SMS reply with the price!

---

## SMS Query Examples

Farmers can send these queries via SMS:

### Single Product

```
Magkano kamatis sa NCR
→ Sa petsang Disyembre 6, ang presyo ng kamatis ay ₱142.54 bawat kilo sa NCR.
```

### Multiple Products

```
Presyo ng kamatis, sibuyas, bawang
→ Kamatis: ₱142.54/kilo, Sibuyas: ₱120.00/kilo, Bawang: ₱180.00/kilo (NCR)
```

### Category Browse

```
Presyo ng lahat ng gulay
→ 1. Kamatis: ₱142.54/kilo
   2. Sibuyas: ₱120.00/kilo
   3. Talong: ₱202.29/tali...
```

### Comparison

```
Ano mas mura, manok o baboy
→ Manok: ₱180.00/kilo (mas mura). Baboy: ₱310.00/kilo. Mas mura ang manok ng ₱130.00.
```

### Budget Planning

```
Ano pwede bilhin ng 500 pesos
→ ₱500 ay pwede bumili ng: 3.5 kilo kamatis, 4.2 kilo sibuyas, o 2.8 kilo manok.
```

---

## Cost Analysis

### EngageSpark Pricing (Approximate)

- **Inbound SMS**: ₱0.50 per message
- **Outbound SMS**: ₱1.00 per message
- **Total per query**: ₱1.50

### Our System Optimization

- **Cache lookups**: FREE (no API calls)
- **Advanced queries**: Uses cache data (still free)
- **LLM only for complex**: <1% of queries

**Result**: ₱1.50 per farmer query (just SMS cost!)

---

## Production Deployment

### Deploy Backend

```bash
# Use Railway, Render, or Heroku
railway up
# or
render deploy

# Get your production URL
# e.g., https://da-price-monitor.up.railway.app
```

### Update EngageSpark Webhook

```
https://da-price-monitor.up.railway.app/api/sms/webhook
```

### Monitor Usage

```bash
# Check SMS logs
GET /api/sms/stats

# Check cache performance
GET /api/cache/stats
```

---

## Demo Script for Hackathon

### Setup

1. Have EngageSpark number displayed: **"Text 0917-XXX-XXXX"**
2. Project the backend logs on screen
3. Have test phone ready

### Demo Flow

**Presenter**:

> "Farmers don't have smartphones or internet. They only have basic phones with SMS. So we integrated SMS!"

**Action**: Send SMS from phone

```
Magkano kamatis sa NCR
```

**Show logs** on projector:

```
📱 Incoming SMS from +639171234567: Magkano kamatis sa NCR
💰 Cache hit! Saved API costs
📤 Sent SMS response: Sa petsang Disyembre 6, ang presyo ng kamatis ay ₱142.54...
```

**Phone receives reply** in seconds!

**Presenter**:

> "Notice how fast? We use cache, so it's FREE. No API costs. Just ₱1.50 for SMS. A farmer can check prices all day for less than a cup of coffee!"

**Demo advanced query**:

```
Ano mas mura, manok o baboy
```

**Show response**:

```
Manok: ₱180.00/kilo (mas mura). Baboy: ₱310.00/kilo.
```

**Presenter**:

> "Farmers can compare prices, plan their budget, check multiple products - all via simple SMS. No internet needed!"

---

## Endpoints Summary

| Endpoint                | Purpose            | Cost             |
| ----------------------- | ------------------ | ---------------- |
| `POST /api/sms/webhook` | Receive farmer SMS | ₱0.50 (inbound)  |
| `POST /api/sms/send`    | Send response      | ₱1.00 (outbound) |
| `POST /api/sms/query`   | Test query flow    | FREE (testing)   |
| Cache lookups           | Process queries    | FREE (no API)    |

---

## Troubleshooting

### SMS not received?

- Check EngageSpark dashboard for delivery status
- Verify phone number format (+639171234567)
- Check backend logs for errors

### Webhook not working?

- Verify webhook URL is HTTPS
- Check ngrok is running (for local dev)
- Test with EngageSpark webhook tester

### Empty responses?

- Check cache has data: `GET /api/cache/stats`
- Refresh cache: `POST /api/cache/refresh`
- Check logs for query processing

---

## Next Steps

1. ✅ Get EngageSpark account
2. ✅ Configure webhook
3. ✅ Test with real phone
4. ✅ Deploy to production
5. ✅ Share number with farmers!

**Farmers can now check prices anytime via SMS! 🌾📱**

# Real SMS Testing Guide - EngageSpark

## Step-by-Step: Test with Real Phone

### Step 1: Get Your EngageSpark Phone Number

1. Log in to https://www.engagespark.com/
2. Go to **Campaigns** → **Phone Numbers**
3. You should have a Philippine number (e.g., `+639171234567`)
4. **This is the number farmers will text!**

---

### Step 2: Expose Your Local Server to Internet

EngageSpark needs to send webhooks to your server. Since you're running locally, use **ngrok**:

```bash
# Download ngrok from https://ngrok.com/download
# Or install via chocolatey:
choco install ngrok

# Run ngrok to expose port 8000
ngrok http 8000
```

You'll see:

```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

**Copy this URL!** (e.g., `https://abc123.ngrok.io`)

---

### Step 3: Configure EngageSpark Webhook

1. Go to EngageSpark dashboard
2. Navigate to **Settings** → **Webhooks** or **Integrations**
3. Add new webhook:
   - **Webhook URL**: `https://abc123.ngrok.io/api/sms/webhook`
   - **Method**: `POST`
   - **Trigger**: `Incoming SMS` or `Message Received`
4. Save webhook

---

### Step 4: Start Your Backend Server

```bash
cd D:\JUNIOR\hackafloodJAR\backend\app
uvicorn main:app --reload
```

You should see:

```
✅ EngageSpark SMS Handler initialized
INFO:     Application startup complete.
```

---

### Step 5: Send Test SMS from Your Phone

**From your real phone, send SMS to your EngageSpark number:**

```
Magkano kamatis sa NCR
```

---

### Step 6: Watch Backend Logs

In your terminal, you should see:

```
📱 Incoming SMS from +639171234567: Magkano kamatis sa NCR
💰 Cache hit! Saved API costs for: Magkano kamatis sa NCR
📤 Sent SMS response to +639171234567: Sa petsang Disyembre 6, ang presyo ng kamatis ay ₱142.54 bawat kilo sa NCR.
```

---

### Step 7: Check Your Phone

Within 5-10 seconds, you should receive SMS reply:

```
Sa petsang Disyembre 6, ang presyo ng kamatis ay ₱142.54 bawat kilo sa NCR.
```

---

## Alternative: Test Without Real SMS (Simulation)

If you don't have EngageSpark number yet, test the flow:

```bash
# Test the SMS query flow (simulates what happens when farmer texts)
curl -X POST http://localhost:8000/api/sms/query \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"09171234567\", \"question\":\"Magkano kamatis sa NCR\"}"
```

Response shows what SMS would contain:

```json
{
  "success": true,
  "phone": "09171234567",
  "query": "Magkano kamatis sa NCR",
  "full_response": "Sa petsang Disyembre 6, ang presyo ng kamatis ay ₱142.54 bawat kilo sa NCR.",
  "sms_response": "Sa petsang Disyembre 6, ang presyo ng kamatis ay ₱142.54 bawat kilo sa NCR.",
  "length": 78,
  "method": "cache"
}
```

---

## Troubleshooting

### Problem: "Webhook not working"

**Check 1: Is ngrok running?**

```bash
# Verify ngrok is forwarding
curl https://your-ngrok-url.ngrok.io/api/cache/stats
```

**Check 2: Is webhook URL correct in EngageSpark?**

- Should be: `https://abc123.ngrok.io/api/sms/webhook`
- NOT: `http://localhost:8000/api/sms/webhook`

**Check 3: Backend logs**

- Look for incoming webhook requests
- Check for errors

### Problem: "SMS received but no reply"

**Check backend logs for:**

```
📱 Incoming SMS from +639171234567: Magkano kamatis sa NCR
❌ Failed to send SMS to +639171234567: [error message]
```

**Verify:**

- EngageSpark API key is correct
- Organization ID is correct
- Account has SMS credits

### Problem: "No SMS received at all"

**Check:**

1. EngageSpark number is correct
2. Webhook is enabled in EngageSpark
3. Ngrok tunnel is active
4. Backend server is running

---

## Quick Test Commands

### Test 1: Simple Query

```bash
curl -X POST http://localhost:8000/api/sms/query \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"09171234567\", \"question\":\"Magkano kamatis sa NCR\"}"
```

### Test 2: Multi-Product

```bash
curl -X POST http://localhost:8000/api/sms/query \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"09171234567\", \"question\":\"Presyo ng kamatis, sibuyas, bawang\"}"
```

### Test 3: Comparison

```bash
curl -X POST http://localhost:8000/api/sms/query \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"09171234567\", \"question\":\"Ano mas mura, manok o baboy\"}"
```

### Test 4: Category

```bash
curl -X POST http://localhost:8000/api/sms/query \
  -H "Content-Type: application/json" \
  -d "{\"phone\":\"09171234567\", \"question\":\"Presyo ng lahat ng gulay\"}"
```

---

## For Hackathon Demo

### Option 1: Use Real SMS (Recommended)

1. Set up ngrok
2. Configure webhook
3. Send SMS from your phone during demo
4. Show logs on projector
5. Show SMS reply on phone (project phone screen)

### Option 2: Simulate SMS

1. Use `/api/sms/query` endpoint
2. Show in Postman or Thunder Client
3. Display JSON response on projector
4. Explain: "This is what SMS would contain"

---

## Demo Script

**Setup (Before Demo):**

```bash
# Terminal 1: Start ngrok
ngrok http 8000

# Terminal 2: Start backend
cd backend/app
uvicorn main:app --reload

# Terminal 3: Keep ready for curl tests
```

**During Demo:**

1. **Show EngageSpark number:**

   - "Farmers text this number: +639XX-XXX-XXXX"

2. **Send SMS from phone:**

   - Text: "Magkano kamatis sa NCR"

3. **Show backend logs (projected):**

   ```
   📱 Incoming SMS from +639171234567: Magkano kamatis sa NCR
   💰 Cache hit! Saved API costs
   📤 Sent SMS response...
   ```

4. **Show phone receiving reply (camera/screen mirror)**

5. **Explain:**
   - "See 'Cache hit'? FREE processing!"
   - "Total cost: ₱1.50 (just SMS)"
   - "Response in 3 seconds!"

---

## Next Steps

1. ✅ Get EngageSpark phone number
2. ✅ Install ngrok
3. ✅ Configure webhook
4. ✅ Test with real phone
5. ✅ Practice demo flow
6. ✅ Prepare phone screen recording/mirroring

**You're ready for live SMS demo! 📱**

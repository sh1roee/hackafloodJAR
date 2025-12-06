# Virtual SMS Testing with Twilio - Complete Setup Guide

This guide shows you how to set up **virtual SMS testing** using Twilio. Unlike EngageSpark, Twilio is much easier to test because it provides a web console where you can send test messages.

---

## Why Twilio for Testing?

✅ **Free Trial**: $15 credit (enough for ~500 SMS messages)  
✅ **Web Console**: Send test SMS directly from browser  
✅ **No Real Phone Needed**: Test without a physical phone  
✅ **Instant Setup**: Get started in 10 minutes  
✅ **Works Globally**: Can send to Philippine numbers (+63)

---

## Step 1: Create Twilio Account

1. Go to **https://www.twilio.com/try-twilio**
2. Sign up with your email
3. Verify your email and phone number
4. You'll get **$15 free credit**

---

## Step 2: Get a Virtual Phone Number

1. After signup, go to **Console Dashboard**
2. Click **Get a Trial Phone Number**
3. Twilio will assign you a US number (e.g., `+1 234 567 8900`)
4. This is the number farmers will text!

> **Note**: Trial accounts can only send to verified numbers. You'll need to verify your real phone number first.

---

## Step 3: Get Your Credentials

1. From Twilio Console, find:

   - **Account SID** (e.g., `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   - **Auth Token** (click to reveal)
   - **Phone Number** (e.g., `+12345678900`)

2. Add these to your `.env` file:

```env
# Twilio SMS Configuration (Virtual Testing)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+12345678900
```

---

## Step 4: Verify Your Phone Number (For Testing)

Since you're on a trial account, you need to verify any phone number you want to send SMS to:

1. Go to **Phone Numbers** → **Verified Caller IDs**
2. Click **Add a new number**
3. Enter your Philippine number: `+639171234567`
4. Twilio will send you a verification code
5. Enter the code to verify

Now you can send SMS to this number!

---

## Step 5: Install Twilio SDK

```bash
# In your backend directory
cd backend
pip install twilio
```

Or add to `requirements.txt`:

```
twilio>=8.10.0
```

---

## Step 6: Expose Your Server with ngrok

Since your backend runs on `localhost:8000`, Twilio can't reach it. Use ngrok to create a public URL:

```bash
# Start ngrok (you already have it!)
cd D:\JUNIOR\hackafloodJAR
.\ngrok.exe http 8000
```

You'll see:

```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the `https://abc123.ngrok.io` URL!**

---

## Step 7: Configure Twilio Webhook

1. Go to **Twilio Console** → **Phone Numbers** → **Manage** → **Active Numbers**
2. Click on your phone number
3. Scroll to **Messaging**
4. Under "A MESSAGE COMES IN":
   - Set to **Webhook**
   - URL: `https://abc123.ngrok.io/api/sms/twilio/webhook`
   - Method: **HTTP POST**
5. Click **Save**

---

## Step 8: Start Your Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Make sure you see:

```
✅ Twilio SMS Handler initialized
📱 Sending from: +12345678900
```

---

## Step 9: Test SMS!

### Option A: Send from Twilio Console (Easiest!)

1. Go to **Twilio Console** → **Messaging** → **Try It Out** → **Send an SMS**
2. From: Your Twilio number
3. To: Your verified phone number
4. Body: `Magkano kamatis sa NCR?`
5. Click **Make Request**

You should:

- See the webhook hit your server (check backend logs)
- Receive an SMS with the price response!

### Option B: Send from Your Real Phone

1. Text your Twilio number: `+12345678900`
2. Message: `Magkano kamatis sa NCR?`
3. Wait for response SMS

### Option C: Use API Testing

```bash
# Test without sending actual SMS
curl -X POST "http://localhost:8000/api/sms/twilio/test" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+639171234567", "question": "Magkano kamatis?"}'
```

---

## Testing Checklist

✅ Twilio account created  
✅ Phone number obtained  
✅ Credentials added to `.env`  
✅ Test phone number verified  
✅ `twilio` package installed  
✅ ngrok running and URL copied  
✅ Twilio webhook configured  
✅ Backend server running  
✅ Test SMS sent successfully

---

## Example SMS Conversations

**Farmer**: `Magkano kamatis sa NCR?`  
**Bot**: `🍅 Kamatis (Medium): ₱80-90/kg (Retail). Pinakamura: ₱70/kg (Wholesale)`

**Farmer**: `Ano mas mura, manok o baboy?`  
**Bot**: `Manok: ₱185-200/kg. Baboy: ₱280-320/kg. Manok ang mas mura ng ₱95-135/kg!`

**Farmer**: `Ano pwede bilhin ng 500 pesos?`  
**Bot**: `With ₱500: Kamatis 6kg (₱85), Sibuyas 8kg (₱60), Bawang 2kg (₱220)...`

---

## Troubleshooting

### "Twilio not configured" error

- Check `.env` file has correct credentials
- Restart backend server after adding credentials

### "Import twilio could not be resolved"

```bash
pip install twilio
```

### Not receiving SMS

- Check ngrok is still running (it times out after 2 hours on free plan)
- Verify webhook URL in Twilio console is correct
- Check backend logs for errors

### "To number not verified" error

- You're on trial account
- Go to Twilio Console → Verified Caller IDs
- Add and verify the recipient's phone number

### ngrok URL changed

- ngrok URL changes every time you restart it
- Update webhook URL in Twilio console with new URL
- Or upgrade to ngrok paid plan for static URL

---

## Cost Breakdown

### Twilio Trial (FREE)

- **$15 credit** on signup
- Each SMS costs **$0.0079** (outbound to Philippines)
- That's **~1,900 messages** for free!

### After Trial

- **Pay-as-you-go**: $0.0079 per SMS
- No monthly fees
- 1000 messages = ~$8

### Upgrading

To send to unverified numbers (production):

1. Upgrade Twilio account (add payment method)
2. No verification needed for recipients
3. Same pricing: $0.0079/SMS

---

## Advanced: Twilio vs EngageSpark

| Feature            | Twilio      | EngageSpark |
| ------------------ | ----------- | ----------- |
| Free Trial         | $15 credit  | Limited     |
| Web Console        | ✅ Yes      | ❌ No       |
| SMS Cost           | $0.0079/SMS | Varies      |
| Setup Time         | 10 minutes  | 30+ minutes |
| Philippine Numbers | ✅ Yes      | ✅ Yes      |
| Testing            | Very Easy   | Complex     |

**Recommendation**: Use Twilio for development/testing, consider EngageSpark for production if cheaper.

---

## Next Steps

1. Test the SMS flow end-to-end
2. Monitor Twilio Console for message logs
3. Check backend logs for query processing
4. Try different price queries
5. Show your teammates! 🎉

---

## Quick Reference

**Your Backend Endpoints:**

- Webhook: `/api/sms/twilio/webhook` (Twilio calls this)
- Send SMS: `/api/sms/twilio/send` (Manual send)
- Test Query: `/api/sms/twilio/test` (No SMS sent)
- Check Balance: `/api/sms/twilio/balance`

**Twilio Dashboard:**
https://console.twilio.com/

**ngrok Web UI:**
http://localhost:4040 (See all webhook requests)

---

Need help? Check:

- Twilio Docs: https://www.twilio.com/docs/sms
- ngrok Docs: https://ngrok.com/docs
- Backend logs: Watch your terminal!

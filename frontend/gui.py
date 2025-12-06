import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API Key safely
SEMAPHORE_API_KEY = os.getenv("SEMAPHORE_API_KEY")

st.set_page_config(
    page_title="Bantay-Bulsa Admin",
    page_icon="🛡️",
    layout="wide"
)

# send semaphore sms
def send_semaphore_sms(number, message):
    """Sends SMS using Semaphore API and returns the status."""
    
    if not SEMAPHORE_API_KEY:
        return {"status": "Error", "message": "API Key missing in .env file"}

    url = "https://api.semaphore.co/api/v4/messages"
    payload = {
        "apikey": SEMAPHORE_API_KEY,
        "number": number,
        "message": message,
        "sendername": "SEMAPHORE"  # Default sender name. Change if you have a registered sender ID.
    }
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        return {"status": "Error", "message": str(e)}

# simulating dti (user/reports))))
@st.cache_data
def load_data():
    # Generate random points around Manila (Lat: 14.5, Lon: 121.0)
    data = pd.DataFrame({
        'lat': np.random.normal(14.6091, 0.02, 100),
        'lon': np.random.normal(120.9821, 0.02, 100),
        'commodity': np.random.choice(['Red Onion', 'Rice (Well Milled)', 'Pork Kasim', 'Galunggong'], 100),
        'reported_price': np.random.randint(50, 300, 100),
        'srp': np.random.randint(40, 250, 100)
    })
    # Calculate overprice percentage
    data['overprice_pct'] = ((data['reported_price'] - data['srp']) / data['srp']) * 100
    data['status'] = data['overprice_pct'].apply(lambda x: 'CRITICAL' if x > 20 else 'NORMAL')
    return data

df = load_data()



# 1. Header
st.title("Bantay-Bulsa: Fair Price Oversight")
st.markdown("Real-time monitoring of urban price exploitation hotspots.")

# Check if API Key is loaded
if not SEMAPHORE_API_KEY:
    st.error("⚠️ WARNING: Semaphore API Key not found. SMS features will not work. Check your .env file.")

# 2. Key Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reports Today", "1,240", "+12%")
col2.metric("Critical Violations", "86", "+5%", delta_color="inverse")
col3.metric("Avg Overpricing", "18%", "+2%")
col4.metric("Most Flagged Item", "Red Onion")

st.divider()

# 3. Main Interface
row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    st.subheader("Exploitation Heatmap")
    st.markdown("Red dots indicate reports where price is **>20% above SRP**.")
    
    # Filter for map (Show only Critical or All)
    map_filter = st.radio("Map Filter:", ["All Reports", "Critical Only"], horizontal=True)
    
    if map_filter == "Critical Only":
        map_data = df[df['status'] == 'CRITICAL']
    else:
        map_data = df
        
    st.map(map_data, zoom=12)

with row1_col2:
    st.subheader("📢 Broadcast Alert (Semaphore)")
    st.info("Send SMS warnings to community leaders in affected areas.")
    
    # SMS Form
    recipient_num = st.text_input("Recipient Number (e.g., 0917xxxxxxx)")
    
    # AI-Generated Message Suggestion based on data
    default_msg = "ALERT: High price manipulation detected in your Barangay for Red Onions. SRP is P140. Report overpricing to 0917-BANTAY."
    message_body = st.text_area("Message Content", value=default_msg, height=100)
    
    if st.button("🚀 Send SMS Alert", type="primary"):
        if not recipient_num:
            st.error("Please enter a phone number.")
        elif not SEMAPHORE_API_KEY:
             st.error("Cannot send: API Key is missing.")
        else:
            with st.spinner("Sending via Semaphore..."):
                # Call the function
                result = send_semaphore_sms(recipient_num, message_body)
                
                # Check results
                if isinstance(result, list) or 'status' in result: 
                     st.success("Message Sent Successfully!")
                     with st.expander("View API Response"):
                         st.json(result)
                else:
                     st.error("Failed to send.")

st.divider()

# 4. Recent Reports Table
st.subheader("Recent Verified Reports")
st.dataframe(
    df[['commodity', 'reported_price', 'srp', 'overprice_pct', 'status']].sort_values(by='overprice_pct', ascending=False),
    use_container_width=True
)
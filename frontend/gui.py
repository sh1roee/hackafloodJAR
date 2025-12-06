import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

SEMAPHORE_API_KEY = os.getenv("SEMAPHORE_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Bantay-Bulsa: Fair Price Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium, modern design
st.markdown("""
<style>
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat container styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Input box styling */
    .stChatInputContainer {
        border-top: 2px solid rgba(255, 255, 255, 0.2);
        padding-top: 1rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        color: white;
        padding: 2rem 0 1rem 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
    }
    
    /* Example buttons */
    .example-btn {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.3rem;
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-block;
    }
    
    .example-btn:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Alert boxes */
    .stAlert {
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 Kumusta! I'm your **Bantay-Bulsa** assistant. I help you verify fair prices and avoid poverty taxes. Ask me about commodity prices in NCR!\n\n**Magtanong sa akin ng presyo ng mga bilihin!** 🛒"
    })

# Helper function to call backend API
def query_backend(user_message: str, use_sms_format: bool = False):
    """Query the backend RAG system"""
    try:
        if use_sms_format:
            endpoint = f"{BACKEND_URL}/api/query-sms"
            payload = {
                "phone": "0917XXXXXXX",  # Placeholder
                "message": user_message
            }
        else:
            endpoint = f"{BACKEND_URL}/api/query"
            payload = {
                "question": user_message,
                "top_k": 5
            }
        
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if use_sms_format:
            return data.get("response", "No response received")
        else:
            return data.get("answer", data.get("error", "No answer available"))
            
    except requests.exceptions.ConnectionError:
        return "❌ **Backend server is not running.** Please start the backend at `http://localhost:8000`"
    except requests.exceptions.Timeout:
        return "⏱️ **Request timed out.** The backend is taking too long to respond."
    except Exception as e:
        return f"❌ **Error:** {str(e)}"

# Send SMS via Semaphore
def send_semaphore_sms(number, message):
    """Sends SMS using Semaphore API"""
    if not SEMAPHORE_API_KEY:
        return {"status": "Error", "message": "API Key missing in .env file"}
    
    url = "https://api.semaphore.co/api/v4/messages"
    payload = {
        "apikey": SEMAPHORE_API_KEY,
        "number": number,
        "message": message,
        "sendername": "BANTAY-BULSA"
    }
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        return {"status": "Error", "message": str(e)}

# =============================================================================
# SIDEBAR - SMS Simulation & Info
# =============================================================================

with st.sidebar:
    st.markdown("## 📱 SMS Simulation")
    st.markdown("See how this chatbot works via SMS for those without internet access.")
    
    st.markdown("---")
    
    # SMS Test Section
    with st.expander("🧪 Test SMS Query", expanded=False):
        st.markdown("Simulate how a farmer/consumer would send an SMS query:")
        
        sms_number = st.text_input("Phone Number", value="09171234567", key="sms_phone")
        sms_query = st.text_area(
            "SMS Message", 
            value="Magkano kamatis sa NCR?",
            height=80,
            key="sms_query"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Get Response", key="sms_sim", use_container_width=True):
                with st.spinner("Processing SMS query..."):
                    response = query_backend(sms_query, use_sms_format=True)
                    st.success("✅ SMS Response:")
                    st.info(response)
        
        with col2:
            if st.button("📨 Send Real SMS", key="real_sms", use_container_width=True):
                if not SEMAPHORE_API_KEY:
                    st.error("⚠️ Semaphore API key not configured")
                else:
                    # Get response first
                    response = query_backend(sms_query, use_sms_format=True)
                    # Send via Semaphore
                    with st.spinner("Sending SMS..."):
                        result = send_semaphore_sms(sms_number, response)
                        if 'error' not in str(result).lower():
                            st.success("✅ SMS sent!")
                        else:
                            st.error(f"Failed: {result}")
    
    st.markdown("---")
    
    # System Status
    st.markdown("## 🔧 System Status")
    
    # Check backend health
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if health_response.status_code == 200:
            st.success("✅ Backend Online")
            health_data = health_response.json()
            st.caption(f"RAG: {'Enabled' if health_data.get('rag_enabled') else 'Disabled'}")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Offline")
    
    # Semaphore API status
    if SEMAPHORE_API_KEY:
        st.success("✅ SMS API Configured")
    else:
        st.warning("⚠️ SMS API Not Set")
    
    st.markdown("---")
    
    # Info
    st.markdown("## ℹ️ About")
    st.markdown("""
    **Bantay-Bulsa** helps the urban poor:
    - ✅ Verify fair commodity prices
    - ✅ Avoid predatory pricing
    - ✅ Get info from government data (DTI, DA)
    - ✅ Accessible via SMS (no internet needed)
    
    **Tech Stack:**
    - RAG (Retrieval Augmented Generation)
    - GPT-4o-mini
    - ChromaDB Vector Store
    - Semaphore SMS API
    """)

# =============================================================================
# MAIN CHAT INTERFACE
# =============================================================================

# Header
st.markdown("""
<div class="main-header">
    <h1>💬 Bantay-Bulsa Chat Assistant</h1>
    <p>Your guide to fair prices and avoiding poverty taxes</p>
</div>
""", unsafe_allow_html=True)

# Example queries
st.markdown("**Try these example questions:**")
col1, col2, col3 = st.columns(3)

example_queries = [
    "Magkano ang kamatis sa NCR?",
    "What is the price of rice?",
    "Presyo ng manok ngayon?",
    "Price of galunggong today",
    "Magkano ang sibuyas?",
    "How much is pork in Manila?"
]

for idx, example in enumerate(example_queries[:3]):
    if col1.button(f"💡 {example}", key=f"ex{idx}", use_container_width=True):
        st.session_state.clicked_example = example

for idx, example in enumerate(example_queries[3:]):
    if col2.button(f"💡 {example}", key=f"ex{idx+3}", use_container_width=True):
        st.session_state.clicked_example = example

if col3.button("🔄 Clear Chat", key="clear", use_container_width=True):
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Chat cleared! Ask me about commodity prices. 😊"
    }]
    st.rerun()

st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle clicked example
if 'clicked_example' in st.session_state:
    example_text = st.session_state.clicked_example
    del st.session_state.clicked_example
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": example_text})
    with st.chat_message("user"):
        st.markdown(example_text)
    
    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching price data..."):
            response = query_backend(example_text)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Chat input
if prompt := st.chat_input("Ask about commodity prices... (Tagalog or English)"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Checking prices from government databases..."):
            response = query_backend(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
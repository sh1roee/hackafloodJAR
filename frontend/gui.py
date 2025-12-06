import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="DA Price Monitor",
    page_icon="🌾",
    layout="centered"
)

# Simple, clean CSS styling with dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #3d3d3d;
        color: #ffffff;
    }
    
    .stChatInputContainer {
        background-color: #2d2d2d;
    }
    
    h1, h2, h3, p, label {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! Ask me about commodity prices in NCR. You can ask in English or Tagalog."
    })

# Helper function to call backend API
def query_backend(user_message: str):
    """Query the backend RAG system"""
    try:
        endpoint = f"{BACKEND_URL}/api/query"
        payload = {
            "question": user_message,
            "top_k": 5
        }
        
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("answer", data.get("error", "No answer available"))
            
    except requests.exceptions.ConnectionError:
        return "❌ Backend server is not running. Please start the backend at http://localhost:8000"
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. The backend is taking too long to respond."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Title
st.title("🌾 DA Price Monitor")
st.caption("Ask about commodity prices in NCR")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about prices... (e.g., Magkano kamatis?)"):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            response = query_backend(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

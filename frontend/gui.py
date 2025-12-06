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
    st.session_state.waiting_for = "crop"  # or "location" or None
    st.session_state.crop = None
    st.session_state.location = None

# Helper function to detect if location is mentioned
def has_location(text: str) -> bool:
    """Check if location is mentioned in the text"""
    locations = ['ncr', 'metro manila', 'manila', 'maynila', 'quezon city', 'makati', 'pasig', 'mandaluyong']
    text_lower = text.lower()
    return any(loc in text_lower for loc in locations)

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
if prompt := st.chat_input("Mag-type dito..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response based on conversation state
    with st.chat_message("assistant"):
        if st.session_state.waiting_for == "crop":
            # Check if user provided both crop AND location in one message
            if has_location(prompt):
                # User provided both - query directly
                with st.spinner("Searching..."):
                    response = query_backend(f"Magkano ang {prompt}")
                    st.markdown(response)
                
                # Reset for next query
                st.session_state.waiting_for = "crop"
            else:
                # User only provided crop
                st.session_state.crop = prompt
                st.session_state.waiting_for = "location"
                response = "Saan ang lokasyon?"
                st.markdown(response)
        elif st.session_state.waiting_for == "location":
            # User provided location
            st.session_state.location = prompt
            st.session_state.waiting_for = None
            
            # Now query the backend
            full_query = f"Magkano ang {st.session_state.crop} sa {st.session_state.location}"
            
            with st.spinner("Searching..."):
                response = query_backend(full_query)
                st.markdown(response)
            
            # Reset for next query
            st.session_state.crop = None
            st.session_state.location = None
            st.session_state.waiting_for = "crop"
        else:
            # Default - shouldn't reach here
            response = "Anong pananim o produkto ang gusto mong itanong ang presyo?"
            st.session_state.waiting_for = "crop"
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

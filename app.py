"""
ChefBot - AI Cooking Assistant
Main application entry point
"""
import streamlit as st
import logging

# Import configuration
from config import GROQ_API_KEY, PAGE_TITLE, PAGE_ICON

# Import utilities
from helpers import init_session_state

# Import UI components
from ui_components import apply_custom_css, render_sidebar

# Import pages
from pages.home import render_home_page
from pages.chat import render_chat_page

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
def main():
    """Main application logic"""
    
    # Initialize session state
    init_session_state()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Check API key
    if not GROQ_API_KEY:
        st.error("❌ ไม่พบ GROQ_API_KEY กรุณาตั้งค่าใน .env file")
        st.code("GROQ_API_KEY=your_api_key_here")
        st.stop()
    
    # Render sidebar
    render_sidebar()
    
    # Route to appropriate page
    if st.session_state.page == "home":
        render_home_page()
    elif st.session_state.page == "chat":
        render_chat_page()
    else:
        logger.error(f"Unknown page: {st.session_state.page}")
        st.error("❌ หน้าที่ต้องการไม่มีในระบบ")
        st.session_state.page = "home"
        st.rerun()


if __name__ == "__main__":
    main()
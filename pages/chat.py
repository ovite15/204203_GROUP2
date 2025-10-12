"""
Chat page layout for ChefBot
"""
import streamlit as st
from helpers import validate_input
from ui_components import render_chat_message
from ai_handler import generate_response
from config import USER_AVATAR, BOT_AVATAR


def render_chat_page():
    """Render the chat page"""
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>💬 ปรุงกับ ChefBot</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize with welcome message if empty
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "สวัสดีครับ! ผมคือ ChefBot ผู้ช่วยพ่อครัวของคุณ 👨‍🍳\n\nบอกผมได้เลยว่าคุณมีวัตถุดิบอะไรบ้าง หรือต้องการทำอาหารแบบไหน ผมจะช่วยหาสูตรที่เหมาะสมให้ครับ!"
        }]
    
    # Display chat messages
    _display_chat_history()
    
    # Chat input
    _handle_chat_input()


def _display_chat_history():
    """Display all chat messages"""
    for message in st.session_state.messages:
        role = message["role"]
        content = message.get("content", "")
        
        if role == "user":
            with st.chat_message("user", avatar=USER_AVATAR):
                st.write(content)
        
        elif role == "assistant" and content:
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                st.write(content)


def _handle_chat_input():
    """Handle user input from chat box"""
    if prompt := st.chat_input("คุณมีวัตถุดิบอะไรบ้าง หรือต้องการทำอาหารอะไร..."):
        # Validate input
        is_valid, error_msg = validate_input(prompt)
        
        if not is_valid:
            st.warning(error_msg)
            st.stop()
        
        # Display user message
        with st.chat_message("user", avatar=USER_AVATAR):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            with st.spinner("กำลังคิด..."):
                response = generate_response(prompt)
                st.write(response)
        
        # Rerun to update chat history
        st.rerun()
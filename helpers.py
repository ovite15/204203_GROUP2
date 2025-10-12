"""
Utility functions for ChefBot application
"""
import streamlit as st
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_INPUT_LENGTH, MAX_CHAT_HISTORY


def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "page": "home",
        "messages": [],
        "chat_history": [],
        "model": DEFAULT_MODEL,
        "temperature": DEFAULT_TEMPERATURE,
        "prompt_type": "cooking",
        "user_info": {
            "ingredients": [],
            "allergies": None,
            "restrictions": None,
            "preferences": None
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def validate_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> tuple[bool, str]:
    """
    Validate user input
    
    Args:
        text: Input text to validate
        max_length: Maximum allowed length
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    text = text.strip()
    
    if not text:
        return False, "กรุณาพิมพ์ข้อความ"
    
    if len(text) > max_length:
        return False, f"ข้อความยาวเกินไป (สูงสุด {max_length} ตัวอักษร)"
    
    return True, ""


def archive_current_chat():
    """Archive current conversation to history"""
    if len(st.session_state.messages) > 1:
        if not st.session_state.chat_history or \
           st.session_state.chat_history[0] != st.session_state.messages:
            st.session_state.chat_history.insert(0, st.session_state.messages.copy())
            # Keep only last N chats
            st.session_state.chat_history = st.session_state.chat_history[:MAX_CHAT_HISTORY]


def reset_chat():
    """Reset to new chat"""
    archive_current_chat()
    st.session_state.messages = []
    st.session_state.page = "home"
    st.session_state.user_info = {
        "ingredients": [],
        "allergies": None,
        "restrictions": None,
        "preferences": None
    }


def load_chat(index: int):
    """
    Load chat from history
    
    Args:
        index: Index of chat in history to load
    """
    archive_current_chat()
    st.session_state.messages = st.session_state.chat_history[index].copy()
    st.session_state.page = "chat"


def get_chat_title(chat: list, max_length: int = 30) -> str:
    """
    Get display title for a chat
    
    Args:
        chat: List of chat messages
        max_length: Maximum length for title
    
    Returns:
        Display title string
    """
    # Get first user message as title
    title = next(
        (msg["content"] for msg in chat if msg["role"] == "user"),
        "บทสนทนา"
    )
    
    # Truncate long titles
    if len(title) > max_length:
        title = title[:max_length] + "..."
    
    return title
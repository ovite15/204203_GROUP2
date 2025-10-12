"""
UI components and styling for ChefBot
"""
import streamlit as st
from config import BOT_AVATAR, USER_AVATAR, MODELS


def apply_custom_css():
    """Apply custom CSS styling to the application"""
    st.markdown("""
        <style>
        /* Main theme colors */
        :root {
            --primary-color: #FF6B6B;
            --secondary-color: #4ECDC4;
            --background: #FFFFFF;
            --surface: #F8F9FA;
            --text-dark: #2C3E50;
            --text-light: #7F8C8D;
        }
        
        /* App background */
        .stApp {
            background-color: var(--background);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FF6B6B 0%, #FF8E8E 100%);
            padding: 1rem;
        }
        
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        
        [data-testid="stSidebar"] .stButton>button {
            background-color: rgba(255, 255, 255, 0.2);
            color: white !important;
            border: 2px solid white;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Main content containers */
        .main-header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
            color: white;
            border-radius: 1rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .main-header h1 {
            color: white !important;
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .main-header p {
            color: rgba(255,255,255,0.9) !important;
            margin-top: 0.5rem;
            font-size: 1.1rem;
        }
        
        /* Feature cards */
        .feature-card {
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border: 2px solid transparent;
            height: 100%;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            border-color: var(--primary-color);
        }
        
        .feature-card h4 {
            color: var(--text-dark) !important;
            text-align: center;
            margin-bottom: 1.5rem;
            font-size: 1.3rem;
        }
        
        /* Primary button */
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
            color: white;
            border: none;
            font-weight: 600;
            padding: 0.75rem 2rem;
            font-size: 1.05rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
        }
        
        /* Text input */
        .stTextInput>div>div>input {
            border: 2px solid #E8E8E8;
            border-radius: 0.5rem;
            padding: 0.75rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
        }
        
        /* File uploader */
        [data-testid="stFileUploader"] {
            background: var(--surface);
            border: 2px dashed #D5D8DC;
            border-radius: 1rem;
            padding: 2rem;
            transition: all 0.3s ease;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: var(--primary-color);
            background: rgba(255, 107, 107, 0.05);
        }
        
        /* Chat messages */
        [data-testid="stChatMessage"] {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Hide default streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with navigation and settings"""
    with st.sidebar:
        st.image(BOT_AVATAR, width=200)
        st.title("🍳 ChefBot")
        st.caption("ผู้ช่วยพ่อครัวอัจฉริยะ")
        st.markdown("---")
        
        # New chat button
        if st.button("🔄 แชทใหม่", use_container_width=True):
            from utils import reset_chat
            reset_chat()
            st.rerun()
        
        # Settings (only in chat page)
        if st.session_state.page == "chat":
            st.markdown("---")
            st.subheader("⚙️ ตั้งค่า")
            
            # Model selection
            st.session_state.model = st.selectbox(
                "โมเดล AI",
                list(MODELS.keys()),
                format_func=lambda x: MODELS[x],
                index=list(MODELS.keys()).index(st.session_state.model)
            )
            
            # Temperature slider
            st.session_state.temperature = st.slider(
                "ความสร้างสรรค์",
                0.0, 2.0, st.session_state.temperature, 0.1,
                help="ค่าสูง = คำตอบหลากหลาย, ค่าต่ำ = คำตอบแน่นอน"
            )
            
            # Available tools
            with st.expander("🛠️ เครื่องมือที่มี"):
                st.markdown("""
                - 🔍 **ค้นหาเว็บ** - ค้นหาข้อมูลออนไลน์
                - 🍳 **ค้นหาสูตร** - Spoonacular API
                - 📊 **โภชนาการ** - USDA Database
                """)
        
        # Chat history
        _render_chat_history()


def _render_chat_history():
    """Render chat history in sidebar"""
    st.markdown("---")
    st.subheader("📜 ประวัติ")
    
    if st.session_state.chat_history:
        from utils import get_chat_title, load_chat
        
        for i, chat in enumerate(st.session_state.chat_history):
            title = get_chat_title(chat)
            
            if st.button(f"💬 {title}", key=f"hist_{i}", use_container_width=True):
                load_chat(i)
                st.rerun()
    else:
        st.info("ยังไม่มีประวัติ", icon="📭")


def render_chat_message(role: str, content: str):
    """
    Render a single chat message
    
    Args:
        role: Message role ('user' or 'assistant')
        content: Message content
    """
    avatar = USER_AVATAR if role == "user" else BOT_AVATAR
    
    with st.chat_message(role, avatar=avatar):
        st.write(content)
"""
Home page layout for ChefBot - with vision support
"""
import streamlit as st
from io import BytesIO
from PIL import Image
from helpers import validate_input, archive_current_chat
from ai_handler import generate_response

# Try to import vision handler
try:
    from vision_handler import is_vision_available, detect_ingredients
    VISION_ENABLED = is_vision_available()
except ImportError:
    VISION_ENABLED = False


def render_home_page():
    """Render the home page"""
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🍳 สวัสดีครับ ChefBot ยินดีรับใช้</h1>
            <p>เลือกวิธีการเริ่มต้น เพื่อค้นหาสูตรอาหารที่ใช่สำหรับคุณ</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Two columns for options
    col1, col2 = st.columns(2, gap="large")
    
    # Left: Upload image
    with col1:
        _render_upload_option()
    
    # Right: Type ingredients
    with col2:
        _render_text_input_option()


def _render_upload_option():
    """Render image upload option"""
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("<h4>📸 อัปโหลดรูปภาพวัตถุดิบ</h4>", unsafe_allow_html=True)
    
    if not VISION_ENABLED:
        st.info("""
        💡 **หมายเหตุ:** ฟีเจอร์นี้ต้องการ:
        - Vision Model (GPT-4V, Claude 3)
        - ไฟล์ `utils/vision.py` และ `utils/llm_client.py`
        - `OPENAI_API_KEY` หรือ `GROQ_API_KEY` ใน `.env`
        """, icon="ℹ️")
        
        uploaded_file = st.file_uploader(
            "อัปโหลดรูปภาพ",
            type=['png', 'jpg', 'jpeg'],
            label_visibility="collapsed",
            disabled=True,
            key="disabled_uploader"
        )
    else:
        uploaded_file = st.file_uploader(
            "อัปโหลดรูปภาพวัตถุดิบ",
            type=['png', 'jpg', 'jpeg'],
            label_visibility="collapsed",
            key="enabled_uploader"
        )
        
        if uploaded_file is not None:
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption="รูปภาพที่อัปโหลด", use_container_width=True)
            
            # Process button
            if st.button("🔍 วิเคราะห์รูปภาพ", use_container_width=True, type="primary", key="analyze_image"):
                _process_image(uploaded_file)
    
    st.markdown('</div>', unsafe_allow_html=True)


def _process_image(uploaded_file):
    """Process uploaded image to detect ingredients"""
    with st.spinner("🔍 กำลังวิเคราะห์รูปภาพ..."):
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Detect ingredients
        ingredients = detect_ingredients(
            uploaded_file,
            temperature=0.7,
            max_tokens=1000
        )
    
    if ingredients:
        ingredients_text = ", ".join(ingredients)
        st.success(f"✅ ตรวจพบวัตถุดิบ: {ingredients_text}")
        
        # Start chat with detected ingredients
        _start_new_chat_with_ingredients(ingredients_text)
    else:
        st.warning("⚠️ ไม่สามารถตรวจพบวัตถุดิบจากรูปภาพ กรุณาลองใหม่หรือพิมพ์ด้วยตัวเอง")


def _render_text_input_option():
    """Render text input option"""
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown("<h4>✍️ พิมพ์ส่วนผสมเอง</h4>", unsafe_allow_html=True)
    
    ingredients = st.text_input(
        "ระบุส่วนผสม (คั่นด้วยจุลภาค)",
        placeholder="เนื้อหมู, หอมใหญ่, กระเทียม, พริก...",
        label_visibility="collapsed",
        key="manual_ingredients"
    )
    
    if st.button("🔍 ค้นหาสูตรอาหาร", use_container_width=True, type="primary", key="search_recipes"):
        is_valid, error_msg = validate_input(ingredients)
        
        if not is_valid:
            st.warning(error_msg)
        else:
            _start_new_chat_with_ingredients(ingredients)
    
    st.markdown('</div>', unsafe_allow_html=True)


def _start_new_chat_with_ingredients(ingredients: str):
    """
    Start a new chat with the given ingredients
    
    Args:
        ingredients: User-provided or detected ingredients
    """
    # Start new chat
    archive_current_chat()
    first_prompt = f"ฉันมีวัตถุดิบคือ: {ingredients}\n\nช่วยแนะนำเมนูอาหารที่เหมาะสมหน่อยครับ"
    st.session_state.messages = []
    st.session_state.page = "chat"
    
    # Generate first response
    with st.spinner("กำลังค้นหาสูตร..."):
        generate_response(first_prompt)
    
    st.rerun()
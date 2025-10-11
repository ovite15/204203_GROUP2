import streamlit as st
import time
import random

st.set_page_config(
    page_title="ChefBot",
    page_icon="https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg",
    layout="wide"
)

# เก็บหน้า ปัจจุบัน, ข้อความในแชท, ภาพที่อัปโหลด และประวัติการแชท
if "page" not in st.session_state:
    st.session_state.page = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# CSS แต่งหน้าเพจ
page_style = """
    <style>
    /* สไตล์ทั่วไป */
    body { color: #E8E8E8; } 
    .stApp { background-color: #E8E8E8; } /* พื้นหลังขาว */
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #E8E8E8; 
        border-right: 1px solid #DDDDDD;
    }
    
    /* คอนเทนเนอร์ */
    [data-testid="stContainer"], .main-container {
        background-color: #EAECEE;
        border: 1px solid #D5D8DC;
        border-radius: 0.75rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .main-container { padding: 2rem; }
    [data-testid="stContainer"] {
        min-height: 350px;
        display: flex;
        flex-direction: column;
    }

    /* Header */
    h1, h2, h3, h4, h5, h6 { color: #000000; } 
    h1 { text-align: center; }
    
    /* Button */
    .stButton>button {
        background-color: #007BFF;
        color: #FFFFFF;
        border: none;
        border-radius: 0.5rem;
        font-weight: bold;
        padding: 0.75rem 1.5rem;
    }
    .stButton>button:hover { 
        background-color: #0056b3;
        color: #FFFFFF; 
    }
    
    /* Chat bubble */
    .message-container { display: flex; align-items: flex-end; margin-bottom: 1rem; gap: 10px; }
    .user-container { justify-content: flex-end; }
    .avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
    .assistant-bubble, .user-bubble { display: inline-block; padding: 10px 18px; border-radius: 20px; max-width: 80%; text-align: left; word-wrap: break-word; }
    .assistant-bubble { background-color: #888E95; color: white; }
    .user-bubble { background-color: #007BFF; color: white; }
    [data-testid="stChatMessage"] { display: none; }


    /* History chat */
    .history-item { background-color: #EAECEE; border-radius: 0.5rem; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.95rem; }

    </style>
"""
st.markdown(page_style, unsafe_allow_html=True)


# Helper Functions
def archive_current_chat():
    """
    เก็บการสนทนาปัจจุบันลงใน chat_history
    เงื่อนไข: เก็บเฉพาะเมื่อมีข้อความมากกว่า 1 ข้อความ
    และป้องกันการเก็บซ้ำ (ถ้าอันบนสุดในประวัติเหมือนกันจะไม่ซ้ำ)
    """
    if len(st.session_state.messages) > 1:
        if not st.session_state.chat_history or st.session_state.chat_history[0] != st.session_state.messages:
            st.session_state.chat_history.insert(0, st.session_state.messages.copy())

def load_chat(index):
    """
    โหลดการสนทนา (จากประวัติ) กลับมาแสดง
    - ก่อนโหลด จะเรียก archive_current_chat() เพื่อไม่ให้ข้อมูลปัจจุบันหาย
    - ตั้ง session_state.messages เป็นบทสนทนาที่ต้องการ แล้วเปลี่ยนหน้าเป็น chat
    - ใช้ st.rerun() เพื่อรีเฟรชหน้า
    """
    archive_current_chat()
    st.session_state.messages = st.session_state.chat_history[index]
    st.session_state.page = "chat"
    st.rerun()

def go_to_home():
    """
    ย้อนกลับไปหน้าแรก (home)
    - เก็บแชทปัจจุบันก่อน
    - ล้าง messages และ uploaded_image เพื่อเริ่มใหม่
    """
    archive_current_chat()
    st.session_state.messages = []
    st.session_state.uploaded_image = None
    st.session_state.page = "home"
    st.rerun()

# --- Sidebar ---
with st.sidebar:

    st.image("https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg", width=250)
    st.title("ChefBot")
    st.markdown("---")
    # ปุ่มเริ่มแชทใหม่ 
    st.button("แชทใหม่", on_click=go_to_home, use_container_width=True)
    st.markdown("---")
    
    st.subheader("ประวัติการปรุง")
    
    #  chat_history
    for i, chat in enumerate(st.session_state.chat_history):
        # หาเนื้อความแรกที่เป็นของ user เพื่อใช้เป็นชื่อหัวข้อสั้นๆ
        title = next((msg["content"] for msg in chat if msg["role"] == "user"), "บทสนทนา")
        st.button(
            f"📜 {title[:25]}..." if len(title) > 25 else f"📜 {title}",
            key=f"history_{i}",
            on_click=load_chat,
            args=(i,),
            use_container_width=True
        )


### --- หน้า HOME ---
if st.session_state.page == "home":
    with st.container(border=True):
        st.title("สวัสดีครับ ChefBot ยินดีรับใช้ 🍳")
        st.markdown("<h3 style='text-align: center;'>เลือกวิธีการเริ่มต้น เพื่อค้นหาสูตรอาหารที่ใช่สำหรับคุณ</h3>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True) 

    col1, col2 = st.columns(2, gap="large")

    # คอลัมน์ซ้าย: อัปโหลดรูปภาพวัตถุดิบ
    with col1:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>อัปโหลดรูปภาพวัตถุดิบ 📸</h4>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("อัปโหลดรูปภาพ", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
            if uploaded_file:
                # ถ้ามีไฟล์ ให้บันทึกการสนทนาปัจจุบันก่อน แล้วไปหน้า chat พร้อมส่งข้อมูลรูปภาพเป็น binary
                archive_current_chat()
                st.session_state.messages = [{"role": "user", "content": "แนะนำเมนูจากรูปภาพนี้หน่อย", "image": uploaded_file.getvalue()}]
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.info("ยังไม่มีไฟล์ที่อัปโหลด")

    # คอลัมน์ขวา: พิมพ์ส่วนผสมเอง
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>พิมพ์ส่วนผสมเอง ✍️</h4>", unsafe_allow_html=True)
            ingredients = st.text_input("ระบุส่วนผสม คั่นด้วยจุลภาค (,)", placeholder="เนื้อหมู, หอมใหญ่, ...")
            # ปุ่มค้นหาสูตร: หากมีส่วนผสม จะสร้าง prompt แรกและไปหน้า chat
            if st.button("ค้นหาสูตรอาหาร", use_container_width=True, type="primary"):
                if ingredients:
                    archive_current_chat()
                    first_prompt = f"ฉันมีวัตถุดิบคือ: {ingredients} ช่วยแนะนำเมนูหน่อย"
                    st.session_state.messages = [{"role": "user", "content": first_prompt}]
                    st.session_state.page = "chat"
                    st.rerun()
                else:
                    st.warning("กรุณาใส่ส่วนผสมอย่างน้อยหนึ่งอย่าง")


### --- หน้า CHAT ---
elif st.session_state.page == "chat":
    with st.container(border=True):
        st.title("💬 ปรุงกับ ChefBot")
    
    st.markdown("<br>", unsafe_allow_html=True) 
    
    # หากยังไม่มีข้อความ ให้ใส่ message ต้อนรับจาก assistant เป็นค่าเริ่มต้น
    if not st.session_state.messages:
        st.session_state.messages = [{"role": "assistant", "content": "สวัสดีครับ มีวัตถุดิบอะไรให้ผมช่วยคิดเมนูบ้าง?"}]
    
    # avatar bot และ user
    bot_avatar_url = "https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg"
    user_avatar_url = "https://cdn-icons-png.flaticon.com/512/1377/1377199.png"

    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # แสดงข้อความทั้งหมดจาก session_state.messages
        for msg in st.session_state.messages:
            # ถ้ามีภาพแนบในข้อความ ให้แสดงภาพนั้น
            if img_data := msg.get("image"):
                st.markdown("<div style='display: flex; justify-content: flex-end;'>", unsafe_allow_html=True)
                st.image(img_data, width=200)
                st.markdown("</div>", unsafe_allow_html=True)

            # แยกสไตล์การแสดงผลตาม role
            if msg["role"] == "assistant":
                st.markdown(f'<div class="message-container"><img src="{bot_avatar_url}" class="avatar"><div class="assistant-bubble">{msg["content"]}</div></div>', unsafe_allow_html=True)
            elif msg.get("content"): # ข้อความจาก user (text)
                st.markdown(f'<div class="message-container user-container"><div class="user-bubble">{msg.get("content", "")}</div><img src="{user_avatar_url}" class="avatar"></div>', unsafe_allow_html=True)

        # ตัว placeholder สำหรับแสดงการพิมพ์ตอบแบบค่อยๆ มา (typing effect)
        response_placeholder = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)

    # ถ้ามีการป้อนข้อความใหม่จากผู้ใช้ผ่าน chat_input จะถูกเพิ่มเข้าไปใน messages แล้วรีเฟรชหน้า
    if prompt := st.chat_input("คุณมีวัตถุดิบอะไรบ้าง..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
    
    # เมื่อข้อความล่าสุดเป็นของ user ให้ระบบตอบกลับอัตโนมัติ
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        
        full_response = ""
        last_message_content = st.session_state.messages[-1]['content']
        assistant_responses = [
            "เยี่ยมเลยครับ! ลองทำ **'ผัดกะเพราหมูสับไข่ดาว'** ดูไหมครับ?",
            f"สำหรับ '{last_message_content}' ผมขอเสนอเมนู **'ต้มยำน้ำข้น'** ครับ ซดร้อนๆ คล่องคอแน่นอน",
            "วัตถุดิบแบบนี้เหมาะกับ **'ไก่ผัดเม็ดมะม่วง'** มากๆ เลยครับ สนใจไหมครับ?"
        ]
        response_text = random.choice(assistant_responses)
        
        for chunk in response_text.split():
            full_response += chunk + " "
            time.sleep(0.05)

            with response_placeholder.container():
                 st.markdown(f'<div class="message-container"><img src="{bot_avatar_url}" class="avatar"><div class="assistant-bubble">{full_response} ▌</div></div>', unsafe_allow_html=True)
        
        with response_placeholder.container():
            st.markdown(f'<div class="message-container"><img src="{bot_avatar_url}" class="avatar"><div class="assistant-bubble">{full_response}</div></div>', unsafe_allow_html=True)

        # บันทึก chat
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        # รีเฟรชหน้าเพื่อให้ UI อัปเดตและแสดงข้อความใหม่
        st.rerun()

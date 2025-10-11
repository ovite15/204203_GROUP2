import os
import json
import streamlit as st
from litellm import completion
from dotenv import load_dotenv
import time

# Import tools
from cook_tool import CookTool
from search_tools import WebSearchTool
from prompts import get_prompt, PROMPTS

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ChefBot",
    page_icon="https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg",
    layout="wide"
)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state.page = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "model" not in st.session_state:
    st.session_state.model = "groq/llama-3.3-70b-versatile"
if "prompt_type" not in st.session_state:
    st.session_state.prompt_type = "cooking"
if "conversation_stage" not in st.session_state:
    st.session_state.conversation_stage = "initial"
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "ingredients": [],
        "allergies": None,
        "restrictions": None,
        "preferences": None
    }

# ══════════════════════════════════════════════════════════════════════════════
# CSS STYLING
# ══════════════════════════════════════════════════════════════════════════════
page_style = """
    <style>
    body { color: #E8E8E8; } 
    .stApp { background-color: #E8E8E8; }
    
    [data-testid="stSidebar"] {
        background-color: #E8E8E8; 
        border-right: 1px solid #DDDDDD;
    }
    
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

    h1, h2, h3, h4, h5, h6 { color: #000000; } 
    h1 { text-align: center; }
    
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
    
    .message-container { 
        display: flex; 
        align-items: flex-end; 
        margin-bottom: 1rem; 
        gap: 10px; 
    }
    .user-container { justify-content: flex-end; }
    .avatar { 
        width: 40px; 
        height: 40px; 
        border-radius: 50%; 
        object-fit: cover; 
    }
    .assistant-bubble, .user-bubble { 
        display: inline-block; 
        padding: 10px 18px; 
        border-radius: 20px; 
        max-width: 70%; 
        text-align: left; 
        word-wrap: break-word; 
    }
    .assistant-bubble { 
        background-color: #888E95; 
        color: white; 
    }
    .user-bubble { 
        background-color: #007BFF; 
        color: white; 
    }
    [data-testid="stChatMessage"] { display: none; }
    
    .history-item { 
        background-color: #EAECEE; 
        border-radius: 0.5rem; 
        padding: 0.75rem 1rem; 
        margin-bottom: 0.5rem; 
        font-size: 0.95rem; 
    }
    
    /* Status expander styling */
    .element-container:has(> .stStatus) {
        margin: 1rem 0;
    }
    </style>
"""
st.markdown(page_style, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK API KEYS
# ══════════════════════════════════════════════════════════════════════════════
if not os.getenv("GROQ_API_KEY"):
    st.error("❌ Missing GROQ_API_KEY. Please add it to your .env file")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# INITIALIZE TOOLS
# ══════════════════════════════════════════════════════════════════════════════
cook_tool = CookTool()
search_tool = WebSearchTool()

# ══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information about recipes, cooking tips, or general questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "Search for cooking recipes based on available ingredients using Spoonacular API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of available ingredients"
                    }
                },
                "required": ["ingredients"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nutrition",
            "description": "Get detailed nutrition information for a specific ingredient from USDA database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredient": {"type": "string", "description": "Name of the ingredient"}
                },
                "required": ["ingredient"]
            }
        }
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# TOOL EXECUTOR
# ══════════════════════════════════════════════════════════════════════════════
def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute the requested tool and return results"""
    try:
        if tool_name == "search_web":
            query = arguments.get("query", "")
            num_results = arguments.get("num_results", 5)
            results = search_tool.search(query, num_results)
            formatted = search_tool.format_results(results)
            return formatted if formatted else "ไม่พบผลการค้นหา"
        
        elif tool_name == "search_recipes":
            ingredients = arguments.get("ingredients", [])
            if not ingredients:
                return "❌ กรุณาระบุวัตถุดิบ"
            
            recipes = cook_tool.search_recipes(ingredients)
            
            if isinstance(recipes, dict) and "error" in recipes:
                return f"⚠️ เกิดข้อผิดพลาด: {recipes['error']}"
            
            if not recipes:
                return f"❌ ไม่พบสูตรอาหารสำหรับวัตถุดิบ: {', '.join(ingredients)}"
            
            formatted = cook_tool.format_recipes(recipes)
            return formatted if formatted else "❌ ไม่สามารถแสดงสูตรอาหารได้"
        
        elif tool_name == "get_nutrition":
            ingredient = arguments.get("ingredient", "")
            if not ingredient:
                return "❌ กรุณาระบุวัตถุดิบที่ต้องการดูข้อมูลโภชนาการ"
            
            nutrition = cook_tool.get_nutrition(ingredient)
            if "error" in nutrition:
                return f"⚠️ {nutrition['error']}"
            
            formatted = cook_tool.format_nutrition(nutrition)
            return formatted
        
        else:
            return f"❌ ไม่รู้จักเครื่องมือ '{tool_name}'"
    
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาด: {str(e)}"

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def archive_current_chat():
    """เก็บการสนทนาปัจจุบันลงประวัติ"""
    if len(st.session_state.messages) > 1:
        if not st.session_state.chat_history or st.session_state.chat_history[0] != st.session_state.messages:
            st.session_state.chat_history.insert(0, st.session_state.messages.copy())

def load_chat(index):
    """โหลดการสนทนาจากประวัติ"""
    archive_current_chat()
    st.session_state.messages = st.session_state.chat_history[index]
    st.session_state.page = "chat"
    st.rerun()

def go_to_home():
    """กลับไปหน้าแรก"""
    archive_current_chat()
    st.session_state.messages = []
    st.session_state.page = "home"
    st.session_state.conversation_stage = "initial"
    st.session_state.user_info = {
        "ingredients": [],
        "allergies": None,
        "restrictions": None,
        "preferences": None
    }
    st.rerun()

def go_to_chat():
    """ไปหน้าแชท"""
    st.session_state.page = "chat"
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg", width=250)
    st.title("ChefBot")
    st.markdown("---")
    
    # ปุ่มแชทใหม่
    st.button("🔄 แชทใหม่", on_click=go_to_home, use_container_width=True)
    
    # ตั้งค่าโมเดล (เฉพาะเมื่ออยู่หน้าแชท)
    if st.session_state.page == "chat":
        st.markdown("---")
        st.subheader("⚙️ ตั้งค่า")
        
        MODELS = {
            "groq/llama-3.3-70b-versatile": "Llama 3.3 70B",
            "groq/llama-3.1-70b-versatile": "Llama 3.1 70B",
            "groq/mixtral-8x7b-32768": "Mixtral 8x7B",
        }
        
        model = st.selectbox(
            "โมเดล AI",
            list(MODELS.keys()),
            format_func=lambda x: MODELS[x],
            index=list(MODELS.keys()).index(st.session_state.model)
        )
        st.session_state.model = model
        
        temperature = st.slider("ความสร้างสรรค์", 0.0, 2.0, 0.7, 0.1)
        
        # แสดงเครื่องมือที่ใช้งานได้
        with st.expander("🛠️ เครื่องมือที่ใช้งานได้"):
            st.markdown("- 🔍 **ค้นหาเว็บ** - ค้นหาสูตรอาหารและข้อมูลออนไลน์")
            st.markdown("- 🍳 **ค้นหาสูตร** - ค้นหาสูตรจากวัตถุดิบ (Spoonacular)")
            st.markdown("- 📊 **ข้อมูลโภชนาการ** - ดูคุณค่าทางโภชนาการ (USDA)")
    
    st.markdown("---")
    st.subheader("📜 ประวัติการปรุง")
    
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history):
            title = next((msg["content"] for msg in chat if msg["role"] == "user"), "บทสนทนา")
            st.button(
                f"💬 {title[:25]}..." if len(title) > 25 else f"💬 {title}",
                key=f"history_{i}",
                on_click=load_chat,
                args=(i,),
                use_container_width=True
            )
    else:
        st.info("ยังไม่มีประวัติการสนทนา")

# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "home":
    with st.container(border=True):
        st.title("สวัสดีครับ ChefBot ยินดีรับใช้ 🍳")
        st.markdown("<h3 style='text-align: center;'>เลือกวิธีการเริ่มต้น เพื่อค้นหาสูตรอาหารที่ใช่สำหรับคุณ</h3>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True) 

    col1, col2 = st.columns(2, gap="large")

    # คอลัมน์ซ้าย: อัปโหลดรูปภาพ
    with col1:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>อัปโหลดรูปภาพวัตถุดิบ 📸</h4>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("อัปโหลดรูปภาพ", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
            
            if uploaded_file:
                archive_current_chat()
                st.session_state.messages = [
                    {"role": "user", "content": "แนะนำเมนูจากรูปภาพนี้หน่อยครับ", "image": uploaded_file.getvalue()}
                ]
                go_to_chat()
            else:
                st.info("💡 อัปโหลดภาพวัตถุดิบที่คุณมี แล้ว ChefBot จะแนะนำเมนูให้")

    # คอลัมน์ขวา: พิมพ์ส่วนผสม
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>พิมพ์ส่วนผสมเอง ✍️</h4>", unsafe_allow_html=True)
            ingredients = st.text_input(
                "ระบุส่วนผสม คั่นด้วยจุลภาค (,)", 
                placeholder="เนื้อหมู, หอมใหญ่, กระเทียม, พริก...",
                key="ingredients_input"
            )
            
            if st.button("🔍 ค้นหาสูตรอาหาร", use_container_width=True, type="primary"):
                if ingredients:
                    archive_current_chat()
                    first_prompt = f"ฉันมีวัตถุดิบคือ: {ingredients} ช่วยแนะนำเมนูหน่อยครับ"
                    st.session_state.messages = [{"role": "user", "content": first_prompt}]
                    go_to_chat()
                else:
                    st.warning("⚠️ กรุณาใส่ส่วนผสมอย่างน้อยหนึ่งอย่าง")


# ══════════════════════════════════════════════════════════════════════════════
# CHAT PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "chat":
    with st.container(border=True):
        st.title("💬 ปรุงกับ ChefBot")
    
    st.markdown("<br>", unsafe_allow_html=True) 
    
    # ข้อความต้อนรับ
    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "assistant", "content": "สวัสดีครับ! ผมคือ ChefBot ผู้ช่วยพ่อครัวของคุณ 👨‍🍳\n\nบอกผมได้เลยว่าคุณมีวัตถุดิบอะไรบ้าง หรือต้องการทำอาหารแบบไหน ผมจะช่วยหาสูตรที่เหมาะสมให้ครับ!"}
        ]
    
    # Avatar URLs
    bot_avatar_url = "https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg"
    user_avatar_url = "https://cdn-icons-png.flaticon.com/512/1377/1377199.png"

    # แสดงข้อความทั้งหมด
    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            # แสดงรูปภาพถ้ามี
            if img_data := msg.get("image"):
                st.markdown("<div style='display: flex; justify-content: flex-end; margin-bottom: 1rem;'>", unsafe_allow_html=True)
                st.image(img_data, width=200, caption="วัตถุดิบของคุณ")
                st.markdown("</div>", unsafe_allow_html=True)

            # แสดงข้อความ
            if msg["role"] == "assistant":
                st.markdown(
                    f'<div class="message-container">'
                    f'<img src="{bot_avatar_url}" class="avatar">'
                    f'<div class="assistant-bubble">{msg["content"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            elif msg.get("content"):
                st.markdown(
                    f'<div class="message-container user-container">'
                    f'<div class="user-bubble">{msg.get("content", "")}</div>'
                    f'<img src="{user_avatar_url}" class="avatar">'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("คุณมีวัตถุดิบอะไรบ้าง..."):
        # เพิ่มข้อความของ user
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # แสดงข้อความของ user ทันที
        st.markdown(
            f'<div class="message-container user-container">'
            f'<div class="user-bubble">{prompt}</div>'
            f'<img src="{user_avatar_url}" class="avatar">'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # สร้างคำตอบจาก AI พร้อม tool calling
        full_response = ""
        
        try:
            # ใช้ placeholder สำหรับแสดง typing indicator
            response_container = st.empty()
            
            with response_container.container():
                st.markdown(
                    f'<div class="message-container">'
                    f'<img src="{bot_avatar_url}" class="avatar">'
                    f'<div class="assistant-bubble">กำลังคิด... 💭</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # ตั้งค่า system prompt
            system_prompt = get_prompt(st.session_state.prompt_type)
            
            messages_with_system = [
                {"role": "system", "content": system_prompt}
            ] + st.session_state.messages
            
            # Tool calling loop
            max_iterations = 5
            for iteration in range(max_iterations):
                response = completion(
                    model=st.session_state.model,
                    messages=messages_with_system,
                    temperature=0.7,
                    max_tokens=2048,
                    tools=tools,
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                
                # ตรวจสอบว่ามี tool calls หรือไม่
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # แสดงสถานะการใช้เครื่องมือ
                    tool_calls_list = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                    
                    messages_with_system.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": tool_calls_list
                    })
                    
                    # ประมวลผล tool calls
                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        # แสดงสถานะ
                        with st.status(f"🔧 กำลังใช้เครื่องมือ: **{func_name}**", expanded=True):
                            st.write("**พารามิเตอร์:**")
                            st.json(func_args)
                            
                            # เรียกใช้เครื่องมือ
                            tool_result = execute_tool(func_name, func_args)
                            
                            st.write("**ผลลัพธ์:**")
                            preview = tool_result[:500] + "..." if len(tool_result) > 500 else tool_result
                            st.markdown(preview)
                        
                        # เพิ่มผลลัพธ์เข้า messages
                        messages_with_system.append({
                            "role": "tool",
                            "content": tool_result,
                            "tool_call_id": tool_call.id
                        })
                    
                    # อัปเดต placeholder
                    with response_container.container():
                        st.markdown(
                            f'<div class="message-container">'
                            f'<img src="{bot_avatar_url}" class="avatar">'
                            f'<div class="assistant-bubble">🔍 ใช้เครื่องมือ: {", ".join([tc.function.name for tc in message.tool_calls])}<br>กำลังประมวลผล...</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    
                    continue
                
                else:
                    # ไม่มี tool calls - นี่คือคำตอบสุดท้าย
                    full_response = message.content or "ขออภัยครับ ไม่สามารถสร้างคำตอบได้"
                    
                    # แสดงคำตอบแบบ streaming effect
                    words = full_response.split()
                    displayed_text = ""
                    
                    for word in words:
                        displayed_text += word + " "
                        with response_container.container():
                            st.markdown(
                                f'<div class="message-container">'
                                f'<img src="{bot_avatar_url}" class="avatar">'
                                f'<div class="assistant-bubble">{displayed_text}▌</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        time.sleep(0.03)
                    
                    # แสดงคำตอบสุดท้าย (ไม่มี cursor)
                    with response_container.container():
                        st.markdown(
                            f'<div class="message-container">'
                            f'<img src="{bot_avatar_url}" class="avatar">'
                            f'<div class="assistant-bubble">{full_response}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    
                    # บันทึกคำตอบ
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    break
            
            else:
                # ถึง max iterations
                full_response = "⚠️ เกิดข้อผิดพลาด: ใช้เครื่องมือมากเกินไป กรุณาลองใหม่อีกครั้ง"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
            
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            full_response = f"ขออภัยครับ เกิดข้อผิดพลาด: {str(e)}"
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })
        
        # รีเฟรชหน้า
        time.sleep(0.5)
        st.rerun()
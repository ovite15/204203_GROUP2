import os
import sys
from pathlib import Path
import streamlit as st
from io import BytesIO
from PIL import Image

# Load .env (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Path setup
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.llm_client import LLMClient, get_available_models
from utils.vision import detect_ingredients_from_image, format_ingredient_list

# ── Page ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Image to text", layout="wide")
st.title("image to text")

# ── Session State ───────────────────────────────────────────────────────
st.session_state.setdefault("llm_client", None)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("ingredients", [])
st.session_state.setdefault("edit_text", "")
st.session_state.setdefault("has_custom", False)
st.session_state.setdefault("confirmed", False)
st.session_state.setdefault("await_confirm", False)
st.session_state.setdefault("await_manual", False)
st.session_state.setdefault("pending_edit_text", "")
st.session_state.setdefault("uploaded_image", None)  

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")

    models = get_available_models()
    selected = st.selectbox("Select Model", models, index=0)
    temp = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_toks = st.slider("Max Tokens", 50, 4000, 1000, 50)

    if st.button("Initialize Model") or st.session_state.llm_client is None:
        with st.spinner("Initializing model..."):
            st.session_state.llm_client = LLMClient(
                model=selected, temperature=temp, max_tokens=max_toks
            )
        st.success(f"Model {selected} initialized!")

    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.await_confirm = False
        st.session_state.await_manual = False
        st.session_state.confirmed = False
        st.session_state.uploaded_image = None
        st.rerun()

    st.subheader("Model Info")
    c = st.session_state.llm_client
    if c:
        st.write(f"**Model:** {c.model}")
        st.write(f"**Temperature:** {c.temperature}")
        st.write(f"**Max Tokens:** {c.max_tokens}")

# ── Check API Key ───────────────────────────────────────────────────────
if not (os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")):
    st.error("Missing OPENAI_API_KEY or GROQ_API_KEY")
    st.stop()

# ── Upload image ───────────────────────────────────────────────────────
st.markdown("อัปโหลดรูปเพื่อดึงวัตถุดิบ")
uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

# Persist image bytes
if uploaded is not None:
    st.session_state.uploaded_image = uploaded.getvalue()

# แสดงรูปก่อน แล้วค่อยเป็นแชต
if st.session_state.uploaded_image:
    image = Image.open(BytesIO(st.session_state.uploaded_image))
    st.image(image, caption="Uploaded image", width="stretch")

# ── Handle new upload ────────────────────────────────────────
if (
    uploaded is not None
    and not st.session_state.await_confirm
    and not st.session_state.await_manual
    and not st.session_state.confirmed
):
    with st.spinner("กำลังวิเคราะห์ภาพเพื่อดึงวัตถุดิบ..."):
        detection = detect_ingredients_from_image(
            uploaded, temperature=temp, max_tokens=max_toks, prefer_provider=None
        )
    detected_items = detection.get("ingredients", []) or []
    if not st.session_state.get("has_custom"):
        st.session_state["ingredients"] = detected_items
        st.session_state["edit_text"] = format_ingredient_list(detected_items)

    names_csv = (
        format_ingredient_list(st.session_state["ingredients"])
        if st.session_state["ingredients"] else ""
    )

    # บันทึกเป็นข้อความของ assistant ลง history
    if names_csv:
        msg = f"คุณมี **{names_csv}** ใช่ไหมครับ? (พิมพ์ 'ใช่' หรือ 'ไม่')"
        st.session_state["await_confirm"] = True
        st.session_state["pending_edit_text"] = names_csv
    else:
        msg = "ไม่พบวัตถุดิบจากภาพ คุณต้องการพิมพ์รายการเองไหม? (พิมพ์ 'ใช่' หรือ 'ไม่')"
        st.session_state["await_confirm"] = True
        st.session_state["pending_edit_text"] = ""

    st.session_state.messages.append({"role": "assistant", "content": msg})

# ── Chat Input ──────────────────────────────────
user_prompt = st.chat_input("พิมพ์ข้อความถึงบอท…") if st.session_state.llm_client else None
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    p = user_prompt.strip().lower()
    YES = {"yes", "y", "ใช่", "ok", "โอเค", "ครับ", "ค่ะ"}
    NO = {"no", "n", "ไม่", "แก้", "แก้ไข", "nope"}

    if st.session_state.get("await_confirm"):
        if p in YES:
            st.session_state["confirmed"] = True
            st.session_state["await_confirm"] = False
            st.session_state.messages.append({"role": "assistant", "content": "ยืนยันรายการวัตถุดิบแล้ว ✅ ขอบคุณครับ!"})
        elif p in NO:
            st.session_state["await_confirm"] = False
            st.session_state["await_manual"] = True
            st.session_state.messages.append({"role": "assistant", "content": "โอเคครับ งั้นคุณมีอะไรมั่งครับ?"})
        else:
            st.session_state["await_confirm"] = False

    elif st.session_state.get("await_manual"):
        parts = [x.strip() for x in user_prompt.split(",")]
        items = [{"name": x, "confidence": 0.9} for x in parts if x]
        st.session_state["ingredients"] = items
        st.session_state["has_custom"] = bool(items)
        st.session_state["edit_text"] = ", ".join(i["name"] for i in items)
        st.session_state["await_manual"] = False
        st.session_state.messages.append({"role": "assistant", "content": "ยืนยันรายการวัตถุดิบแล้ว ✅ ขอบคุณครับ!"})

    else:
        
        chat_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        try:
            reply = st.session_state.llm_client.chat(chat_messages)
        except Exception as e:
            reply = f"เกิดข้อผิดพลาด: {e}"
        st.session_state.messages.append({"role": "assistant", "content": reply})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

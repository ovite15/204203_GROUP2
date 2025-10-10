import os
import sys
from pathlib import Path

import streamlit as st

# Load .env (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.llm_client import LLMClient, get_available_models  
from utils.vision import (  
    detect_ingredients_from_image,
    format_ingredient_list,
)
st.title("image to text")
# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    models = get_available_models()
    selected = st.selectbox("Select Model", models, index=0)
    temp = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_toks = st.slider("Max Tokens", 50, 4000, 1000, 50)

    # Ensure state keys exist to avoid AttributeError
    st.session_state.setdefault("llm_client", None)
    st.session_state.setdefault("messages", [])

    if st.button("Initialize Model") or st.session_state.llm_client is None:
        with st.spinner("Initializing model..."):
            st.session_state.llm_client = LLMClient(model=selected, temperature=temp, max_tokens=max_toks)
        st.success(f"Model {selected} initialized!")

    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    st.subheader("Model Info")
    c = st.session_state.llm_client
    if c:
        st.write(f"**Model:** {c.model}")
        st.write(f"**Temperature:** {c.temperature}")
        st.write(f"**Max Tokens:** {c.max_tokens}")

# ── Check API Keys ─────────────────────────────────────────────────────────
if not (os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")):
    st.error("Missing OPENAI_API_KEY or GROQ_API_KEY")
    st.stop()

# ── Session State ─────────────────────────────────────────────────────────
st.session_state.setdefault("ingredients", [])
st.session_state.setdefault("editing", False)
st.session_state.setdefault("confirmed", False)
st.session_state.setdefault("has_custom", False)
st.session_state.setdefault("edit_text", "")
st.session_state.setdefault("llm_client", None)
st.session_state.setdefault("messages", [])

# ── Tabs UI ────────────────────────────────────────────────────────────────
tab_img, tab_text = st.tabs(["อัปโหลดรูป", "พิมพ์รายการเอง"])

# ========== upload image ==========
with tab_img:
    uploaded = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        with st.spinner("กำลังวิเคราะห์ภาพเพื่อดึงวัตถุดิบ..."):
            detection = detect_ingredients_from_image(
                uploaded,
                temperature=temp,
                max_tokens=max_toks,
                prefer_provider=None,
            )

        st.image(uploaded, caption="Uploaded image", width="stretch")

        # Only update detected ingredients if user hasn't customized
        detected_items = detection.get("ingredients", []) or []
        if not st.session_state.get("has_custom"):
            st.session_state["ingredients"] = detected_items
            st.session_state["edit_text"] = format_ingredient_list(detected_items)

        # Build the question in Thai
        names_csv = format_ingredient_list(st.session_state["ingredients"]) if st.session_state["ingredients"] else ""
        question = f"คุณมี {names_csv} ใช่ไหมครับ?" if names_csv else "ไม่พบวัตถุดิบจากภาพ คุณต้องการแก้ไขรายการเองไหม?"

        st.subheader("ตรวจสอบรายการวัตถุดิบ")
        st.info(question)

        col1, col2 = st.columns(2)
        yes_clicked = col1.button("ใช่", key="yes_img")
        edit_clicked = col2.button("แก้ไข", key="edit_img")

        if yes_clicked:
            st.session_state["confirmed"] = True
            st.session_state["editing"] = False
            st.success("ยืนยันรายการวัตถุดิบแล้ว ขอบคุณครับ!")

        if edit_clicked:
            st.session_state["editing"] = True
            st.session_state["edit_text"] = names_csv  # preload

        if st.session_state.get("editing"):
            st.markdown("แก้ไขรายชื่อวัตถุดิบ")
            edited = st.text_area("", value=st.session_state.get("edit_text", names_csv), height=100, key="edit_area_img")
            save_col, cancel_col = st.columns(2)
            if save_col.button("บันทึก (Save)", key="save_img"):
                parts = [p.strip() for p in (edited or "").split(",")]
                items = [{"name": p, "confidence": 0.9} for p in parts if p]
                st.session_state["ingredients"] = items
                st.session_state["has_custom"] = True
                st.session_state["editing"] = False
                st.session_state["edit_text"] = ", ".join([i["name"] for i in items])
                st.success("ปรับปรุงรายการแล้ว")
            if cancel_col.button("ยกเลิก (Cancel)", key="cancel_img"):
                st.session_state["editing"] = False

# ========== type manually ==========
with tab_text:
    st.markdown("พิมพ์รายการวัตถุดิบเอง เช่น **ฉันมี ไข่, หมูสับ, ต้นหอม**")
    preset = st.session_state["edit_text"] or format_ingredient_list(st.session_state["ingredients"]) or ""
    typed = st.text_input("พิมพ์รายการ", value=preset, key="typed_input")
    c3, c4 = st.columns(2)
    if c3.button("ยืนยันข้อความ", key="confirm_text"):
        parts = [p.strip() for p in (typed or "").split(",")]
        items = [{"name": p, "confidence": 0.9} for p in parts if p]
        st.session_state["ingredients"] = items
        st.session_state["has_custom"] = True
        st.session_state["editing"] = False
        st.session_state["confirmed"] = True
        st.session_state["edit_text"] = ", ".join(i["name"] for i in items)
        st.success("ยืนยันรายการข้อความแล้ว")
    if c4.button("ล้างรายการ", key="clear_text"):
        st.session_state["ingredients"] = []
        st.session_state["has_custom"] = False
        st.session_state["edit_text"] = ""
        st.session_state["confirmed"] = False
        st.info("ล้างรายการเรียบร้อย")

# ── Summary ───────────────────────────────────────────────────
if st.session_state["ingredients"]:
    st.divider()
    st.subheader("สรุปรายการวัตถุดิบ")
    st.write(format_ingredient_list(st.session_state["ingredients"]))

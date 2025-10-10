import os
import streamlit as st
from litellm import completion
from dotenv import load_dotenv

# use tool
from cook_tool import CookTool
from search_tools import WebSearchTool



load_dotenv()

st.set_page_config(page_title="💬 Groq Chat", page_icon="💬")
st.title("💬 cooking ")

# ── Session State ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    st.session_state.model = "groq/llama-3.1-8b-instant"

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    MODELS = {
        "groq/llama-3.1-8b-instant": "Llama 3.1 8B",
        "groq/llama-3.3-70b-versatile": "Llama 3.3 70B",
        "groq/deepseek-r1-distill-llama-70b": "DeepSeek R1 70B",
        "groq/mixtral-8x7b-32768": "Mixtral 8x7B",
    }
    
    model = st.selectbox("Model", list(MODELS.keys()), format_func=lambda x: MODELS[x])
    st.session_state.model = model
    
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("Max tokens", 128, 4096, 1024, 128)
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ── Check API Key ────────────────────────────────────────────────────────────
if not os.getenv("GROQ_API_KEY"):
    st.error("Missing GROQ_API_KEY")
    st.stop()

# ── Display Messages ─────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Instance CookTool ───────────────────────────────────────────────────────
cook_tool = CookTool()

# ── Chat Input ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("Type a message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # ตรวจว่าผู้ใช้พูดถึงวัตถุดิบไหม
            if any(word in prompt.lower() for word in ["ingredient", "ingredients", "cooking", "menu", "food"]):
                result = cook_tool.search_recipes(prompt)
                if not recipes or ("error" in recipes):
                    placeholder.markdown("🔎 ไม่พบสูตรอาหารจาก API กำลังค้นเว็บแทน...")
                    web_results = search_tool.search(prompt)
                    full_response = search_tool.format_results(web_results)
                else:
                    full_response = cook_tool.format_recipes(recipes)

                placeholder.markdown(full_response)

            else:
   
                system_prompt = """You are a helpful cooking assistant. Follow this multi-turn chain of thought when users mention ingredients:

1. **Identify Ingredients**: When user mentions ingredients, acknowledge them warmly

2. **Ask ONE Question at a Time** (follow this order):
   - **Turn 1**: Ask ONLY about food allergies
   - **Turn 2**: Ask ONLY about dietary restrictions
   - **Turn 3**: Ask ONLY about preferences
   - **Turn 4**: Suggest recipes after all info gathered
ื
  **Additional Rules for Searching & Fallback:**

- First, try to look up recipes using web / API sources.  
- If you find matching recipes, present them (title, ingredients, maybe link).  
- If web / API search yields nothing relevant, then **think yourself** and invent 2-3 recipe ideas based on the ingredients.  
- Always prefer *real recipes* from external sources first, and only fall back to invented ones when necessary.  
- Be conversational, friendly, and match the users language (Thai or English).   

**IMPORTANT RULES:**
- Ask ONLY ONE question per response
- Wait for user's answer before asking the next question
- Keep track of what you've already asked
- Don't suggest recipes until you have all 3 answers
- Be conversational and friendly
- Match user's language (Thai or English)
"""

                messages_with_system = [
                    {"role": "system", "content": system_prompt}
                ] + st.session_state.messages
            
                response = completion(
                    model=st.session_state.model,
                    messages=messages_with_system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
            
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
            
                placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"Error: {e}")
            full_response = f"[Error: {e}]"
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": full_response})

import os
import streamlit as st
from litellm import completion

# Load .env (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

st.set_page_config(page_title="💬 Groq Chat", page_icon="💬")
st.title("💬 Groq Chat")

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
            # System prompt with multi-turn chain of thought for food recommendations
            system_prompt = """You are a helpful cooking assistant. Follow this multi-turn chain of thought when users mention ingredients:

**Multi-Turn Chain of Thought Process:**

1. **Identify Ingredients**: When user mentions ingredients, acknowledge them warmly

2. **Ask ONE Question at a Time** (follow this order):
   - **Turn 1**: Ask ONLY about food allergies
     Example: "มีอาหารที่แพ้หรือเปล่าคะ?" or "Do you have any food allergies?"
   
   - **Turn 2** (after they answer): Ask ONLY about dietary restrictions
     Example: "มีข้อจำกัดด้านอาหารไหม เช่น กินเจ ฮาลาล หรือไม่กินเนื้อสัตว์?" 
     or "Any dietary restrictions like vegetarian, vegan, halal?"
   
   - **Turn 3** (after they answer): Ask ONLY about preferences
     Example: "ชอบทำอาหารแบบไหน เผ็ด หวาน ง่ายๆ หรือสุขภาพ?" 
     or "What's your preference? Spicy, sweet, quick, or healthy?"
   
   - **Turn 4** (after all info gathered): NOW suggest 2-3 recipes based on their ingredients and restrictions

**IMPORTANT RULES:**
- Ask ONLY ONE question per response
- Wait for user's answer before asking the next question
- Keep track of what you've already asked
- Don't suggest recipes until you have all 3 answers
- Be conversational and friendly
- Match user's language (Thai or English)

**Example Flow:**
User: "I have chicken, tomatoes, and rice"
You: "Great! Do you have any food allergies?"
User: "No allergies"
You: "Perfect! Any dietary restrictions like halal or vegetarian?"
User: "Halal please"
You: "Got it! What style do you prefer - spicy, mild, or healthy?"
User: "Spicy"
You: "Awesome! Here are 3 halal spicy recipes with chicken, tomatoes and rice: [recipes]"
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
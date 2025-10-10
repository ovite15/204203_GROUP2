import os
import json
import streamlit as st
from litellm import completion
from dotenv import load_dotenv

# use tool
from cook_tool import CookTool
from search_tools import WebSearchTool
from prompts import get_prompt, get_custom_prompt, PROMPTS

load_dotenv()

st.set_page_config(page_title="💬 Groq Chat", page_icon="💬")
st.title("💬 AI Cooking Assistant with Tools")

# ── Session State ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    st.session_state.model = "groq/llama-3.3-70b-versatile"

if "prompt_type" not in st.session_state:
    st.session_state.prompt_type = "cooking"

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    MODELS = {
        "groq/llama-3.3-70b-versatile": "Llama 3.3 70B (Tool Support)",
        "groq/llama-3.1-70b-versatile": "Llama 3.1 70B (Tool Support)",
        "groq/mixtral-8x7b-32768": "Mixtral 8x7B",
    }
    
    model = st.selectbox("Model", list(MODELS.keys()), format_func=lambda x: MODELS[x])
    st.session_state.model = model
    
    # Prompt selector
    st.markdown("---")
    prompt_type = st.selectbox(
        "🎯 Prompt Style",
        options=list(PROMPTS.keys()),
        format_func=lambda x: x.replace("_", " ").title(),
        index=list(PROMPTS.keys()).index(st.session_state.prompt_type)
    )
    st.session_state.prompt_type = prompt_type
    
    # Show current prompt preview
    with st.expander("📄 View Current Prompt"):
        st.code(get_prompt(prompt_type), language="markdown")
    
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("Max tokens", 128, 4096, 1024, 128)
    
    st.markdown("---")
    st.markdown("### 🛠️ Available Tools")
    st.markdown("- 🔍 Web Search")
    st.markdown("- 🍳 Recipe Search")
    st.markdown("- 📊 Nutrition Info")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ── Check API Key ────────────────────────────────────────────────────────────
if not os.getenv("GROQ_API_KEY"):
    st.error("Missing GROQ_API_KEY")
    st.stop()

# ── Initialize Tools ─────────────────────────────────────────────────────────
cook_tool = CookTool()
search_tool = WebSearchTool()

# ── Tool Definitions ─────────────────────────────────────────────────────────
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information. Use this when user asks about current events, news, or general information not related to cooking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "Search for cooking recipes based on available ingredients. Use this when user mentions ingredients or asks for recipe suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of available ingredients (e.g., ['chicken', 'rice', 'garlic'])"
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
            "description": "Get detailed nutrition information for a specific ingredient or food item from USDA database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredient": {
                        "type": "string",
                        "description": "Name of the ingredient to look up (e.g., 'chicken breast', 'brown rice')"
                    }
                },
                "required": ["ingredient"]
            }
        }
    }
]

# ── Tool Executor ────────────────────────────────────────────────────────────
def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute the requested tool and return results"""
    try:
        if tool_name == "search_web":
            query = arguments.get("query", "")
            num_results = arguments.get("num_results", 5)
            results = search_tool.search(query, num_results)
            formatted = search_tool.format_results(results)
            return formatted if formatted else "No search results found."
        
        elif tool_name == "search_recipes":
            ingredients = arguments.get("ingredients", [])
            if not ingredients:
                return "Error: No ingredients provided. Please specify ingredients to search for recipes."
            
            recipes = cook_tool.search_recipes(ingredients)
            
            # Check if error
            if isinstance(recipes, dict) and "error" in recipes:
                return f"Recipe search error: {recipes['error']}"
            
            # Check if empty
            if not recipes:
                return f"No recipes found for ingredients: {', '.join(ingredients)}. Try different ingredients or ask me to suggest recipes based on my knowledge."
            
            formatted = cook_tool.format_recipes(recipes)
            return formatted if formatted else "No recipes could be formatted."
        
        elif tool_name == "get_nutrition":
            ingredient = arguments.get("ingredient", "")
            if not ingredient:
                return "Error: No ingredient specified."
            
            nutrition = cook_tool.get_nutrition(ingredient)
            if "error" in nutrition:
                return f"Nutrition lookup error: {nutrition['error']}"
            
            # Format nutrition info
            result = f"**{nutrition.get('description', ingredient)}**\n\n"
            result += "**Nutrition Facts (per 100g):**\n"
            nutrients = nutrition.get('nutrients', {})
            if not nutrients:
                return f"No nutrition data available for {ingredient}"
            
            for nutrient, value in list(nutrients.items())[:10]:  # Limit to 10 nutrients
                result += f"- {nutrient}: {value}\n"
            return result
        
        else:
            return f"Error: Unknown tool '{tool_name}'"
    
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

# ── Display Messages ─────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ── Chat Input ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("Type a message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response with tool calling
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # Get system prompt from prompts.py
            system_prompt = get_prompt(st.session_state.prompt_type)
            
            # Prepare messages with system prompt
            messages_with_system = [
                {"role": "system", "content": system_prompt}
            ] + st.session_state.messages
            
            # Tool calling loop (max 5 iterations to prevent infinite loops)
            max_iterations = 5
            for iteration in range(max_iterations):
                # Call LLM
                response = completion(
                    model=st.session_state.model,
                    messages=messages_with_system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                
                # Check if LLM wants to call a tool
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Prepare assistant message with tool calls
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
                    
                    # Add assistant message to conversation (for API)
                    messages_with_system.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": tool_calls_list
                    })
                    
                    # Execute each tool call
                    tool_results_text = []
                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        # Show what tool is being used
                        with st.status(f"🔧 Using tool: **{func_name}**", expanded=True):
                            st.write(f"**Arguments:**")
                            st.json(func_args)
                            
                            # Execute tool
                            tool_result = execute_tool(func_name, func_args)
                            tool_results_text.append(f"**{func_name}**: {tool_result[:100]}...")
                            
                            st.write(f"**Result Preview:**")
                            result_preview = tool_result[:300] + "..." if len(tool_result) > 300 else tool_result
                            st.markdown(result_preview)
                        
                        # Add tool result to messages (for API)
                        messages_with_system.append({
                            "role": "tool",
                            "content": tool_result,
                            "tool_call_id": tool_call.id
                        })
                    
                    # Show summary of tools used
                    placeholder.markdown(f"🔍 Used tools: {', '.join([tc.function.name for tc in message.tool_calls])}\n\nProcessing results...")
                    
                    # Continue loop to get LLM's response to tool results
                    continue
                
                else:
                    # No more tool calls - this is the final response
                    full_response = message.content or "No response generated."
                    placeholder.markdown(full_response)
                    
                    # Add final assistant response to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    break
            
            else:
                # Max iterations reached
                full_response = "⚠️ Maximum tool calling iterations reached. The model may be stuck in a loop. Please try:\n- Rephrasing your question\n- Using a different model\n- Clearing the chat and starting over"
                placeholder.markdown(full_response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
            
        except Exception as e:
            st.error(f"Error: {e}")
            full_response = f"❌ Error: {str(e)}\n\nPlease make sure you're using a model that supports function calling (e.g., Llama 3.3 70B or Llama 3.1 70B)."
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })
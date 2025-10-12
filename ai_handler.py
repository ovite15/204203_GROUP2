"""
AI response generation with tool calling support
"""
import json
import streamlit as st
import logging
from litellm import completion
from prompts import get_prompt
from tools_executor import execute_tool
from config import TOOL_DEFINITIONS, MAX_TOOL_ITERATIONS, MAX_TOKENS

logger = logging.getLogger(__name__)


def generate_response(user_message: str) -> str:
    """
    Generate AI response with tool calling support
    
    Args:
        user_message: User's input message
    
    Returns:
        AI-generated response string
    """
    try:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_message})
        
        # Prepare messages with system prompt
        system_prompt = get_prompt(st.session_state.prompt_type)
        messages = [
            {"role": "system", "content": system_prompt}
        ] + st.session_state.messages
        
        # Tool calling loop
        for iteration in range(MAX_TOOL_ITERATIONS):
            response = completion(
                model=st.session_state.model,
                messages=messages,
                temperature=st.session_state.temperature,
                max_tokens=MAX_TOKENS,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check for tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Process tool calls
                messages = _process_tool_calls(messages, message)
                continue  # Continue to next iteration
            
            else:
                # No more tool calls - this is the final response
                final_response = message.content or "ขออภัยครับ ไม่สามารถสร้างคำตอบได้"
                
                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                return final_response
        
        # Max iterations reached
        error_msg = "⚠️ ระบบใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        return error_msg
    
    except Exception as e:
        logger.error(f"Response generation error: {str(e)}", exc_info=True)
        error_msg = "ขออภัยครับ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        return error_msg


def _process_tool_calls(messages: list, message) -> list:
    """
    Process tool calls from the AI model
    
    Args:
        messages: Current message history
        message: Message object with tool calls
    
    Returns:
        Updated message history
    """
    # Add assistant message with tool calls
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
    
    messages.append({
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": tool_calls_list
    })
    
    # Execute tools
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        
        # Show tool execution status
        with st.status(f"🔧 ใช้เครื่องมือ: {func_name}", expanded=False) as status:
            st.write(f"**พารามิเตอร์:** `{json.dumps(func_args, ensure_ascii=False)}`")
            
            tool_result = execute_tool(func_name, func_args)
            
            st.write("**ผลลัพธ์:**")
            preview = tool_result[:300] + "..." if len(tool_result) > 300 else tool_result
            st.write(preview)
            
            status.update(label=f"✅ {func_name} - สำเร็จ", state="complete")
        
        # Add tool result to messages
        messages.append({
            "role": "tool",
            "content": tool_result,
            "tool_call_id": tool_call.id
        })
    
    return messages
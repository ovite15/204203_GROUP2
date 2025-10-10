"""
Utility functions for LiteLLM integration
"""
import os
from typing import Dict, List, Any, Optional
import litellm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMClient:
    """Wrapper class for LiteLLM operations"""

    def __init__(self, model: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 1000):
        self.model = model or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Set API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            os.environ["GOOGLE_API_KEY"] = google_key
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Send a chat completion request

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters for the completion

        Returns:
            str: The response content
        """
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """
        Send a streaming chat completion request

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters for the completion

        Yields:
            str: Chunks of the response content
        """
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True,
                **kwargs
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"


def get_available_models() -> List[str]:
    """Get list of available models"""
    return [
        # OpenAI (optional)
        "gpt-4o-mini",
        "gpt-4o",

        # Groq models (use as: provider/model-id => "groq/[model-id]")
        "groq/allam-2-7b",
        "groq/deepseek-r1-distill-llama-70b",
        "groq/gemma2-9b-it",
        "groq/compound",
        "groq/compound-mini",
        "groq/llama-3.1-8b-instant",
        "groq/llama-3.3-70b-versatile",
        "groq/meta-llama/llama-4-maverick-17b-128e-instruct",
        "groq/meta-llama/llama-4-scout-17b-16e-instruct",
        "groq/meta-llama/llama-guard-4-12b",
        "groq/meta-llama/llama-prompt-guard-2-22m",
        "groq/meta-llama/llama-prompt-guard-2-86m",
        "groq/moonshotai/kimi-k2-instruct",
        "groq/moonshotai/kimi-k2-instruct-0905",
        "groq/openai/gpt-oss-120b",
        "groq/openai/gpt-oss-20b",
        "groq/playai-tts",
        "groq/playai-tts-arabic",
        "groq/qwen/qwen3-32b",
    ]


def format_messages(chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Format chat history for LiteLLM"""
    formatted_messages = []
    for message in chat_history:
        formatted_messages.append({
            "role": message["role"],
            "content": message["content"]
        })
    return formatted_messages

"""
LLM Client wrapper for multiple providers
"""
import os
from typing import List, Dict, Any, Optional
from litellm import completion
import logging

logger = logging.getLogger(__name__)


def get_available_models() -> List[str]:
    """
    Get list of available models based on configured API keys
    
    Returns:
        List of available model names
    """
    models = []
    
    # OpenAI models (if API key available)
    if os.getenv("OPENAI_API_KEY"):
        models.extend([
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ])
    
    # Groq models (if API key available)
    if os.getenv("GROQ_API_KEY"):
        models.extend([
            "groq/llama-3.3-70b-versatile",
            "groq/llama-3.1-70b-versatile",
            "groq/mixtral-8x7b-32768"
        ])
    
    # Default to gpt-4o-mini if no models available
    if not models:
        models.append("gpt-4o-mini")
    
    return models


class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initialize LLM client
        
        Args:
            model: Model name
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized LLMClient with model: {model}")
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """
        Send chat messages and get response
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional arguments for the LLM
        
        Returns:
            Response text
        """
        try:
            response = completion(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens)
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}", exc_info=True)
            raise
    
    def chat_with_image(
        self,
        prompt: str,
        image_url: str,
        **kwargs
    ) -> str:
        """
        Send prompt with image and get response
        
        Args:
            prompt: Text prompt
            image_url: URL or base64 data URL of image
            **kwargs: Additional arguments
        
        Returns:
            Response text
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        
        try:
            response = completion(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens)
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error in vision completion: {str(e)}", exc_info=True)
            raise
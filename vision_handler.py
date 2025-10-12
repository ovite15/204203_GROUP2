"""
Vision and image processing utilities for ChefBot
"""
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Try to import vision utilities
try:
    from utils.vision import detect_ingredients_from_image, format_ingredient_list
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    logger.warning("Vision utilities not available")

# Try to import LLM client
try:
    from utils.llm_client import LLMClient, get_available_models
    LLM_CLIENT_AVAILABLE = True
except ImportError:
    LLM_CLIENT_AVAILABLE = False
    logger.warning("LLM client not available")


def is_vision_available() -> bool:
    """Check if vision functionality is available"""
    has_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY"))
    return VISION_AVAILABLE and LLM_CLIENT_AVAILABLE and has_key


def detect_ingredients(
    image_file,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> List[str]:
    """
    Detect ingredients from uploaded image
    
    Args:
        image_file: Uploaded file object
        temperature: LLM temperature
        max_tokens: Maximum tokens
    
    Returns:
        List of ingredient names
    """
    if not VISION_AVAILABLE:
        return []
    
    try:
        detection = detect_ingredients_from_image(
            image_file,
            temperature=temperature,
            max_tokens=max_tokens,
            prefer_provider=None
        )
        
        ingredients = detection.get("ingredients", []) or []
        
        # Extract just the names
        names = [item.get("name", "") for item in ingredients if item.get("name")]
        return names
    
    except Exception as e:
        logger.error(f"Error detecting ingredients: {str(e)}", exc_info=True)
        return []
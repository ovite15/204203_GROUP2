"""
Vision utilities for ingredient detection from images
"""
import base64
import json
import logging
from io import BytesIO
from typing import List, Dict, Any, Optional
from PIL import Image

from utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


def image_to_base64_url(image_file) -> str:
    """
    Convert image file to base64 data URL
    
    Args:
        image_file: Uploaded file object or BytesIO
    
    Returns:
        Base64 data URL string
    """
    try:
        # Read image
        if hasattr(image_file, 'read'):
            image_bytes = image_file.read()
        else:
            image_bytes = image_file
        
        # Convert to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create data URL
        return f"data:image/jpeg;base64,{base64_image}"
    
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        raise


def detect_ingredients_from_image(
    image_file,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    prefer_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Detect ingredients from uploaded image using vision model
    
    Args:
        image_file: Uploaded image file
        temperature: LLM temperature
        max_tokens: Maximum tokens
        prefer_provider: Preferred provider (e.g., 'openai', 'anthropic')
    
    Returns:
        Dictionary with detected ingredients
    """
    try:
        # Convert image to base64
        image_url = image_to_base64_url(image_file)
        
        # Create prompt for ingredient detection
        prompt = """
        Please analyze this image and identify all visible food ingredients.
        
        Return your response as a JSON object with this structure:
        {
            "ingredients": [
                {"name": "ingredient_name", "confidence": 0.95},
                ...
            ]
        }
        
        Rules:
        - Only list actual ingredients you can see
        - Use common ingredient names in English
        - Confidence should be between 0.0 and 1.0
        - Be specific (e.g., "red bell pepper" not just "vegetable")
        """
        
        # Initialize client with vision-capable model
        model = "gpt-4o-mini"  # Default vision model
        client = LLMClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Get response
        response = client.chat_with_image(prompt, image_url)
        
        # Parse JSON response
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            
            # Remove markdown code blocks if present
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            result = json.loads(response_clean.strip())
            
            return result
        
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON response, extracting manually")
            # Fallback: try to extract ingredient names from text
            ingredients = _extract_ingredients_from_text(response)
            return {"ingredients": ingredients}
    
    except Exception as e:
        logger.error(f"Error detecting ingredients: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "ingredients": []
        }


def _extract_ingredients_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Fallback method to extract ingredients from plain text
    
    Args:
        text: Response text
    
    Returns:
        List of ingredient dictionaries
    """
    ingredients = []
    
    # Simple extraction: look for lines with ingredient-like words
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('*'):
            # Remove bullet points and numbers
            line = line.lstrip('•-*0123456789. ')
            if len(line) > 2 and len(line) < 50:  # Reasonable length
                ingredients.append({
                    "name": line,
                    "confidence": 0.7
                })
    
    return ingredients[:20]  # Limit to 20 ingredients


def format_ingredient_list(ingredients: List[Dict[str, Any]]) -> str:
    """
    Format ingredient list as comma-separated string
    
    Args:
        ingredients: List of ingredient dictionaries
    
    Returns:
        Formatted string
    """
    if not ingredients:
        return ""
    
    names = [item.get("name", "") for item in ingredients if item.get("name")]
    return ", ".join(names)
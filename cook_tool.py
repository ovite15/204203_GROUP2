"""
Cooking and recipe tools using Spoonacular and USDA APIs
"""
import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class CookTool:
    """Cooking and recipe suggestion tool with Thai language support"""

    def __init__(self, usda_api_key=None, spoonacular_api_key=None):
        self.usda_api_key = usda_api_key or os.getenv("USDA_API_KEY")
        self.spoonacular_api_key = spoonacular_api_key or os.getenv("SPOONACULAR_API")
        self.usda_base = "https://api.nal.usda.gov/fdc/v1/foods/search"
        self.spoon_base = "https://api.spoonacular.com/recipes"

    def _translate_thai_to_english(self, ingredients: List[str]) -> List[str]:
        """
        Translate Thai ingredient names to English using LLM
        
        Args:
            ingredients: List of ingredient names (may be Thai or English)
        
        Returns:
            List of English ingredient names
        """
        # Check if ingredients contain Thai characters
        has_thai = any(self._is_thai(ing) for ing in ingredients)
        
        if not has_thai:
            return ingredients  # Already in English
        
        try:
            from litellm import completion
            
            ingredients_str = ", ".join(ingredients)
            
            prompt = f"""Translate these Thai food ingredient names to English. 
Only return the English names, comma-separated, nothing else.

Thai ingredients: {ingredients_str}

English translation:"""

            response = completion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            english_text = response.choices[0].message.content.strip()
            
            # Clean up and split
            english_ingredients = [ing.strip() for ing in english_text.split(",")]
            
            logger.info(f"Translated {ingredients} → {english_ingredients}")
            return english_ingredients
        
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            # Fallback: return original
            return ingredients
    
    def _is_thai(self, text: str) -> bool:
        """Check if text contains Thai characters"""
        thai_range = range(0x0E00, 0x0E7F)
        return any(ord(char) in thai_range for char in text)

    def get_nutrition(self, ingredient: str) -> Dict[str, Any]:
        """
        Get nutrition info from USDA API
        
        Args:
            ingredient: Name of ingredient (Thai or English)
            
        Returns:
            Dictionary with nutrition data or error
        """
        if not self.usda_api_key:
            return {"error": "Missing USDA API key"}

        # Translate if Thai
        if self._is_thai(ingredient):
            english_ingredients = self._translate_thai_to_english([ingredient])
            ingredient = english_ingredients[0] if english_ingredients else ingredient

        params = {"query": ingredient, "api_key": self.usda_api_key}
        try:
            r = requests.get(self.usda_base, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            if "foods" not in data or not data["foods"]:
                return {"error": "No nutrition data found"}
            
            first = data["foods"][0]
            return {
                "description": first.get("description", ""),
                "nutrients": {
                    n["nutrientName"]: n["value"] 
                    for n in first.get("foodNutrients", [])
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def search_recipes(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Search for recipes using Spoonacular API
        
        Args:
            ingredients: List of ingredient names (Thai or English)
            
        Returns:
            List of recipe dictionaries or error dict
        """
        if not self.spoonacular_api_key:
            return {"error": "Missing Spoonacular API key"}

        # Translate Thai ingredients to English
        english_ingredients = self._translate_thai_to_english(ingredients)

        url = f"{self.spoon_base}/findByIngredients"
        params = {
            "ingredients": ",".join(english_ingredients), 
            "number": 5, 
            "apiKey": self.spoonacular_api_key,
            "ranking": 2,  # Maximize used ingredients
            "ignorePantry": False
        }
        
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            if not data:
                return []
            
            return data
        except Exception as e:
            return {"error": str(e)}

    def format_recipes(self, recipes: List[Dict[str, Any]]) -> str:
        """
        Format recipe list into Markdown text with detailed missing ingredients
        
        Args:
            recipes: List of recipe dictionaries
            
        Returns:
            Formatted markdown string
        """
        if not recipes or (isinstance(recipes, dict) and "error" in recipes):
            return "❌ ไม่พบสูตรอาหารจาก API"

        text = "## 🍳 สูตรอาหารที่แนะนำ\n\n"
        
        for idx, r in enumerate(recipes, 1):
            text += f"### {idx}. 🍽️ {r['title']}\n\n"
            
            # Show image
            if "image" in r:
                text += f"![{r['title']}]({r['image']})\n\n"
            
            # Get ingredients
            used = r.get('usedIngredients', [])
            missed = r.get('missedIngredients', [])
            unused = r.get('unusedIngredients', [])
            
            # Calculate match percentage
            total_needed = len(used) + len(missed)
            match_percent = (len(used) / total_needed * 100) if total_needed > 0 else 0
            
            # Show match score
            text += f"**📊 ความเหมาะสม: {match_percent:.0f}%** "
            text += f"(มี {len(used)}/{total_needed} ชนิด)\n\n"
            
            # Show used ingredients (what you have)
            if used:
                text += "**✅ วัตถุดิบที่คุณมีอยู่แล้ว:**\n"
                for ing in used:
                    name = ing.get('name', 'Unknown')
                    amount = ing.get('amount', 0)
                    unit = ing.get('unit', '')
                    text += f"  - {name}"
                    if amount and unit:
                        text += f" ({amount} {unit})"
                    text += "\n"
                text += "\n"
            
            # Show missed ingredients (what you need to buy) - HIGHLIGHTED
            if missed:
                text += f"**🛒 ต้องซื้อเพิ่ม ({len(missed)} ชนิด):**\n"
                for ing in missed:
                    name = ing.get('name', 'Unknown')
                    amount = ing.get('amount', 0)
                    unit = ing.get('unit', '')
                    aisle = ing.get('aisle', '')
                    
                    text += f"  - **{name}**"
                    if amount and unit:
                        text += f" - จำนวน: {amount} {unit}"
                    if aisle:
                        text += f" (หาได้ที่: {aisle})"
                    text += "\n"
                text += "\n"
            else:
                text += "**🎉 มีวัตถุดิบครบแล้ว!**\n\n"
            
            # Show unused ingredients (extras you have but won't use)
            if unused:
                text += "**ℹ️ วัตถุดิบที่เหลือ (ไม่ได้ใช้ในเมนูนี้):**\n"
                for ing in unused:
                    name = ing.get('name', 'Unknown')
                    text += f"  - {name}\n"
                text += "\n"
            
            # Add recipe ID and link
            if 'id' in r:
                recipe_id = r['id']
                text += f"🔗 [ดูสูตรเต็ม](https://spoonacular.com/recipes/-{recipe_id})\n"
            
            text += "\n" + "─" * 50 + "\n\n"
        
        return text
    
    def format_nutrition(self, nutrition: Dict[str, Any]) -> str:
        """
        Format nutrition data into readable text
        
        Args:
            nutrition: Nutrition dictionary from get_nutrition
            
        Returns:
            Formatted nutrition string
        """
        if "error" in nutrition:
            return f"❌ {nutrition['error']}"
        
        description = nutrition.get("description", "Unknown food")
        nutrients = nutrition.get("nutrients", {})
        
        if not nutrients:
            return f"📊 **{description}**\n\nไม่พบข้อมูลโภชนาการ"
        
        text = f"📊 **{description}**\n\n"
        text += "**ข้อมูลโภชนาการ (ต่อ 100g):**\n\n"
        
        # Priority nutrients to show first
        priority = ["Energy", "Protein", "Total lipid (fat)", "Carbohydrate, by difference"]
        
        # Show priority nutrients first
        for nutrient in priority:
            if nutrient in nutrients:
                value = nutrients[nutrient]
                text += f"- **{nutrient}**: {value}\n"
        
        # Show other nutrients (limit to top 10)
        other_nutrients = {k: v for k, v in nutrients.items() if k not in priority}
        for i, (nutrient, value) in enumerate(list(other_nutrients.items())[:10]):
            text += f"- **{nutrient}**: {value}\n"
        
        if len(other_nutrients) > 10:
            text += f"\n*...และอื่นๆ อีก {len(other_nutrients) - 10} รายการ*\n"
        
        return text
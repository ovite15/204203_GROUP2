"""
Cooking and recipe tools using Spoonacular and USDA APIs
"""
import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class CookTool:
    """Cooking and recipe suggestion tool using Spoonacular and USDA APIs"""

    def __init__(self, usda_api_key=None, spoonacular_api_key=None):
        self.usda_api_key = usda_api_key or os.getenv("USDA_API_KEY")
        self.spoonacular_api_key = spoonacular_api_key or os.getenv("SPOONACULAR_API")
        self.usda_base = "https://api.nal.usda.gov/fdc/v1/foods/search"
        self.spoon_base = "https://api.spoonacular.com/recipes"

    def get_nutrition(self, ingredient: str) -> Dict[str, Any]:
        """
        Get nutrition info from USDA API
        
        Args:
            ingredient: Name of ingredient to look up
            
        Returns:
            Dictionary with nutrition data or error
        """
        if not self.usda_api_key:
            return {"error": "Missing USDA API key"}

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
            ingredients: List of ingredient names
            
        Returns:
            List of recipe dictionaries or error dict
        """
        if not self.spoonacular_api_key:
            return {"error": "Missing Spoonacular API key"}

        url = f"{self.spoon_base}/findByIngredients"
        params = {
            "ingredients": ",".join(ingredients), 
            "number": 5, 
            "apiKey": self.spoonacular_api_key
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
        Format recipe list into Markdown text
        
        Args:
            recipes: List of recipe dictionaries
            
        Returns:
            Formatted markdown string
        """
        if not recipes or (isinstance(recipes, dict) and "error" in recipes):
            return "❌ ไม่พบสูตรอาหารจาก API"

        text = ""
        for r in recipes:
            text += f"🍽️ **{r['title']}**\n"
            
            if "image" in r:
                text += f"![{r['title']}]({r['image']})\n"
            
            used = [i['name'] for i in r.get('usedIngredients', [])]
            missed = [i['name'] for i in r.get('missedIngredients', [])]
            
            text += f"✅ มีแล้ว: {', '.join(used)}\n"
            text += f"🛒 ขาด: {', '.join(missed)}\n"
            
            # Add recipe ID for reference
            if 'id' in r:
                text += f"🔗 Recipe ID: {r['id']}\n"
            
            text += "\n"
        
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
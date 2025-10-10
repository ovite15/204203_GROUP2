import os
import requests
from dotenv import load_dotenv

load_dotenv()


class CookTool:
    """Cooking and recipe suggestion tool using Spoonacular and USDA APIs"""

    def __init__(self, usda_api_key=None, spoonacular_api_key=None):
        self.usda_api_key = usda_api_key or os.getenv("USDA_API_KEY")
        self.spoonacular_api_key = spoonacular_api_key or os.getenv("SPOONACULAR_API")
        self.usda_base = "https://api.nal.usda.gov/fdc/v1/foods/search"
        self.spoon_base = "https://api.spoonacular.com/recipes"

    # ──────────────────────────────────────────────
    def get_nutrition(self, ingredient: str):
        """Get nutrition info from USDA API"""
        if not self.usda_api_key:
            return {"error": "Missing USDA API key"}

        params = {"query": ingredient, "api_key": self.usda_api_key}
        try:
            r = requests.get(self.usda_base, params=params)
            r.raise_for_status()
            data = r.json()
            if "foods" not in data or not data["foods"]:
                return {"error": "No nutrition data found"}
            first = data["foods"][0]
            return {
                "description": first.get("description", ""),
                "nutrients": {
                    n["nutrientName"]: n["value"] for n in first.get("foodNutrients", [])
                }
            }
        except Exception as e:
            return {"error": str(e)}

    # ──────────────────────────────────────────────
    def search_recipes(self, ingredients):
        """Search for recipes using Spoonacular API"""
        if not self.spoonacular_api_key:
            return {"error": "Missing Spoonacular API key"}

        url = f"{self.spoon_base}/findByIngredients"
        params = {"ingredients": ",".join(ingredients), "number": 5, "apiKey": self.spoonacular_api_key}
        try:
            r = requests.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            if not data:
                return []
            return data
        except Exception as e:
            return {"error": str(e)}

    # ──────────────────────────────────────────────
    def format_recipes(self, recipes):
        """Format recipe list into Markdown text"""
        if not recipes or isinstance(recipes, dict) and "error" in recipes:
            return "❌ ไม่พบสูตรอาหารจาก API"

        text = ""
        for r in recipes:
            text += f"🍽️ **{r['title']}**\n"
            if "image" in r:
                text += f"![img]({r['image']})\n"
            used = [i['name'] for i in r.get('usedIngredients', [])]
            missed = [i['name'] for i in r.get('missedIngredients', [])]
            text += f"✅ มีแล้ว: {', '.join(used)}\n"
            text += f"🛒 ขาด: {', '.join(missed)}\n\n"
        return text

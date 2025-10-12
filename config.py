"""
Configuration and constants for ChefBot application
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# API KEYS
# ══════════════════════════════════════════════════════════════════════════════
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
USDA_API_KEY = os.getenv("USDA_API_KEY")
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API")

# ══════════════════════════════════════════════════════════════════════════════
# MODEL CONFIGURATIONS
# ══════════════════════════════════════════════════════════════════════════════
MODELS = {
    # OpenAI Models (Recommended for vision)
    "gpt-4o-mini": "GPT-4o Mini (Default)",
    "gpt-4o": "GPT-4o",
    "gpt-4-turbo": "GPT-4 Turbo",
    "gpt-3.5-turbo": "GPT-3.5 Turbo",
    
    # Groq Models (Fast inference)
    "groq/llama-3.3-70b-versatile": "Llama 3.3 70B (Groq)",
    "groq/llama-3.1-70b-versatile": "Llama 3.1 70B (Groq)",
    "groq/mixtral-8x7b-32768": "Mixtral 8x7B (Groq)",
}

DEFAULT_MODEL = "gpt-4o-mini"  # Changed to GPT-4o Mini
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS = 2048
MAX_TOOL_ITERATIONS = 5

# Vision settings
VISION_TEMPERATURE = 0.7
VISION_MAX_TOKENS = 1000

# ══════════════════════════════════════════════════════════════════════════════
# UI CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
BOT_AVATAR = "https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg"
USER_AVATAR = "https://cdn-icons-png.flaticon.com/512/1377/1377199.png"

PAGE_TITLE = "ChefBot - ผู้ช่วยพ่อครัว"
PAGE_ICON = "👨‍🍳"

# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════════════════
MAX_INPUT_LENGTH = 2000
MAX_CHAT_HISTORY = 20

# ══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "ค้นหาข้อมูลจากเว็บเกี่ยวกับสูตรอาหาร คำแนะนำในการทำอาหาร",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "คำค้นหา"},
                    "num_results": {"type": "integer", "description": "จำนวนผลลัพธ์", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "ค้นหาสูตรอาหารจากวัตถุดิบที่มี (Spoonacular API)",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "รายการวัตถุดิบ"
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
            "description": "ดูข้อมูลโภชนาการของวัตถุดิบ (USDA Database)",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredient": {"type": "string", "description": "ชื่อวัตถุดิบ"}
                },
                "required": ["ingredient"]
            }
        }
    }
]
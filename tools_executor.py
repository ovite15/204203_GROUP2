"""
Tool execution logic for ChefBot
"""
import streamlit as st
import logging
from cook_tool import CookTool
from search_tools import WebSearchTool

logger = logging.getLogger(__name__)


@st.cache_resource
def get_tools():
    """Initialize and cache tool instances"""
    return {
        "cook": CookTool(),
        "search": WebSearchTool()
    }


def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    Execute tool and return formatted results
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
    
    Returns:
        Formatted result string
    """
    try:
        tools = get_tools()
        cook_tool = tools["cook"]
        search_tool = tools["search"]
        
        if tool_name == "search_web":
            return _execute_search_web(search_tool, arguments)
        
        elif tool_name == "search_recipes":
            return _execute_search_recipes(cook_tool, arguments)
        
        elif tool_name == "get_nutrition":
            return _execute_get_nutrition(cook_tool, arguments)
        
        else:
            return f"❌ ไม่รู้จักเครื่องมือ '{tool_name}'"
    
    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}", exc_info=True)
        return "⚠️ เกิดข้อผิดพลาดในการใช้เครื่องมือ กรุณาลองใหม่"


def _execute_search_web(search_tool: WebSearchTool, arguments: dict) -> str:
    """Execute web search tool"""
    query = arguments.get("query", "")
    num_results = arguments.get("num_results", 5)
    
    if not query:
        return "❌ กรุณาระบุคำค้นหา"
    
    results = search_tool.search(query, num_results)
    formatted = search_tool.format_results(results)
    return formatted or "ไม่พบผลการค้นหา"


def _execute_search_recipes(cook_tool: CookTool, arguments: dict) -> str:
    """Execute recipe search tool"""
    ingredients = arguments.get("ingredients", [])
    
    if not ingredients:
        return "❌ กรุณาระบุวัตถุดิบ"
    
    recipes = cook_tool.search_recipes(ingredients)
    
    if isinstance(recipes, dict) and "error" in recipes:
        logger.error(f"Recipe search error: {recipes['error']}")
        return "⚠️ ไม่สามารถค้นหาสูตรอาหารได้ กรุณาลองใหม่อีกครั้ง"
    
    if not recipes:
        return f"❌ ไม่พบสูตรอาหารสำหรับ: {', '.join(ingredients)}"
    
    return cook_tool.format_recipes(recipes) or "❌ ไม่สามารถแสดงสูตรได้"


def _execute_get_nutrition(cook_tool: CookTool, arguments: dict) -> str:
    """Execute nutrition lookup tool"""
    ingredient = arguments.get("ingredient", "")
    
    if not ingredient:
        return "❌ กรุณาระบุวัตถุดิบ"
    
    nutrition = cook_tool.get_nutrition(ingredient)
    
    if "error" in nutrition:
        logger.error(f"Nutrition error: {nutrition['error']}")
        return f"⚠️ ไม่พบข้อมูลโภชนาการของ '{ingredient}'"
    
    return cook_tool.format_nutrition(nutrition)
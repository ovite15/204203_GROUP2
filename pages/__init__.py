"""
Pages module for ChefBot application
"""

from .home import render_home_page
from .chat import render_chat_page

__all__ = ['render_home_page', 'render_chat_page']
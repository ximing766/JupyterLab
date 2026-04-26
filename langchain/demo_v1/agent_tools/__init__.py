from .web import fetch_text_from_url
from .system import get_current_date, get_weather
from .text_analysis import analyze_text_substrings

def get_all_tools():
    """返回系统中所有可用的工具"""
    return [
        fetch_text_from_url,
        get_current_date,
        get_weather,
        analyze_text_substrings
    ]

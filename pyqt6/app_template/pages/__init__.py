# -*- coding: utf-8 -*-
"""
Pages module for Generic PyQt6 Application Template
Contains all page classes and page management functionality
"""

from .base_page import BasePage
from .placeholder_page import (
    PlaceholderPage,
    COM1PlaceholderPage,
    COM2PlaceholderPage,
    ChartPlaceholderPage
)
from .settings_page import SettingsPage
from .page_manager import PageManager, PageInfo

__all__ = [
    'BasePage',
    'PlaceholderPage',
    'COM1PlaceholderPage',
    'COM2PlaceholderPage',
    'ChartPlaceholderPage',
    'SettingsPage',
    'PageManager',
    'PageInfo'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Generic PyQt6 Template'
__description__ = 'Page management system for PyQt6 applications'
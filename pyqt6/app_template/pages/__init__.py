# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from .base_page import BasePage
from .settings_page import SettingsPage
from .example_page import ExamplePage
from .page_manager import PageManager, PageInfo

__all__ = [
    'BasePage',
    'SettingsPage',
    'ExamplePage',
    'PageManager',
    'PageInfo'
]

# Version info
__version__ = '1.0.0'
__author__ = 'Generic PyQt6 Template'
__description__ = 'Page management system for PyQt6 applications'
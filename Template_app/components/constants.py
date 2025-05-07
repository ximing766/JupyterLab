from PyQt6.QtGui import QFont
from PyQt6.QtCore import QSize

# Window settings
WINDOW_TITLE = "Remote COM Debug Tool"
INITIAL_GEOMETRY_X = 100
INITIAL_GEOMETRY_Y = 100
INITIAL_GEOMETRY_WIDTH = 800
INITIAL_GEOMETRY_HEIGHT = 600

# Navigation bar settings
NAV_MIN_WIDTH = 65
NAV_MAX_WIDTH = 300
NAV_ITEMS = ["Page 1", "Page 2"]
NAV_ITEM_FONT_FAMILY = "Segoe UI"
NAV_ITEM_FONT_SIZE = 10
# NAV_ITEM_FONT_WEIGHT = QFont.Weight.Bold # QFont will be created in main.py using these
NAV_ITEM_SIZE_HINT_WIDTH = 65
NAV_ITEM_SIZE_HINT_HEIGHT = 50

# Title bar settings
TITLE_BAR_HEIGHT = 30
TITLE_LABEL_TEXT = "Modern App"
# CONTROL_BTN_SIZE = QSize(20, 20) # QSize will be created in main.py
CONTROL_BTN_SIZE_WIDTH = 20
CONTROL_BTN_SIZE_HEIGHT = 20

# Page settings
# PAGE_TITLE_FONT = QFont("Segoe UI", 12, QFont.Weight.Bold) # QFont will be created in main.py
PAGE_TITLE_FONT_FAMILY = "Segoe UI"
PAGE_TITLE_FONT_SIZE = 12
PAGE_TITLE_HEIGHT = 30

# Splitter settings
SPLITTER_INITIAL_SIZES = [80, 500]

# File and Path settings
PIC_FOLDER_NAME = "pic"
ICON_FILE_NAME = "my.ico"
DEFAULT_IMAGE_FILES = ['bg.png', 'my.png', 'my.png', 'my.png']

# Theme Button
THEME_BUTTON_TEXT = " 🌓 "

# Control Button Texts
MINIMIZE_BTN_TEXT = "─"
MAXIMIZE_BTN_TEXT_NORMAL = "□"
MAXIMIZE_BTN_TEXT_MAXIMIZED = "❐"
CLOSE_BTN_TEXT = "❌"

# Background Images
BACKGROUND_IMAGE_FILES = ["person1.jpg", "city1.jpg", "carton1.jpg", "landscape1.jpg", "person2.jpg", "landscape2.jpg"]
CURRENT_BACKGROUND_IMAGE_INDEX = 0
# nav_bar.py
from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QSizePolicy, QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from components.image_utils import cycle_background_image_index
from components.constants import (
    NAV_MIN_WIDTH, NAV_MAX_WIDTH, NAV_ITEMS, NAV_ITEM_FONT_FAMILY, NAV_ITEM_FONT_SIZE,
    NAV_ITEM_SIZE_HINT_WIDTH, NAV_ITEM_SIZE_HINT_HEIGHT,
    THEME_BUTTON_TEXT
)

class NavBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.nav_list = None  # 暴露导航列表供外部连接信号
        self.init_ui()

    def _handle_theme_button_click(self):
        cycle_background_image_index()
        if self.parent():
            self.parent().update()

    def init_ui(self):
        self.setMinimumWidth(NAV_MIN_WIDTH)
        self.setMaximumWidth(NAV_MAX_WIDTH)
        nav_layout = QVBoxLayout(self)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.nav_list = QListWidget()
        self.nav_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.nav_list.setStyleSheet("background:rgba(36, 42, 56, 0);")

        for item_text in NAV_ITEMS:
            list_item = QListWidgetItem(item_text)
            list_item.setFont(QFont(NAV_ITEM_FONT_FAMILY, NAV_ITEM_FONT_SIZE, QFont.Weight.Bold))
            list_item.setSizeHint(QSize(NAV_ITEM_SIZE_HINT_WIDTH, NAV_ITEM_SIZE_HINT_HEIGHT))
            list_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.nav_list.addItem(list_item)

        self.theme_button = QPushButton(THEME_BUTTON_TEXT)
        self.theme_button.clicked.connect(self._handle_theme_button_click)
        self.theme_button.setStyleSheet("background:rgba(36, 42, 56, 0);")

        nav_layout.addWidget(self.nav_list)
        nav_layout.addWidget(self.theme_button)
        
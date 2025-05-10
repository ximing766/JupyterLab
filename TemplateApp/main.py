# 标准库导入
import sys
import os
import json
import re
import datetime
import time
import queue
from pathlib import Path
# 串口通信
import serial
# Qt核心模块
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QUrl, QTimer,
    QDateTime, QThread, QMargins, QPointF,
    pyqtSignal, QObject, Qt
)
# Qt界面模块
from PyQt6.QtWidgets import *
# Qt图形和绘制
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QTextCursor,
    QPixmap, QPainter, QIcon, QCursor,
    QClipboard, QIntValidator, QPen,
    QLinearGradient, QTextCharFormat,
    QTextOption, QTextDocument
)
# Qt图表模块
from PyQt6.QtCharts import (
    QChart, QChartView,
    QLineSeries, QValueAxis
)

# 项目模块导入
from common_ui.title_bar import TitleBar
from common_ui.nav_bar import NavBar
from components.theme_manager import ThemeManager
from components.constants import (
    INITIAL_GEOMETRY_X, INITIAL_GEOMETRY_Y, INITIAL_GEOMETRY_WIDTH, INITIAL_GEOMETRY_HEIGHT,
    TITLE_BAR_HEIGHT, TITLE_LABEL_TEXT, NAV_MIN_WIDTH, NAV_MAX_WIDTH, NAV_ITEMS, NAV_ITEM_FONT_FAMILY,
    NAV_ITEM_FONT_SIZE, NAV_ITEM_SIZE_HINT_WIDTH, NAV_ITEM_SIZE_HINT_HEIGHT, THEME_BUTTON_TEXT,
    PAGE_TITLE_FONT_FAMILY, PAGE_TITLE_FONT_SIZE, PAGE_TITLE_HEIGHT, CONTROL_BTN_SIZE_WIDTH, CONTROL_BTN_SIZE_HEIGHT,
    MINIMIZE_BTN_TEXT, MAXIMIZE_BTN_TEXT_NORMAL, MAXIMIZE_BTN_TEXT_MAXIMIZED, CLOSE_BTN_TEXT,
    SPLITTER_INITIAL_SIZES, PIC_FOLDER_NAME
)
from components.image_utils import get_app_icon, get_background_pixmap, load_pixmap, get_image_path
from page.client_page import ClientPage
from page.server_page import ServerPage


class MainWindow(QMainWindow):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_theme = ThemeManager.DARK_THEME
        self.drag_pos = QPoint()
        self.server_serial_thread = None
        self.client_serial_thread = None
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |         # 无边框
            Qt.WindowType.WindowMinimizeButtonHint |    # 允许最小化
            Qt.WindowType.WindowMaximizeButtonHint      # 允许最大化
        )
        self.setWindowIcon(get_app_icon())
        

        self.init_ui()
        
    def init_ui(self):
        self.setGeometry(INITIAL_GEOMETRY_X, INITIAL_GEOMETRY_Y, INITIAL_GEOMETRY_WIDTH, INITIAL_GEOMETRY_HEIGHT)

        title_bar = TitleBar(self)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav_container = NavBar(self)
        self.nav_bar  = nav_container           # Store nav_bar instance
        self.nav_list = self.nav_bar.nav_list   # 获取导航列表实例
        self.nav_list.currentRowChanged.connect(self.switch_page)

        self.stacked_widget = QStackedWidget()
        self.create_pages()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(nav_container)
        splitter.addWidget(self.stacked_widget)
        splitter.setStretchFactor(1, 1)         # 设置堆栈窗口可以拉伸
        splitter.setSizes(SPLITTER_INITIAL_SIZES)

        main_layout.addWidget(title_bar)
        main_layout.addWidget(splitter)  
        
        self.apply_theme()
        self.nav_list.setCurrentRow(0)

    def create_pages(self):
        server_page = ServerPage(self)
        client_page = ClientPage(self)
        
        self.stacked_widget.addWidget(server_page)
        self.stacked_widget.addWidget(client_page)

    def paintEvent(self, event):
        painter   = QPainter(self)
        bg_pixmap = get_background_pixmap()
        if bg_pixmap and not bg_pixmap.isNull():
            painter.drawPixmap(self.rect(), bg_pixmap)
        super().paintEvent(event)
    
    def apply_theme(self):
        stylesheet = ThemeManager.get_stylesheet(self.current_theme)
        self.setStyleSheet(stylesheet)
        
    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def mousePressEvent(self, event):
        idx   = self.stacked_widget.currentIndex()
        count = self.stacked_widget.count()
        if event.button() == Qt.MouseButton.XButton2:
            new_idx = (idx - 1 + count) % count     
            self.stacked_widget.setCurrentIndex(new_idx)
            self.nav_list.setCurrentRow(new_idx)
        elif event.button() == Qt.MouseButton.XButton1:
            new_idx = (idx + 1) % count
            self.stacked_widget.setCurrentIndex(new_idx)
            self.nav_list.setCurrentRow(new_idx)
        else:
            super().mousePressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # 使用Fusion样式更好支持透明效果
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

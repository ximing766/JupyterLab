# title_bar.py
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from components.constants import (
    TITLE_BAR_HEIGHT, TITLE_LABEL_TEXT, CONTROL_BTN_SIZE_WIDTH, CONTROL_BTN_SIZE_HEIGHT,
    MINIMIZE_BTN_TEXT, MAXIMIZE_BTN_TEXT_NORMAL, MAXIMIZE_BTN_TEXT_MAXIMIZED, CLOSE_BTN_TEXT
)

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent  # 保存父窗口引用
        self.init_ui()
        self.setup_styles()

    def init_ui(self):
        self.setObjectName("titleBar")
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        title_layout = QHBoxLayout(self)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(5)

        # 启用鼠标追踪
        self.setAttribute(Qt.WidgetAttribute.WA_MouseTracking)

        # 标题和图标
        self.title_label = QLabel(TITLE_LABEL_TEXT)
        self.title_label.setObjectName("titleLabel")

        # 窗口控制按钮
        btn_size = QSize(CONTROL_BTN_SIZE_WIDTH, CONTROL_BTN_SIZE_HEIGHT)

        minimize_btn = QPushButton(MINIMIZE_BTN_TEXT)
        minimize_btn.setFixedSize(btn_size)
        minimize_btn.clicked.connect(self.parent.showMinimized)

        self.maximize_btn = QPushButton(MAXIMIZE_BTN_TEXT_NORMAL)
        self.maximize_btn.setFixedSize(btn_size)
        self.maximize_btn.clicked.connect(self.toggle_maximize)

        close_btn = QPushButton(CLOSE_BTN_TEXT)
        close_btn.setFixedSize(btn_size)
        close_btn.clicked.connect(self.parent.close)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(close_btn)
    
    def setup_styles(self):
        # 设置标题栏样式
        self.setStyleSheet("""
            QPushButton {
                border: none;
                font-size: 10px;
                padding: 5px;
                background: transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#closeButton:hover {
                background-color: #ff4444;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.parent.move(self.parent.pos() + event.globalPosition().toPoint() - self.parent.drag_pos)
            self.parent.drag_pos = event.globalPosition().toPoint()

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.maximize_btn.setText(MAXIMIZE_BTN_TEXT_NORMAL)
        else:
            self.parent.showMaximized()
            self.maximize_btn.setText(MAXIMIZE_BTN_TEXT_MAXIMIZED)
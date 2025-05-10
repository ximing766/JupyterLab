from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QSplitter, QLabel, QTextEdit
from .base_page import BasePage


class ClientPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_layout()

    def init_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.main_container = QSplitter(Qt.Orientation.Horizontal)
        self.main_container.setStyleSheet("background: transparent;")

        self.label = QLabel("Client Page")
        self.label.setStyleSheet("background: transparent;")

        self.text_edit = QTextEdit()

        self.main_container.addWidget(self.label)
        self.main_container.addWidget(self.text_edit)

        layout.addWidget(self.main_container)
        
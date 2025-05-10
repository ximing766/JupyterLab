from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QSplitter, QLabel, QTextEdit
from .base_page import BasePage


class ServerPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_layout()

    def init_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self.main_container = QSplitter(Qt.Orientation.Horizontal)
        self.main_container.setStyleSheet(
            "QSplitter { background-color: transparent; }"
            "QSplitter::handle { background-color: rgba(128, 128, 128, 80); }"
        )

        self.label = QLabel("Server Page")
        self.main_container.addWidget(self.label)

        self.display_box = QTextEdit()
        self.display_box.setReadOnly(True) 
        self.display_box.setStyleSheet("background-color: rgba(255, 255, 255, 30); color: white;")  
        self.main_container.addWidget(self.display_box)

        layout.addWidget(self.main_container)
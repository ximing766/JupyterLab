from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt


class BasePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:rgba(36, 42, 56, 0);")
        self.init_layout()

    def init_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        self.main_container = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.main_container)
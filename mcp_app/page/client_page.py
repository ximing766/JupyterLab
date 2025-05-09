from .base_page import BasePage


class ClientPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:rgba(36, 42, 56, 0);")
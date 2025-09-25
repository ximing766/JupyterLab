# -*- coding: utf-8 -*-

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import InfoBar, InfoBarPosition

class BasePage(QWidget):
    page_activated = pyqtSignal(str)  # Emitted when page becomes active
    page_deactivated = pyqtSignal(str)  # Emitted when page becomes inactive
    data_changed = pyqtSignal(str, object)  # Emitted when page data changes
    
    def __init__(self, page_id: str, parent=None):
        super().__init__(parent)
        
        self.page_id = page_id
        self._is_active = False
        self._is_initialized = False
        
        # Set object name for identification
        self.setObjectName(page_id)
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface - minimal layout"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Initialize content
        self.init_content()
        
        self._is_initialized = True
    
    def apply_theme(self):
        """Apply current theme to the page - can be overridden in subclasses"""
        # Default implementation - subclasses can override this
        pass
    
    def init_content(self):
        """Initialize page content - override in subclasses"""
        pass
    
    def get_page_id(self) -> str:
        """Get page identifier"""
        return self.page_id
    
    def is_active(self) -> bool:
        """Check if page is currently active"""
        return self._is_active
    
    def is_initialized(self) -> bool:
        """Check if page is initialized"""
        return self._is_initialized
    
    def activate(self):
        """Activate the page - called when page becomes visible"""
        if not self._is_active:
            self._is_active = True
            self.on_activate()
            self.page_activated.emit(self.page_id)
    
    def deactivate(self):
        """Deactivate the page - called when page becomes hidden"""
        if self._is_active:
            self._is_active = False
            self.on_deactivate()
            self.page_deactivated.emit(self.page_id)
    
    def on_activate(self):
        """Called when page is activated - override in subclasses"""
        pass
    
    def on_deactivate(self):
        """Called when page is deactivated - override in subclasses"""
        pass
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.activate()
    
    def hideEvent(self, event):
        """Handle hide event"""
        super().hideEvent(event)
        self.deactivate()
    
    def __str__(self):
        return f"BasePage(id='{self.page_id}')"
    
    def __repr__(self):
        return self.__str__()
    
    # Information display methods
    def show_info(self, title: str = "信息", content: str = "", duration: int = 3000):
        """Show info message"""
        InfoBar.info(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
    
    def show_success(self, title: str = "成功", content: str = "", duration: int = 3000):
        """Show success message"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
    
    def show_warning(self, title: str = "警告", content: str = "", duration: int = 3000):
        """Show warning message"""
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
    
    def show_error(self, title: str = "错误", content: str = "", duration: int = 5000):
        """Show error message"""
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )
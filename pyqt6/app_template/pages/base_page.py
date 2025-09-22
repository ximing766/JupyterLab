# -*- coding: utf-8 -*-
"""
Base Page Class for Generic PyQt6 Application Template
Provides common functionality for all application pages
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QFont
from qfluentwidgets import ScrollArea, SubtitleLabel


class BasePage(QWidget):
    """Base class for all application pages"""
    
    # Signals
    page_activated = pyqtSignal(str)  # Emitted when page becomes active
    page_deactivated = pyqtSignal(str)  # Emitted when page becomes inactive
    data_changed = pyqtSignal(str, object)  # Emitted when page data changes
    
    def __init__(self, page_id: str, title: str = "", parent=None):
        super().__init__(parent)
        
        self.page_id = page_id
        self.title = title or page_id.title()
        self._is_active = False
        self._is_initialized = False
        
        # Set object name for identification
        self.setObjectName(page_id)
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface - override in subclasses"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Add title if provided
        if self.title:
            self.title_label = SubtitleLabel(self.title)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.title_label)
        
        # Create content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add scroll area for content
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidget(self.content_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Initialize content
        self.init_content()
        
        self._is_initialized = True
    
    def init_content(self):
        """Initialize page content - override in subclasses"""
        pass
    
    def get_page_id(self) -> str:
        """Get page identifier"""
        return self.page_id
    
    def get_title(self) -> str:
        """Get page title"""
        return self.title
    
    def set_title(self, title: str):
        """Set page title"""
        self.title = title
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)
    
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
    
    def refresh(self):
        """Refresh page content - override in subclasses"""
        pass
    
    def clear(self):
        """Clear page content - override in subclasses"""
        pass
    
    def get_data(self):
        """Get page data - override in subclasses"""
        return None
    
    def set_data(self, data):
        """Set page data - override in subclasses"""
        pass
    
    def validate(self) -> bool:
        """Validate page data - override in subclasses"""
        return True
    
    def save_state(self) -> dict:
        """Save page state - override in subclasses"""
        return {
            'page_id': self.page_id,
            'title': self.title,
            'is_active': self._is_active
        }
    
    def restore_state(self, state: dict):
        """Restore page state - override in subclasses"""
        if 'title' in state:
            self.set_title(state['title'])
    
    def add_content_widget(self, widget):
        """Add widget to content area"""
        if hasattr(self, 'content_layout'):
            self.content_layout.addWidget(widget)
    
    def remove_content_widget(self, widget):
        """Remove widget from content area"""
        if hasattr(self, 'content_layout'):
            self.content_layout.removeWidget(widget)
            widget.setParent(None)
    
    def clear_content(self):
        """Clear all content widgets"""
        if hasattr(self, 'content_layout'):
            while self.content_layout.count():
                child = self.content_layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
    
    def set_content_margins(self, left: int, top: int, right: int, bottom: int):
        """Set content area margins"""
        if hasattr(self, 'content_layout'):
            self.content_layout.setContentsMargins(left, top, right, bottom)
    
    def set_content_spacing(self, spacing: int):
        """Set content area spacing"""
        if hasattr(self, 'content_layout'):
            self.content_layout.setSpacing(spacing)
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.activate()
    
    def hideEvent(self, event):
        """Handle hide event"""
        super().hideEvent(event)
        self.deactivate()
    
    def __str__(self):
        return f"BasePage(id='{self.page_id}', title='{self.title}')"
    
    def __repr__(self):
        return self.__str__()
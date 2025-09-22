# -*- coding: utf-8 -*-
"""
Placeholder Page for Generic PyQt6 Application Template
Replaces COM1/COM2/CHART pages with blank placeholder pages
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, PushButton, 
    FluentIcon as FIF, InfoBar, InfoBarPosition
)
from .base_page import BasePage


class PlaceholderPage(BasePage):
    """Placeholder page for future functionality"""
    
    def __init__(self, page_id: str, title: str = "", description: str = "", icon=None, parent=None):
        self.description = description or f"This is a placeholder for {page_id} functionality."
        self.icon = icon or FIF.DOCUMENT
        super().__init__(page_id, title, parent)
    
    def init_content(self):
        """Initialize placeholder content"""
        # Create main card
        self.main_card = CardWidget()
        self.main_card.setFixedHeight(300)
        
        # Card layout
        card_layout = QVBoxLayout(self.main_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)
        
        # Add vertical spacer
        card_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Title
        title_label = TitleLabel(self.title or f"{self.page_id.upper()} Page")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)
        
        # Description
        desc_label = BodyLabel(self.description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)
        
        # Status label
        status_label = BodyLabel("🚧 Under Development")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        status_label.setFont(status_font)
        status_label.setStyleSheet("color: #FF6B35;")
        card_layout.addWidget(status_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Add spacer
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Coming soon button
        self.coming_soon_btn = PushButton("Coming Soon", self)
        self.coming_soon_btn.setIcon(FIF.INFO)
        self.coming_soon_btn.setEnabled(False)
        button_layout.addWidget(self.coming_soon_btn)
        
        # Learn more button
        self.learn_more_btn = PushButton("Learn More", self)
        self.learn_more_btn.setIcon(FIF.HELP)
        self.learn_more_btn.clicked.connect(self.show_info)
        button_layout.addWidget(self.learn_more_btn)
        
        # Add spacer
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        card_layout.addLayout(button_layout)
        
        # Add vertical spacer
        card_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Add card to content
        self.add_content_widget(self.main_card)
        
        # Add spacer to center the card
        self.content_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    
    def show_info(self):
        """Show information about this placeholder page"""
        info_text = f"This is a placeholder page for {self.page_id} functionality.\n\n"
        info_text += "You can replace this placeholder with your own implementation by:\n"
        info_text += "1. Creating a new page class that inherits from BasePage\n"
        info_text += "2. Implementing the init_content() method\n"
        info_text += "3. Registering the new page in the main window\n\n"
        info_text += "Check the documentation for more details."
        
        InfoBar.info(
            title="Placeholder Page",
            content=info_text,
            orient=Qt.Orientation.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
    
    def set_description(self, description: str):
        """Update page description"""
        self.description = description
        # Update description label if it exists
        if hasattr(self, 'main_card'):
            # Find and update description label
            for i in range(self.main_card.layout().count()):
                item = self.main_card.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), BodyLabel):
                    widget = item.widget()
                    if widget.text() != "🚧 Under Development":
                        widget.setText(description)
                        break
    
    def set_status(self, status: str, color: str = "#FF6B35"):
        """Update page status"""
        if hasattr(self, 'main_card'):
            # Find and update status label
            for i in range(self.main_card.layout().count()):
                item = self.main_card.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), BodyLabel):
                    widget = item.widget()
                    if "🚧" in widget.text() or "✅" in widget.text() or "⚠️" in widget.text():
                        widget.setText(status)
                        widget.setStyleSheet(f"color: {color};")
                        break
    
    def enable_functionality(self, enabled: bool = True):
        """Enable or disable coming soon button"""
        if hasattr(self, 'coming_soon_btn'):
            self.coming_soon_btn.setEnabled(enabled)
            if enabled:
                self.coming_soon_btn.setText("Available")
                self.coming_soon_btn.setIcon(FIF.ACCEPT)
                self.set_status("✅ Available", "#10B981")
            else:
                self.coming_soon_btn.setText("Coming Soon")
                self.coming_soon_btn.setIcon(FIF.INFO)
                self.set_status("🚧 Under Development", "#FF6B35")
    
    def on_activate(self):
        """Called when page is activated"""
        super().on_activate()
        # You can add custom activation logic here
        pass
    
    def on_deactivate(self):
        """Called when page is deactivated"""
        super().on_deactivate()
        # You can add custom deactivation logic here
        pass


class COM1PlaceholderPage(PlaceholderPage):
    """Placeholder for COM1 functionality"""
    
    def __init__(self, parent=None):
        super().__init__(
            page_id="com1",
            title="COM1 Interface",
            description="This page will contain COM1 serial communication functionality.\n"
                       "Features will include port selection, data transmission, and real-time monitoring.",
            icon=FIF.CONNECT,
            parent=parent
        )


class COM2PlaceholderPage(PlaceholderPage):
    """Placeholder for COM2 functionality"""
    
    def __init__(self, parent=None):
        super().__init__(
            page_id="com2",
            title="COM2 Interface",
            description="This page will contain COM2 serial communication functionality.\n"
                       "Features will include port selection, data transmission, and real-time monitoring.",
            icon=FIF.CONNECT,
            parent=parent
        )


class ChartPlaceholderPage(PlaceholderPage):
    """Placeholder for Chart functionality"""
    
    def __init__(self, parent=None):
        super().__init__(
            page_id="chart",
            title="Data Visualization",
            description="This page will contain data visualization and charting functionality.\n"
                       "Features will include real-time charts, data analysis, and export capabilities.",
            icon=FIF.CHART,
            parent=parent
        )
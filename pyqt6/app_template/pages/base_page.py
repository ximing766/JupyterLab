# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import InfoBar, InfoBarPosition, qconfig, Theme, setCustomStyleSheet, themeColor, TableWidget

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
        
        self.init_ui()
        
        qconfig.themeChanged.connect(self._on_theme_changed)
        self._apply_unified_theme()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.init_content()

        self._is_initialized = True
    
    def _apply_unified_theme(self):
        light_qss = """
        QWidget {
            background-color: transparent;
            color: rgb(32, 32, 32);
        }
        QDialog {
            background-color: rgb(255, 255, 255);
            color: rgb(32, 32, 32);
            border: 1px solid rgb(229, 231, 235);
            border-radius: 8px;
        }
        """
        dark_qss = """
        QWidget {
            background-color: transparent;
            color: rgb(255, 255, 255);
        }
        QDialog {
            background-color: rgb(45, 45, 45);
            color: rgb(255, 255, 255);
            border: 1px solid rgb(75, 85, 99);
            border-radius: 8px;
        }
        """
        self.setStyleSheet(light_qss if qconfig.theme == Theme.LIGHT else dark_qss)

    def _on_theme_changed(self, theme: Theme):
        self._apply_unified_theme()
    
    def apply_table_styling(self, table_widget):
        light_qss = f"""
        QTableWidget {{
            background: transparent;
            gridline-color: rgba(148, 163, 184, 0.4);
        }}
        
        QTableWidget::item {{
            background-color: rgba(218, 237, 243, 0.5);
            color: rgb(51, 65, 85);
        }}
        
        QTableWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(59, 130, 246, 0.2),
                stop:1 rgba(37, 99, 235, 0.15));
            color: rgb(204, 87, 240);
        }}
        
        QTableWidget::item:focus {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(16, 185, 129, 0.15),
                stop:1 rgba(5, 150, 105, 0.1));
        }}
        
        QHeaderView::section {{
            background: rgba(162, 225, 233, 0.95);
            color: rgb(28, 108, 145);
            font-size: 14px;
            font-weight: bold;
        }}
        """
        
        dark_qss = f"""
        QTableWidget {{
            background: transparent;
            gridline-color: rgba(71, 85, 105, 0.5);
        }}
        
        QTableWidget::item {{
            background-color: rgba(30, 41, 59, 0.55);
            color: rgb(226, 232, 240);
        }}
        
        QTableWidget::item:selected {{
            background: rgba(170, 100, 236, 0.3);
            color: rgb(12, 183, 226);
        }}
        
        QTableWidget::item:focus {{
            background: rgba(173, 88, 159, 0.5);
        }}
        
        QHeaderView::section {{
            background: rgba(35, 44, 71, 0.9);
            color: rgb(221, 230, 241);
            font-weight: bold;
            font-size: 14px;
        }}
        """
        
        # Apply the custom styling to the specific table widget
        setCustomStyleSheet(table_widget, light_qss, dark_qss)
    
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
    def show_info(self, title: str = "信息", content: str = "", duration: int = 1000):
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
    
    def show_success(self, title: str = "成功", content: str = "", duration: int = 1000):
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
    
    def show_warning(self, title: str = "警告", content: str = "", duration: int = 2000):
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
    
    def show_error(self, title: str = "错误", content: str = "", duration: int = 2000):
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
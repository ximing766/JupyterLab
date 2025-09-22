# -*- coding: utf-8 -*-
"""
Generic PyQt6 Application Template - Main Window
Extracted from UWB Dash application for reusability
"""

import sys
import os
import json
from pathlib import Path
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, pyqtSignal, QEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QIcon
from qfluentwidgets import (
    MSFluentWindow, FluentIcon as FIF, NavigationItemPosition,
    setTheme, Theme, MessageBox
)

from config.config_manager import ConfigManager
from config.theme_manager import ThemeManager
from pages.settings_page import SettingsPage
from pages.base_page import BasePage
from pages.placeholder_page import PlaceholderPage
from .splash_screen import SplashScreen


class MainWindow(MSFluentWindow):
    """Generic main window template with navigation and theme support"""
    
    theme_changed = pyqtSignal()
    
    def __init__(self, app_name="Generic App", app_icon=None, logo_path=None):
        super().__init__()
        
        # Basic window setup
        self.app_name = app_name
        self.logo_path = logo_path
        self.setWindowTitle(self.app_name)
        
        # Set window icon if provided
        if app_icon and Path(app_icon).exists():
            self.setWindowIcon(QIcon(str(app_icon)))
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.theme_manager = ThemeManager()
        
        # Window properties
        self.drag_pos = QPoint()
        self.background_cache = None
        self.last_window_size = QSize()
        self.splash_screen = None
        
        # Page registry for dynamic page management
        self.pages = {}
        self.nav_items = {}
        
        # Show splash screen first
        self.show_splash_screen()
        
        # Initialize UI after splash
        QTimer.singleShot(100, self.init_ui)
        
        # Apply initial theme
        self.apply_theme()
    
    def show_splash_screen(self):
        """Show splash screen during initialization"""
        self.splash_screen = SplashScreen(self.app_name, self.logo_path)
        self.splash_screen.finished.connect(self.on_splash_finished)
        self.splash_screen.show_splash()
        self.splash_screen.start_loading(duration=2000)
    
    def on_splash_finished(self):
        """Called when splash screen finishes"""
        if self.splash_screen:
            self.splash_screen.deleteLater()
            self.splash_screen = None
        self.show()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setMinimumSize(1000, 700)
        self.setGeometry(100, 100, 1200, 800)
        
        # Create default pages
        self.create_default_pages()
        
        # Setup navigation
        self.setup_navigation()
        
        # Apply theme
        setTheme(Theme.DARK)
    
    def create_default_pages(self):
        """Create default placeholder pages"""
        # Create placeholder pages to replace COM1/COM2/CHART
        self.page1 = PlaceholderPage("Page 1", "This is a placeholder for your first page")
        self.page2 = PlaceholderPage("Page 2", "This is a placeholder for your second page")
        self.page3 = PlaceholderPage("Page 3", "This is a placeholder for your third page")
        
        # Create settings page
        self.settings_page = SettingsPage(self.config_manager, self)
        
        # Register pages
        self.register_page("page1", self.page1)
        self.register_page("page2", self.page2)
        self.register_page("page3", self.page3)
        self.register_page("settings", self.settings_page)
    
    def setup_navigation(self):
        """Setup navigation bar with registered pages"""
        # Add main pages to navigation
        self.nav_items["page1"] = self.addSubInterface(
            self.page1, FIF.HOME, "Page 1"
        )
        self.nav_items["page2"] = self.addSubInterface(
            self.page2, FIF.DOCUMENT, "Page 2"
        )
        self.nav_items["page3"] = self.addSubInterface(
            self.page3, FIF.CHAT, "Page 3"
        )
        
        # Add settings page at bottom
        self.nav_items["settings"] = self.addSubInterface(
            self.settings_page, FIF.SETTING, "Settings", 
            position=NavigationItemPosition.BOTTOM
        )
    
    def register_page(self, page_id, page_widget):
        """Register a new page for dynamic management"""
        if not isinstance(page_widget, QWidget):
            raise ValueError("Page widget must be a QWidget instance")
        
        self.pages[page_id] = page_widget
        page_widget.setObjectName(page_id)
    
    def add_page(self, page_id, page_widget, icon, title, position=None):
        """Add a new page to the application"""
        # Register the page
        self.register_page(page_id, page_widget)
        
        # Add to navigation
        nav_position = position or NavigationItemPosition.TOP
        nav_item = self.addSubInterface(page_widget, icon, title, position=nav_position)
        self.nav_items[page_id] = nav_item
        
        return nav_item
    
    def remove_page(self, page_id):
        """Remove a page from the application"""
        if page_id in self.pages:
            # Remove from navigation if exists
            if page_id in self.nav_items:
                # Note: MSFluentWindow doesn't have a direct remove method
                # This would need to be implemented based on specific requirements
                del self.nav_items[page_id]
            
            # Remove from pages registry
            del self.pages[page_id]
    
    def get_page(self, page_id):
        """Get a registered page by ID"""
        return self.pages.get(page_id)
    
    def switch_to_page(self, page_id):
        """Switch to a specific page"""
        if page_id in self.pages:
            page = self.pages[page_id]
            self.stackedWidget.setCurrentWidget(page)
            
            # Update navigation selection
            if hasattr(self, 'navigationInterface'):
                self.navigationInterface.setCurrentItem(page_id)
    
    def mousePressEvent(self, event):
        """Handle mouse events for navigation"""
        # Handle mouse side buttons for page navigation
        if hasattr(self, 'stackedWidget') and self.stackedWidget:
            current_idx = self.stackedWidget.currentIndex()
            total_pages = self.stackedWidget.count()
            
            if event.button() == Qt.MouseButton.XButton1:  # Forward button
                new_idx = (current_idx + 1) % total_pages
                self.stackedWidget.setCurrentIndex(new_idx)
                self._update_navigation_selection(new_idx)
                event.accept()
                return
            elif event.button() == Qt.MouseButton.XButton2:  # Back button
                new_idx = (current_idx - 1 + total_pages) % total_pages
                self.stackedWidget.setCurrentIndex(new_idx)
                self._update_navigation_selection(new_idx)
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def _update_navigation_selection(self, index):
        """Update navigation selection based on page index"""
        if hasattr(self, 'navigationInterface') and index < self.stackedWidget.count():
            widget = self.stackedWidget.widget(index)
            if widget and hasattr(widget, 'objectName'):
                self.navigationInterface.setCurrentItem(widget.objectName())
    
    def paintEvent(self, event):
        """Handle background painting"""
        background_config = self.config_manager.get_background_config()
        
        if not background_config.get('enabled', False):
            super().paintEvent(event)
            return
        
        # Cache background for performance
        if not self.background_cache or self.size() != self.last_window_size:
            self._update_background_cache(background_config)
        
        if self.background_cache:
            painter = QPainter(self)
            painter.setOpacity(background_config.get('opacity', 1.0))
            
            # Center the background
            x = (self.width() - self.background_cache.width()) // 2
            y = (self.height() - self.background_cache.height()) // 2
            painter.drawPixmap(x, y, self.background_cache)
        else:
            super().paintEvent(event)
    
    def _update_background_cache(self, background_config):
        """Update the background cache"""
        current_image = background_config.get('current_image')
        if not current_image:
            return
        
        background_path = Path(current_image)
        if not background_path.is_absolute():
            # Assume relative to application directory
            app_dir = Path(__file__).parent.parent.parent
            background_path = app_dir / current_image
        
        if background_path.exists():
            size = self.size()
            background = QPixmap(str(background_path))
            self.background_cache = background.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.last_window_size = size
    
    def apply_theme(self):
        """Apply the current theme"""
        theme_config = self.theme_manager.get_current_theme()
        
        if theme_config.get('is_dark', True):
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
        
        # Emit theme changed signal
        self.theme_changed.emit()
    
    def show_help_dialog(self):
        """Show help dialog"""
        help_content = f"""
        <h2>🚀 {self.app_name} 使用指南</h2>
        
        <h3>📊 功能特性</h3>
        <p>• <b>模块化设计</b>：易于扩展和维护</p>
        <p>• <b>主题切换</b>：支持深色/浅色模式</p>
        <p>• <b>背景自定义</b>：个性化界面体验</p>
        
        <h3>🎯 页面管理</h3>
        <p>• 动态页面添加和移除</p>
        <p>• 灵活的导航系统</p>
        
        <h3>⚙️ 设置选项</h3>
        <p>• 主题管理</p>
        <p>• 背景配置</p>
        <p>• 应用设置</p>
        """
        
        w = MessageBox(
            title='帮助支持',
            content=help_content,
            parent=self
        )
        w.yesButton.setText('我知道了')
        w.cancelButton.hide()
        w.exec()
    
    def show_about_dialog(self):
        """Show about dialog"""
        about_content = f"""
        <h3>📋 应用信息</h3>
        <p><b>应用名称：</b>{self.app_name}</p>
        <p><b>版本：</b>v1.0.0</p>
        <p><b>构建日期：</b>2025年1月</p>
        <p><b>Python版本：</b>3.8+</p>
        
        <h3>🛠️ 技术栈</h3>
        <p>• <b>PyQt6</b>：现代化GUI框架</p>
        <p>• <b>QFluentWidgets</b>：Fluent Design组件</p>
        """
        
        w = MessageBox(
            title=f'关于 {self.app_name}',
            content=about_content,
            parent=self
        )
        w.yesButton.setText('确定')
        w.cancelButton.hide()
        w.exec()
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Save current configuration
        self.config_manager.save_config()
        super().closeEvent(event)
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
    FluentWindow, FluentIcon as FIF, NavigationItemPosition,
    setTheme, Theme, MessageBox
)

from config.config_manager import ConfigManager
from config.theme_manager import ThemeManager
from pages.settings_page import SettingsPage
from pages.base_page import BasePage
from pages.page_manager import PageManager
from .splash_screen import SplashScreen


class MainWindow(FluentWindow):
    """Generic main window template with navigation and theme support"""
    theme_changed = pyqtSignal()
    
    def __init__(self, app_name="Generic App", logo_path=None, user_manager=None):
        super().__init__()
        
        # Basic window setup
        self.app_name = app_name
        self.logo_path = logo_path
        self.setWindowTitle(self.app_name)

        if logo_path and Path(logo_path).exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        
        # Initialize managers
        self.user_manager = user_manager
        self.config_manager = ConfigManager()
        self.theme_manager = ThemeManager()
        self.page_manager = PageManager(parent=self)
        
        # Set user manager for page manager if available
        if hasattr(self, 'user_manager') and self.user_manager:
            self.page_manager.set_user_manager(self.user_manager)
        
        # Load user-specific config if user management is enabled
        if self.user_manager and self.user_manager.is_authenticated():
            current_user = self.user_manager.get_current_user()
            if current_user:
                self.config_manager.set_current_user(current_user['username'])
                user_config = self.user_manager.load_user_config(current_user['username'])
                if user_config:
                    self.config_manager.load_config_from_dict(user_config)
        
        # Window properties
        self.drag_pos = QPoint()
        self.background_cache = None
        self.last_window_size = QSize()
        self.splash_screen = None
        
        # Page registry for dynamic page management
        self.pages = {}
        self.nav_items = {}
        
        self.show_splash_screen()
        
        QTimer.singleShot(100, self.init_ui)   # XXX: 待定main中Page注册完毕
        
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
        
        self.setup_navigation() # 获取可见页面
        
        # Pass user_manager to settings page if available
        if hasattr(self, 'user_manager') and self.user_manager:
            settings_page = self.page_manager.get_page_instance('settings')
            if settings_page:
                settings_page.user_manager = self.user_manager
            
            # Connect user manager signals to refresh page permissions
            self.user_manager.user_logged_in.connect(self.on_user_login_changed)
            self.user_manager.user_logged_out.connect(self.on_user_login_changed)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setWindowOpacity(1.0)
    
    def setup_navigation(self):  # BM: 添加所有注册页面到nav bar
        """Setup navigation bar with registered pages"""
        visible_pages = self.page_manager.get_visible_pages()  # XXX:页面级权限管理
        print(f"setup_navigation, visible pages: {visible_pages.keys()}")
        
        # Sort pages by order
        sorted_pages = sorted(visible_pages.items(), key=lambda x: x[1].order)
        
        # Add pages to navigation
        for page_id, page_info in sorted_pages:
            if page_info.enabled and page_info.visible:
                if page_id == "settings":
                    # Settings page needs special parameters
                    page_instance = page_info.create_instance(self.config_manager, self)
                    
                    # Connect settings page signals
                    page_instance.background_changed.connect(self.on_background_changed)
                    page_instance.theme_changed.connect(self.on_theme_changed)
                else:
                    # Other pages use default parameters
                    page_instance = page_info.create_instance(self)
                
                # Determine navigation position
                if page_info.order >= 90:  # Settings and other bottom items
                    position = NavigationItemPosition.BOTTOM
                else:
                    position = NavigationItemPosition.TOP
                
                # Add to navigation
                nav_item = self.addSubInterface(
                    page_instance, 
                    page_info.icon or FIF.DOCUMENT, 
                    page_info.title, 
                    position=position
                )
                
                self.pages[page_id] = page_instance
                self.nav_items[page_id] = nav_item
    
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
            
            # Fill the entire window with the background
            painter.drawPixmap(0, 0, self.width(), self.height(), self.background_cache)
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
            app_dir = Path(__file__).parent.parent
            background_path = app_dir / current_image
        
        if background_path.exists():
            size = self.size()
            background = QPixmap(str(background_path))
            if not background.isNull():
                self.background_cache = background.scaled(
                    size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.last_window_size = size
            else:
                print(f"Failed to load image: {background_path}")
        else:
            print(f"Background image not found: {background_path}")

    # BUG: 登陆完成时mainwindow还没有创建,这里不会收到, 预留给未来切换用户
    def on_user_login_changed(self): 
        print("receive login change signal")
        """Handle user login/logout to refresh page permissions"""
        # Switch to user-specific configuration if logged in
        if self.user_manager and self.user_manager.is_logged_in():
            current_user = self.user_manager.get_current_user()
            if current_user:
                # Set current user in config manager
                self.config_manager.set_current_user(current_user['username'])
                # Load user-specific configuration
                user_config = self.user_manager.load_user_config(current_user['username'])
                if user_config:
                    self.config_manager.load_config_from_dict(user_config)
        else:
            # Clear current user and reload default configuration when logged out
            self.config_manager.set_current_user(None)
            self.config_manager.reload_config()
        
        if hasattr(self, 'page_manager'):
            # Refresh page permissions
            self.page_manager.refresh_page_permissions()
            
            # Rebuild navigation to show/hide pages based on new permissions
            self.setup_navigation()
            
        # Apply theme and background from the loaded configuration
        self.apply_theme()
        self.update()  # Refresh background
    
    def on_background_changed(self, background_path):
        """Handle background change from settings page"""
        self.background_cache = None
        self.update()
    
    def on_theme_changed(self, theme):
        """Handle theme change from settings page"""
        self.apply_theme()
    
    def apply_theme(self):
        """Apply theme to the application"""
        try:
            # Get current theme name
            current_theme = self.config_manager.get_theme()
            
            # Get current theme configuration
            current_theme_config = self.config_manager.get_current_theme()

            # Apply theme to qfluentwidgets based on theme name
            if current_theme.lower() == "dark":
                setTheme(Theme.DARK)
            else:
                setTheme(Theme.LIGHT)
            
            # Apply theme to all pages that support it
            for page_id, page_info in self.page_manager._pages.items():
                if page_info.instance and hasattr(page_info.instance, 'apply_theme'):
                    page_info.instance.apply_theme()
            
        except Exception as e:
            print(f"Error applying theme: {e}")
            import traceback
            traceback.print_exc()
    
    def show_help_dialog(self):
        """Show help dialog"""
        help_content = f"""
        <h2>🚀 {self.app_name} 使用指南</h2>
        <h3>📊 功能特性</h3>
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
        self.config_manager.save_config()
        super().closeEvent(event)
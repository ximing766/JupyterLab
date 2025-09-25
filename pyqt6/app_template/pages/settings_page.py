# -*- coding: utf-8 -*-
"""
Settings Page for Generic PyQt6 Application Template
Contains theme management, background switching, and other general settings
"""

import os
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QWidget
from PyQt6.QtGui import QDesktopServices
from qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, PushSettingCard,
    HyperlinkCard, PrimaryPushSettingCard,
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox,
    ExpandLayout, ScrollArea, qconfig, Theme, setTheme
)
from .base_page import BasePage


class SettingsPage(BasePage):
    """Settings page with theme management and other general settings"""
    
    # Signals
    theme_changed = pyqtSignal(str)  # Emitted when theme changes
    background_changed = pyqtSignal(str)  # Emitted when background changes
    setting_changed = pyqtSignal(str, object)  # Emitted when any setting changes
    
    def __init__(self, config_manager=None, parent=None):
        self.config_manager = config_manager
        super().__init__("settings", parent)
    
    def apply_theme(self):
        """Apply current theme to the page"""
        if self.config_manager:
            current_theme = self.config_manager.get_theme()
            
            # Update theme card text based on current theme
            if hasattr(self, 'theme_card'):
                theme_display = "Dark" if current_theme.lower() == "dark" else "Light"
                self.theme_card.setContent(theme_display)
                
            # Apply theme-specific styling to the page
            if current_theme.lower() == "dark":
                # Dark theme styling
                self.setStyleSheet("""
                    QWidget {
                        background-color: transparent;
                        color: white;
                    }
                """)
            else:
                # Light theme styling
                self.setStyleSheet("""
                    QWidget {
                        background-color: transparent;
                        color: black;
                    }
                """)
    
    def init_content(self):
        """Initialize page content"""
        scroll_widget = ScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container widget for scroll content
        scroll_content = QWidget()
        
        # Create vertical layout for settings groups (use QVBoxLayout instead of ExpandLayout)
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(20)  # Add spacing between groups
        content_layout.setContentsMargins(20, 20, 20, 20)  # Add margins
        
        # Create settings groups
        appearance_group = self.create_appearance_group()
        application_group = self.create_application_group()
        about_group = self.create_about_group()
        
        # Add groups to layout
        content_layout.addWidget(appearance_group)
        content_layout.addWidget(application_group)
        content_layout.addWidget(about_group)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        # Set the container as scroll widget content
        scroll_content.setLayout(content_layout)
        scroll_widget.setWidget(scroll_content)
        
        # Add scroll widget to main layout
        self.layout.addWidget(scroll_widget)
        
        # Apply initial theme
        self.apply_theme()
    
    def create_appearance_group(self):
        """Create appearance settings group"""
        group = SettingCardGroup("外观", self)
        
        # Get current theme from config
        current_theme = "Light"
        if self.config_manager:
            theme_config = self.config_manager.get_theme_config()
            current_theme = "Dark" if theme_config.get('is_dark', False) else "Light"
        
        # Theme setting card - use PushSettingCard instead of ComboBoxSettingCard
        self.theme_card = PushSettingCard(
            current_theme,
            FIF.BRUSH,
            "主题",
            "选择应用程序主题",
            parent=group
        )
        self.theme_card.clicked.connect(self.on_theme_clicked)
        
        # Background image card - directly cycle through background images
        self.background_card = PushSettingCard(
            "切换背景",
            FIF.PHOTO,
            "背景图片",
            "点击切换背景图片",
            parent=group
        )
        self.background_card.clicked.connect(self.cycle_background_image)
        
        group.addSettingCard(self.theme_card)
        group.addSettingCard(self.background_card)
        
        return group
    
    def create_application_group(self):
        group = SettingCardGroup("应用程序", self)
        
        # Language setting card
        self.language_card = PushSettingCard(
            "中文",
            FIF.LANGUAGE,
            "语言",
            "更改应用程序语言",
            parent=group
        )
        self.language_card.clicked.connect(self.on_language_clicked)
        
        # Reset settings card
        self.reset_card = PrimaryPushSettingCard(
            "重置",
            FIF.UPDATE,
            "重置设置",
            "将所有设置恢复为默认值",
            parent=group
        )
        self.reset_card.clicked.connect(self.reset_settings)
        
        group.addSettingCard(self.language_card)
        group.addSettingCard(self.reset_card)
        
        return group
    
    def create_about_group(self):
        """Create about settings group"""
        group = SettingCardGroup("关于", self)
        
        # Help card - fix HyperlinkCard parameter order
        self.help_card = HyperlinkCard(
            "https://github.com/zhiyiYo/PyQt-Fluent-Widgets",
            "打开帮助页面",
            FIF.HELP,
            "帮助",
            "发现新功能并学习有用的技巧",
            parent=group
        )
        
        # Feedback card
        self.feedback_card = PushSettingCard(
            "提供反馈",
            FIF.FEEDBACK,
            "反馈",
            "提供反馈以帮助我们改进应用程序",
            parent=group
        )
        self.feedback_card.clicked.connect(self.show_feedback_dialog)
        
        # Check update card
        self.update_card = PushSettingCard(
            "检查更新",
            FIF.UPDATE,
            "软件更新",
            "检查并安装应用程序更新",
            parent=group
        )
        self.update_card.clicked.connect(self.check_update)
        
        # About card
        self.about_card = PushSettingCard(
            "查看许可证",
            FIF.INFO,
            "关于",
            "版权所有 © 2024. 保留所有权利。",
            parent=group
        )
        
        group.addSettingCard(self.help_card)
        group.addSettingCard(self.feedback_card)
        group.addSettingCard(self.update_card)
        group.addSettingCard(self.about_card)

        return group
    
    def on_theme_clicked(self):
        """Handle theme button click - cycle through themes"""
        current_text = self.theme_card.button.text()
        themes = ["Light", "Dark"]
        
        try:
            current_index = themes.index(current_text)
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]
        except ValueError:
            next_theme = "Light"  # Default fallback
        
        # Update button text
        self.theme_card.button.setText(next_theme)
        
        # Save to config first
        if self.config_manager:
            self.config_manager.set_theme(next_theme.lower())
        
        # Emit signal to main window to handle theme application
        self.theme_changed.emit(next_theme.lower())
        self.setting_changed.emit("theme", next_theme.lower())
        
        # Show info
        self.show_success("Theme Changed", f"Theme changed to {next_theme}", 2000)
    
    def on_theme_changed(self, theme):
        """Handle theme change"""
        print(f"Theme changed to: {theme}")
        if self.config_manager:
            self.config_manager.set_theme(theme)
    
    def cycle_background_image(self):
        """Cycle through background images in assets/PIC folder"""
        if not self.config_manager:
            self.show_warning("配置错误", "配置管理器未初始化")
            return
        
        # Get available images from config manager (which reads from assets/PIC)
        available_images = self.config_manager.get_available_backgrounds()
        
        if not available_images:
            self.show_warning("无背景图片", "assets/PIC 文件夹中没有找到图片文件")
            return
        
        # Get current background configuration
        current_image = self.config_manager.get_current_background()
        current_index = self.config_manager.get_background_config().get("current_index", 0)
        
        # Calculate next index
        next_index = (current_index + 1) % len(available_images)
        next_image = available_images[next_index]
        
        # Update button text to show current image name
        image_name = os.path.basename(next_image)
        self.background_card.setContent(f"当前: {image_name}")
        
        # Save to config
        self.config_manager.set_current_background(next_image)
        self.config_manager.set_background_enabled(True)
        
        # Emit signal
        self.background_changed.emit(next_image)
        self.setting_changed.emit("background_image", next_image)
        
        # Show info
        self.show_success("背景已切换", f"背景图片已切换到 {image_name}", 2000)
    
    def select_background_image(self):
        """Select background image"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image files (*.png *.jpg *.jpeg *.bmp *.gif)")
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                image_path = file_paths[0]
                
                # Save to config
                if self.config_manager:
                    self.config_manager.add_background_image(image_path)
                    self.config_manager.set_current_background(image_path)
                
                # Emit signal
                self.background_changed.emit(image_path)
                self.setting_changed.emit("background_image", image_path)
                
                # Show success message
                self.show_success("Background Updated", f"Background image set to {os.path.basename(image_path)}", 3000)
    
    def on_autosave_changed(self, enabled: bool):
        """Handle auto-save setting change"""
        if self.config_manager:
            self.config_manager.set_autosave(enabled)
        
        self.setting_changed.emit("autosave", enabled)
        
        status = "enabled" if enabled else "disabled"
        self.show_info("Auto-save Setting", f"Auto-save {status}", 2000)
    
    def on_language_clicked(self):
        """Handle language button click - cycle through languages"""
        current_text = self.language_card.button.text()
        languages = ["English", "中文", "Auto"]
        
        try:
            current_index = languages.index(current_text)
            next_index = (current_index + 1) % len(languages)
            next_language = languages[next_index]
        except ValueError:
            next_language = "English"  # Default fallback
        
        # Update button text
        self.language_card.button.setText(next_language)
        
        # Save to config
        if self.config_manager:
            self.config_manager.set_language(next_language.lower())
        
        self.setting_changed.emit("language", next_language.lower())
        
        self.show_info("Language Setting", f"Language set to {next_language}. Restart required for full effect.", 3000)
    
    def on_language_changed(self, language: str):
        """Handle language change (legacy method for compatibility)"""
        self.on_language_clicked()
    
    def reset_settings(self):
        """Reset all settings to default"""
        # Show confirmation dialog
        msg_box = MessageBox(
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?\n\nThis action cannot be undone.",
            self
        )
        
        if msg_box.exec():
            # Reset config
            if self.config_manager:
                self.config_manager.reset_to_defaults()
            
            # Reset UI
            self.load_settings()
            
            # Emit signal
            self.setting_changed.emit("reset", True)
            
            self.show_success("Settings Reset", "All settings have been reset to default values", 3000)
    
    def show_feedback_dialog(self):
        """Show feedback dialog"""
        self.show_info("Feedback", "Thank you for your interest in providing feedback!\n\nPlease visit our GitHub repository or contact us directly.", 4000)
    
    def check_update(self):
        """Check for updates"""
        self.show_info("Update Check", "You are using the latest version of the application template.\n\nVersion: 1.0.0", 3000)
    
    def load_settings(self):
        """Load settings from config"""
        if not self.config_manager:
            return
        
        # Load theme - update button text based on current theme
        theme = self.config_manager.get_theme()
        theme_map = {
            "light": "Light",
            "dark": "Dark", 
            "auto": "Auto"
        }
        if theme in theme_map:
            self.theme_card.button.setText(theme_map[theme])
        
        # Load language - update button text based on current language
        language = self.config_manager.get_language()
        lang_map = {
            "english": "English",
            "中文": "中文",
            "auto": "Auto"
        }
        if language in lang_map:
            self.language_card.button.setText(lang_map[language])
    
    def save_settings(self):
        """Save current settings"""
        if self.config_manager:
            self.config_manager.save_config()
    
    def on_activate(self):
        """Called when settings page is activated"""
        super().on_activate()
        self.load_settings()
    
    def on_deactivate(self):
        """Called when settings page is deactivated"""
        super().on_deactivate()
        # Auto-save removed as per requirements
    
    def __str__(self):
        return f"SettingsPage(id='{self.page_id}')"
# -*- coding: utf-8 -*-
"""
Settings Page for Generic PyQt6 Application Template
Contains theme management, background switching, and other general settings
"""

import os
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt6.QtGui import QDesktopServices
from qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, ComboBoxSettingCard, 
    PushSettingCard, HyperlinkCard, PrimaryPushSettingCard,
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
        super().__init__("settings", "Settings", parent)
    
    def init_content(self):
        """Initialize settings content"""
        # Create scroll area for settings
        self.scroll_widget = ScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        
        # Create expand layout for setting cards
        self.expand_layout = ExpandLayout()
        
        # Create setting groups
        self.create_appearance_group()
        self.create_application_group()
        self.create_about_group()
        
        # Set layout
        self.scroll_widget.setLayout(self.expand_layout)
        self.add_content_widget(self.scroll_widget)
    
    def create_appearance_group(self):
        """Create appearance settings group"""
        self.appearance_group = SettingCardGroup("Appearance", self)
        
        # Theme setting card - use PushSettingCard instead of ComboBoxSettingCard
        self.theme_card = PushSettingCard(
            "Light",
            FIF.BRUSH,
            "Application theme",
            "Change the appearance of your application"
        )
        self.theme_card.clicked.connect(self.on_theme_clicked)
        
        # Background setting card
        self.background_card = SwitchSettingCard(
            FIF.PHOTO,
            "Background image",
            "Enable custom background image",
            parent=self.appearance_group
        )
        self.background_card.switchButton.checkedChanged.connect(self.on_background_toggle)
        
        # Background selection card
        self.background_select_card = PushSettingCard(
            "Select background",
            FIF.FOLDER,
            "Background image",
            "Choose a custom background image",
            parent=self.appearance_group
        )
        self.background_select_card.clicked.connect(self.select_background_image)
        
        # Add cards to group
        self.appearance_group.addSettingCard(self.theme_card)
        self.appearance_group.addSettingCard(self.background_card)
        self.appearance_group.addSettingCard(self.background_select_card)
        
        # Add group to layout
        self.expand_layout.addWidget(self.appearance_group)
    
    def create_application_group(self):
        """Create application settings group"""
        self.application_group = SettingCardGroup("Application", self)
        
        # Auto-save setting card
        self.autosave_card = SwitchSettingCard(
            FIF.SAVE,
            "Auto-save settings",
            "Automatically save settings when changed",
            parent=self.application_group
        )
        self.autosave_card.switchButton.checkedChanged.connect(self.on_autosave_changed)
        
        # Language setting card - use PushSettingCard instead of ComboBoxSettingCard
        self.language_card = PushSettingCard(
            "English",
            FIF.LANGUAGE,
            "Language",
            "Choose your preferred language"
        )
        self.language_card.clicked.connect(self.on_language_clicked)
        
        # Reset settings card
        self.reset_card = PushSettingCard(
            "Reset",
            FIF.DELETE,
            "Reset settings",
            "Reset all settings to default values",
            parent=self.application_group
        )
        self.reset_card.clicked.connect(self.reset_settings)
        
        # Add cards to group
        self.application_group.addSettingCard(self.autosave_card)
        self.application_group.addSettingCard(self.language_card)
        self.application_group.addSettingCard(self.reset_card)
        
        # Add group to layout
        self.expand_layout.addWidget(self.application_group)
    
    def create_about_group(self):
        """Create about and help group"""
        self.about_group = SettingCardGroup("About", self)
        
        # Help card
        self.help_card = HyperlinkCard(
            "https://github.com/your-repo/app-template",
            "Open help page",
            FIF.HELP,
            "Help",
            "Get help and documentation",
            parent=self.about_group
        )
        
        # Feedback card
        self.feedback_card = PrimaryPushSettingCard(
            "Provide feedback",
            FIF.FEEDBACK,
            "Feedback",
            "Help us improve the application",
            parent=self.about_group
        )
        self.feedback_card.clicked.connect(self.show_feedback_dialog)
        
        # About card
        self.about_card = PushSettingCard(
            "Check update",
            FIF.INFO,
            "About",
            "Generic PyQt6 Application Template v1.0.0",
            parent=self.about_group
        )
        self.about_card.clicked.connect(self.check_update)
        
        # Add cards to group
        self.about_group.addSettingCard(self.help_card)
        self.about_group.addSettingCard(self.feedback_card)
        self.about_group.addSettingCard(self.about_card)
        
        # Add group to layout
        self.expand_layout.addWidget(self.about_group)
    
    def on_theme_clicked(self):
        """Handle theme button click - cycle through themes"""
        current_text = self.theme_card.button.text()
        themes = ["Light", "Dark", "Auto"]
        
        try:
            current_index = themes.index(current_text)
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]
        except ValueError:
            next_theme = "Light"  # Default fallback
        
        # Update button text
        self.theme_card.button.setText(next_theme)
        
        # Apply theme
        theme_map = {
            "Light": Theme.LIGHT,
            "Dark": Theme.DARK,
            "Auto": Theme.AUTO
        }
        
        if next_theme in theme_map:
            theme = theme_map[next_theme]
            setTheme(theme)
            
            # Save to config
            if self.config_manager:
                self.config_manager.set_theme(next_theme.lower())
            
            # Emit signal
            self.theme_changed.emit(next_theme.lower())
            self.setting_changed.emit("theme", next_theme.lower())
            
            # Show info
            InfoBar.success(
                title="Theme Changed",
                content=f"Theme changed to {next_theme}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def on_theme_changed(self, theme_text: str):
        """Handle theme change (legacy method for compatibility)"""
        self.on_theme_clicked()
    
    def on_background_toggle(self, enabled: bool):
        """Handle background toggle"""
        if self.config_manager:
            self.config_manager.set_background_enabled(enabled)
        
        # Emit signal
        self.background_changed.emit("enabled" if enabled else "disabled")
        self.setting_changed.emit("background_enabled", enabled)
        
        # Show info
        status = "enabled" if enabled else "disabled"
        InfoBar.info(
            title="Background Setting",
            content=f"Background image {status}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
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
                InfoBar.success(
                    title="Background Updated",
                    content=f"Background image set to {os.path.basename(image_path)}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def on_autosave_changed(self, enabled: bool):
        """Handle auto-save setting change"""
        if self.config_manager:
            self.config_manager.set_autosave(enabled)
        
        self.setting_changed.emit("autosave", enabled)
        
        status = "enabled" if enabled else "disabled"
        InfoBar.info(
            title="Auto-save Setting",
            content=f"Auto-save {status}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
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
        
        InfoBar.info(
            title="Language Setting",
            content=f"Language set to {next_language}. Restart required for full effect.",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
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
            
            InfoBar.success(
                title="Settings Reset",
                content="All settings have been reset to default values",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def show_feedback_dialog(self):
        """Show feedback dialog"""
        InfoBar.info(
            title="Feedback",
            content="Thank you for your interest in providing feedback!\n\nPlease visit our GitHub repository or contact us directly.",
            orient=Qt.Orientation.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self
        )
    
    def check_update(self):
        """Check for updates"""
        InfoBar.info(
            title="Update Check",
            content="You are using the latest version of the application template.\n\nVersion: 1.0.0",
            orient=Qt.Orientation.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
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
        
        # Load background settings
        bg_enabled = self.config_manager.get_background_enabled()
        self.background_card.switchButton.setChecked(bg_enabled)
        
        # Load other settings
        autosave = self.config_manager.get_autosave()
        self.autosave_card.switchButton.setChecked(autosave)
        
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
        if self.config_manager and self.config_manager.get_autosave():
            self.save_settings()
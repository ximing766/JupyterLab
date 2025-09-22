# -*- coding: utf-8 -*-
"""
Theme Manager for Generic PyQt6 Application Template
Handles theme switching and customization
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from qfluentwidgets import setTheme, Theme, isDarkTheme


class ThemeManager(QObject):
    """Manages application themes and styling"""
    
    # Signals
    theme_changed = pyqtSignal(str)  # Emits theme name when changed
    
    # Theme constants
    LIGHT_THEME = "light"
    DARK_THEME = "dark"
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self._current_theme = self.DARK_THEME
        
        # Default theme configurations
        self._themes = {
            self.LIGHT_THEME: {
                "name": "Light Theme",
                "is_dark": False,
                "primary_color": "#0078d4",
                "background_color": "#ffffff",
                "text_color": "#000000",
                "secondary_color": "#f3f2f1",
                "accent_color": "#106ebe",
                "border_color": "#d1d1d1"
            },
            self.DARK_THEME: {
                "name": "Dark Theme",
                "is_dark": True,
                "primary_color": "#0078d4",
                "background_color": "#202020",
                "text_color": "#ffffff",
                "secondary_color": "#2d2d2d",
                "accent_color": "#4cc2ff",
                "border_color": "#404040"
            }
        }
        
        # Load theme from config if available
        if self.config_manager:
            theme_config = self.config_manager.get_theme_config()
            self._current_theme = theme_config.get("current_theme", self.DARK_THEME)
            
            # Merge custom themes if any
            custom_themes = theme_config.get("themes", {})
            self._themes.update(custom_themes)
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get available theme names and display names"""
        return {theme_id: config["name"] for theme_id, config in self._themes.items()}
    
    def get_current_theme_id(self) -> str:
        """Get current theme ID"""
        return self._current_theme
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme configuration"""
        return self._themes.get(self._current_theme, self._themes[self.DARK_THEME]).copy()
    
    def get_theme_config(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific theme"""
        return self._themes.get(theme_id, {}).copy() if theme_id in self._themes else None
    
    def set_theme(self, theme_id: str) -> bool:
        """Set current theme
        
        Args:
            theme_id: Theme identifier
            
        Returns:
            bool: True if theme was set successfully
        """
        if theme_id not in self._themes:
            return False
        
        old_theme = self._current_theme
        self._current_theme = theme_id
        
        # Apply theme to QFluentWidgets
        self._apply_fluent_theme()
        
        # Save to config if available
        if self.config_manager:
            self.config_manager.set_theme(theme_id)
        
        # Emit signal if theme actually changed
        if old_theme != theme_id:
            self.theme_changed.emit(theme_id)
        
        return True
    
    def toggle_theme(self) -> str:
        """Toggle between light and dark themes
        
        Returns:
            str: New theme ID
        """
        current_config = self.get_current_theme()
        
        if current_config.get("is_dark", True):
            # Switch to light theme
            new_theme = self.LIGHT_THEME
        else:
            # Switch to dark theme
            new_theme = self.DARK_THEME
        
        self.set_theme(new_theme)
        return new_theme
    
    def is_dark_theme(self) -> bool:
        """Check if current theme is dark"""
        current_config = self.get_current_theme()
        return current_config.get("is_dark", True)
    
    def add_custom_theme(self, theme_id: str, theme_config: Dict[str, Any]) -> bool:
        """Add a custom theme
        
        Args:
            theme_id: Unique theme identifier
            theme_config: Theme configuration dictionary
            
        Returns:
            bool: True if theme was added successfully
        """
        # Validate required fields
        required_fields = ["name", "is_dark", "primary_color", "background_color"]
        if not all(field in theme_config for field in required_fields):
            return False
        
        # Add default values for missing optional fields
        default_values = {
            "text_color": "#ffffff" if theme_config["is_dark"] else "#000000",
            "secondary_color": "#2d2d2d" if theme_config["is_dark"] else "#f3f2f1",
            "accent_color": "#4cc2ff" if theme_config["is_dark"] else "#106ebe",
            "border_color": "#404040" if theme_config["is_dark"] else "#d1d1d1"
        }
        
        for key, value in default_values.items():
            if key not in theme_config:
                theme_config[key] = value
        
        # Add theme
        self._themes[theme_id] = theme_config
        
        # Save to config if available
        if self.config_manager:
            self.config_manager.add_theme(theme_id, theme_config)
        
        return True
    
    def remove_custom_theme(self, theme_id: str) -> bool:
        """Remove a custom theme
        
        Args:
            theme_id: Theme identifier to remove
            
        Returns:
            bool: True if theme was removed successfully
        """
        # Don't allow removal of default themes
        if theme_id in [self.LIGHT_THEME, self.DARK_THEME]:
            return False
        
        if theme_id not in self._themes:
            return False
        
        # If removing current theme, switch to default
        if self._current_theme == theme_id:
            self.set_theme(self.DARK_THEME)
        
        # Remove theme
        del self._themes[theme_id]
        
        # Note: ConfigManager doesn't have remove_theme method
        # This would need to be implemented if needed
        
        return True
    
    def _apply_fluent_theme(self):
        """Apply theme to QFluentWidgets"""
        current_config = self.get_current_theme()
        
        if current_config.get("is_dark", True):
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
    
    def get_theme_stylesheet(self, widget_type: str = "general") -> str:
        """Get stylesheet for current theme
        
        Args:
            widget_type: Type of widget to get stylesheet for
            
        Returns:
            str: CSS stylesheet string
        """
        current_config = self.get_current_theme()
        
        if widget_type == "general":
            return f"""
            QWidget {{
                background-color: {current_config['background_color']};
                color: {current_config['text_color']};
            }}
            
            QFrame {{
                border: 1px solid {current_config['border_color']};
                background-color: {current_config['secondary_color']};
            }}
            
            QPushButton {{
                background-color: {current_config['primary_color']};
                color: {current_config['text_color']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {current_config['accent_color']};
            }}
            
            QPushButton:pressed {{
                background-color: {current_config['primary_color']};
            }}
            """
        
        elif widget_type == "transparent":
            return f"""
            QWidget {{
                background: rgba(36, 42, 56, 0.2);
                border-radius: 8px;
            }}
            """
        
        return ""
    
    def apply_to_widget(self, widget, widget_type: str = "general"):
        """Apply current theme to a specific widget
        
        Args:
            widget: Qt widget to apply theme to
            widget_type: Type of styling to apply
        """
        stylesheet = self.get_theme_stylesheet(widget_type)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
    
    def sync_with_system(self) -> bool:
        """Sync theme with system theme if possible
        
        Returns:
            bool: True if sync was successful
        """
        try:
            # Use QFluentWidgets' system theme detection
            if isDarkTheme():
                return self.set_theme(self.DARK_THEME)
            else:
                return self.set_theme(self.LIGHT_THEME)
        except Exception as e:
            print(f"Failed to sync with system theme: {e}")
            return False
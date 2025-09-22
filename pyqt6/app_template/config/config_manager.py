# -*- coding: utf-8 -*-
"""
Configuration Manager for Generic PyQt6 Application Template
Handles application settings, themes, and background configurations
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class ConfigManager:
    """Manages application configuration settings"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_dir: Custom configuration directory path
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to application directory
            app_dir = Path(__file__).parent.parent
            self.config_dir = app_dir / "config"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration file paths
        self.main_config_path = self.config_dir / "app_config.json"
        self.theme_config_path = self.config_dir / "theme_config.json"
        self.background_config_path = self.config_dir / "background_config.json"
        
        # Load configurations
        self._main_config = self._load_main_config()
        self._theme_config = self._load_theme_config()
        self._background_config = self._load_background_config()
    
    def _load_main_config(self) -> Dict[str, Any]:
        """Load main application configuration"""
        default_config = {
            "app_name": "Generic App",
            "version": "1.0.0",
            "window": {
                "width": 1200,
                "height": 800,
                "min_width": 1000,
                "min_height": 700
            },
            "features": {
                "mouse_navigation": True,
                "background_enabled": True,
                "theme_switching": True
            },
            "settings": {
                "language": "english",
                "autosave": True
            }
        }
        
        return self._load_json_config(self.main_config_path, default_config)
    
    def _load_theme_config(self) -> Dict[str, Any]:
        """Load theme configuration"""
        default_config = {
            "current_theme": "dark",
            "themes": {
                "dark": {
                    "name": "Dark Theme",
                    "is_dark": True,
                    "primary_color": "#0078d4",
                    "background_color": "#202020"
                },
                "light": {
                    "name": "Light Theme",
                    "is_dark": False,
                    "primary_color": "#0078d4",
                    "background_color": "#ffffff"
                }
            }
        }
        
        return self._load_json_config(self.theme_config_path, default_config)
    
    def _load_background_config(self) -> Dict[str, Any]:
        """Load background configuration"""
        # Default background images (relative to assets folder)
        default_images = [
            "backgrounds/default1.jpg",
            "backgrounds/default2.jpg",
            "backgrounds/default3.jpg"
        ]
        
        default_config = {
            "enabled": True,
            "opacity": 1.0,
            "current_image": default_images[0] if default_images else None,
            "available_images": default_images,
            "current_index": 0
        }
        
        return self._load_json_config(self.background_config_path, default_config)
    
    def _load_json_config(self, file_path: Path, default_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load JSON configuration with fallback to defaults"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(default_config, config)
            else:
                # Save default configuration
                self._save_json_config(file_path, default_config)
                return default_config.copy()
        except Exception as e:
            print(f"Error loading config from {file_path}: {e}")
            return default_config.copy()
    
    def _save_json_config(self, file_path: Path, config: Dict[str, Any]):
        """Save JSON configuration to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving config to {file_path}: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with default config"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    # Main configuration methods
    def get_main_config(self) -> Dict[str, Any]:
        """Get main configuration"""
        return self._main_config.copy()
    
    def get_language(self) -> str:
        """Get current language setting"""
        return self._main_config.get("settings", {}).get("language", "english")
    
    def set_language(self, language: str):
        """Set language setting"""
        if "settings" not in self._main_config:
            self._main_config["settings"] = {}
        self._main_config["settings"]["language"] = language
        self._save_json_config(self.main_config_path, self._main_config)
    
    def get_autosave(self) -> bool:
        """Get autosave setting"""
        return self._main_config.get("settings", {}).get("autosave", True)
    
    def set_autosave(self, enabled: bool):
        """Set autosave setting"""
        if "settings" not in self._main_config:
            self._main_config["settings"] = {}
        self._main_config["settings"]["autosave"] = enabled
        self._save_json_config(self.main_config_path, self._main_config)
    
    def update_main_config(self, updates: Dict[str, Any]):
        """Update main configuration"""
        self._main_config = self._merge_configs(self._main_config, updates)
        self._save_json_config(self.main_config_path, self._main_config)
    
    # Theme configuration methods
    def get_theme_config(self) -> Dict[str, Any]:
        """Get theme configuration"""
        return self._theme_config.copy()
    
    def get_theme(self) -> str:
        """Get current theme name"""
        return self._theme_config.get("current_theme", "dark")
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme settings"""
        current_theme_name = self._theme_config.get("current_theme", "dark")
        themes = self._theme_config.get("themes", {})
        return themes.get(current_theme_name, themes.get("dark", {}))
    
    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self._theme_config.get("themes", {}):
            self._theme_config["current_theme"] = theme_name
            self._save_json_config(self.theme_config_path, self._theme_config)
            return True
        return False
    
    def add_theme(self, theme_name: str, theme_config: Dict[str, Any]):
        """Add a new theme"""
        if "themes" not in self._theme_config:
            self._theme_config["themes"] = {}
        
        self._theme_config["themes"][theme_name] = theme_config
        self._save_json_config(self.theme_config_path, self._theme_config)
    
    # Background configuration methods
    def get_background_config(self) -> Dict[str, Any]:
        """Get background configuration"""
        return self._background_config.copy()
    
    def get_background_enabled(self) -> bool:
        """Get background enabled status"""
        return self._background_config.get("enabled", False)
    
    def set_background_enabled(self, enabled: bool):
        """Enable or disable background"""
        self._background_config["enabled"] = enabled
        self._save_json_config(self.background_config_path, self._background_config)
    
    def set_background_opacity(self, opacity: float):
        """Set background opacity (0.0 to 1.0)"""
        self._background_config["opacity"] = max(0.0, min(1.0, opacity))
        self._save_json_config(self.background_config_path, self._background_config)
    
    def get_available_backgrounds(self) -> List[str]:
        """Get list of available background images"""
        return self._background_config.get("available_images", [])
    
    def add_background_image(self, image_path: str):
        """Add a new background image"""
        available_images = self._background_config.get("available_images", [])
        if image_path not in available_images:
            available_images.append(image_path)
            self._background_config["available_images"] = available_images
            self._save_json_config(self.background_config_path, self._background_config)
    
    def remove_background_image(self, image_path: str):
        """Remove a background image"""
        available_images = self._background_config.get("available_images", [])
        if image_path in available_images:
            available_images.remove(image_path)
            self._background_config["available_images"] = available_images
            
            # If current image was removed, switch to first available
            if self._background_config.get("current_image") == image_path:
                if available_images:
                    self.set_current_background(available_images[0])
                else:
                    self._background_config["current_image"] = None
                    self._background_config["current_index"] = 0
            
            self._save_json_config(self.background_config_path, self._background_config)
    
    def set_current_background(self, image_path: str):
        """Set current background image"""
        available_images = self._background_config.get("available_images", [])
        if image_path in available_images:
            self._background_config["current_image"] = image_path
            self._background_config["current_index"] = available_images.index(image_path)
            self._save_json_config(self.background_config_path, self._background_config)
            return True
        return False
    
    def next_background(self) -> Optional[str]:
        """Switch to next background image"""
        available_images = self._background_config.get("available_images", [])
        if not available_images:
            return None
        
        current_index = self._background_config.get("current_index", 0)
        next_index = (current_index + 1) % len(available_images)
        
        next_image = available_images[next_index]
        self._background_config["current_image"] = next_image
        self._background_config["current_index"] = next_index
        self._save_json_config(self.background_config_path, self._background_config)
        
        return next_image
    
    def previous_background(self) -> Optional[str]:
        """Switch to previous background image"""
        available_images = self._background_config.get("available_images", [])
        if not available_images:
            return None
        
        current_index = self._background_config.get("current_index", 0)
        prev_index = (current_index - 1) % len(available_images)
        
        prev_image = available_images[prev_index]
        self._background_config["current_image"] = prev_image
        self._background_config["current_index"] = prev_index
        self._save_json_config(self.background_config_path, self._background_config)
        
        return prev_image
    
    # General methods
    def save_config(self):
        """Save all configurations"""
        self._save_json_config(self.main_config_path, self._main_config)
        self._save_json_config(self.theme_config_path, self._theme_config)
        self._save_json_config(self.background_config_path, self._background_config)
    
    def reload_config(self):
        """Reload all configurations from files"""
        self._main_config = self._load_main_config()
        self._theme_config = self._load_theme_config()
        self._background_config = self._load_background_config()
    
    def reset_to_defaults(self):
        """Reset all configurations to defaults"""
        # Remove existing config files
        for config_path in [self.main_config_path, self.theme_config_path, self.background_config_path]:
            if config_path.exists():
                config_path.unlink()
        
        # Reload with defaults
        self.reload_config()
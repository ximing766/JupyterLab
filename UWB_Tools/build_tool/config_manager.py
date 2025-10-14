#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
                      UWB Build Tool - Configuration Manager Module
==============================================================================

Description:
    Configuration management system for UWB build tool. Handles persistent
    storage and retrieval of application settings, build modes, project history,
    and user preferences using JSON-based configuration files.

Author:         Cardshare@QLL
Created:        2025
Version:        1.0.0

==============================================================================
"""

import json
import os
from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

class ConfigManager(QObject):
    config_changed = pyqtSignal()
    
    def __init__(self, config_file: str = "config.json"):
        super().__init__()
        self.config_file = config_file
        self.config_path = os.path.join(os.path.dirname(__file__), config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        default_config = {
            "project_history": [],
            "last_project": "",
            "last_config_mode": "Debug",
            "selected_mode": "INGATE_MASTER_TRANSIT",
            "window_geometry": None,
            "window_state": None,
            "display_mode": "compact",  # compact or extended
            "build_modes": {
                "INGATE_MASTER_TRANSIT": {
                    "display_name": "INGATE主锚点传输模式",
                    "description": "入口网关主锚点传输模式",
                    "macros": {
                        "UWBIOT_APP_BUILD__DEMO_TRANSIT": 1,
                        "ANCHOR_MODE": "MASTER_ANCHOR",
                        "GATE_MODE": "INGATE"
                    }
                }
            }
        }
        
        if not os.path.exists(self.config_path):
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (json.JSONDecodeError, FileNotFoundError):
            return default_config
    
    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.config_changed.emit()
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def add_project_to_history(self, project_path: str):
        if project_path and project_path not in self.config["project_history"]:
            self.config["project_history"].insert(0, project_path)

            if len(self.config["project_history"]) > 10:
                self.config["project_history"] = self.config["project_history"][:10]
            self.save_config()
    
    def remove_project_from_history(self, project_path: str):
        """从历史记录中移除项目"""
        if project_path in self.config["project_history"]:
            self.config["project_history"].remove(project_path)
            self.save_config()
    
    def clear_project_history(self):
        """清空项目历史记录"""
        self.config["project_history"] = []
        self.save_config()
    
    def get_project_history(self) -> List[str]:
        """获取项目历史记录"""
        return self.config.get("project_history", [])
    
    def set_last_project(self, project_path: str):
        """设置最后选择的项目"""
        self.config["last_project"] = project_path
        self.add_project_to_history(project_path)
    
    def get_last_project(self) -> str:
        """获取最后选择的项目"""
        return self.config.get("last_project", "")
    
    def set_config_mode(self, mode: str):
        """设置配置模式 (Debug/Release)"""
        self.config["last_config_mode"] = mode
        self.save_config()
    
    def get_config_mode(self) -> str:
        """获取配置模式"""
        return self.config.get("last_config_mode", "Debug")
    
    def set_selected_mode(self, mode: str):

        self.config["selected_mode"] = mode
        self.save_config()
    
    def get_selected_mode(self) -> str:
        return self.config.get("selected_mode", "INGATE_MASTER_TRANSIT")
    
    def get_config(self) -> Dict[str, Any]:
        return self.config
    
    def get_build_modes(self) -> Dict[str, Any]:
        return self.config.get('build_modes', {})
    
    def get_mode_config(self, mode_key: str) -> Dict[str, Any]:
        build_modes = self.get_build_modes()
        return build_modes.get(mode_key, {})
    
    def get_mode_macros(self, mode_key: str) -> Dict[str, Any]:
        mode_config = self.get_mode_config(mode_key)
        return mode_config.get("macros", {})
    
    def add_build_mode(self, mode_key: str, display_name: str, description: str, macros: Dict[str, Any]):
        if "build_modes" not in self.config:
            self.config["build_modes"] = {}
        
        self.config["build_modes"][mode_key] = {
            "display_name": display_name,
            "description": description,
            "macros": macros
        }
        self.save_config()
    
    def remove_build_mode(self, mode_key: str):
        if "build_modes" in self.config and mode_key in self.config["build_modes"]:
            del self.config["build_modes"][mode_key]

            if self.get_selected_mode() == mode_key:
                available_modes = list(self.get_build_modes().keys())
                if available_modes:
                    self.set_selected_mode(available_modes[0])
            self.save_config()
    
    def set_window_geometry(self, geometry):
        if geometry:
            self.config["window_geometry"] = geometry.data().hex()
        else:
            self.config["window_geometry"] = None
        self.save_config()
    
    def get_window_geometry(self):
        from PyQt6.QtCore import QByteArray
        geometry_hex = self.config.get("window_geometry")
        if geometry_hex:
            return QByteArray(bytes.fromhex(geometry_hex))
        return None
    
    def set_window_state(self, state):
        if state:
            self.config["window_state"] = state.data().hex()
        else:
            self.config["window_state"] = None
        self.save_config()
    
    def get_window_state(self):
        from PyQt6.QtCore import QByteArray
        state_hex = self.config.get("window_state")
        if state_hex:
            return QByteArray(bytes.fromhex(state_hex))
        return None
    
    def set_display_mode(self, mode: str):
        """Set display mode (compact or extended)"""
        self.config["display_mode"] = mode
        self.save_config()
        self.config_changed.emit()
    
    def get_display_mode(self) -> str:
        """Get display mode"""
        return self.config.get("display_mode", "compact")
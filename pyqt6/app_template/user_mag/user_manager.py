# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal

from database import DatabaseManager, UserDatabase, User


class UserSession:
    """Current user session information"""
    def __init__(self):
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.role: Optional[str] = None
        self.full_name: Optional[str] = None
        self.email: Optional[str] = None
        self.is_authenticated: bool = False
        self.login_time: Optional[datetime] = None
    
    def clear(self):
        """Clear session data"""
        self.user_id = None
        self.username = None
        self.role = None
        self.full_name = None
        self.email = None
        self.is_authenticated = False
        self.login_time = None
    
    def set_user(self, user: User):
        """Set session data from User object"""
        self.user_id = user.id
        self.username = user.username
        self.role = user.role
        self.full_name = user.full_name
        self.email = user.email
        self.is_authenticated = True
        self.login_time = datetime.now()
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.role == 'admin'


class UserManager(QObject):
    """Manages user authentication and database operations"""
    user_logged_in  = pyqtSignal(str)  # username
    user_logged_out = pyqtSignal()
    user_created    = pyqtSignal(str)  # username
    user_updated    = pyqtSignal(str)  # username
    user_deleted    = pyqtSignal(str)  # username
    
    def __init__(self, config_dir: Optional[str] = None):
        super().__init__()
        
        # Setup paths
        if config_dir:
            self.config_dir = Path(config_dir)
            self.app_config_dir = Path(__file__).parent.parent / "config"
            self.app_config_dir.mkdir(exist_ok=True)
        else:
            # Database is now in the same directory as user_manager.py
            self.config_dir = Path(__file__).parent
            # Config directory is still in the parent/config
            self.app_config_dir = Path(__file__).parent.parent / "config"
            self.app_config_dir.mkdir(exist_ok=True)
        
        self.config_dir.mkdir(exist_ok=True)
        self.base_config_path = self.app_config_dir / "config.json"
        self.user_configs_dir = self.app_config_dir / "users"
        self.user_configs_dir.mkdir(exist_ok=True)
        
        # Initialize database components (using default database path)
        self.db_manager = DatabaseManager()
        self.user_db = UserDatabase(self.db_manager)
        
        # Current session
        self.current_session = UserSession()
        
        # Initialize with default users
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default admin and user accounts if they don't exist"""
        self.user_db.create_default_users()
        
        # Create config files for default users
        if not (self.user_configs_dir / "admin.json").exists():
            self._create_user_config('admin')
        if not (self.user_configs_dir / "user.json").exists():
            self._create_user_config('user')
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user with username and password"""
        user = self.user_db.authenticate_user(username, password)
        if user:
            self.current_session.set_user(user)
            self.user_logged_in.emit(username)
            return True
        return False
    
    def logout(self):
        """Logout current user"""
        if self.current_session.is_authenticated:
            self.current_session.clear()
            self.user_logged_out.emit()
    
    def create_user(self, username: str, password: str, email: str = "", 
                   full_name: str = "", role: str = "user") -> bool:
        """Create a new user"""
        user = self.user_db.create_user(username, password, email, full_name, role)
        if user:
            # Create user config file
            self._create_user_config(username)
            # Emit signal
            self.user_created.emit(username)
            return True
        return False
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        # Get username before update for signal
        username = None
        try:
            with self.user_db.db_manager.session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return False
                username = user.username
        except Exception as e:
            print(f"Error getting user for update: {e}")
            return False
        
        success = self.user_db.update_user(user_id, **kwargs)
        
        if success and username:
            # Emit signal
            self.user_updated.emit(username)
        
        return success
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (soft delete by setting is_active=False)"""
        # Get username before delete for signal
        user = self.user_db.get_user_by_id(user_id)
        if not user or user.username == 'admin':  # Protect admin user
            return False
        
        username = user.username
        success = self.user_db.delete_user(user_id, soft_delete=True)
        
        if success:
            # Emit signal
            self.user_deleted.emit(username)
        
        return success
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.user_db.get_all_users()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = self.user_db.get_user_by_id(user_id)
        return user.to_dict() if user else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        user = self.user_db.get_user_by_username(username)
        return user.to_dict() if user else None
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return self.user_db.user_exists(username)
    
    def get_user_count(self) -> int:
        """Get total user count"""
        return self.user_db.get_user_count()
    
    # Configuration management methods (unchanged)
    def _create_user_config(self, username: str):
        """Create default config file for user"""
        config_path = self.user_configs_dir / f"{username}.json"
        
        if not config_path.exists():
            default_config = {
                "user": {
                    "username": username,
                    "preferences": {
                        "theme": "light",
                        "language": "en"
                    }
                },
                "app": {
                    "window": {
                        "width": 1200,
                        "height": 800,
                        "maximized": False
                    },
                    "features": {
                        "user_management": True
                    }
                }
            }
            
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error creating user config: {e}")
    
    def get_user_config_path(self, username: str = None) -> Path:
        """Get path to user config file"""
        if username is None:
            username = self.current_session.username or "default"
        return self.user_configs_dir / f"{username}.json"
    
    def load_user_config(self, username: str = None) -> Dict[str, Any]:
        """Load user-specific configuration"""
        config_path = self.get_user_config_path(username)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading user config: {e}")
        
        # Return base config if user config doesn't exist
        return self.load_base_config()
    
    def load_base_config(self) -> Dict[str, Any]:
        """Load base application configuration"""
        if self.base_config_path.exists():
            try:
                with open(self.base_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading base config: {e}")
        
        return {}
    
    def save_user_config(self, config_data: Dict[str, Any], username: str = None):
        """Save user-specific configuration"""
        config_path = self.get_user_config_path(username)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving user config: {e}")
    
    def is_user_management_enabled(self) -> bool:
        """Check if user management is enabled in config"""
        config = self.load_user_config()
        return config.get('app', {}).get('features', {}).get('user_management', False)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current logged in user info"""
        if self.current_session.is_authenticated:
            return {
                'id': self.current_session.user_id,
                'username': self.current_session.username,
                'role': self.current_session.role,
                'full_name': self.current_session.full_name,
                'email': self.current_session.email,
                'login_time': self.current_session.login_time.isoformat() if self.current_session.login_time else None
            }
        return None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_session.is_authenticated
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in (alias for is_authenticated)"""
        return self.is_authenticated()
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.current_session.is_admin()
    
    def close(self):
        """Close database connections"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
    
    def __del__(self):
        """Destructor to ensure database connections are closed"""
        self.close()
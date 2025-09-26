# -*- coding: utf-8 -*-
import bcrypt
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .database_manager import DatabaseManager
from .models import User

class UserDatabase:
    """User database operations interface"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_user(self, username: str, password: str, email: str = "", 
                   full_name: str = "", role: str = "user") -> Optional[User]:
        try:
            with self.db_manager.session_scope() as session:
                # Check if user already exists
                existing_user = session.query(User).filter_by(username=username).first()
                if existing_user:
                    return None
                
                # Hash password
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                # Create user
                new_user = User(
                    username=username,
                    password_hash=password_hash.decode('utf-8'),
                    email=email,
                    full_name=full_name,
                    role=role,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                session.add(new_user)
                session.flush()  # Get the ID before commit
                
                return new_user
                
        except IntegrityError:
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        try:
            with self.db_manager.session_scope() as session:
                user = session.query(User).filter_by(
                    username=username, 
                    is_active=True
                ).first()
                
                if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                    user.last_login = datetime.utcnow()
                    
                    # Detach the user from session to avoid DetachedInstanceError
                    session.expunge(user)
                    return user
                
                return None
                
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            with self.db_manager.session_scope() as session:
                return session.query(User).filter_by(id=user_id).first()
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            with self.db_manager.session_scope() as session:
                return session.query(User).filter_by(username=username).first()
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        try:
            with self.db_manager.session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return False
                
                # Update allowed fields
                allowed_fields = ['email', 'full_name', 'role', 'is_active', 'config_data']
                for field, value in kwargs.items():
                    if field in allowed_fields:
                        setattr(user, field, value)
                
                # Handle password update separately
                if 'password' in kwargs:
                    password_hash = bcrypt.hashpw(kwargs['password'].encode('utf-8'), bcrypt.gensalt())
                    user.password_hash = password_hash.decode('utf-8')
                
                return True
                
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: int, soft_delete: bool = True) -> bool:
        try:
            with self.db_manager.session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user or user.username == 'admin':  # Protect admin user
                    return False
                
                if soft_delete:
                    user.is_active = False
                else:
                    session.delete(user)
                
                return True
                
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def get_all_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(User)
                if not include_inactive:
                    query = query.filter_by(is_active=True)
                users = query.all()
                # Convert to dict within session to avoid DetachedInstanceError
                return [user.to_dict() for user in users]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def get_users_by_role(self, role: str, include_inactive: bool = False) -> List[User]:
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(User).filter_by(role=role)
                if not include_inactive:
                    query = query.filter_by(is_active=True)
                return query.all()
        except Exception as e:
            print(f"Error getting users by role: {e}")
            return []
    
    def user_exists(self, username: str) -> bool:
        try:
            with self.db_manager.session_scope() as session:
                user = session.query(User).filter_by(username=username).first()
                return user is not None
        except Exception as e:
            print(f"Error checking user existence: {e}")
            return False
    
    def get_user_count(self, include_inactive: bool = False) -> int:
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(User)
                if not include_inactive:
                    query = query.filter_by(is_active=True)
                return query.count()
        except Exception as e:
            print(f"Error getting user count: {e}")
            return 0
    
    def create_default_users(self):
        if not self.user_exists('admin'):
            admin_user = self.create_user(
                username='admin',
                password='admin123',
                email='admin@localhost',
                full_name='Administrator',
                role='admin'
            )
            if admin_user:
                print("Default admin user created: admin/admin123")
        
        # Create default regular user
        if not self.user_exists('user'):
            regular_user = self.create_user(
                username='user',
                password='user123',
                email='user@localhost',
                full_name='Regular User',
                role='user'
            )
            if regular_user:
                print("Default user created: user/user123")
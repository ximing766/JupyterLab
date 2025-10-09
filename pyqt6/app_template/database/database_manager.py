# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from .models import Base


class DatabaseManager:
    """Base database manager class"""
    
    def __init__(self, db_path: Optional[str] = None, echo: bool = False):
        """
        Initialize database manager
        
        Args:
            db_path: Path to the database file. If None, uses default location
            echo: Whether to echo SQL statements for debugging
        """
        self._engine: Optional[Engine] = None
        self._SessionLocal: Optional[sessionmaker] = None
        self._db_path = self._setup_db_path(db_path)
        self._echo = echo
        
        # Initialize database
        self._initialize_database()
    
    def _setup_db_path(self, db_path: Optional[str]) -> Path:
        """Setup database path"""
        if db_path:
            return Path(db_path)
        else:
            # Default to database directory (same as this module)
            db_dir = Path(__file__).parent
            db_dir.mkdir(exist_ok=True)
            return db_dir / "app.db"
    
    def _initialize_database(self):
        """Initialize database engine and session factory"""
        # Ensure parent directory exists
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        self._engine = create_engine(
            f'sqlite:///{self._db_path}',
            echo=self._echo,
            pool_pre_ping=True,  # Verify connections before use
            connect_args={"check_same_thread": False}  # Allow multi-threading
        )
        
        # Create all tables
        Base.metadata.create_all(self._engine)
        
        # Create session factory
        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False
        )
    
    @property
    def engine(self) -> Engine:
        """Get database engine"""
        if self._engine is None:
            raise RuntimeError("Database not initialized")
        return self._engine
    
    @property
    def db_path(self) -> Path:
        """Get database file path"""
        return self._db_path
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if self._SessionLocal is None:
            raise RuntimeError("Database not initialized")
        return self._SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db_manager.session_scope() as session:
                # Do database operations
                pass
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables"""
        if self._engine is None:
            raise RuntimeError("Database not initialized")
        Base.metadata.create_all(self._engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        if self._engine is None:
            raise RuntimeError("Database not initialized")
        Base.metadata.drop_all(self._engine)
    
    def close(self):
        """Close database connections"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._SessionLocal = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
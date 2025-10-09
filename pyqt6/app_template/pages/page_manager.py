# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from typing import Dict, List, Optional, Type, Any
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QStackedWidget
from qfluentwidgets import FluentIcon as FIF
from .base_page import BasePage
from .settings_page import SettingsPage

class PageInfo:
    """Information about a registered page"""
    def __init__(self, page_id: str, title: str, page_class: Type[BasePage], 
                 icon=None, tooltip: str = "", enabled: bool = True, 
                 visible: bool = True, order: int = 0, required_role: str = None):
        self.page_id = page_id
        self.title = title
        self.page_class = page_class
        self.icon = icon
        self.tooltip = tooltip or title
        self.enabled = enabled
        self.visible = visible
        self.order = order
        self.required_role = required_role  # Required user role to access this page
        self.instance = None  # Page instance (created when needed)
    
    def create_instance(self, *args, **kwargs) -> BasePage:
        """Create page instance if not exists"""
        if self.instance is None:
            self.instance = self.page_class(*args, **kwargs)
        return self.instance
    
    def __str__(self):
        return f"PageInfo(id='{self.page_id}', title='{self.title}', enabled={self.enabled})"

class PageManager(QObject):
    """Manages application pages and navigation"""
    page_registered = pyqtSignal(str, str)  # page_id, title
    page_unregistered = pyqtSignal(str)  # page_id
    page_changed = pyqtSignal(str, str)  # old_page_id, new_page_id
    page_activated = pyqtSignal(str)  # page_id
    page_deactivated = pyqtSignal(str)  # page_id
    
    def __init__(self, stacked_widget: QStackedWidget = None, parent=None):
        super().__init__(parent)
        
        self.stacked_widget = stacked_widget
        self._pages: Dict[str, PageInfo] = {}
        self._current_page_id: Optional[str] = None
        self._page_order: List[str] = []
        self.user_manager = None  # Will be set by main window
        
        self._register_default_pages()
    
    def _register_default_pages(self):
        self.register_page(
            "settings", "Settings", SettingsPage,
            icon=FIF.SETTING, tooltip="Application Settings", order=99
        )
    
    def register_page(self, page_id: str, title: str, page_class: Type[BasePage],
                     icon=None, tooltip: str = "", enabled: bool = True,
                     visible: bool = True, order: int = 0, required_role: str = None) -> bool:
        if page_id in self._pages:
            print(f"Warning: Page '{page_id}' is already registered")
            return False
        
        if not issubclass(page_class, BasePage):
            print(f"Error: Page class must inherit from BasePage")
            return False
        
        page_info = PageInfo(
            page_id=page_id,
            title=title,
            page_class=page_class,
            icon=icon,
            tooltip=tooltip,
            enabled=enabled,
            visible=visible,
            order=order,
            required_role=required_role
        )
        
        self._pages[page_id] = page_info
        self._update_page_order()
        self.page_registered.emit(page_id, title)
        
        return True
    
    def unregister_page(self, page_id: str) -> bool:
        """Unregister a page"""
        if page_id not in self._pages:
            print(f"Warning: Page '{page_id}' is not registered")
            return False
        
        page_info = self._pages[page_id]
        
        # Remove from stacked widget if exists
        if self.stacked_widget and page_info.instance:
            index = self.stacked_widget.indexOf(page_info.instance)
            if index >= 0:
                self.stacked_widget.removeWidget(page_info.instance)
        
        # Clean up instance
        if page_info.instance:
            page_info.instance.setParent(None)
            page_info.instance = None
        
        # Remove from registry
        del self._pages[page_id]
        
        # Update page order
        self._update_page_order()
        
        # Update current page if needed
        if self._current_page_id == page_id:
            self._current_page_id = None
        
        # Emit signal
        self.page_unregistered.emit(page_id)
        
        print(f"Page '{page_id}' unregistered successfully")
        return True
    
    def get_page_info(self, page_id: str) -> Optional[PageInfo]:
        """Get page information"""
        return self._pages.get(page_id)
    
    def get_page_instance(self, page_id: str, *args, **kwargs) -> Optional[BasePage]:
        """Get or create page instance"""
        page_info = self.get_page_info(page_id)
        if not page_info:
            return None
        
        # Create instance if not exists
        if page_info.instance is None:
            # Pass parent as the first argument if not provided
            if 'parent' not in kwargs and self.parent:
                kwargs['parent'] = self.parent
            page_info.instance = page_info.create_instance(*args, **kwargs)
            
            # Add to stacked widget if available
            if self.stacked_widget:
                self.stacked_widget.addWidget(page_info.instance)
        
        return page_info.instance
    
    def get_all_pages(self) -> Dict[str, PageInfo]:
        """Get all registered pages"""
        return self._pages.copy()
    
    def get_visible_pages(self) -> Dict[str, PageInfo]:
        """Get all visible pages (with permission check)"""
        visible_pages = {}
        for pid, info in self._pages.items():
            if info.visible and self._check_page_permission(info):
                visible_pages[pid] = info
        return visible_pages
    
    def get_enabled_pages(self) -> Dict[str, PageInfo]:
        """Get all enabled pages"""
        return {pid: info for pid, info in self._pages.items() if info.enabled}
    
    def get_page_order(self) -> List[str]:
        """Get page IDs in display order"""
        return self._page_order.copy()
    
    def set_page_enabled(self, page_id: str, enabled: bool) -> bool:
        """Enable or disable a page"""
        page_info = self.get_page_info(page_id)
        if not page_info:
            return False
        
        page_info.enabled = enabled
        return True
    
    def set_page_visible(self, page_id: str, visible: bool) -> bool:
        """Show or hide a page"""
        page_info = self.get_page_info(page_id)
        if not page_info:
            return False
        
        page_info.visible = visible
        self._update_page_order()
        return True
    
    def set_page_order(self, page_id: str, order: int) -> bool:
        """Set page display order"""
        page_info = self.get_page_info(page_id)
        if not page_info:
            return False
        
        page_info.order = order
        self._update_page_order()
        return True
    
    def navigate_to_page(self, page_id: str, *args, **kwargs) -> bool:
        """Navigate to a specific page"""
        page_info = self.get_page_info(page_id)
        if not page_info or not page_info.enabled:
            print(f"Cannot navigate to page '{page_id}': not found or disabled")
            return False
        
        # Check page permission
        if not self._check_page_permission(page_info):
            print(f"Cannot navigate to page '{page_id}': insufficient permissions")
            return False
        
        # Get or create page instance
        page_instance = self.get_page_instance(page_id, *args, **kwargs)
        if not page_instance:
            print(f"Failed to create page instance for '{page_id}'")
            return False
        
        # Switch to page in stacked widget
        if self.stacked_widget:
            old_page_id = self._current_page_id
            
            # Deactivate current page
            if old_page_id and old_page_id != page_id:
                old_page = self.get_page_instance(old_page_id)
                if old_page:
                    old_page.deactivate()
                    self.page_deactivated.emit(old_page_id)
            
            # Switch to new page
            self.stacked_widget.setCurrentWidget(page_instance)
            self._current_page_id = page_id
            
            # Activate new page
            page_instance.activate()
            self.page_activated.emit(page_id)
            
            # Emit page changed signal
            if old_page_id != page_id:
                self.page_changed.emit(old_page_id or "", page_id)
            
            print(f"Navigated to page '{page_id}'")
            return True
        
        return False
    
    def get_current_page_id(self) -> Optional[str]:
        """Get current active page ID"""
        return self._current_page_id
    
    def get_current_page(self) -> Optional[BasePage]:
        """Get current active page instance"""
        if self._current_page_id:
            return self.get_page_instance(self._current_page_id)
        return None
    
    def refresh_current_page(self):
        """Refresh current page"""
        current_page = self.get_current_page()
        if current_page:
            current_page.refresh()
    
    def set_stacked_widget(self, stacked_widget: QStackedWidget):
        """Set the stacked widget for page display"""
        self.stacked_widget = stacked_widget
        
        # Add existing page instances to stacked widget
        for page_info in self._pages.values():
            if page_info.instance:
                self.stacked_widget.addWidget(page_info.instance)
    
    def _update_page_order(self):
        """Update page display order"""
        # Sort pages by order, then by registration order
        visible_pages = [(pid, info) for pid, info in self._pages.items() if info.visible]
        visible_pages.sort(key=lambda x: (x[1].order, x[0]))
        
        self._page_order = [pid for pid, _ in visible_pages]
    
    def clear_all_pages(self):
        """Clear all registered pages"""
        page_ids = list(self._pages.keys())
        for page_id in page_ids:
            self.unregister_page(page_id)
    
    def get_page_count(self) -> int:
        """Get total number of registered pages"""
        return len(self._pages)
    
    def get_visible_page_count(self) -> int:
        """Get number of visible pages"""
        return len([p for p in self._pages.values() if p.visible])
    
    def page_exists(self, page_id: str) -> bool:
        """Check if page exists"""
        return page_id in self._pages
    
    def set_user_manager(self, user_manager):
        """Set user manager for permission checking"""
        self.user_manager = user_manager
    
    def _check_page_permission(self, page_info: PageInfo) -> bool:
        """Check if current user has permission to access the page"""
        # 1:没有指定访问权限，默认允许访问
        if not page_info.required_role:
            return True
        
        # 2:用户管理未启用，拒绝访问
        if not self.user_manager or not self.user_manager.is_user_management_enabled():
            return False
        
        # If user is not authenticated, deny access to role-restricted pages
        if not self.user_manager.is_authenticated():
            return False
        
        # Check user role
        current_user = self.user_manager.get_current_user()
        if not current_user:
            return False
        
        user_role = current_user.get('role', 'user')
        
        # Admin can access all pages
        if user_role == 'admin':
            return True
        
        # Check if user role matches required role
        return user_role == page_info.required_role
    
    def refresh_page_permissions(self):
        """Refresh page visibility based on current user permissions"""
        # This will trigger navigation update in the main window
        self.page_changed.emit("", self._current_page_id or "")
    
    def __str__(self):
        return f"PageManager(pages={len(self._pages)}, current='{self._current_page_id}')"
    
    def __repr__(self):
        return self.__str__()
# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QPushButton,
                            QLineEdit, QComboBox, QMessageBox, QDialog,
                            QFormLayout, QDialogButtonBox, QHeaderView,
                            QFrame, QSpacerItem, QSizePolicy, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor
from qfluentwidgets import (PushButton, LineEdit, ComboBox, TableWidget,
                           ToolButton,
                           BodyLabel, setFont, FluentIcon as FIF, 
                           setCustomStyleSheet, isDarkTheme, themeColor)
from typing import Dict, Any, List, Optional

from pages import BasePage


class UserDialog(QDialog):
    """Dialog for creating/editing users"""
    
    def __init__(self, parent=None, user_data=None, is_edit=False):
        super().__init__(parent)
        self.user_data = user_data
        self.is_edit = is_edit
        # Store reference to parent page - check if it has user_manager attribute
        self.parent_page = parent if hasattr(parent, 'user_manager') else None
        
        self.setWindowTitle("编辑用户" if is_edit else "创建用户")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.setup_ui()
        
        if is_edit and user_data:
            self.load_user_data()
    
    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Username field
        self.username_edit = LineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        if self.is_edit:
            self.username_edit.setEnabled(False)  # Cannot change username
        form_layout.addRow("用户名:", self.username_edit)
        
        # Password field
        self.password_edit = LineEdit()
        self.password_edit.setEchoMode(LineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("请输入密码" if not self.is_edit else "留空则不修改密码")
        form_layout.addRow("密码:", self.password_edit)
        
        # Full name field
        self.fullname_edit = LineEdit()
        self.fullname_edit.setPlaceholderText("请输入全名")
        form_layout.addRow("全名:", self.fullname_edit)
        
        # Email field
        self.email_edit = LineEdit()
        self.email_edit.setPlaceholderText("请输入邮箱")
        form_layout.addRow("邮箱:", self.email_edit)
        
        # Role field
        self.role_combo = ComboBox()
        self.role_combo.addItems(["user", "admin"])
        form_layout.addRow("角色:", self.role_combo)
        
        # Status field (for edit only)
        if self.is_edit:
            self.status_combo = ComboBox()
            self.status_combo.addItems(["激活", "禁用"])
            form_layout.addRow("状态:", self.status_combo)
        
        layout.addLayout(form_layout)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = PushButton("取消")
        self.save_button = PushButton("保存" if self.is_edit else "创建")
        self.save_button.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save_user)
    
    def save_user(self):
        """Save user data"""
        # Validate data first
        is_valid, error_msg = self.validate_data()
        if not is_valid:
            if self.parent_page:
                self.parent_page.show_error("验证错误", error_msg)
            return
        
        user_data = self.get_user_data()
        
        if self.is_edit:
            # Update existing user
            success = self.parent_page.user_manager.update_user(
                user_id=self.user_data['id'],
                username=user_data['username'],
                email=user_data.get('email', ''),
                full_name=user_data.get('full_name', ''),
                role=user_data.get('role', 'user'),
                password=user_data.get('password') if user_data.get('password') else None
            )
            
            if success:
                if self.parent_page:
                    self.parent_page.show_success("成功", f"用户 {self.user_data['username']} 更新成功")
                self.accept()  # Close dialog only on success
            else:
                if self.parent_page:
                    self.parent_page.show_error("错误", "更新用户失败")
        else:
            # Create new user - check if parent_page and user_manager exist
            if not self.parent_page:
                # If no parent page, we can't show error or access user_manager
                return
            
            if not self.parent_page.user_manager:
                self.parent_page.show_error("错误", "用户管理器不可用")
                return
                
            success = self.parent_page.user_manager.create_user(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data.get('email', ''),
                full_name=user_data.get('full_name', ''),
                role=user_data.get('role', 'user')
            )
            
            if success:
                if self.parent_page:
                    self.parent_page.show_success("成功", f"用户 {user_data['username']} 创建成功")
                self.accept()  # Close dialog only on success
            else:
                if self.parent_page:
                    self.parent_page.show_error("错误", "创建用户失败")
    
    def load_user_data(self):
        """Load user data into form"""
        if not self.user_data:
            return
        
        self.username_edit.setText(self.user_data.get('username', ''))
        self.fullname_edit.setText(self.user_data.get('full_name', ''))
        self.email_edit.setText(self.user_data.get('email', ''))
        
        # Set role
        role = self.user_data.get('role', 'user')
        role_index = self.role_combo.findText(role)
        if role_index >= 0:
            self.role_combo.setCurrentIndex(role_index)
        
        # Set status (for edit mode)
        if self.is_edit and hasattr(self, 'status_combo'):
            is_active = self.user_data.get('is_active', True)
            status_text = "激活" if is_active else "禁用"
            status_index = self.status_combo.findText(status_text)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)
    
    def get_user_data(self) -> Dict[str, Any]:
        """Get user data from form"""
        data = {
            'username': self.username_edit.text().strip(),
            'full_name': self.fullname_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'role': self.role_combo.currentText()
        }
        
        # Add password if provided
        password = self.password_edit.text()
        if password:
            data['password'] = password
        
        # Add status for edit mode
        if self.is_edit and hasattr(self, 'status_combo'):
            data['is_active'] = self.status_combo.currentText() == "激活"
        
        return data
    
    def validate_data(self) -> tuple[bool, str]:
        """Validate form data"""
        username = self.username_edit.text().strip()
        if not username:
            return False, "用户名不能为空"
        
        if not self.is_edit:
            password = self.password_edit.text()
            if not password:
                return False, "密码不能为空"
            if len(password) < 6:
                return False, "密码长度至少6位"
        
        email = self.email_edit.text().strip()
        if email and '@' not in email:
            return False, "邮箱格式不正确"
        return True, ""

class UserManagementPage(BasePage):
    """User management page for administrators"""
    
    def __init__(self, parent=None):
        super().__init__("user_management", parent)
        self.user_manager = None
        self.users_data = []
        
        # Try to get user manager from parent immediately
        if hasattr(self.parent(), 'user_manager'):
            self.user_manager = self.parent().user_manager
        
    def init_content(self):
        """Initialize page content"""
        # Get user manager from parent window
        if hasattr(self.parent(), 'user_manager'):
            self.user_manager = self.parent().user_manager
        
        if self.user_manager:
            # print(f"Is authenticated: {self.user_manager.is_authenticated()}")
            # print(f"Is admin: {self.user_manager.is_admin()}")
            current_user = self.user_manager.get_current_user()
            # print(f"Current user: {current_user}")
        
        self.setup_ui()
        self.load_users()
        
        if self.user_manager:
            self.user_manager.user_created.connect(self.on_user_changed)
            self.user_manager.user_updated.connect(self.on_user_changed)
            self.user_manager.user_deleted.connect(self.on_user_changed)
    
    def setup_ui(self):
        """Setup user interface"""
        # Clear existing layout content
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Add user button
        self.add_user_btn = PushButton("添加用户")
        self.add_user_btn.setIcon(FIF.ADD)
        self.add_user_btn.clicked.connect(self.add_user)
        
        # Refresh button
        self.refresh_btn = ToolButton(FIF.SYNC)
        self.refresh_btn.setIcon(FIF.SYNC)
        self.refresh_btn.clicked.connect(self.load_users)
        
        toolbar_layout.addWidget(self.add_user_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addStretch()
        
        self.layout.addLayout(toolbar_layout)
        
        self.users_table = TableWidget(self)
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Full Name", "Email", "Role", "Status", "Actions"]
        )

        # Enhanced table styling with theme support
        self.users_table.verticalHeader().hide()                    # Hide row numbers
        self.users_table.setAlternatingRowColors(True)              # Zebra stripes
        self.users_table.setBorderVisible(True)                     # Border visible
        self.users_table.setBorderRadius(8)                         # 8px border radius
        self.users_table.resizeColumnsToContents()                  # Auto-resize columns

        # Apply enhanced styling with light/dark theme support
        self.apply_table_styling(self.users_table)

        setFont(self.users_table, 13, QFont.Weight.Medium)          # Global 13pt medium font

        # Header styling improvements
        header = self.users_table.horizontalHeader()
        header.setHighlightSections(False)
        header.setFont(QFont('Consolas', 13, QFont.Weight.DemiBold))
        
        # Set column widths
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Username
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Full name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Email
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Role
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.layout.addWidget(self.users_table)
        
        # Status bar
        self.status_label = BodyLabel("就绪")
        self.layout.addWidget(self.status_label)
    
    def load_users(self):
        """Load users from database"""
        if not self.user_manager:
            return
        try:
            self.users_data = self.user_manager.get_all_users()
            self.populate_table()
            self.status_label.setText(f"已加载 {len(self.users_data)} 个用户")
        except Exception as e:
            self.show_error("错误", f"加载用户失败: {str(e)}")
    
    def populate_table(self):
        """Populate users table"""
        self.users_table.setRowCount(len(self.users_data))
        
        for row, user in enumerate(self.users_data):
            # ID
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            
            # Username
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
            
            # Full name
            self.users_table.setItem(row, 2, QTableWidgetItem(user.get('full_name', '')))
            
            # Email
            self.users_table.setItem(row, 3, QTableWidgetItem(user.get('email', '')))
            
            # Role
            role_item = QTableWidgetItem(user['role'])
            if user['role'] == 'admin':
                role_item.setBackground(QColor(173, 216, 230))
            self.users_table.setItem(row, 4, role_item)
            
            # Status
            status_text = "激活" if user['is_active'] else "禁用"
            status_item = QTableWidgetItem(status_text)
            if not user['is_active']:
                status_item.setBackground(Qt.GlobalColor.lightGray)
            self.users_table.setItem(row, 5, status_item)
            
            # Actions
            self.create_action_buttons(row, user)
    
    def create_action_buttons(self, row: int, user: Dict[str, Any]):
        """Create action buttons for user row"""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 2, 5, 2)
        actions_layout.setSpacing(5)
        
        # Edit button
        edit_btn = ToolButton(FIF.EDIT)
        edit_btn.setFixedSize(60, 25)
        edit_btn.clicked.connect(lambda: self.edit_user(user))
        
        # Delete button (disabled for admin user)
        delete_btn = ToolButton(FIF.DELETE)
        delete_btn.setFixedSize(60, 25)
        delete_btn.setStyleSheet("QToolButton { background-color: #f34f4f;}")
        delete_btn.clicked.connect(lambda: self.delete_user(user))
        
        if user['username'] == 'admin':
            actions_layout.addWidget(edit_btn)
            self.users_table.setCellWidget(row, 6, actions_widget)
            return

        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        self.users_table.setCellWidget(row, 6, actions_widget)
    
    def add_user(self):
        """Add new user"""
        dialog = UserDialog(self, is_edit=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh user list after successful creation
            self.load_users()
    
    def edit_user(self, user: Dict[str, Any]):
        """Edit existing user"""
        dialog = UserDialog(self, user_data=user, is_edit=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh user list after successful update
            self.load_users()
    
    def delete_user(self, user: Dict[str, Any]):
        """Delete user"""
        if user['username'] == 'admin':
            self.show_warning("警告", "无法删除管理员账户")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除用户 {user['username']} 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.user_manager.delete_user(user['id'])
            
            if success:
                self.show_success("成功", f"用户 {user['username']} 已删除")
            else:
                self.show_error("错误", "删除用户失败")
    
    def on_user_changed(self, username: str):
        """Handle user data changes"""
        # Reload users after a short delay to allow database to update
        QTimer.singleShot(500, self.load_users)
    
    def on_activate(self):
        """Called when page is activated"""
        super().on_activate()
        # Refresh user list when page is activated
        if self.user_manager and self.user_manager.is_admin():
            self.load_users()
    
    def on_deactivate(self):
        """Called when page is deactivated"""
        super().on_deactivate()
# -*- coding: utf-8 -*-
"""
Login Dialog for User Authentication
Provides a clean and modern login interface using QFluentWidgets
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from qfluentwidgets import (
    LineEdit, PushButton, CheckBox, InfoBar, InfoBarPosition,
    FluentIcon as FIF, setTheme, Theme, isDarkTheme
)
from typing import Optional


class LoginDialog(QDialog):
    """Modern login dialog with user authentication using QFluentWidgets"""
    
    # Signals
    login_successful = pyqtSignal(str)  # username
    login_failed = pyqtSignal(str)      # error message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户登录")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Set fluent theme
        setTheme(Theme.DARK)
        
        # Initialize UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Focus on username field
        self.username_edit.setFocus()
        
        # Show default credentials info
        self.show_default_credentials_info()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("系统登录")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Input container
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(15)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        # Username field
        self.username_edit = LineEdit()
        self.username_edit.setPlaceholderText("用户名")
        self.username_edit.setClearButtonEnabled(True)
        self.username_edit.setFixedHeight(40)
        input_layout.addWidget(self.username_edit)
        
        # Password field
        self.password_edit = LineEdit()
        self.password_edit.setPlaceholderText("密码")
        self.password_edit.setEchoMode(LineEdit.EchoMode.Password)
        self.password_edit.setClearButtonEnabled(True)
        self.password_edit.setFixedHeight(40)
        input_layout.addWidget(self.password_edit)
        
        # Remember me checkbox
        self.remember_checkbox = CheckBox("记住用户名")
        input_layout.addWidget(self.remember_checkbox)
        
        main_layout.addWidget(input_container)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Cancel button
        self.cancel_button = PushButton("取消")
        self.cancel_button.setIcon(FIF.CANCEL)
        self.cancel_button.setFixedHeight(35)
        self.cancel_button.setFixedWidth(100)
        
        # Login button
        self.login_button = PushButton("登录")
        self.login_button.setIcon(FIF.ACCEPT)
        self.login_button.setFixedHeight(35)
        self.login_button.setFixedWidth(100)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        main_layout.addLayout(button_layout)
        
        # Set default button
        self.login_button.setDefault(True)
    
    def connect_signals(self):
        """Connect UI signals"""
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject)
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)
    
    def show_default_credentials_info(self):
        """Show information about default credentials"""
        pass  # Info is now shown in the UI directly
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        # Validate input
        if not username:
            self.show_error("请输入用户名")
            self.username_edit.setFocus()
            return
        
        if not password:
            self.show_error("请输入密码")
            self.password_edit.setFocus()
            return
        
        # Disable login button during authentication
        self.login_button.setEnabled(False)
        self.login_button.setText("登录中...")
        
        # Emit signal with credentials
        self.login_successful.emit(username)
    
    def show_error(self, message: str):
        """Show error message using InfoBar"""
        InfoBar.error(
            title="登录失败",
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def show_success(self, message: str):
        """Show success message using InfoBar"""
        InfoBar.success(
            title="登录成功",
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def reset_login_button(self):
        """Reset login button state"""
        self.login_button.setEnabled(True)
        self.login_button.setText("登录")
    
    def get_credentials(self) -> tuple[str, str]:
        """Get entered credentials"""
        return self.username_edit.text().strip(), self.password_edit.text()
    
    def set_username(self, username: str):
        """Set username field"""
        self.username_edit.setText(username)
        self.password_edit.setFocus()
    
    def clear_form(self):
        """Clear the login form"""
        if not self.remember_checkbox.isChecked():
            self.username_edit.clear()
        self.password_edit.clear()
        self.reset_login_button()
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.clear_form()
        super().closeEvent(event)


class LoginController:
    """Controller for handling login logic"""
    
    def __init__(self, user_manager, parent=None):
        self.user_manager = user_manager
        self.parent = parent
        self.dialog = None
    
    def show_login_dialog(self) -> bool:
        """Show login dialog and handle authentication"""
        self.dialog = LoginDialog(self.parent)
        
        # Connect signals
        self.dialog.login_successful.connect(self.handle_login_attempt)
        
        # Load remembered username if any
        # TODO: Implement remember username functionality
        
        # Show dialog
        result = self.dialog.exec()   #XXX 阻塞等待用户登陆完成
        
        if result == QDialog.DialogCode.Accepted:
            return True
        else:
            return False
    
    def handle_login_attempt(self, username: str):
        """Handle login attempt"""
        if not self.dialog:
            return
        
        # Get credentials
        username, password = self.dialog.get_credentials()
        
        # Attempt authentication
        if self.user_manager.authenticate(username, password):
            # Login successful
            self.dialog.show_success(f"欢迎, {username}!")
            QTimer.singleShot(1000, self.dialog.accept)  # Delay to show success message
        else:
            # Login failed
            self.dialog.show_error("用户名或密码错误")
            self.dialog.reset_login_button()
            self.dialog.password_edit.clear()
            self.dialog.password_edit.setFocus()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.user_manager.is_authenticated()
    
    def get_current_user(self):
        """Get current authenticated user"""
        return self.user_manager.get_current_user()
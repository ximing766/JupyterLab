# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys
import os
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QWidget, QSpacerItem, QSizePolicy, QDialog
from qfluentwidgets import (setThemeColor, setTheme, Theme, SplitTitleBar, isDarkTheme,
                            BodyLabel, CheckBox, HyperlinkButton, LineEdit, PrimaryPushButton, InfoBar, InfoBarPosition,
                            FluentIcon as FIF)
from typing import Optional

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class ModernLoginWindow(Window):
    """Modern login window with user authentication using QFluentWidgets and PyQt6"""
    
    # Signals - integrated from login_dialog.py
    login_successful = pyqtSignal(str)  # username
    login_failed = pyqtSignal(str)      # error message
    
    def __init__(self, user_manager=None, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.setupUI()
        self.setupWindow()
        
    def setupUI(self):
        """Create UI elements programmatically"""
        # Main horizontal layout
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        
        # Background image label (left side) - using nature1.jpg
        self.label = QLabel()
        self.label.setText("")
        # Set background image to nature1.jpg
        background_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "PIC", "nature1.jpg"
        ).replace(os.sep, '/')
        
        self.label.setStyleSheet(f"""
            QLabel {{
                background-image: url({background_path});
                background-repeat: no-repeat;
                background-position: center;
            }}
        """)
        self.label.setScaledContents(True)
        self.horizontalLayout.addWidget(self.label)
        
        # Right panel widget
        self.widget = QWidget()
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QSize(360, 0))
        self.widget.setMaximumSize(QSize(360, 16777215))
        self.widget.setStyleSheet("QLabel{ font: 13px 'Microsoft YaHei' }")
        
        # Right panel layout
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout_2.setSpacing(9)
        
        # Top spacer
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        
        # Logo label - using assets/logo.png
        self.label_2 = QLabel()
        self.label_2.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QSize(100, 100))
        self.label_2.setMaximumSize(QSize(100, 100))
        
        # Set logo image from assets folder
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "logo.png"
        )
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            self.label_2.setPixmap(logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_2.setStyleSheet("""
            QLabel {
                border-radius: 50px;
            }
        """)
        self.label_2.setScaledContents(True)
        self.verticalLayout_2.addWidget(self.label_2, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # Small spacer
        spacerItem1 = QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.verticalLayout_2.addItem(spacerItem1)
        
        # Username label
        self.label_5 = BodyLabel(self.widget)
        self.verticalLayout_2.addWidget(self.label_5)
        
        # Username input - renamed to match login_dialog.py
        self.username_edit = LineEdit(self.widget)
        self.username_edit.setClearButtonEnabled(True)
        self.username_edit.setFixedHeight(40)
        self.verticalLayout_2.addWidget(self.username_edit)
        
        # Password label
        self.label_6 = BodyLabel(self.widget)
        self.verticalLayout_2.addWidget(self.label_6)
        
        # Password input - renamed to match login_dialog.py
        self.password_edit = LineEdit(self.widget)
        self.password_edit.setEchoMode(LineEdit.EchoMode.Password)
        self.password_edit.setClearButtonEnabled(True)
        self.password_edit.setFixedHeight(40)
        self.verticalLayout_2.addWidget(self.password_edit)
        
        # Small spacer
        spacerItem2 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.verticalLayout_2.addItem(spacerItem2)
        
        # Remember password checkbox - renamed to match login_dialog.py
        self.remember_checkbox = CheckBox(self.widget)
        self.remember_checkbox.setChecked(True)
        self.verticalLayout_2.addWidget(self.remember_checkbox)
        
        # Small spacer
        spacerItem3 = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.verticalLayout_2.addItem(spacerItem3)
        
        # Login button - renamed to match login_dialog.py
        self.login_button = PrimaryPushButton(self.widget)
        self.login_button.setIcon(FIF.ACCEPT)
        self.login_button.clicked.connect(self.handle_login)  # Connect login function
        self.login_button.setFixedHeight(35)
        self.verticalLayout_2.addWidget(self.login_button)
        
        # Small spacer
        spacerItem4 = QSpacerItem(20, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.verticalLayout_2.addItem(spacerItem4)
        
        # Forgot password link
        self.pushButton_2 = HyperlinkButton(self.widget)
        self.verticalLayout_2.addWidget(self.pushButton_2)
        
        # Bottom spacer
        spacerItem5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(spacerItem5)
        
        # Add right panel to main layout
        self.horizontalLayout.addWidget(self.widget)
        
        # Set text content
        self.retranslateUi()
        
        # Connect signals - integrated from login_dialog.py
        self.connect_signals()
        
        # Focus on username field
        self.username_edit.setFocus()
        
    def retranslateUi(self):
        """Set text content for UI elements"""
        self.setWindowTitle("登录")
        self.label_5.setText("用户名")
        self.username_edit.setPlaceholderText("Username:")
        self.label_6.setText("密码")
        self.password_edit.setPlaceholderText("Password:")
        self.remember_checkbox.setText("记住密码")
        self.login_button.setText("登录")
        self.pushButton_2.setText("找回密码")
        
    def setupWindow(self):
        """Setup window properties and effects"""
        setThemeColor('#28afe9')
        
        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()
        
        self.label.setScaledContents(False)
        self.setWindowTitle('🌟 欢迎回来')
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1000, 650)  # Fixed size
        self.setMinimumSize(1000, 650)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Title bar styling
        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI';
                padding: 0 4px;
                color: white
            }
        """)
        
        # Center window
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def connect_signals(self):
        """Connect UI signals - integrated from login_dialog.py"""
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)
    
    def handle_login(self):
        """Handle login button click - integrated from login_dialog.py"""
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
        
        # Attempt authentication if user_manager is available
        if self.user_manager:
            if self.user_manager.authenticate(username, password):
                # Login successful
                self.show_success(f"欢迎, {username}!")
                self.login_successful.emit(username)
                QTimer.singleShot(1000, self.accept)  # Delay to show success message
            else:
                # Login failed
                self.show_error("用户名或密码错误")
                self.reset_login_button()
                self.password_edit.clear()
                self.password_edit.setFocus()
                self.login_failed.emit("用户名或密码错误")
        else:
            # No user manager, emit successful login for demo
            self.show_success(f"欢迎, {username}!")
            self.login_successful.emit(username)
            QTimer.singleShot(1000, self.accept)
    
    def show_error(self, message: str):
        """Show error message using InfoBar - integrated from login_dialog.py"""
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
        """Show success message using InfoBar - integrated from login_dialog.py"""
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
        """Reset login button state - integrated from login_dialog.py"""
        self.login_button.setEnabled(True)
        self.login_button.setText("登录")
    
    def get_credentials(self) -> tuple[str, str]:
        """Get entered credentials - integrated from login_dialog.py"""
        return self.username_edit.text().strip(), self.password_edit.text()
    
    def set_username(self, username: str):
        """Set username field - integrated from login_dialog.py"""
        self.username_edit.setText(username)
        self.password_edit.setFocus()
    
    def clear_form(self):
        """Clear the login form - integrated from login_dialog.py"""
        if not self.remember_checkbox.isChecked():
            self.username_edit.clear()
        self.password_edit.clear()
        self.reset_login_button()
    
    def accept(self):
        """Override accept method to work as dialog"""
        self.close()
    
    def reject(self):
        """Override reject method to work as dialog"""
        self.close()
    
    def exec(self):
        """Execute as modal dialog"""
        self.show()
        return True

    def resizeEvent(self, e):
        """Handle window resize event"""
        super().resizeEvent(e)
        # Since we're using gradient background, no need to handle image resizing
        
    def systemTitleBarRect(self, size):
        """Returns the system title bar rect, only works for macOS"""
        return QRect(size.width() - 75, 0, 75, size.height())
    
    def closeEvent(self, event):
        """Handle dialog close event - integrated from login_dialog.py"""
        self.clear_form()
        super().closeEvent(event)


class LoginController:
    """Controller for handling login logic - integrated from login_dialog.py"""
    
    def __init__(self, user_manager, parent=None):
        self.user_manager = user_manager
        self.parent = parent
        self.dialog = None
    
    def show_login_dialog(self) -> bool:
        """Show login dialog and handle authentication"""
        self.dialog = ModernLoginWindow(self.user_manager, self.parent)
        
        # Connect signals
        self.dialog.login_successful.connect(self.handle_login_success)
        self.dialog.login_failed.connect(self.handle_login_failure)
        
        # Load remembered username if any
        # TODO: Implement remember username functionality
        
        # Show dialog
        result = self.dialog.exec()
        
        if result:
            return True
        else:
            return False
    
    def handle_login_success(self, username: str):
        """Handle successful login"""
        pass  # Can be extended as needed
    
    def handle_login_failure(self, error_message: str):
        """Handle failed login"""
        pass  # Can be extended as needed



if __name__ == '__main__':
    # Enable DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    w = ModernLoginWindow()
    w.show()
    app.exec()
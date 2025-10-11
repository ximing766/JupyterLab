# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys
import os
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QTimer, QEventLoop
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QWidget, QSpacerItem, QSizePolicy, QDialog
from qfluentwidgets import (setThemeColor, setTheme, Theme, SplitTitleBar, isDarkTheme, 
                            BodyLabel, CheckBox, HyperlinkButton, LineEdit, PrimaryPushButton, InfoBar, InfoBarPosition,
                            FluentIcon as FIF)
from typing import Optional
def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

if isWin11():
    from qframelesswindow import AcrylicWindow as Window
    print('Use AcrylicWindow on Win11')
else:
    from qframelesswindow import FramelessWindow as Window
    print('Use FramelessWindow on non-Win11')

class LoginDialog(Window):
    login_successful = pyqtSignal(str)  # username
    login_failed = pyqtSignal(str)      # error message
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = None  # Will be set by LoginController
        self._event_loop = None
        self._dialog_result = None
        self.setupUI()
        self.setupWindow()
        
    def setupUI(self):
        """Create UI elements programmatically"""
        # Main horizontal layout
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        
        self.label = QLabel()
        self.label.setText("")
        background_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
            "assets", "PIC", "nature3.jpg").replace(os.sep, '/')
        
        self.label.setMinimumSize(QSize(650, 500))
        self.label.setMaximumSize(QSize(650, 500))
        
        if os.path.exists(background_path):
            background_pixmap = QPixmap(background_path)
            # 缩放图片以适应标签尺寸，保持宽高比
            scaled_pixmap = background_pixmap.scaled(
                650, 650, 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label.setScaledContents(False)  # 禁用自动缩放，我们手动控制
        else:
            # 如果图片文件不存在，使用渐变色背景
            self.label.setStyleSheet("""
                QLabel {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    border: none;
                }
            """)
        self.label.setScaledContents(False)
        self.horizontalLayout.addWidget(self.label)
        
        # Right panel widget
        self.widget = QWidget()
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setStyleSheet("background-color: rgba(95, 140, 170, 0.527);")
        
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
            # 创建圆形遮罩
            size = min(logo_pixmap.width(), logo_pixmap.height())
            mask = QPixmap(size, size)
            mask.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(Qt.GlobalColor.black)
            painter.drawEllipse(0, 0, size, size)
            painter.end()
            
            # 应用遮罩到原始图片
            rounded_pixmap = QPixmap(size, size)
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, size, size, logo_pixmap)
            painter.end()
            
            self.label_2.setPixmap(rounded_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
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
        
        # Username input - renamed to match login_dialog.py
        self.username_edit = LineEdit(self.widget)
        self.username_edit.setClearButtonEnabled(True)
        self.username_edit.setFixedHeight(40)
        self.username_edit.setText("admin")  # 设置默认值为 admin
        self.verticalLayout_2.addWidget(self.username_edit)
        
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
        
        self.horizontalLayout.addWidget(self.widget)
        
        self.retranslateUi()
        self.connect_signals()
        self.password_edit.setFocus()  # 设置密码输入框为默认选中
        
    def retranslateUi(self):
        self.username_edit.setPlaceholderText("Username:")
        self.password_edit.setPlaceholderText("Password:")
        self.remember_checkbox.setText("Remember me")
        self.login_button.setText("Login")
        self.pushButton_2.setText("Forgot password?")   
        
    def setupWindow(self):
        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()
        
        self.label.setScaledContents(False)
        # self.setWindowTitle('Login')
        self.setWindowOpacity(1)
        
        
        # 设置初始大小，但允许调整大小
        self.resize(800, 500)
        self.setMinimumSize(800, 500)
        
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def connect_signals(self):
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)
        self.login_button.clicked.connect(self.handle_login)
    
    def handle_login(self):
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
        
        self.login_button.setEnabled(False)
        self.login_button.setText("登录中...")
        
        self.login_successful.emit(username)
    
    def show_error(self, message: str):
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
        InfoBar.success(
            title="登录成功",
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def get_credentials(self) -> tuple[str, str]:
        return self.username_edit.text().strip(), self.password_edit.text()
    
    def clear_form(self):
        if not self.remember_checkbox.isChecked():
            self.username_edit.clear()
        self.password_edit.clear()
    
    def accept(self):
        self._dialog_result = True
        if self._event_loop:
            self._event_loop.quit()
        self.close()
    
    def exec(self):
        """Execute as modal dialog with custom event loop"""
        self._event_loop = QEventLoop()
        self._dialog_result = None
        self.show()
        
        # 阻塞等待用户操作
        if self._event_loop:
            self._event_loop.exec()
        
        return self._dialog_result if self._dialog_result is not None else False

    def resizeEvent(self, e):
        """Handle window resize event"""
        super().resizeEvent(e)
        
        # 当窗口大小改变时，重新调整背景图片
        new_width = self.width() - 300  # 减去右侧面板的宽度
        new_height = self.height()
        
        background_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "PIC", "nature3.jpg"
        ).replace(os.sep, '/')
        
        if os.path.exists(background_path) and new_width > 0 and new_height > 0:
            background_pixmap = QPixmap(background_path)
            # 重新缩放图片以适应新的窗口尺寸
            scaled_pixmap = background_pixmap.scaled(
                new_width, new_height, 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)
            self.label.setFixedSize(new_width, new_height)
    
    def closeEvent(self, event):
        """Handle dialog close event - integrated from login_dialog.py"""
        self.clear_form()
        super().closeEvent(event)


class LoginController:
    """Controller for handling login logic - integrated from login_dialog.py"""
    
    def __init__(self, user_manager, parent=None):
        self.user_manager = user_manager
        self.parent = parent
        self.login = None
        self._authenticated = False
        self._current_username = None
    
    def show_login_dialog(self) -> bool:
        """Show login dialog and handle authentication"""
        self.login = LoginDialog(self.parent)
        
        self.login.login_successful.connect(self.handle_login_attempt)
        
        # TODO: Implement remember username functionality
        
        result = self.login.exec()   # Block and wait for user login completion
        return result
    
    def handle_login_attempt(self, username: str):
        if not self.login:
            return
        
        username, password = self.login.get_credentials()
        
        if self.user_manager.authenticate(username, password):
            self.login.show_success(f"欢迎, {username}!")
            self.login.accept()
        else:
            self.login.show_error("用户名或密码错误")
            self.login.password_edit.clear()
            self.login.password_edit.setFocus()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.user_manager.is_authenticated()
    
    def get_current_user(self):
        """Get current authenticated user"""
        return self.user_manager.get_current_user()


if __name__ == '__main__':
    # Enable DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    w = LoginDialog()
    w.show()
    app.exec()
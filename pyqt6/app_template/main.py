#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.main_window import MainWindow
from user_mag import UserManager, LoginController

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Generic App Template")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Your Organization")
    
    # Initialize user manager
    user_manager = UserManager()
    
    # Check if user management is enabled
    if user_manager.is_user_management_enabled():
        # Show login dialog
        login_controller = LoginController(user_manager)
        if not login_controller.show_login_dialog():
            # User cancelled login or closed dialog
            sys.exit(0)
        
        if not login_controller.is_authenticated():
            # Authentication failed
            QMessageBox.critical(None, "登录失败", "用户认证失败，应用程序将退出。")
            sys.exit(1)

    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
    if not os.path.exists(logo_path):
        logo_path = None
    
    # Create main window with user manager
    window = MainWindow(
        app_name="Generic App Template",
        logo_path=logo_path,
        user_manager=user_manager
    )
    
    from pages.example_page import ExamplePage
    from user_mag import UserManagementPage
    from qfluentwidgets import FluentIcon as FIF
    
    # Add example page to application
    window.page_manager.register_page(
        page_id="example",
        title="示例页面",
        page_class=ExamplePage,
        icon=FIF.HOME,
        tooltip="展示如何创建自定义页面",
        order=1
    )
    
    # Add user management page (only visible to admins)
    window.page_manager.register_page(
        page_id="user_management",
        title="用户管理",
        page_class=UserManagementPage,
        icon=FIF.PEOPLE,
        tooltip="管理系统用户和权限",
        order=10,
        required_role="admin"  # XXX Only admin can access
    )
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
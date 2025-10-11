#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme
from qfluentwidgets import FluentIcon as FIF

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
    
    user_manager = UserManager()
    if user_manager.is_user_management_enabled():
        login_controller = LoginController(user_manager)
        if not login_controller.show_login_dialog():
            sys.exit(0)
        
        if not login_controller.is_authenticated():
            QMessageBox.critical(None, "登录失败", "用户认证失败，应用程序将退出。")
            sys.exit(1)

    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
    if not os.path.exists(logo_path):
        logo_path = None
    
    window = MainWindow(
        app_name="Generic App Template",
        logo_path=logo_path,
        user_manager=user_manager
    )
    
    from pages.example_page import ExamplePage
    from user_mag import UserManagementPage
    from qfluentwidgets import FluentIcon as FIF
    
    window.page_manager.register_page(
        page_id="example",
        title="示例页面",
        page_class=ExamplePage,
        icon=FIF.HOME,
        tooltip="展示如何创建自定义页面",
        order=1
    )
    
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
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.main_window import MainWindow

# ============================================================================
# 页面添加示例 - Example of Adding Custom Pages
# ============================================================================
# 
# 如果你想添加自定义页面到应用程序，请按照以下步骤：
# If you want to add custom pages to the application, follow these steps:
#
# 1. 创建页面类 (Create Page Class):
#    - 继承自 BasePage 类
#    - 实现 init_content() 方法来定义页面内容
#    - 可选择重写 on_activate() 和 on_deactivate() 方法
#
# 2. 注册页面 (Register Page):
#    - 使用 page_manager.register_page() 方法注册页面
#    - 或者使用 main_window.add_page() 方法直接添加到导航
#
# 示例代码 (Example Code):
# 
# from pages.example_page import ExamplePage
# from qfluentwidgets import FluentIcon as FIF
# 
# # 在 main() 函数中，创建 MainWindow 后添加：
# # Add after creating MainWindow in main() function:
# 
# # 方法1：使用页面管理器注册页面
# # Method 1: Register page using page manager
# window.page_manager.register_page(
#     page_id="example",
#     title="示例页面", 
#     page_class=ExamplePage,
#     icon=FIF.HOME,
#     tooltip="这是一个示例页面",
#     order=1  # 页面显示顺序
# )
#
# # 方法2：直接添加页面到导航
# # Method 2: Add page directly to navigation
# example_page = ExamplePage(window)
# window.add_page(
#     page_id="example",
#     page_widget=example_page,
#     icon=FIF.HOME,
#     title="示例页面"
# )
#
# 更多示例请参考 pages/example_page.py 文件
# For more examples, see pages/example_page.py file
# ============================================================================


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Generic App Template")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Your Organization")
    

    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
    if not os.path.exists(logo_path):
        logo_path = None
    
    window = MainWindow(
        app_name="Generic App Template",
        logo_path=logo_path
    )
    
    from pages.example_page import ExamplePage
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
    
    # ============================================================================
    
    # 注意：不要在这里调用 window.show()，因为 MainWindow 会在启动动画完成后自动显示
    # Note: Don't call window.show() here, MainWindow will show automatically after splash screen
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Application Example
演示如何基于通用模板创建自定义应用
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from qfluentwidgets import FluentIcon, PushButton, BodyLabel

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.main_window import MainWindow
from pages.base_page import BasePage


class WelcomePage(BasePage):
    """欢迎页面示例"""
    
    def __init__(self, parent=None):
        super().__init__("欢迎", FluentIcon.HOME, parent)
    
    def init_content(self):
        """初始化页面内容"""
        # 创建欢迎标题
        title = BodyLabel("欢迎使用自定义应用！")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        
        # 创建描述文本
        description = BodyLabel(
            "这是一个基于通用模板创建的自定义应用示例。\n"
            "您可以在这里添加自己的功能和页面。"
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin: 10px; line-height: 1.5;")
        
        # 创建操作按钮
        action_button = PushButton("开始使用")
        action_button.setFixedSize(120, 36)
        action_button.clicked.connect(self.on_action_clicked)
        
        # 添加到布局
        self.content_layout.addWidget(title)
        self.content_layout.addWidget(description)
        self.content_layout.addWidget(action_button)
        self.content_layout.addStretch()
    
    def on_action_clicked(self):
        """处理按钮点击事件"""
        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.success(
            title="成功",
            content="欢迎使用自定义应用！",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def on_page_activated(self):
        """页面激活时调用"""
        print("欢迎页面已激活")


class DataPage(BasePage):
    """数据页面示例"""
    
    def __init__(self, parent=None):
        super().__init__("数据", FluentIcon.CHART, parent)
    
    def init_content(self):
        """初始化页面内容"""
        # 页面标题
        title = BodyLabel("数据管理")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        
        # 数据显示区域
        data_label = BodyLabel("这里可以显示您的数据内容")
        data_label.setStyleSheet("margin: 10px; padding: 20px; background-color: rgba(0,0,0,0.05); border-radius: 8px;")
        
        # 刷新按钮
        refresh_button = PushButton("刷新数据")
        refresh_button.setIcon(FluentIcon.SYNC)
        refresh_button.setFixedSize(120, 36)
        refresh_button.clicked.connect(self.refresh_data)
        
        # 添加到布局
        self.content_layout.addWidget(title)
        self.content_layout.addWidget(data_label)
        self.content_layout.addWidget(refresh_button)
        self.content_layout.addStretch()
    
    def refresh_data(self):
        """刷新数据"""
        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.info(
            title="提示",
            content="数据已刷新",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1500,
            parent=self
        )


class CustomMainWindow(MainWindow):
    """自定义主窗口"""
    
    def __init__(self):
        # 设置自定义应用信息
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if not os.path.exists(logo_path):
            logo_path = None
        
        super().__init__(
            app_name="我的自定义应用",
            logo_path=logo_path
        )
    
    def create_default_pages(self):
        """创建默认页面（重写父类方法）"""
        # 注册自定义页面
        self.page_manager.register_page(
            "welcome",
            "欢迎",
            FluentIcon.HOME,
            WelcomePage
        )
        
        self.page_manager.register_page(
            "data",
            "数据",
            FluentIcon.CHART,
            DataPage
        )
        
        # 保留设置页面
        from pages.settings_page import SettingsPage
        self.page_manager.register_page(
            "settings",
            "设置",
            FluentIcon.SETTING,
            SettingsPage,
            config_manager=self.config_manager,
            theme_manager=self.theme_manager
        )


def main():
    """自定义应用入口"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("我的自定义应用")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("我的组织")
    
    # Create custom main window
    window = CustomMainWindow()
    
    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
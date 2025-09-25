# -*- coding: utf-8 -*-
"""
Example Page for Generic PyQt6 Application Template
Demonstrates how to create custom pages with proper theme support
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout
from PyQt6.QtCore import Qt
from qfluentwidgets import FluentIcon as FIF, PushButton, InfoBar, InfoBarPosition, isDarkTheme
from .base_page import BasePage


class ExamplePage(BasePage):
    """Example page demonstrating custom page creation with theme support"""
    
    def __init__(self, parent=None):
        super().__init__("example", parent)
    
    def init_content(self):
        """Initialize page content"""
        # Set layout margins and spacing for the existing layout
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Title
        title_label = QLabel("示例页面")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Description
        desc_label = QLabel("这是一个示例页面，展示如何创建自定义页面")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        
        # Text area for demonstration
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在这里输入一些文本...")
        self.text_edit.setMaximumHeight(150)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Example buttons
        self.info_btn = PushButton("显示信息", self)
        self.info_btn.setIcon(FIF.INFO)
        self.info_btn.clicked.connect(lambda: self.show_info("信息提示", "这是一个信息提示消息"))
        
        self.success_btn = PushButton("显示成功", self)
        self.success_btn.setIcon(FIF.COMPLETED)
        self.success_btn.clicked.connect(lambda: self.show_success("成功", "操作执行成功！"))
        
        self.warning_btn = PushButton("显示警告", self)
        self.warning_btn.setIcon(FIF.COMPLETED)
        self.warning_btn.clicked.connect(lambda: self.show_warning("警告", "这是一个警告消息"))
        
        self.clear_btn = PushButton("清空文本", self)
        self.clear_btn.setIcon(FIF.DELETE)
        self.clear_btn.clicked.connect(self.clear_text)
        
        # Add buttons to layout
        button_layout.addWidget(self.info_btn)
        button_layout.addWidget(self.success_btn)
        button_layout.addWidget(self.warning_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        
        # Store labels for theme updates
        self.title_label = title_label
        self.desc_label = desc_label
        
        # Apply initial theme
        self.apply_theme()
        
        # Add all widgets to the existing layout from BasePage
        self.layout.addWidget(title_label)
        self.layout.addWidget(desc_label)
        self.layout.addWidget(self.text_edit)
        self.layout.addLayout(button_layout)
        self.layout.addStretch()
    
    def apply_theme(self):
        """Apply theme-appropriate styles"""
        is_dark = isDarkTheme()
        
        # Define colors based on theme
        if is_dark:
            title_color = "#ffffff"
            desc_color = "#cccccc"
            features_color = "#ffffff"
            features_text_color = "#aaaaaa"
        else:
            title_color = "#333333"
            desc_color = "#666666"
            features_color = "#333333"
            features_text_color = "#555555"
    
    def showEvent(self, event):
        super().showEvent(event)
        self.apply_theme()
    
    def clear_text(self):
        self.text_edit.clear()
        self.show_success("已清空", "文本内容已清空")
    
    def on_activate(self):
        print(f"Example page activated")
    
    def on_deactivate(self):
        print(f"Example page deactivated")
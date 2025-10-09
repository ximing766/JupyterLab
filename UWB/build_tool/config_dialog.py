#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
                      UWB Build Tool - Configuration Dialog Module
==============================================================================

Description:
    Configuration dialog interface for managing UWB application build modes.
    Provides a user-friendly GUI for creating, editing, and deleting build
    configurations with associated macro definitions and settings.

Author:         Cardshare@QLL
Created:        2025
Version:        1.0.0

==============================================================================
"""

import sys
import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QLabel, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox, QFrame, QTextEdit,
    QSplitter
)
from PyQt6.QtCore import Qt, pyqtSlot, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette

class ConfigDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("构建模式配置")
        self.setModal(True)
        self.resize(700, 550)
        
        # 设置窗口样式
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "compile_tool.ico")))
        
        # 创建动画效果的属性
        self.button_animations = {}
        
        self.init_ui()
        self.load_modes()
        self.setup_connections()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 内容区域使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        left_panel = self.create_mode_list_panel()
        right_panel = self.create_mode_details_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter, 1)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("saveButton")
        self.save_button.setIcon(QIcon.fromTheme("document-save"))
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setIcon(QIcon.fromTheme("dialog-cancel"))
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def create_horizontal_line(self):
        """创建水平分隔线"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setObjectName("horizontalLine")
        return line
        
    def create_mode_list_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("leftPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(10)
        
        # 标题和按钮区域
        header_layout = QHBoxLayout()
        
        list_label = QLabel("模式列表")
        list_label.setObjectName("sectionLabel")
        header_layout.addWidget(list_label)
        
        header_layout.addStretch()
        
        # 添加按钮
        self.add_button = QPushButton()
        self.add_button.setObjectName("addButton")
        self.add_button.setToolTip("添加新模式")
        self.add_button.setText("添加")
        self.add_button.setFixedSize(70, 28)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_button_animation(self.add_button)
        header_layout.addWidget(self.add_button)
        
        # 删除按钮
        self.delete_button = QPushButton()
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setToolTip("删除选中的模式")
        self.delete_button.setText("删除")
        self.delete_button.setFixedSize(70, 28)
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_button_animation(self.delete_button)
        header_layout.addWidget(self.delete_button)
        
        layout.addLayout(header_layout)
        
        # 列表区域
        self.mode_list = QListWidget()
        self.mode_list.setObjectName("modeList")
        self.mode_list.setAlternatingRowColors(True)  # 交替行颜色
        self.mode_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.mode_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.mode_list)
        
        return panel
        
    def setup_button_animation(self, button):
        """为按钮设置悬停动画效果"""
        animation = QPropertyAnimation(button, b"minimumSize")
        animation.setDuration(100)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.button_animations[button] = animation
        
        # 连接鼠标进入和离开事件
        button.enterEvent = lambda e, b=button: self.button_enter_event(e, b)
        button.leaveEvent = lambda e, b=button: self.button_leave_event(e, b)
        
    def create_mode_details_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("rightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 标题区域
        details_label = QLabel("模式详情")
        details_label.setObjectName("sectionLabel")
        layout.addWidget(details_label)
        layout.addWidget(self.create_horizontal_line())
        layout.addSpacing(5)
        
        # 表单区域
        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(15)
        
        # 模式名称
        name_label = QLabel("模式名称:")
        name_label.setObjectName("fieldLabel")
        form_layout.addWidget(name_label, 0, 0)
        
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("nameEdit")
        self.name_edit.setPlaceholderText("输入模式的唯一标识符")
        form_layout.addWidget(self.name_edit, 0, 1)
        
        # 显示名称
        display_name_label = QLabel("显示名称:")
        display_name_label.setObjectName("fieldLabel")
        form_layout.addWidget(display_name_label, 1, 0)
        
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setObjectName("displayNameEdit")
        self.display_name_edit.setPlaceholderText("输入在界面上显示的名称")
        form_layout.addWidget(self.display_name_edit, 1, 1)
        
        layout.addLayout(form_layout)
        layout.addSpacing(10)
        
        # 宏定义区域
        macros_layout = QVBoxLayout()
        
        macros_label = QLabel("宏定义:")
        macros_label.setObjectName("sectionLabel")
        macros_layout.addWidget(macros_label)
        
        self.macros_edit = QTextEdit()
        self.macros_edit.setObjectName("macrosEdit")
        self.macros_edit.setPlaceholderText("格式: MACRO_NAME=value\n每行一个宏定义\n例如:\nAPP_TYPE=1\nDEBUG_LEVEL=3")
        
        # 设置等宽字体
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.macros_edit.setFont(font)
        
        macros_layout.addWidget(self.macros_edit)
        layout.addLayout(macros_layout, 1)  # 让宏定义编辑区域占据剩余空间
        
        return panel
        
    def button_enter_event(self, event, button):
        """按钮鼠标进入事件"""
        current_size = button.size()
        animation = self.button_animations[button]
        animation.setStartValue(QSize(current_size.width(), current_size.height()))
        animation.setEndValue(QSize(current_size.width() + 5, current_size.height() + 2))
        animation.start()
        
    def button_leave_event(self, event, button):
        """按钮鼠标离开事件"""
        current_size = button.size()
        animation = self.button_animations[button]
        animation.setStartValue(QSize(current_size.width(), current_size.height()))
        animation.setEndValue(QSize(current_size.width() - 5, current_size.height() - 2))
        animation.start()
        
    def setup_connections(self):
        self.mode_list.currentItemChanged.connect(self.on_mode_selected)
        self.add_button.clicked.connect(self.add_mode)
        self.delete_button.clicked.connect(self.delete_mode)
        self.save_button.clicked.connect(self.save_config)
        

        self.name_edit.textChanged.connect(self.on_data_changed)
        self.display_name_edit.textChanged.connect(self.on_data_changed)
        self.macros_edit.textChanged.connect(self.on_data_changed)
        self.cancel_button.clicked.connect(self.reject)
        

        self.name_edit.textChanged.connect(self.on_data_changed)
        self.macros_edit.textChanged.connect(self.on_data_changed)
        
    def load_modes(self):
        self.mode_list.clear()
        config = self.config_manager.get_config()
        
        for mode_name, mode_data in config.get('build_modes', {}).items():
            display_name = mode_data.get('display_name', mode_name)
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, mode_name)
            self.mode_list.addItem(item)
            
        if self.mode_list.count() > 0:
            self.mode_list.setCurrentRow(0)
            
    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_mode_selected(self, current, previous):
        if current is None:
            self.clear_details()
            return
            
        mode_name = current.data(Qt.ItemDataRole.UserRole)
        config = self.config_manager.get_config()
        mode_data = config.get('build_modes', {}).get(mode_name, {})
        
        self.name_edit.setText(mode_name)
        self.display_name_edit.setText(mode_data.get('display_name', ''))
        

        macros = mode_data.get('macros', {})
        macros_text = '\n'.join([f'{key}={value}' for key, value in macros.items()])
        self.macros_edit.setPlainText(macros_text)
        
    def clear_details(self):
        self.name_edit.clear()
        self.display_name_edit.clear()
        self.macros_edit.clear()
        
    @pyqtSlot()
    def add_mode(self):

        base_name = "new_mode"
        counter = 1
        config = self.config_manager.get_config()
        modes = config.get('build_modes', {})
        
        while f"{base_name}_{counter}" in modes:
            counter += 1
            
        new_mode_name = f"{base_name}_{counter}"
        
        item = QListWidgetItem(new_mode_name)
        item.setData(Qt.ItemDataRole.UserRole, new_mode_name)
        self.mode_list.addItem(item)
        self.mode_list.setCurrentItem(item)
        

        self.name_edit.setText(new_mode_name)
        self.display_name_edit.setText(new_mode_name)
        self.macros_edit.clear()
        
    @pyqtSlot()
    def delete_mode(self):
        current_item = self.mode_list.currentItem()
        if current_item is None:
            return
            
        mode_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除模式 '{current_item.text()}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            row = self.mode_list.row(current_item)
            self.mode_list.takeItem(row)
            

            if self.mode_list.count() > 0:
                new_row = min(row, self.mode_list.count() - 1)
                self.mode_list.setCurrentRow(new_row)
            else:
                self.clear_details()
                
    @pyqtSlot()
    def on_data_changed(self):

        current_item = self.mode_list.currentItem()
        if current_item:
            display_name = self.display_name_edit.text() or self.name_edit.text()
            if display_name:
                current_item.setText(display_name)
            
    @pyqtSlot()
    def save_config(self):
        try:
            config = self.config_manager.get_config()
            new_modes = {}
            

            for i in range(self.mode_list.count()):
                item = self.mode_list.item(i)
                mode_name = item.data(Qt.ItemDataRole.UserRole)
                

                if item == self.mode_list.currentItem():

                    if not self.name_edit.text().strip():
                        QMessageBox.warning(self, "错误", "模式名称不能为空")
                        return
                    

                    macros = {}
                    macros_text = self.macros_edit.toPlainText().strip()
                    if macros_text:
                        for line in macros_text.split('\n'):
                            line = line.strip()
                            if line and '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()

                                if value.isdigit():
                                    macros[key] = int(value)
                                elif value.replace('.', '', 1).isdigit():
                                    macros[key] = float(value)
                                else:
                                    macros[key] = value
                    
                    new_modes[self.name_edit.text().strip()] = {
                        'display_name': self.display_name_edit.text().strip(),
                        'macros': macros
                    }
                else:

                    existing_mode = config.get('build_modes', {}).get(mode_name, {})
                    if existing_mode:
                        new_modes[mode_name] = existing_mode
            

            config['build_modes'] = new_modes
            self.config_manager.config = config
            self.config_manager.save_config()
            
            QMessageBox.information(self, "成功", "配置已保存")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时出错: {str(e)}")
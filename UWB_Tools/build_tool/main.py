#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
                            UWB Build Tool - Main Module
==============================================================================

Description:
    Main GUI application for UWB project build management. Provides a user-friendly
    interface for compiling UWB applications with different configurations and modes.
    Supports both MCUXpresso IDE builds and make-based compilation workflows.

Author:         Cardshare@QLL
Created:        2025
Version:        1.0.0

==============================================================================
"""

import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QLabel, QComboBox, QPushButton, QTextEdit,
    QFileDialog, QMessageBox, QFrame, QSplitter, QDialog, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QEvent, QUrl
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QDesktopServices
import re

from config_manager import ConfigManager
from build_thread import BuildThread, HeaderGeneratorThread
from config_dialog import ConfigDialog

class UwbBuildTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.build_thread = None
        self.header_thread = None
        self.build_start_time = None
        self.build_timer = QTimer()
        self.build_timer.timeout.connect(self.update_build_time)
        
        # Display mode: True for compact, False for extended (default)
        self.is_compact_mode = False
        self.output_widget = None  # Will hold current output widget
        
        self.init_ui()
        self.load_config()
        self.setup_connections()
        
        # Show startup instructions
        self.show_startup_instructions()
    
    def init_ui(self):
        self.setWindowTitle("UWB BUILD TOOL")
        
        # Set window size based on display mode
        if self.is_compact_mode:
            self.setMinimumSize(450, 200)
            self.setMaximumSize(450, 200)
            self.resize(450, 200)
        else:
            self.setMinimumSize(650, 400)
            self.setMaximumSize(650, 400)
            self.resize(650, 400)
        
        # Set window to stay on top and handle transparency
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setWindowOpacity(1.0)
        
        # Install event filter to handle focus changes
        self.installEventFilter(self)
        
        icon_path = os.path.join(os.path.dirname(__file__), "compile_tool.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.load_stylesheet()
        self.setStyleSheet(self.styleSheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setAutoFillBackground(True)
        pal = central_widget.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        central_widget.setPalette(pal)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        config_widget = self.create_compact_config_area()
        main_layout.addWidget(config_widget)
        
        # Create output area based on display mode
        if self.is_compact_mode:
            self.output_widget = self.create_compact_output_area()
        else:
            self.output_widget = self.create_large_output_area()
        main_layout.addWidget(self.output_widget, 1)
    
    def create_compact_config_area(self) -> QWidget:
        config_widget = QWidget()
        config_widget.setObjectName("configArea")
        config_widget.setMaximumHeight(120)
        
        config_layout = QVBoxLayout(config_widget)
        config_layout.setSpacing(6)
        config_layout.setContentsMargins(8, 8, 8, 8)
        
        project_layout = QHBoxLayout()
        project_layout.setSpacing(6)
        
        project_label = QLabel("项目:")
        # project_label.setMinimumWidth(40)
        project_layout.addWidget(project_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setEditable(True)
        # self.project_combo.setMinimumWidth(350)
        self.project_combo.setSizePolicy(self.project_combo.sizePolicy().horizontalPolicy(), self.project_combo.sizePolicy().verticalPolicy())
        # Enable context menu for project combo
        self.project_combo.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        project_layout.addWidget(self.project_combo, 1)
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setObjectName("browseButton")
        self.browse_button.setFixedWidth(50)
        project_layout.addWidget(self.browse_button)
        
        # Add delete project button
        self.delete_project_button = QPushButton("删除")
        self.delete_project_button.setObjectName("deleteButton")
        self.delete_project_button.setFixedWidth(50)
        self.delete_project_button.setToolTip("删除当前选中的项目")
        project_layout.addWidget(self.delete_project_button)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedWidth(2)
        separator.setStyleSheet("QFrame { color: #cccccc; background-color: #cccccc; }")
        project_layout.addWidget(separator)
        
        # Add config and clear buttons after browse button
        self.config_button = QPushButton("配置")
        self.config_button.setObjectName("configButton")
        self.config_button.setFixedWidth(50)
        self.config_button.setFixedHeight(28)
        project_layout.addWidget(self.config_button)

        self.clear_output_button = QPushButton("清空")
        self.clear_output_button.setObjectName("clearButton")
        self.clear_output_button.setFixedWidth(50)
        self.clear_output_button.setFixedHeight(28)
        project_layout.addWidget(self.clear_output_button)
        
        config_layout.addLayout(project_layout)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)
        
        mode_label = QLabel("方案:")
        mode_label.setMinimumWidth(35)
        controls_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        # self.mode_combo.setMinimumWidth(200)
        # self.mode_combo.setFixedWidth(80)
        self.populate_mode_combo()
        controls_layout.addWidget(self.mode_combo)
        
        config_label = QLabel("模式:")
        config_label.setMinimumWidth(35)
        # controls_layout.addWidget(config_label)
        
        self.config_mode_combo = QComboBox()
        self.config_mode_combo.addItems(["Debug", "Release"])
        # self.config_mode_combo.setFixedWidth(80)
        controls_layout.addWidget(self.config_mode_combo)
        
        controls_layout.addStretch()
        
        self.generate_header_button = QPushButton(".h")
        self.generate_header_button.setObjectName("generateButton")
        self.generate_header_button.setFixedWidth(35)   
        self.generate_header_button.setFixedHeight(28)
        controls_layout.addWidget(self.generate_header_button)
        
        self.open_firmware_folder_button = QPushButton("📁")
        self.open_firmware_folder_button.setObjectName("openFirmwareFolderButton")
        self.open_firmware_folder_button.setFixedWidth(35)
        self.open_firmware_folder_button.setFixedHeight(28)
        self.open_firmware_folder_button.setToolTip("打开固件文件夹")
        controls_layout.addWidget(self.open_firmware_folder_button)
        
        self.make_button = QPushButton("➽")
        self.make_button.setObjectName("makeButton")
        self.make_button.setFixedWidth(35)
        self.make_button.setFixedHeight(28)
        controls_layout.addWidget(self.make_button)

        # Add display mode toggle button
        self.toggle_mode_button = QPushButton("⚡")
        self.toggle_mode_button.setObjectName("toggleModeButton")
        self.toggle_mode_button.setFixedWidth(35)
        self.toggle_mode_button.setFixedHeight(28)
        self.toggle_mode_button.setToolTip("切换显示模式")
        controls_layout.addWidget(self.toggle_mode_button)
        
        config_layout.addLayout(controls_layout)
        
        return config_widget
    
    def create_compact_output_area(self) -> QWidget:
        """创建紧凑的输出区域，显示单行输出框"""
        output_widget = QWidget()
        output_widget.setObjectName("compactOutputArea")
        
        output_layout = QVBoxLayout(output_widget)
        # output_layout.setSpacing(4)
        output_layout.setContentsMargins(1, 1, 1, 1)
        
        # Create single-line output text area
        self.output_text = QTextEdit()
        self.output_text.setObjectName("compactOutputText")
        # self.output_text.setMaximumHeight(60)  # Increased height for better visibility
        # self.output_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.output_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        return output_widget
    
    def populate_mode_combo(self):
        """填充模式下拉列表"""
        self.mode_combo.clear()
        build_modes = self.config_manager.get_build_modes()
        
        for mode_key, mode_config in build_modes.items():
            display_name = mode_config.get("display_name", mode_key)
            self.mode_combo.addItem(display_name, mode_key)
    
    def create_large_output_area(self) -> QWidget:
        """创建大的输出区域"""
        output_widget = QWidget()
        output_widget.setObjectName("outputArea")
        
        output_layout = QVBoxLayout(output_widget)
        output_layout.setSpacing(4)
        output_layout.setContentsMargins(8, 4, 8, 8)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        output_label = QLabel("编译输出")
        output_label.setObjectName("outputLabel")
        header_layout.addWidget(output_label)
        
        self.build_time_label = QLabel("")
        self.build_time_label.setObjectName("buildTimeLabel")
        header_layout.addWidget(self.build_time_label)
        
        header_layout.addStretch()
        
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)
        
        output_layout.addLayout(header_layout)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setObjectName("outputText")
        
        self.output_text.setAcceptRichText(True)
        
        font = self.output_text.font()
        font.setFamily("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.output_text.setFont(font)
        output_layout.addWidget(self.output_text, 1)
        
        return output_widget
    
    @pyqtSlot()
    def toggle_display_mode(self):
        """切换显示模式"""
        self.is_compact_mode = not self.is_compact_mode
        
        # Remove current output widget
        if self.output_widget:
            self.output_widget.setParent(None)
            self.output_widget.deleteLater()
        
        # Create new output widget based on new mode
        if self.is_compact_mode:
            self.output_widget = self.create_compact_output_area()
            # Update window size for compact mode
            self.setMinimumSize(450, 200)
            self.setMaximumSize(450, 200)
            self.resize(450, 200)
        else:
            self.output_widget = self.create_large_output_area()
            # Update window size for extended mode
            self.setMinimumSize(650, 400)
            self.setMaximumSize(650, 400)
            self.resize(650, 400)
        
        # Add new output widget to layout
        central_widget = self.centralWidget()
        main_layout = central_widget.layout()
        main_layout.addWidget(self.output_widget, 1)
        
        # Update button tooltip
        if self.is_compact_mode:
            self.toggle_mode_button.setToolTip("切换到扩展模式")
        else:
            self.toggle_mode_button.setToolTip("切换到紧凑模式")
        
        # Save the new display mode
        self.save_config()
    
    def load_stylesheet(self):
        try:
            style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
            if os.path.exists(style_path):
                with open(style_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                    self.setStyleSheet(stylesheet)
                    print(f"样式表加载成功: {style_path}")
            else:
                print(f"样式表文件不存在: {style_path}")
        except Exception as e:
            print(f"加载样式表失败: {e}")
    
    def setup_connections(self):
        self.browse_button.clicked.connect(self.browse_project)
        self.delete_project_button.clicked.connect(self.delete_current_project)
        self.generate_header_button.clicked.connect(self.generate_headers)
        self.open_firmware_folder_button.clicked.connect(self.open_firmware_folder)
        self.make_button.clicked.connect(self.start_make)
        self.clear_output_button.clicked.connect(self.clear_output)
        self.config_button.clicked.connect(self.open_config_dialog)
        self.toggle_mode_button.clicked.connect(self.toggle_display_mode)
        
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        self.config_mode_combo.currentTextChanged.connect(self.on_config_mode_changed)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
    
    def get_project_display_name(self, full_path: str) -> str:
        if not full_path:
            return ""
        return os.path.basename(full_path.rstrip(os.sep))
    
    def load_config(self):
        history = self.config_manager.get_project_history()
        self.project_combo.clear()
        for path in history:
            display_name = self.get_project_display_name(path)
            self.project_combo.addItem(display_name, path)
        
        last_project = self.config_manager.get_last_project()
        if last_project:
            for i in range(self.project_combo.count()):
                if self.project_combo.itemData(i) == last_project:
                    self.project_combo.setCurrentIndex(i)
                    break
        
        self.config_mode_combo.setCurrentText(self.config_manager.get_config_mode())
        
        selected_mode = self.config_manager.get_selected_mode()
        if selected_mode:
            for i in range(self.mode_combo.count()):
                if self.mode_combo.itemData(i) == selected_mode:
                    self.mode_combo.setCurrentIndex(i)
                    break
        
        # Load display mode
        display_mode = self.config_manager.get_display_mode()
        self.is_compact_mode = (display_mode == "compact")
        
        geometry = self.config_manager.get_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.config_manager.get_window_state()
        if state:
            self.restoreState(state)
    
    def save_config(self):
        # Save display mode
        display_mode = "compact" if self.is_compact_mode else "extended"
        self.config_manager.set_display_mode(display_mode)
        
        self.config_manager.set_window_geometry(self.saveGeometry())
        self.config_manager.set_window_state(self.saveState())
    
    @pyqtSlot()
    def browse_project(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            selected_dirs = dialog.selectedFiles()
            if selected_dirs:
                project_path = selected_dirs[0]
                display_name = self.get_project_display_name(project_path)
                self.project_combo.addItem(display_name, project_path)
                self.project_combo.setCurrentText(display_name)
                self.config_manager.set_last_project(project_path)
                self.update_project_history()
    
    def update_project_history(self):
        history = self.config_manager.get_project_history()
        current_data = self.project_combo.currentData()
        
        self.project_combo.clear()
        for path in history:
            display_name = self.get_project_display_name(path)
            self.project_combo.addItem(display_name, path)
        
        if current_data:
            for i in range(self.project_combo.count()):
                if self.project_combo.itemData(i) == current_data:
                    self.project_combo.setCurrentIndex(i)
                    break
    
    @pyqtSlot()
    def generate_headers(self):
        if self.header_thread and self.header_thread.isRunning():
            QMessageBox.warning(self, "警告", "头文件生成正在进行中，请稍候...")
            return
        
        project_path = self.project_combo.currentData()
        if not project_path:
            QMessageBox.warning(self, "警告", "请选择项目路径")
            return
        
        current_index = self.mode_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "警告", "请选择一个模式")
            return
            
        mode_key = self.mode_combo.itemData(current_index)
        mode_display_name = self.mode_combo.currentText()
        
        self.header_thread = HeaderGeneratorThread()
        self.header_thread.setup_generation_with_mode(mode_key, self.config_manager, project_path)
        
        self.header_thread.generation_finished.connect(self.on_header_generation_finished)
        
        self.generate_header_button.setEnabled(False)
        self.append_output(f"开始生成头文件: {mode_display_name}")
        self.append_output(f"目标路径: {self.header_thread.project_config_path}")
        self.header_thread.start()
    
    @pyqtSlot(bool, str)
    def on_header_generation_finished(self, success: bool, message: str):
        self.generate_header_button.setEnabled(True)
        
        if success:
            self.append_output(f"✓ {message}")
        else:
            self.append_output(f"✗ {message}")
            QMessageBox.critical(self, "错误", f"头文件生成失败:\n{message}")
    
    @pyqtSlot()
    def _validate_and_setup_build(self, setup_method):
        project_path = self.project_combo.currentData()
        if not project_path:
            QMessageBox.warning(self, "警告", "请选择项目路径")
            return False
        
        if not os.path.exists(project_path):
            QMessageBox.warning(self, "警告", f"项目路径不存在: {project_path}")
            return False
        
        if self.build_thread and self.build_thread.isRunning():
            QMessageBox.warning(self, "警告", "构建正在进行中，请稍候...")
            return False
        
        config_mode = self.config_mode_combo.currentText()
        
        self.build_thread = BuildThread()
        setup_method(self.build_thread, project_path, config_mode)
        
        self.build_thread.build_started.connect(self.on_build_started)
        self.build_thread.build_progress.connect(self.on_build_progress)
        self.build_thread.build_finished.connect(self.on_build_finished)
        
        self.build_thread.start()
    
    @pyqtSlot()
    def open_firmware_folder(self):
        project_path = self.project_combo.currentData()
        if not project_path:
            QMessageBox.warning(self, "警告", "请选择项目路径")
            return
        
        config_mode = self.config_mode_combo.currentText()
        firmware_dir = os.path.join(project_path, config_mode)
        
        if not os.path.exists(firmware_dir):
            QMessageBox.warning(self, "警告", f"固件目录不存在: {firmware_dir}")
            return
            
        # 使用系统默认文件管理器打开文件夹
        QDesktopServices.openUrl(QUrl.fromLocalFile(firmware_dir))
        self.append_output(f"已打开固件文件夹: {firmware_dir}")
    
    @pyqtSlot()
    def start_make(self):
        # Get current selected scheme name
        scheme_name = self.mode_combo.currentText() if self.mode_combo.currentIndex() >= 0 else None
        self._validate_and_setup_build(lambda thread, path, mode: thread.setup_make(path, mode, scheme_name))
    
    @pyqtSlot()
    def clear_output(self):
        if hasattr(self, 'output_text'):
            self.output_text.clear()
    
    @pyqtSlot()
    def open_config_dialog(self):
        dialog = ConfigDialog(self.config_manager, self)
        # 连接配置保存信号到刷新模式列表的方法
        dialog.config_saved.connect(self.populate_mode_combo)
        dialog.exec()
    
    @pyqtSlot()
    def delete_current_project(self):
        """删除当前选中的项目"""
        current_index = self.project_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "警告", "请选择要删除的项目")
            return
        
        current_text = self.project_combo.currentText()
        current_data = self.project_combo.currentData()
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除项目 '{current_text}' 吗？\n\n路径: {current_data}", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from config manager
            self.config_manager.remove_project_from_history(current_data)
            
            # Remove from combo box
            self.project_combo.removeItem(current_index)
            
            # If this was the last project, clear the last project setting
            if self.project_combo.count() == 0:
                self.config_manager.set_last_project("")
            else:
                # Set the first project as current if available
                if self.project_combo.count() > 0:
                    self.project_combo.setCurrentIndex(0)
                    new_current_data = self.project_combo.currentData()
                    if new_current_data:
                        self.config_manager.set_last_project(new_current_data)
    
    def show_startup_instructions(self):
        """显示应用启动时的操作说明"""
        instructions = """
   1. 新项目需先在 MCUXpresso 中创建并完成首次编译
   2. 新项目应选择到 project/RhodesV4_XXX 目录下
   3. 路径验证:
      • 若项目名称包含 "UTN" 或 "32"，必须存在路径: demos/SE051W/demo_transit/inc
      • 否则，需存在路径: demos/SR150_SE051W/demo_transit/inc
"""
        self.output_text.setPlainText(instructions)
        
        # Validate current project path if exists
        current_project = self.project_combo.currentText()

    
    @pyqtSlot()
    def on_build_started(self):
        self.make_button.setEnabled(False)
        self.generate_header_button.setEnabled(False)

        self.build_start_time = time.time()
        self.build_timer.start(100)
        
        # Update status labels based on current mode (only for extended mode)
        if not self.is_compact_mode and hasattr(self, 'status_label'):
            self.status_label.setText("构建中...")
            self.status_label.setObjectName("statusBuilding")
            self.status_label.setStyleSheet("")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
        
        self.append_output("=== 开始构建 ===")
    
    @pyqtSlot(str)
    def on_build_progress(self, message: str):
        self.append_output(message)
    
    @pyqtSlot(bool, str)
    def on_build_finished(self, success: bool, message: str):
        self.make_button.setEnabled(True)
        self.generate_header_button.setEnabled(True)

        self.build_timer.stop()
        if self.build_start_time:
            total_time = time.time() - self.build_start_time
            time_text = f"耗时: {total_time:.1f}s"
            
            if hasattr(self, 'build_time_label'):
                self.build_time_label.setText(time_text)

        if success:
            status_text = "构建成功"
            status_obj = "statusSuccess"
            self.append_output(f"✓ {message}")
        else:
            status_text = "构建失败"
            status_obj = "statusError"
            self.append_output(f"✗ {message}")
        
        # Update status labels based on current mode (only for extended mode)
        if not self.is_compact_mode and hasattr(self, 'status_label'):
            self.status_label.setText(status_text)
            self.status_label.setObjectName(status_obj)
            self.status_label.setStyleSheet("")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
    
    def update_build_time(self):
        if self.build_start_time:
            elapsed_time = time.time() - self.build_start_time
            time_text = f"耗时: {elapsed_time:.1f}s"
            
            if hasattr(self, 'build_time_label'):
                self.build_time_label.setText(time_text)
    
    def append_output(self, text: str):
        is_error = self.is_error_line(text)
        
        # Always append to output_text (both compact and extended modes)
        if hasattr(self, 'output_text'):
            if is_error:
                highlighted_text = f'<span style="background-color: #ffebee; color: #c62828; font-weight: bold; padding: 2px 4px; border-radius: 3px;">{text}</span>'
            else:
                highlighted_text = text
            
            self.output_text.append(highlighted_text)
            scrollbar = self.output_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # No additional status label updates needed in compact mode
    
    def is_error_line(self, text: str) -> bool:
        text_lower = text.lower()
        text_stripped = text.strip()
        
        error_keywords = ['error', 'failed', 'ERROR', 'Error']
        
        if any(keyword in text_lower for keyword in error_keywords):
            false_positives = [
                'no error',
                '0 errors',
                'without error',
                'ignore error',
                'suppress error'
            ]
            
            if not any(fp in text_lower for fp in false_positives):
                return True
        
        return False
    
    @pyqtSlot(str)
    def on_project_changed(self, text: str):
        current_data = self.project_combo.currentData()
        if current_data:
            self.config_manager.set_last_project(current_data)
    
    @pyqtSlot(str)
    def on_config_mode_changed(self, text: str):
        self.config_manager.set_config_mode(text)
    
    @pyqtSlot(str)
    def on_mode_changed(self, text: str):
        current_index = self.mode_combo.currentIndex()
        if current_index >= 0:
            mode_key = self.mode_combo.itemData(current_index)
            if mode_key:
                self.config_manager.set_selected_mode(mode_key)
    
    def eventFilter(self, obj, event):
        """Handle window focus events for transparency"""
        if obj == self:
            if event.type() == QEvent.Type.WindowActivate:
                # Window gained focus - make fully opaque
                self.setWindowOpacity(1.0)
            elif event.type() == QEvent.Type.WindowDeactivate:
                # Window lost focus - make semi-transparent
                self.setWindowOpacity(0.5)
        return super().eventFilter(obj, event)
    
    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, ctypes.byref(ctypes.c_int(0)), ctypes.sizeof(ctypes.c_int)
                )
            except Exception as e:
                print(f"Failed to set title bar theme: {e}")
    
    def closeEvent(self, event):
        if self.build_thread and self.build_thread.isRunning():
            self.build_thread.stop_build()
            self.build_thread.wait(3000)
        
        if self.header_thread and self.header_thread.isRunning():
            self.header_thread.terminate()
            self.header_thread.wait(1000)
        
        self.save_config()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("UWB Build Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("UWB Cardshare@QLL")
    app.setStyle("Windows")
    
    window = UwbBuildTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
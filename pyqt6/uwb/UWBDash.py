import sys
import os
import json
import re
import datetime
import time
import queue
import random
from pathlib import Path
import serial
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QUrl, QTimer,
    QDateTime, QThread, QMargins, QPointF,
    pyqtSignal, QObject, QPointF, QRectF,
    QEvent, QRect
)
from PyQt6.QtWidgets import *
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QTextCursor,
    QPixmap, QPainter, QIcon, QCursor,
    QClipboard, QIntValidator, QPen,
    QLinearGradient, QTextCharFormat,
    QTextOption, QTextDocument, QAction
)
from PyQt6.QtCharts import (
    QChart, QChartView,
    QLineSeries, QValueAxis
)
from qfluentwidgets import (
    MSFluentWindow, FluentWindow, SettingCardGroup, PushSettingCard, HyperlinkCard,
    FluentIcon as FIF, InfoBar, InfoBarPosition, setTheme, Theme, isDarkTheme, ComboBoxSettingCard,
    MessageBox, ScrollArea, SubtitleLabel, setFont, ComboBox, SpinBox, EditableComboBox,
    setTheme, Theme, qconfig, PushButton, CheckBox, PrimaryPushButton, BodyLabel, TableWidget,
    LineEdit, ToolButton, TextEdit, SwitchButton, CaptionLabel, DotInfoBadge, SearchLineEdit, ToolButton, PrimaryToolButton,
    PrimaryToolButton, CompactSpinBox, OptionsSettingCard, ConfigItem, OptionsConfigItem, OptionsValidator, QConfig,
    NavigationItemPosition, RoundMenu, ProgressBar, CardWidget, ProgressRing, IconWidget
)
from log import Logger
from position_view import PositionView
from splash_screen import SplashScreen
import csv
import math

APP_VERSION = "v2.3"
APP_NAME = "UWBDash"
BUILD_DATE = "2025年11月"
AUTHOR = "@Qilang²"


class SearchLineEditWithHistory(SearchLineEdit):
    """
    SearchLineEdit with history functionality
    """
    def __init__(self, parent=None, component_name="default"):
        super().__init__(parent)
        self.search_history = []
        self.max_history = 10
        self.parent_window = None  # Will be set by parent
        self.component_name = component_name  # Fixed component name for persistent storage
        self.setup_history_menu()
    
    def set_parent_window(self, parent_window):
        """Set parent window reference for config access"""
        self.parent_window = parent_window
        self.load_history_from_config()
    
    def load_history_from_config(self):
        """Load search history from config file"""
        if self.parent_window and hasattr(self.parent_window, 'config_path'):
            try:
                if self.parent_window.config_path.exists():
                    with open(self.parent_window.config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                    
                    # Get search history for this specific search component
                    search_config = config_data.get("search_history", {})
                    self.search_history = search_config.get(self.component_name, [])
                    
                    # Limit to max_history items
                    if len(self.search_history) > self.max_history:
                        self.search_history = self.search_history[:self.max_history]
            except Exception as e:
                print(f"Error loading search history: {e}")
    
    def save_history_to_config(self):
        """Save search history to config file"""
        if self.parent_window and hasattr(self.parent_window, 'config_path'):
            try:
                config_data = {}
                if self.parent_window.config_path.exists():
                    with open(self.parent_window.config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                
                # Ensure search_history section exists
                if "search_history" not in config_data:
                    config_data["search_history"] = {}
                
                # Save history for this specific component
                config_data["search_history"][self.component_name] = self.search_history
                
                # Write back to file
                with open(self.parent_window.config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving search history: {e}")
    
    def setup_history_menu(self):
        """Setup history menu for search history"""
        # Create a QAction for the history button with custom color
        from PyQt6.QtGui import QColor
        from qfluentwidgets import isDarkTheme
        
        # Set custom color for the history icon
        icon_color = QColor(100, 149, 237) if isDarkTheme() else QColor(70, 130, 180)  # Steel blue color
        self.history_action = QAction(FIF.HISTORY.icon(color=icon_color), "Search History", self)
        self.history_action.triggered.connect(self.show_history_menu)
        
        # Add the history action to the search line edit
        self.addAction(self.history_action, QLineEdit.ActionPosition.TrailingPosition)
    
    def show_history_menu(self):
        """Show history menu"""
        if not self.search_history:
            return
            
        menu = RoundMenu(parent=self)
        for history_item in self.search_history:
            # Create QAction properly for menu
            action = QAction(history_item, self)
            menu.addAction(action)
            action.triggered.connect(lambda checked, text=history_item: self.select_history_item(text))
        
        # Show menu at the bottom of the search line edit
        pos = self.mapToGlobal(QPoint(0, self.height()))
        menu.exec(pos)
    
    def select_history_item(self, text):
        """Select history item and trigger search"""
        self.setText(text)
        self.searchSignal.emit(text)
    
    def add_to_history(self, text):
        """Add search text to history"""
        if text and text not in self.search_history:
            self.search_history.insert(0, text)
            if len(self.search_history) > self.max_history:
                self.search_history = self.search_history[:self.max_history]
            # Save to config file
            self.save_history_to_config()
    
    def get_history(self):
        """Get search history"""
        return self.search_history.copy()
    
    def clear_history(self):
        """Clear search history"""
        self.search_history.clear()
        self.save_history_to_config()


def time_decorator(func):
    """
    函数执行时间decorator
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__} took {(end_time - start_time) * 1000:.4f} ms to execute.")
        return result
    return wrapper

class MainWindow(FluentWindow): # MSFluentWindow
    theme_changed = pyqtSignal()
    def __init__(self):
        super().__init__()
        icon_path = Path(__file__).parent / "logo.ico"
        app_path  = Path(os.getcwd())
        print(f"app_path: {app_path}")
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setWindowTitle(APP_NAME)

        self.current_theme               = ThemeManager.DARK_THEME
        self.config_path                 = Path(__file__).parent / "config.json"
        self._load_unified_config()
        self.logger                      = Logger(app_path=str(app_path))
        self.csv_title                   = ['Master', 'Slave', 'NLOS', 'RSSI', 'Speed','X', 'Y', 'Z', 'Auth', 'Trans']
        self.background_cache            = None         # 添加背景缓存
        self.last_window_size            = QSize()      # 添加窗口尺寸记录
        self.drag_pos                    = QPoint()
        self.red_length                  = 0  # 设置默认红区长度
        self.blue_length                 = 0  # 设置默认蓝区长度
        self.data_bits                   = 8
        self.parity                      = 'N'          # N-无校验
        self.stop_bits                   = 1
        self.current_csv_log_file_path   = None
        self.current_text_log_file_path  = None
        self.current_text_log_file_path2 = None
        self.current_ports               = []
        self.current_ports2              = []
        self.data_buffer                 = []
        self.data_buffer2                = []
        self.time_log_data = []  # Store time log entries
        self.last_time_log_count = 0  # Track data changes for refresh optimization
        self.load_historical_time_logs()  # Load existing time logs from buffer
        
        # Initialize output format states (True = STR, False = HEX)
        self.output_format_str = True   # COM1 output format (default: STR)
        self.output_format_str2 = True  # COM2 output format (default: STR)
        
        # Create config class and load configuration
        class AppConfig(QConfig):
            logLevelItem = OptionsConfigItem(
                "LogLevel", "level", "ALL",      # group, key, default
                OptionsValidator(["ALL", "MIN"])
            )
        
        self.config = AppConfig()
        # Use unified config for app settings
        self.current_log_level = self.app_config.get("LogLevel", {}).get("level", "ALL")
        print(f"current_log_level: {self.current_log_level}")
        
        # Sync QConfig with unified config file
        if self.current_log_level in ["ALL", "MIN"]:
            self.config.logLevelItem.value = self.current_log_level
            self.config.save()
        
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(250)

        self.display_timer2 = QTimer()
        self.display_timer2.timeout.connect(self.update_display2)
        self.display_timer2.start(250)

        self.log_worker = LogWorker(self.logger)
        self.log_worker.start()

        self.chart_thread = ChartUpdateThread()
        self.chart_thread.update_chart.connect(self.update_chart)
        self.chart_thread.start()

        # MYTODO 
        # self.highlight_config_timer = QTimer()
        # self.highlight_config_timer.timeout.connect(self.reload_highlight_config)
        # self.highlight_config_timer.start(10000)

        self.uwb_data = {
            'master'   : [],
            'slave'    : [],
            'nlos'     : [],
            'rssi'     : [],
            'speed'    : [],
        }

        self.init_ui()

    def update_port_button_style(self, button, is_connected):
        """Update SwitchButton state based on connection status"""
        try:
            # SwitchButton uses setChecked to show connection state
            button.setChecked(is_connected)
        except Exception as e:
            print(f"按钮状态设置错误: {e}")
            pass

    def paintEvent(self, event):
        if not self.background_cache or self.size() != self.last_window_size:
            size = self.size()
            if not self.background_image:
                print("Warning: No background image set.")
                if self.background_images:
                    # Use the first available image
                    for img in self.background_images:
                        test_path = Path(__file__).parent / img
                        if test_path.exists():
                            self.background_image = img
                            self._save_unified_config() # Save the fallback
                            print(f"Using first available image: {img}")
                            break
                    else:
                        # No images found in the list
                        print("Error: No background images available.")
                        return
                else:
                    print("Error: No background images available.")
                    return
            
            background_path = Path(__file__).parent / self.background_image
            if not background_path.exists(): # Fallback if current image is somehow invalid
                print(f"Warning: Background image {self.background_image} not found. Falling back to default.")
                if self.background_images:
                    for img in self.background_images:
                        test_path = Path(__file__).parent / img
                        if test_path.exists():
                            self.background_image = img
                            self._save_unified_config() # Save the fallback
                            background_path = test_path
                            print(f"Using fallback image: {img}")
                            break
                    else:
                        print("Error: No background images available.")
                        return
                else: # Ultimate fallback if list is also empty (should not happen with proper config loading)
                    print("Error: No background images available.")
                    return

            background = QPixmap(str(background_path))
            self.background_cache = background.scaled(
                size, 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.FastTransformation
            )
            self.last_window_size = size
            
        painter = QPainter(self) 
        # Use configurable background opacity (0.0~1.0)
        painter.setOpacity(getattr(self, 'background_opacity', 1.0))
        x = (self.width() - self.background_cache.width()) // 2
        y = (self.height() - self.background_cache.height()) // 2
        painter.drawPixmap(x, y, self.background_cache)
    
    def _load_unified_config(self):
        """Load all configuration from unified config.json file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                
                background_config = config_data.get("background", {})
                self.background_images = background_config.get("background_images", [])
                self.background_image = background_config.get("current_background_image", None)
                # Background opacity (0.0 ~ 1.0)
                self.background_opacity = float(background_config.get("opacity", 1.0))
                
                self.app_config = config_data.get("app", {})
                
                highlight_config = config_data.get("highlight", {})
                self.highlight_config = {k: QColor(v) for k, v in highlight_config.items()}
                
                self.quick_send_data = config_data.get("quick_send", {})
                
                # Validate background configuration
                if not self.background_images:
                    print("Warning: No background images found in config file.")
                    self.background_images = []
                    self.background_image = None
                    self.background_image_index = 0
                    return
                
                if self.background_image not in self.background_images:
                    print(f"Warning: Current background image '{self.background_image}' not found in images list. Using first image.")
                    self.background_image = self.background_images[0]
                    self._save_unified_config() # Save the corrected config
                
                # Initialize background_image_index based on the loaded current_background_image
                if self.background_image and self.background_image in self.background_images:
                    self.background_image_index = self.background_images.index(self.background_image)
                else:
                    self.background_image_index = 0
                    self.background_image = self.background_images[0] if self.background_images else None

            else:
                print("Warning: Config file not found. Please create a config.json file with all configurations.")
                self.background_images = []
                self.background_image = None
                self.background_image_index = 0
                self.app_config = {}
                self.highlight_config = {}
                self.quick_send_data = {}
                
        except Exception as e:
            print(f"Error loading unified config: {e}")
            self.background_images = []
            self.background_image = None
            self.background_image_index = 0
            self.app_config = {}
            self.highlight_config = {}
            self.quick_send_data = {}

    def _save_unified_config(self):
        print("保存配置函数被调用")
        config_data = {
            "background": {
                "background_images": self.background_images,
                "current_background_image": self.background_image,
                "opacity": getattr(self, 'background_opacity', 1.0)
            },
            "app": self.app_config,
            "highlight": {k: v.name() for k, v in self.highlight_config.items()},
            "quick_send": self.quick_send_data
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving unified config: {e}")

    def reload_highlight_config(self):
        self._save_unified_config()

    def init_ui(self):
        self.setMinimumSize(1000, 700)
        self.setGeometry(100, 100, 1000, 700)
    
        self.create_pages()
        
        self.load_quick_send_config()
        
        self.COM1_page.setObjectName("COM1")
        self.COM2_page.setObjectName("COM2") 
        self.Chart_page.setObjectName("CHART")
        # 实例化测试页面并赋值给self.testInterface
        self.testInterface = TestPage(self)
        self.testInterface.setObjectName("TEST")
        
        self.Settings_page = self.create_settings_page()
        
        # BM:NAV bar
        self.nav_com1 = self.addSubInterface(self.COM1_page, FIF.CONNECT, "COM1") 
        self.nav_com2 = self.addSubInterface(self.COM2_page, FIF.CONNECT, "COM2")
        self.addSubInterface(self.Chart_page, FIF.PIE_SINGLE, "CHART")
        # 使用已实例化的self.testInterface添加导航
        self.addSubInterface(self.testInterface, FIF.LABEL, "测试")
        self.addSubInterface(self.Settings_page, FIF.SETTING, "Setting", position=NavigationItemPosition.BOTTOM)

        self.navigationInterface.setExpandWidth(125)   # 展开时宽度设为 300 px

        self.apply_theme()
        setTheme(Theme.DARK)

        # 页面切换时动态重挂载图表到对应页面
        if hasattr(self, 'stackedWidget'):
            try:
                self.stackedWidget.currentChanged.connect(self.on_page_changed)
            except Exception:
                pass
    
    def mousePressEvent(self, event):
        if hasattr(self, 'stackedWidget') and self.stackedWidget:
            current_idx = self.stackedWidget.currentIndex()
            total_pages = self.stackedWidget.count()
            
            if event.button() == Qt.MouseButton.XButton1:  # Forward button (side button 1)
                new_idx = (current_idx + 1) % total_pages
                self.stackedWidget.setCurrentIndex(new_idx)
                # Update navigation if available
                if hasattr(self, 'navigationInterface'):
                    self.navigationInterface.setCurrentItem(self.stackedWidget.widget(new_idx).objectName())
                event.accept()
                return
            elif event.button() == Qt.MouseButton.XButton2:  # Back button (side button 2)  
                new_idx = (current_idx - 1 + total_pages) % total_pages
                self.stackedWidget.setCurrentIndex(new_idx)
                # Update navigation if available
                if hasattr(self, 'navigationInterface'):
                    self.navigationInterface.setCurrentItem(self.stackedWidget.widget(new_idx).objectName())
                event.accept()
                return
        
        super().mousePressEvent(event)

    def on_page_changed(self, index):
        """在Chart/测试页面之间移动图表，使其只在当前页面显示"""
        try:
            widget = self.stackedWidget.widget(index)
            if not widget:
                return
            name = widget.objectName()
            if name == "TEST":
                self.attach_chart_to_test_page()
            elif name == "CHART":
                self.attach_chart_to_chart_page()
        except Exception:
            pass

    def attach_chart_to_test_page(self):
        """将图表挂载到测试页面顶部容器"""
        try:
            if not hasattr(self, 'chart_widget') or not self.chart_widget:
                return
            if not hasattr(self, 'testInterface') or not hasattr(self.testInterface, 'chart_container_layout'):
                return
            # 解除旧父子关系后重新挂载
            self.chart_widget.setParent(None)
            self.testInterface.chart_container_layout.addWidget(self.chart_widget)
            self.chart_widget.show()
        except Exception:
            pass

    def attach_chart_to_chart_page(self):
        """Attach chart back to the Chart page (top splitter)."""
        try:
            if not hasattr(self, 'chart_widget') or not self.chart_widget:
                return
            if not hasattr(self, 'main_splitter') or not self.main_splitter:
                return
            self.chart_widget.setParent(None)
            # 确保位于splitter顶部
            self.main_splitter.insertWidget(0, self.chart_widget)
            self.chart_widget.show()
            # Re-apply stretch factors and sizes to avoid oversized chart
            try:
                # Smaller weight for chart, larger for bottom content
                self.main_splitter.setStretchFactor(0, 1)
                self.main_splitter.setStretchFactor(1, 3)
                # Set initial size ratio (relative values)
                self.main_splitter.setSizes([80, 220])
            except Exception:
                pass
        except Exception:
            pass
    
    def wheelEvent(self, event):
        # Get current interface from MSFluentWindow's stackedWidget
        current_widget = self.stackedWidget.currentWidget()
        delta = event.angleDelta().y()
        
        if current_widget == self.COM1_page:  # COM 1 page
            if delta > 0:  # Scroll up
                if hasattr(self, 'auto_scroll'):
                    self.auto_scroll.setChecked(True)  
            elif delta < 0 and hasattr(self, 'auto_scroll') and not self.auto_scroll.isChecked():
                # Optional: add additional scroll down logic
                pass
        elif current_widget == self.COM2_page:  # COM 2 page
            if delta > 0:  # Scroll up
                if hasattr(self, 'auto_scroll2'):
                    self.auto_scroll2.setChecked(True)  
            elif delta < 0 and hasattr(self, 'auto_scroll2') and not self.auto_scroll2.isChecked():
                # Optional: add additional scroll down logic
                pass
                
        super().wheelEvent(event)

    def eventFilter(self, obj, event):
        if (hasattr(self, 'serial_display') and hasattr(self, 'serial_display2') and 
            (obj == self.serial_display or obj == self.serial_display2) and 
            event.type() == QEvent.Type.Wheel):
            self.wheelEvent(event)
            return True # 阻止事件进一步传播
        return super().eventFilter(obj, event)
    
    def show_help_dialog(self):
        """Show help dialog with modern Fluent Design"""
        help_content = """
        <h2>🚀 UWB Dash 使用指南</h2>
        <h3>📊 数据监控</h3>
        <p>• <b>实时数据</b>：查看当前位置和距离信息</p>
        <p>• <b>图表显示</b>：观察位置变化趋势</p>
        <p>• <b>数据记录</b>：保存历史数据用于分析</p>
        <h3>🎯 定位功能</h3>
        <p>• 实时位置可视化</p>
        <p>• 支持多个用户同时在线监控</p>
        <h3>⚙️ 设置选项</h3>
        <p>• 主题切换：浅色/深色模式</p>
        <p>• 背景自定义：个性化界面</p>
        <h3>⌨️ 一些功能 </h3>
        <p>• <b>鼠标侧键</b>：快速切换页面（前进/后退）</p>
        <p>• <b>空格键</b>：暂停/恢复日志滚动</p>
        <p>• <b>Log Level过滤</b>：按日志级别筛选显示内容</p>
        <p>• <b>快捷发送</b>：预设常用指令，一键发送</p>
        
        """
        w = MessageBox(
            title='帮助支持',
            content=help_content,
            parent=self
        )
        w.yesButton.setText('🤣我知道了🤣')
        w.cancelButton.hide()
        w.exec()

    def show_about_dialog(self):
        """Show about dialog with modern Fluent Design"""
        about_content = f"""
        <div style="text-align: center; padding: 10px;">
            <div style=" border-radius: 8px; padding: 15px; margin: 10px 0;">
                <h3 style="color: #666; margin-bottom: 10px;">📋 版本信息</h3>
                <p style="margin: 5px 0;"><b>版本：</b>{APP_VERSION}</p>
                <p style="margin: 5px 0;"><b>构建日期：</b>{BUILD_DATE}</p>
                <p style="margin: 5px 0;"><b>Python版本：</b>3.8+</p>
            </div>
            
            <div style=" border-radius: 8px; padding: 15px; margin: 10px 0;">
                <h3 style="color: #666; margin-bottom: 10px;">👨‍💻 作者信息</h3>
                <p style="margin: 5px 0;"><b>CardShare@Qilang²</b></p>
            </div>
        </div>
        """
        
        w = MessageBox(
            title='UWBDASH',
            content=about_content,
            parent=self
        )
        w.yesButton.setText('确定')
        w.cancelButton.hide()
        w.exec()
    
    def open_highlight_config_dialog(self):
        dialog = HighlightConfigDialog(self.highlight_config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.highlight_config = dialog.get_config()
            # Save the updated highlight configuration to unified config file
            self._save_unified_config()
    
    def on_log_level_changed(self, level):
        """Handle log level change from settings page"""
        self.current_log_level = level.value
        # Update app config and save to file
        if not hasattr(self, 'app_config'):
            self.app_config = {}
        if "LogLevel" not in self.app_config:
            self.app_config["LogLevel"] = {}
        self.app_config["LogLevel"]["level"] = level.value
        self._save_unified_config()
        
        # Also update QConfig system
        self.config.logLevelItem.value = level.value
        self.config.save()
        
        InfoBar.info(
            title='Log等级已更改',
            content=f'Log等级为: {level.value}',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def should_filter_log_message(self, message):
        if self.current_log_level == 'ALL':
            return False  # Show all messages
        elif self.current_log_level == 'MIN':
            # MIN mode: exclude messages containing HALUCI and empty lines
            return 'HALUCI' in message.upper() or message.strip() == ''
        
        return False  # Default: don't filter

    def create_pages(self): # BM: Create Page
        # Store pages as instance variables for MSFluentWindow
        self.COM1_page  = self.create_COM_page()
        self.COM2_page  = self.create_COM_page2()
        self.Chart_page = self.create_Chart_page()
    
    def create_COM_page2(self): # BM: COM2 Page
        COM2_page = QWidget()
        layout = QVBoxLayout(COM2_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        top_widget = QWidget()
        top_widget.setStyleSheet("background: rgba(36, 42, 56, 0.2);")
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)
        
        self.port_combo2 = ComboBox()

        self.baud_combo2 = EditableComboBox()
        self.baud_combo2.setFixedWidth(110)
        self.baud_combo2.addItems(['9600', '115200', '230400', '460800', '3000000'])
        self.baud_combo2.setCurrentText('3000000')


        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 0, 10, 0)
        status_layout.setSpacing(10)

        # Switch button for serial port control
        self.toggle_btn2 = SwitchButton(self)
        self.toggle_btn2.setChecked(False)
        self.toggle_btn2.checkedChanged.connect(self.toggle_port2)
        self.toggle_btn2.setOffText("")
        self.toggle_btn2.setOnText("")

        line_top_1 = QFrame()
        line_top_1.setFrameShape(QFrame.Shape.VLine)
        line_top_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        # Output format toggle button (STR/HEX) for COM2
        self.output_format_btn2 = PushButton("STR")
        self.output_format_btn2.setFixedWidth(50)
        self.output_format_btn2.setToolTip("切换输出格式 (STR/HEX)")
        self.output_format_btn2.clicked.connect(self.toggle_output_format2)
        self.output_format_str2 = True  # True for STR, False for HEX

        self.max_lines_spin2 = CompactSpinBox()
        self.max_lines_spin2.setRange(50000, 300000)
        self.max_lines_spin2.setValue(150000)
        self.max_lines_spin2.setSingleStep(10000)
        self.max_lines_spin2.valueChanged.connect(self.update_max_lines2)
        self.current_lines_label2 = QLabel("Row: 0")
        self.current_lines_label2.setStyleSheet("background: transparent;")
        
        line_top_2 = QFrame()
        line_top_2.setFrameShape(QFrame.Shape.VLine)
        line_top_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        self.Address_label_2 = QLabel("0000  -")
        self.Address_label_2.setStyleSheet("background: transparent;")
        self.Transaction_time_label_2 = QLabel("0000ms")
        self.Transaction_time_label_2.setStyleSheet("background: transparent;")

        line_top_3 = QFrame()
        line_top_3.setFrameShape(QFrame.Shape.VLine)
        line_top_3.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_3.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")
        
        self.search_line2 = SearchLineEditWithHistory(component_name="com2_search")
        self.search_line2.set_parent_window(self)  # Set parent window reference
        self.search_line2.setPlaceholderText("Search")
        self.search_line2.setFixedWidth(300)
        self.search_line2.searchSignal.connect(self.on_search_triggered2)
        self.search_line2.clearSignal.connect(self.on_search_cleared2)
        self.search_line2.returnPressed.connect(self.on_search_triggered2)
        
        # Add previous and next search buttons for COM2
        self.search_prev_btn2 = ToolButton(FIF.DOWN)
        self.search_prev_btn2.setFixedSize(30, 30)
        self.search_prev_btn2.clicked.connect(self.search_previous2)
        self.search_prev_btn2.setToolTip("Previous match")
        
        self.search_next_btn2 = ToolButton(FIF.DOWN)
        self.search_next_btn2.setFixedSize(30, 30)
        self.search_next_btn2.clicked.connect(self.search_next2)
        self.search_next_btn2.setToolTip("Next match")
        
        # Search result count label for COM2
        self.search_count_label2 = BodyLabel("0/0")
        self.search_count_label2.setStyleSheet("background: transparent;")
        self.search_count_label2.setMinimumWidth(40)
        
        top_layout.addWidget(self.port_combo2)
        top_layout.addWidget(self.baud_combo2)
        top_layout.addWidget(self.toggle_btn2)
        # top_layout.addSpacing(10)
        top_layout.addWidget(line_top_1)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.output_format_btn2)
        top_layout.addWidget(self.max_lines_spin2)
        top_layout.addWidget(self.current_lines_label2)
        top_layout.addSpacing(10)
        top_layout.addWidget(line_top_2)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.Address_label_2)
        top_layout.addWidget(self.Transaction_time_label_2)
        top_layout.addSpacing(10)
        top_layout.addWidget(line_top_3)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.search_line2)
        top_layout.addWidget(self.search_prev_btn2)
        top_layout.addWidget(self.search_next_btn2)
        top_layout.addWidget(self.search_count_label2)
        top_layout.addStretch()

        layout.addWidget(top_widget)

        self.splitter2 = QSplitter(Qt.Orientation.Vertical)
        self.create_display_area2(self.splitter2)
    
        bottom_widget = QWidget()
        # bottom_widget.setStyleSheet("background: rgba(36, 42, 56, 0.8);")
        bottom_layout = QVBoxLayout(bottom_widget)
        
        # Create horizontal layout for the main controls
        controls_layout = QHBoxLayout()
        
        self.clear_btn2 = ToolButton(FIF.DELETE)
        self.clear_btn2.setFixedWidth(50)
        self.clear_btn2.clicked.connect(self.serial_display2.clear)

        self.timestamp2 = CheckBox("🕒")
        self.timestamp2.setStyleSheet("background: transparent")
        self.timestamp2.setObjectName("timestamp")
        self.timestamp2.setToolTip("每行前添加时间戳")
        self.timestamp2.setChecked(True)
        self.auto_scroll2 = CheckBox("📌")
        self.auto_scroll2.setStyleSheet("background: transparent")
        self.auto_scroll2.setObjectName("autoScroll")
        self.auto_scroll2.setChecked(False)
        self.auto_scroll2.setToolTip("锁定滚动条到底部")

        # COM2 sending controls
        self.send_judge2 = CheckBox("HEX")
        self.send_judge2.setStyleSheet("background: transparent")
        self.send_judge2.setChecked(True)
        self.send_judge2.clicked.connect(self.toggle_send_mode2)

        self.send_line_edit2 = LineEdit()
        self.send_line_edit2.setPlaceholderText("e.g., AA BB or 0xAA 0xBB or String")
        self.send_line_edit2.setClearButtonEnabled(True)

        # Large input box for expanded mode (initially hidden)
        self.large_send_edit2 = TextEdit()
        self.large_send_edit2.setPlaceholderText("e.g., AA BB or 0xAA 0xBB or String")
        self.large_send_edit2.setMaximumHeight(300)
        # 不使用show()，通过布局可见性控制显示

        self.send_btn2 = ToolButton(FIF.SEND)
        self.send_btn2.setFixedWidth(60)
        self.send_btn2.clicked.connect(self.com2_send_data)

        # Quick send components for COM2
        self.quick_send_combo2 = ComboBox()
        self.quick_send_combo2.setFixedWidth(120)
        self.quick_send_combo2.setPlaceholderText("Quick Send")
        self.quick_send_combo2.currentTextChanged.connect(self.on_quick_send_selected2)
        
        self.quick_config_btn2 = ToolButton(FIF.SETTING)
        self.quick_config_btn2.setFixedSize(30, 30)
        self.quick_config_btn2.setToolTip("Configure Quick Send")
        self.quick_config_btn2.clicked.connect(self.show_quick_send_config)

        # Expand/collapse button for COM2
        self.expand_btn2 = ToolButton(FIF.DOWN)
        self.expand_btn2.setFixedSize(30, 30)
        self.expand_btn2.clicked.connect(self.toggle_input_size2)
        self.is_expanded2 = True

        line_bottom_1 = QFrame()
        line_bottom_1.setFrameShape(QFrame.Shape.VLine)
        line_bottom_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        line_bottom_2 = QFrame()
        line_bottom_2.setFrameShape(QFrame.Shape.VLine)
        line_bottom_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        self.open_text_log_file_btn2 = PushButton("📄TEXT")
        self.open_text_log_file_btn2.setFixedWidth(75)
        self.open_text_log_file_btn2.setToolTip("打开当前Text日志文件")
        self.open_text_log_file_btn2.clicked.connect(self.open_current_text_log_file2)
        self.open_text_log_file_btn2.setEnabled(False)

        self.open_log_folder_btn2 = PushButton("📁")
        self.open_log_folder_btn2.setFixedWidth(50)
        self.open_log_folder_btn2.setToolTip("打开日志文件夹")
        self.open_log_folder_btn2.clicked.connect(self.open_log_folder)

        controls_layout.addWidget(self.clear_btn2)
        controls_layout.addWidget(self.open_text_log_file_btn2)
        controls_layout.addWidget(self.open_log_folder_btn2)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(line_bottom_1)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(self.timestamp2)
        controls_layout.addWidget(self.auto_scroll2)
        controls_layout.addWidget(self.send_judge2)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(line_bottom_2)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(self.send_line_edit2)
        controls_layout.addWidget(self.send_btn2)
        controls_layout.addWidget(self.quick_send_combo2)
        controls_layout.addWidget(self.quick_config_btn2)
        controls_layout.addStretch()
        controls_layout.addWidget(self.expand_btn2)
        
        bottom_layout.addWidget(self.large_send_edit2)
        bottom_layout.addLayout(controls_layout)
        
        self.splitter2.addWidget(bottom_widget)
        self.splitter2.setSizes([2000, 500])  
        
        layout.addWidget(self.splitter2)
        
        self.port_scan_timer2 = QTimer()
        self.port_scan_timer2.timeout.connect(self.refresh_ports2)
        self.port_scan_timer2.start(1000)
        self.refresh_ports2()
        
        return COM2_page
    
    def update_max_lines2(self, value):
        self.serial_display2.document().setMaximumBlockCount(value)
    
    def update_current_lines2(self):
        current_count = self.serial_display2.document().blockCount()
        self.current_lines_label2.setText(f"Row: {current_count}")
        max_lines = self.serial_display2.document().maximumBlockCount()
        if current_count >= max_lines:
            self.serial_display2.clear()

    def create_display_area2(self, layout):
        self.serial_display2 = QTextEdit()
        self.serial_display2.setReadOnly(True)
        self.serial_display2.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # 确保能接收键盘事件
        self.serial_display2.installEventFilter(self) # 安装事件过滤器
        self.serial_display2.document().setMaximumBlockCount(150000)  # 限制最大行数
        # self.serial_display2.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # 自动换行
        # self.serial_display2.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)  # 允许在任何位置换行
        self.serial_display2.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 不自动换行
        
        self.serial_display2.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_display2.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        font = QFont("Microsoft YaHei", 12)
        self.serial_display2.setFont(font)
        
        self.serial_display2.setStyleSheet("""
            QTextEdit {
                background-color          : rgba(36, 42, 56, 0.2);
                border                    : 1.5px solid #3a4a5c;
                border-radius             : 1px;
                padding                   : 12px;
                color                     : {theme['text']};
                font-size                 : 15px;
                font-family               : 'JetBrains Mono', 'Consolas', 'Microsoft YaHei', monospace;
                selection-background-color: #088bef;
                selection-color           : #ffffff;

            }
            QTextEdit:focus {
                border          : 1.5px solid #477faa;
                background-color: rgba(27, 32, 44, 0.99);
            }
            
        """)
        
        self.serial_display2.document().blockCountChanged.connect(self.update_current_lines2)
        self.update_current_lines2()

        self.serial_display2.keyPressEvent = self.on_display_key_press2
        
        layout.addWidget(self.serial_display2)
    
    
    def on_display_key_press2(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.auto_scroll2.setChecked(not self.auto_scroll2.isChecked())
        QTextEdit.keyPressEvent(self.serial_display2, event)
    
    def refresh_ports2(self):
        import serial.tools.list_ports
        current_port = self.port_combo2.currentText() if self.port_combo2.count() > 0 else ""
        ports = list(serial.tools.list_ports.comports())
        available_ports = [port.device for port in ports]
        if set(available_ports) != set(self.current_ports2):
            self.port_combo2.clear()
            for port in ports:
                self.port_combo2.addItem(port.device)
            if current_port and self.port_combo2.findText(current_port) >= 0:
                self.port_combo2.setCurrentText(current_port)
            self.current_ports2 = available_ports
    
    def toggle_port2(self):
        if self.toggle_btn2.isChecked():
            try:
                port = self.port_combo2.currentText()
                if not port:
                    raise Exception("请选择串口")
                    
                baud = int(self.baud_combo2.currentText())
                self.serial2 = serial.Serial(
                    port     = port,
                    baudrate = baud,
                    bytesize = self.data_bits,
                    parity   = self.parity,
                    stopbits = self.stop_bits,
                    timeout  = 0.1
                )
                
                if not self.serial2.is_open:
                    self.serial2.open()
                
                self.serial_thread2 = SerialReadThread(self.serial2)
                self.serial_thread2.data_received.connect(self.handle_serial_2_data)
                self.serial_thread2.connection_lost.connect(self.handle_serial2_connection_lost)
                # 根据当前输出格式设置是否按换行分割（STR: True, HEX: False）
                try:
                    self.serial_thread2.set_split_on_newline(self.output_format_str2)
                except Exception:
                    pass
                self.serial_thread2.start()
                
                current_time      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                port_name         = self.port_combo2.currentText().replace(":", "_")
                text_log_filename = f"[{port_name}] {current_time}.log"

                # 确保 logger 实例及其目录属性存在
                if hasattr(self.logger, 'text_log_dir'):
                    self.current_text_log_file_path2 = os.path.join(self.logger.text_log_dir, text_log_filename)
                    self.logger.create_logger("UwbLog2", text_log_filename, "text") # 创建 Text 日志
                    self.open_text_log_file_btn2.setEnabled(True)
                else:
                    # 如果无法获取 log_dir，则禁用按钮并打印警告
                    print("警告: Logger 对象缺少 csv_log_dir 或 text_log_dir 属性，'打开日志文件'功能可能不可用。")
                    self.current_text_log_file_path2 = None
                
                # Update button style to connected state
                self.update_port_button_style(self.toggle_btn2, True)
                
            except Exception as e:
                error_msg = f"打开串口失败: {str(e)}\n"
                error_msg += f"串口: {self.port_combo2.currentText()}\n"
                error_msg += f"波特率: {self.baud_combo2.currentText()}\n"
                error_msg += f"异常类型: {type(e).__name__}"
                print(f"COM2串口异常详情: {error_msg}")  # 添加控制台输出用于调试
                QMessageBox.warning(self, "错误", error_msg)
                
                # 确保在异常时清理可能已创建的资源
                try:
                    if hasattr(self, 'serial_thread2') and self.serial_thread2 is not None:
                        self.serial_thread2.stop()
                        self.serial_thread2 = None
                    if hasattr(self, 'serial2') and self.serial2 is not None:
                        self.serial2.close()
                        self.serial2 = None
                except:
                    pass  # 忽略清理时的异常
                
                self.toggle_btn2.setChecked(False)  # Reset switch state on error
                self.update_port_button_style(self.toggle_btn2, False)  # Reset button style
        else:
            try:
                if hasattr(self, 'serial_thread2') and self.serial_thread2 is not None:
                    self.serial_thread2.stop()
                    self.serial_thread2 = None

                if hasattr(self, 'serial2') and self.serial2 is not None:
                    self.serial2.close()
                    self.serial2 = None
                
                # Update button style to disconnected state
                self.update_port_button_style(self.toggle_btn2, False)
                
            except Exception as e:
                print(f"关闭串口2时发生错误: {str(e)}")
                # 即使出错也要重置状态
                if hasattr(self, 'serial_thread2'):
                    self.serial_thread2 = None
                if hasattr(self, 'serial2'):
                    self.serial2 = None
                # Update button style to disconnected state
                self.update_port_button_style(self.toggle_btn2, False)
    
    def handle_serial_2_data(self, data):
        try:
            # Apply format conversion based on current setting
            if hasattr(self, 'output_format_str2') and not self.output_format_str2:
                # HEX format - format data and add line break at the end
                formatted_data = self.format_data_for_display(data, is_str_format=False)
                text = formatted_data  # Don't add \n here, let format_data_for_display handle it
            else:
                # STR format (default)
                text = data.decode('utf-8', errors='ignore')
                
            self.log_worker.add_log_task("UwbLog2", "info", text.strip())
            text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
            self.data_buffer2.append(text)

            # Only process special patterns in STR mode
            if not hasattr(self, 'output_format_str2') or self.output_format_str2:
                if "@@@ Time of Write Card End" in text:
                    #"@@@ Time of Write Card End     = 00:14:520  │ 80D7 │  710 ms"
                    match = re.search(r"│\s*([0-9A-Fa-f]+)\s*│\s*(\d+)\s*ms", text)
                    if match:
                        address = match.group(1)
                        transaction_time = match.group(2)
                        
                        if hasattr(self, 'Address_label_2') and self.Address_label_2 is not None:
                            self.Address_label_2.setText(f"{address}  -")
                        
                        if hasattr(self, 'Transaction_time_label_2') and self.Transaction_time_label_2 is not None:
                            self.Transaction_time_label_2.setText(f"{transaction_time}ms")

        except Exception as e:
            print(f"数据处理错误 (on_data_received): {str(e)}")

    def handle_serial2_connection_lost(self, error_msg):
        """Handle serial connection lost for COM2"""
        try:
            # Update UI status to indicate disconnection
            # self.toggle_btn2.setText("打开串口")
            
            # Clean up serial resources
            if hasattr(self, 'serial_thread2'):
                self.serial_thread2.stop()
                self.serial_thread2 = None
            if hasattr(self, 'serial2'):
                self.serial2.close()
                self.serial2 = None
        except Exception as e:
            print(f"处理串口2连接丢失错误: {str(e)}")

    def create_COM_page(self):   # BM : COM1 PAGE
        COM1_page = QWidget()
        layout = QVBoxLayout(COM1_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        top_widget = QWidget()
        top_widget.setStyleSheet("background: rgba(36, 42, 56, 0.2);")
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)
        
        self.port_combo = ComboBox()

        self.baud_combo = EditableComboBox()
        self.baud_combo.setFixedWidth(110)
        self.baud_combo.addItems(['9600', '115200', '230400', '460800', '3000000'])
        self.baud_combo.setCurrentText('3000000')

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 0, 10, 0)
        status_layout.setSpacing(10)

        # Switch button for serial port control
        self.toggle_btn = SwitchButton(self)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.checkedChanged.connect(self.toggle_port)
        self.toggle_btn.setOffText("")
        self.toggle_btn.setOnText("")


        line_top_1 = QFrame()
        line_top_1.setFrameShape(QFrame.Shape.VLine)
        line_top_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        # Output format toggle button (STR/HEX)
        self.output_format_btn = PushButton("STR")
        self.output_format_btn.setFixedWidth(50)
        self.output_format_btn.setToolTip("切换输出格式 (STR/HEX)")
        self.output_format_btn.clicked.connect(self.toggle_output_format)
        self.output_format_str = True  # True for STR, False for HEX
        
        self.max_lines_spin = CompactSpinBox()
        self.max_lines_spin.setRange(50000, 300000)
        self.max_lines_spin.setValue(150000)
        self.max_lines_spin.setSingleStep(10000)
        self.max_lines_spin.valueChanged.connect(self.update_max_lines)
        self.current_lines_label = QLabel("Row: 0")
        self.current_lines_label.setStyleSheet("background: transparent;")

        line_top_2 = QFrame()
        line_top_2.setFrameShape(QFrame.Shape.VLine)
        line_top_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        self.Address_label = QLabel("0000  -")
        self.Address_label.setStyleSheet("background: transparent;")
        self.Transaction_time_label = QLabel("0000ms")
        self.Transaction_time_label.setStyleSheet("background: transparent;")
        
        line_top_3 = QFrame()
        line_top_3.setFrameShape(QFrame.Shape.VLine)
        line_top_3.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_3.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")
        
        self.time_log_btn = PushButton("❃")
        self.time_log_btn.setFixedWidth(35)
        self.time_log_btn.setToolTip("显示包含时间信息的日志")
        self.time_log_btn.clicked.connect(self.show_time_log_dialog) # BM: Time Log 
        
        self.protocol_parse_btn = PushButton("⚡")
        self.protocol_parse_btn.setFixedWidth(35)
        self.protocol_parse_btn.setToolTip("协议解析工具")
        self.protocol_parse_btn.clicked.connect(self.show_protocol_parse_dialog) # BM: Protocol Parse

        line_top_4 = QFrame()
        line_top_4.setFrameShape(QFrame.Shape.VLine)
        line_top_4.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_4.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        self.search_line = SearchLineEditWithHistory(component_name="com1_search")
        self.search_line.set_parent_window(self)  # Set parent window reference
        self.search_line.setPlaceholderText("Search")
        self.search_line.setFixedWidth(300)
        self.search_line.searchSignal.connect(self.on_search_triggered)
        self.search_line.clearSignal.connect(self.on_search_cleared)
        self.search_line.returnPressed.connect(self.on_search_triggered)
        
        # Add previous and next search buttons
        self.search_prev_btn = ToolButton(FIF.UP)
        self.search_prev_btn.setFixedSize(30, 30)
        self.search_prev_btn.clicked.connect(self.search_previous)
        self.search_prev_btn.setToolTip("Previous match")
        
        self.search_next_btn = ToolButton(FIF.DOWN)
        self.search_next_btn.setFixedSize(30, 30)
        self.search_next_btn.clicked.connect(self.search_next)
        self.search_next_btn.setToolTip("Next match")
        
        self.search_count_label = BodyLabel("0/0")
        self.search_count_label.setStyleSheet("background: transparent;")
        self.search_count_label.setMinimumWidth(40)

        # BM:仪表开关
        line_top_5 = QFrame()
        line_top_5.setFrameShape(QFrame.Shape.VLine)
        line_top_5.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_5.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")
        
        self.status_panel_toggle_btn = ToolButton(FIF.HIDE)
        self.status_panel_toggle_btn.setFixedWidth(35)
        self.status_panel_toggle_btn.setToolTip("隐藏状态监控面板")
        self.status_panel_toggle_btn.clicked.connect(self.toggle_status_panel)
        self.status_panel_visible = True  # 默认显示

        top_layout.addWidget(self.port_combo)
        top_layout.addWidget(self.baud_combo)
        top_layout.addWidget(self.toggle_btn)
        # top_layout.addSpacing(10)
        top_layout.addWidget(line_top_1)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.output_format_btn)
        top_layout.addWidget(self.max_lines_spin)
        top_layout.addWidget(self.current_lines_label)
        top_layout.addSpacing(10)
        top_layout.addWidget(line_top_2)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.Address_label)
        top_layout.addWidget(self.Transaction_time_label)
        top_layout.addSpacing(10)
        top_layout.addWidget(line_top_3)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.time_log_btn)
        top_layout.addWidget(self.protocol_parse_btn)
        top_layout.addSpacing(10)
        top_layout.addWidget(line_top_4)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.search_line)
        top_layout.addWidget(self.search_prev_btn)
        top_layout.addWidget(self.search_next_btn)
        top_layout.addWidget(self.search_count_label)
        top_layout.addSpacing(10)
        top_layout.addWidget(line_top_5)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.status_panel_toggle_btn)
        top_layout.addStretch()

        layout.addWidget(top_widget)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.create_display_area(self.splitter)
        
        bottom_widget = QWidget()
        # bottom_widget.setStyleSheet("background: rgba(36, 42, 56, 0.25);")
        bottom_layout = QVBoxLayout(bottom_widget)
        
        # Create horizontal layout for the main controls
        controls_layout = QHBoxLayout()

        line_bottom_1 = QFrame()
        line_bottom_1.setFrameShape(QFrame.Shape.VLine)
        line_bottom_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        line_bottom_2 = QFrame()
        line_bottom_2.setFrameShape(QFrame.Shape.VLine)
        line_bottom_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        self.open_csv_log_file_btn = PushButton("📄CSV")
        self.open_csv_log_file_btn.setFixedWidth(75)
        self.open_csv_log_file_btn.setToolTip("打开当前CSV日志文件")
        self.open_csv_log_file_btn.clicked.connect(self.open_current_csv_file)
        self.open_csv_log_file_btn.setEnabled(False)

        self.open_text_log_file_btn = PushButton("📄TEXT")
        self.open_text_log_file_btn.setFixedWidth(75)
        self.open_text_log_file_btn.setToolTip("打开当前Text日志文件")
        self.open_text_log_file_btn.clicked.connect(self.open_current_text_log_file)
        self.open_text_log_file_btn.setEnabled(False)

        self.open_log_folder_btn = PushButton("📁")
        self.open_log_folder_btn.setFixedWidth(50)
        self.open_log_folder_btn.setToolTip("打开日志文件夹")
        self.open_log_folder_btn.clicked.connect(self.open_log_folder)

        self.clear_btn = ToolButton(FIF.DELETE)
        self.clear_btn.setFixedWidth(50)
        self.clear_btn.clicked.connect(self.serial_display.clear)

        self.timestamp = CheckBox("🕒")
        self.timestamp.setStyleSheet("background: transparent")
        self.timestamp.setObjectName("timestamp")
        self.timestamp.setChecked(True)

        self.auto_scroll = CheckBox("📌")
        self.auto_scroll.setStyleSheet("background: transparent")
        self.auto_scroll.setObjectName("autoScroll")
        self.auto_scroll.setChecked(False)

        self.send_judge = CheckBox("HEX")
        self.send_judge.setStyleSheet("background: transparent")
        self.send_judge.setChecked(True)
        self.send_judge.clicked.connect(self.toggle_send_mode)

        self.send_line_edit = LineEdit()
        self.send_line_edit.setPlaceholderText("e.g., AA BB or 0xAA 0xBB or String")
        self.send_line_edit.setClearButtonEnabled(True)

        # BM:输入框开关
        self.large_send_edit = TextEdit()
        self.large_send_edit.setPlaceholderText("e.g., AA BB or 0xAA 0xBB or String")
        self.large_send_edit.setMaximumHeight(300)
        self.large_send_edit.setVisible(False)

        self.send_btn = ToolButton(FIF.SEND)
        self.send_btn.setFixedWidth(60)
        self.send_btn.clicked.connect(self.com1_send_data)

        # Quick send components
        self.quick_send_combo = ComboBox()
        self.quick_send_combo.setFixedWidth(120)
        self.quick_send_combo.setPlaceholderText("Quick Send")
        self.quick_send_combo.currentTextChanged.connect(self.on_quick_send_selected)
        
        self.quick_config_btn = ToolButton(FIF.DEVELOPER_TOOLS)
        self.quick_config_btn.setFixedSize(30, 30)
        self.quick_config_btn.setToolTip("Configure Quick Send")
        self.quick_config_btn.clicked.connect(self.show_quick_send_config)

        # BM:串口发送开关
        self.expand_btn = ToolButton(FIF.UP)  # Change icon to DOWN since input is expanded by default
        self.expand_btn.setFixedSize(30, 30)
        self.expand_btn.clicked.connect(self.toggle_input_size)
        self.is_expanded = False

        controls_layout.addWidget(self.clear_btn)
        controls_layout.addWidget(self.open_csv_log_file_btn)
        controls_layout.addWidget(self.open_text_log_file_btn)
        controls_layout.addWidget(self.open_log_folder_btn)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(line_bottom_1)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(self.timestamp)
        controls_layout.addWidget(self.auto_scroll)
        controls_layout.addWidget(self.send_judge)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(line_bottom_2)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(self.send_line_edit)
        controls_layout.addWidget(self.send_btn)
        controls_layout.addWidget(self.quick_send_combo)
        controls_layout.addWidget(self.quick_config_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.expand_btn)
        
        bottom_layout.addWidget(self.large_send_edit)
        bottom_layout.addLayout(controls_layout)
        
        self.splitter.addWidget(bottom_widget)
        self.splitter.setSizes([2000, 100])  # 设置初始大小比例
        
        layout.addWidget(self.splitter)
        
        self.port_scan_timer = QTimer()
        self.port_scan_timer.timeout.connect(self.refresh_ports)
        self.port_scan_timer.start(1000)
        self.refresh_ports()
        
        return COM1_page
    
    def update_max_lines(self, value):
        """更新显示区域最大行数"""
        self.serial_display.document().setMaximumBlockCount(value)
    
    def update_current_lines(self):
        """更新当前行数显示"""
        current_count = self.serial_display.document().blockCount()
        self.current_lines_label.setText(f"Row: {current_count}")
        # 如果当前行数等于最大行数，自动清除
        max_lines = self.serial_display.document().maximumBlockCount()
        if current_count >= max_lines:
            self.serial_display.clear()

    def create_display_area(self, layout):
        display_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：日志显示区域
        self.serial_display = QTextEdit()
        self.serial_display.setReadOnly(True)
        self.serial_display.document().setMaximumBlockCount(150000)  # 限制最大行数
        self.serial_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 不自动换行
        self.serial_display.installEventFilter(self) # 安装事件过滤器
        
        # 优化显示性能
        self.serial_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        font = QFont("Microsoft YaHei", 12)
        self.serial_display.setFont(font)
        self.serial_display.setStyleSheet("""
            QTextEdit {
                background-color          : rgba(36, 42, 56, 0.2);
                border                    : 1.5px solid #3a4a5c;
                border-radius             : 1px;
                padding                   : 12px;
                color                     : {theme['text']};
                font-size                 : 15px;
                font-family               : 'JetBrains Mono', 'Consolas', 'Microsoft YaHei', monospace;
                selection-background-color: #088bef;
                selection-color           : #ffffff;
            }
            QTextEdit:focus {
                border          : 1.5px solid #477faa;
                background-color: rgba(27, 32, 44, 0.99);
            }
        """)
        
        self.serial_display.document().blockCountChanged.connect(self.update_current_lines)
        self.update_current_lines()

        # 添加鼠标事件处理
        self.serial_display.keyPressEvent = self.on_display_key_press
        self.font_size = 12  # 初始字体大小
        
        # 右侧：状态监控面板
        self.status_panel = self.create_status_panel()
        
        # 添加到分割器
        display_splitter.addWidget(self.serial_display)
        display_splitter.addWidget(self.status_panel)
        
        # 设置分割比例 (5:1)
        display_splitter.setSizes([5000, 1000])
        display_splitter.setCollapsible(0, False)  # 日志区域不可折叠
        display_splitter.setCollapsible(1, True)   # 状态面板可折叠
        
        # 初始化状态数据
        self.status_data = {
            'Link': 'FFFF',
            'USER': {'used': 0, 'total': 20},
            'AUTH': {'used': 0, 'total': 20},
            'TRANS': {'used': 0, 'total': 10},
            'DTPML': {'used': 0, 'total': 20}
        }
        
        layout.addWidget(display_splitter)

    def create_status_panel(self):
        # BM: 仪表配置
        panel = QWidget()
        panel.setFixedWidth(275)  # 固定宽度确保紧凑显示
        panel.setStyleSheet("""
            QWidget {
                background-color: rgba(36, 42, 56, 0.1);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        # layout.setContentsMargins(8, 8, 8, 8)
        # layout.setSpacing(8)
        
        # 创建5个状态卡
        self.link_card = self.create_status_card("LINK", "FFFF", FIF.TILES, is_link=True)
        self.user_card = self.create_status_card("USERS", 20, FIF.PEOPLE)
        self.auth_card = self.create_status_card("AUTH", 20, FIF.IOT)
        self.trans_card = self.create_status_card("TRANS", 10, FIF.IOT)
        self.dtpml_card = self.create_status_card("DTPML", 20, FIF.IOT)
        
        layout.addWidget(self.link_card)
        layout.addWidget(self.user_card, 1)  # 添加拉伸因子
        layout.addWidget(self.auth_card, 1)  # 添加拉伸因子
        layout.addWidget(self.trans_card, 1)  # 添加拉伸因子
        layout.addWidget(self.dtpml_card, 1)  # 添加拉伸因子
        
        return panel

    def toggle_status_panel(self):
        """切换状态面板显示/隐藏"""
        if hasattr(self, 'status_panel'):
            if self.status_panel_visible:
                self.status_panel.setVisible(False)  # 使用setVisible而不是hide()
                self.status_panel_toggle_btn.setIcon(FIF.VIEW.icon())
                self.status_panel_toggle_btn.setToolTip("显示状态监控面板")
            else:
                self.status_panel.setVisible(True)   # 使用setVisible而不是show()
                self.status_panel_toggle_btn.setIcon(FIF.HIDE.icon())
                self.status_panel_toggle_btn.setToolTip("隐藏状态监控面板")
            self.status_panel_visible = not self.status_panel_visible

    def create_status_card(self, title, total, icon, is_link=False):
        """创建单个状态卡"""
        card = CardWidget()
        
        # 根据是否为LINK卡设置不同高度
        if is_link:
            card.setFixedHeight(50)  # LINK卡高度为原来的三分之一
        else:
            card.setMinimumHeight(120)  # 其他卡片设置最小高度，允许拉伸
        
        layout = QVBoxLayout(card)
        
        # 顶部：图标 + 标题 + 总数
        top_container = QWidget()
        top_container.setFixedHeight(35)
        top_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.1);      
            }
            BodyLabel {
                background-color: transparent;
                border: none;
            }
        """)
        
        top_layout = QHBoxLayout(top_container)
        # top_layout.setContentsMargins(8, 4, 8, 4)
        
        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(20, 20)
        title_label = QLabel(title)
        title_label.setStyleSheet("""
                background-color: transparent;
                font-weight: bold;
                font-size: 14px;
                color: rgba(255, 255, 255, 1);
            """)
        
        top_layout.addSpacing(15)
        top_layout.addWidget(icon_widget)
        top_layout.addSpacing(5)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        
        # 总数显示
        if is_link:
            total_label = QLabel(str(total))
            total_label.setStyleSheet("""
                font-size: 16px;
                color: rgba(35, 150, 158, 1);
                background-color: transparent;
                font-weight:bold;
            """)
            top_layout.addWidget(total_label)
            top_layout.addSpacing(15)
        
        layout.addWidget(top_container)
        
        # 底部：进度条和数据显示
        if not is_link:
            bottom_layout = QHBoxLayout()

            progress = ProgressRing()
            progress.setRange(0, total)
            progress.setValue(0)
            progress.setTextVisible(True)
            progress.setFixedSize(60, 60)
            progress.setStrokeWidth(10)
            
            # 数据显示框
            data_layout = QHBoxLayout()
            data_layout.setSpacing(4)

            used_widget = QWidget()
            used_widget.setFixedSize(50, 50)
            used_widget.setStyleSheet("""
                background-color: rgba(255, 107, 129, 0.6);
                border-radius: 4px;
                padding: 2px;
            """)
            used_layout = QVBoxLayout(used_widget)
            used_layout.setContentsMargins(2, 2, 2, 2)
            used_layout.setSpacing(0)
            used_title = QLabel("USED")
            used_title.setStyleSheet("""
                background-color: transparent;
                font-weight:bold;
            """)
            used_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            used_layout.addWidget(used_title)
            used_value = QLabel("0")
            used_value.setStyleSheet("""
                font-size:15px;
            """)
            used_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            used_layout.addWidget(used_value)
            
            free_widget = QWidget()
            free_widget.setFixedSize(50, 50)
            free_widget.setStyleSheet("""
                background-color: rgba(72, 207, 173, 0.6);
                border-radius: 4px;
                padding: 2px;
            """)
            free_layout = QVBoxLayout(free_widget)
            free_layout.setContentsMargins(2, 2, 2, 2)
            free_layout.setSpacing(0)
            free_title = QLabel("FREE")
            free_title.setStyleSheet("""
                background-color: transparent;
                font-weight: bold;
            """)
            free_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            free_layout.addWidget(free_title)
            free_value = QLabel(str(total))
            free_value.setStyleSheet("""
                font-size:15px;
            """)
            free_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            free_layout.addWidget(free_value)
            
            all_widget = QWidget()
            all_widget.setFixedSize(50, 50)
            all_widget.setStyleSheet("""
                background-color: rgba(77, 130, 211, 0.6);
                border-radius: 4px;
                padding: 2px;
            """)
            all_layout = QVBoxLayout(all_widget)
            all_layout.setContentsMargins(2, 2, 2, 2)
            all_layout.setSpacing(0)
            all_title = QLabel("ALL")
            all_title.setStyleSheet("""
                background-color: transparent;
                font-weight: bold;
            """)
            all_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            all_layout.addWidget(all_title)
            all_value = QLabel(str(total))
            all_value.setStyleSheet("""
                font-size: 15px;
                
            """)
            all_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            all_layout.addWidget(all_value)
            
            data_layout.addWidget(used_widget)
            data_layout.addWidget(free_widget)
            data_layout.addWidget(all_widget)
            
            bottom_layout.addWidget(progress)
            bottom_layout.addLayout(data_layout)
            
            layout.addLayout(bottom_layout)
            
            setattr(card, 'progress', progress)
            setattr(card, 'used_value', used_value)
            setattr(card, 'free_value', free_value)
        else:
            # LINK卡片只显示地址信息
            setattr(card, 'total_label', total_label)
        
        return card

    # BM: 更新仪表数据
    def update_status_card(self, card_type, used_value=None, link_value=None):
        """更新状态卡数据"""
        if card_type == "LINK" and link_value is not None:
            self.link_card.total_label.setText(str(link_value))
            self.status_data['Link'] = link_value
        elif card_type in ["USER", "AUTH", "TRANS", "DTPML"] and used_value is not None:
            card_map = {
                "USER": self.user_card,
                "AUTH": self.auth_card,
                "TRANS": self.trans_card,
                "DTPML": self.dtpml_card
            }
            
            card = card_map[card_type]
            total = self.status_data[card_type]['total']
            free = total - used_value
            
            # 更新进度条
            card.progress.setValue(used_value)
            
            # 更新数据显示
            card.used_value.setText(str(used_value))
            card.free_value.setText(str(free))
            
            # 更新状态数据
            self.status_data[card_type]['used'] = used_value

    def create_Chart_page(self):  # BM: Chart Page
        Chart_page = QWidget()
        layout = QVBoxLayout(Chart_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
    
        chart_widget = self.create_chart_area()
        main_splitter.addWidget(chart_widget)

        canvas_splitter = QSplitter(Qt.Orientation.Horizontal)

        table_widget = self.create_test_area()  # 这里包含了表格和闸机动画区域
        canvas_splitter.addWidget(table_widget)
        
        bottom_right = QWidget()
        bottom_right_layout = QVBoxLayout(bottom_right)
        bottom_right_layout.setContentsMargins(5, 5, 5, 5)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.multi_gate_toggle_btn = PushButton("🚪")
        self.multi_gate_toggle_btn.setFixedSize(50, 30)
        self.multi_gate_toggle_btn.clicked.connect(self.toggle_multi_gate_mode)
        button_layout.addWidget(self.multi_gate_toggle_btn)
        
        self.layout_toggle_btn = PushButton("⚡")
        self.layout_toggle_btn.setFixedSize(50, 30)
        self.layout_toggle_btn.clicked.connect(self.toggle_layout_mode)
        button_layout.addWidget(self.layout_toggle_btn)
        bottom_right_layout.addLayout(button_layout)
        
        self.position_view = PositionView(self)
        bottom_right_layout.addWidget(self.position_view)
        # 初始化时刷新红蓝区域
        self.position_view.refresh_areas()
        canvas_splitter.addWidget(bottom_right)
        
        # 保存splitter引用以便后续控制
        self.main_splitter = main_splitter
        self.canvas_splitter = canvas_splitter
        self.chart_widget = chart_widget
        self.table_widget = table_widget
        self.is_expanded_mode = False
        self.is_multi_gate_mode = False  # 多闸机模式状态

        canvas_splitter.setSizes([100, 100])
        # Set vertical splitter stretch factors and sizes to avoid oversized chart
        try:
            main_splitter.setStretchFactor(0, 1)
            main_splitter.setStretchFactor(1, 3)
            main_splitter.setSizes([100, 200])
        except Exception:
            pass
        main_splitter.addWidget(canvas_splitter)
        # Sizes will be re-applied in attach_chart_to_chart_page when switching pages
        main_splitter.setSizes([80, 220])

        layout.addWidget(main_splitter)
        return Chart_page
    
    def toggle_layout_mode(self):   #BM: 扩展模式
        """切换布局模式：正常模式 <-> 扩展模式"""
        if not self.is_expanded_mode:
            # 切换到扩展模式：隐藏图表和表格区域
            self.chart_widget.hide()
            
            # 隐藏表格区域（保留动画区域）
            if hasattr(self, 'data_table'):
                # 找到包含data_table的top_table widget并隐藏
                table_widget = self.data_table.parent()
                if table_widget:
                    table_widget.hide()
            
            # 调整splitter比例，让动画区域和位置区域按1:2显示
            self.canvas_splitter.setSizes([50, 150])  # 动画区域:位置区域 = 1:2
            self.main_splitter.setSizes([0, 300])     # 隐藏图表区域
            
            # 设置扩展模式下的显示缩放为1.2倍（适中的放大值）
            if hasattr(self, 'gate_animation'):
                self.gate_animation.set_display_scale(1.2)
            if hasattr(self, 'position_view'):
                self.position_view.set_display_scale(1.2)
            
            self.layout_toggle_btn.setText("📊")
            self.is_expanded_mode = True
        else:
            # 切换回正常模式：显示所有区域
            self.chart_widget.show()
            
            # 显示表格区域
            if hasattr(self, 'data_table'):
                table_widget = self.data_table.parent()
                if table_widget:
                    table_widget.show()
            
            # 恢复原始比例
            self.canvas_splitter.setSizes([100, 100])
            self.main_splitter.setSizes([100, 200])
            
            # 恢复正常模式下的显示缩放为1.0倍
            if hasattr(self, 'gate_animation'):
                self.gate_animation.set_display_scale(1.0)
            if hasattr(self, 'position_view'):
                self.position_view.set_display_scale(1.0)
            
            self.layout_toggle_btn.setText("⚡")
            self.is_expanded_mode = False
    
    def toggle_multi_gate_mode(self):
        self.is_multi_gate_mode = not self.is_multi_gate_mode
        
        if self.is_multi_gate_mode:
            self.multi_gate_toggle_btn.setText("🚪🚪")
        else:
            self.multi_gate_toggle_btn.setText("🚪")
        
        # 通知position_view更新显示
        if hasattr(self, 'position_view'):
            self.position_view.set_multi_gate_mode(self.is_multi_gate_mode)

    
    def create_chart_area(self):
        top_widget = QWidget()
        top_widget.setStyleSheet("background: rgba(36, 42, 56, 0);")
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(10)

        self.charts  = {}
        self.series  = {}
        chart_titles = {
            'master'   : 'Master',
            'slave'    : 'Slave',
            'nlos'     : 'NLOS',
            'rssi'     : 'RSSI',
            'speed'    : 'Speed'
        }
        for key, title in chart_titles.items():
            series = QLineSeries()
            colors = {
                'master'   : QColor("#FF6B6B"),
                'slave'    : QColor("#4ECDC4"),
                'nlos'     : QColor("#45B7D1"),
                'rssi'     : QColor("#68ecae"),
                'speed'    : QColor("#FFBE0B")
            }
            series.setColor(colors[key])
            series.setPen(QPen(colors[key], 3))   # 曲线加粗
            series.setPointsVisible(False)        # 显示数据点
            series.setPointLabelsVisible(False)   # 显示点标签（可选）
            series.setPointLabelsColor(colors[key].darker(150))
            self.series[key] = series

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle(title)
            chart.setTitleFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            chart.setTitleBrush(colors[key].darker(120))
            chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            chart.legend().hide()
            
            # 优化渐变背景 - 更丰富的渐变效果
            gradient = QLinearGradient(0, 0, 0, 1)
            gradient.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
            gradient.setColorAt(0.0, QColor(60, 62, 68, 150))   # 顶部颜色增强
            gradient.setColorAt(0.3, QColor(50, 52, 60, 100))   # 添加中间过渡色
            gradient.setColorAt(0.7, QColor(40, 42, 50, 70))    # 添加中间过渡色
            gradient.setColorAt(1.0, QColor(32, 34, 38, 40))    # 底部颜色微调
            chart.setBackgroundBrush(gradient)
            chart.setBackgroundRoundness(12)        # 增加圆角
            chart.setMargins(QMargins(8, 10, 8, 8)) # 调整边距
            
            # 优化阴影效果
            chart.setDropShadowEnabled(True)
            # 边框美化
            chart.setBackgroundPen(QPen(QColor(140, 150, 180, 70), 1.2))
            
            # X轴美化
            axis_x = QValueAxis()
            axis_x.setRange(0, 100)
            axis_x.setLabelFormat("%d")
            axis_x.setLabelsColor(QColor("#E5E9F0").lighter(110))  # 稍微提亮标签
            axis_x.setGridLineVisible(True)
            axis_x.setGridLineColor(QColor(255, 255, 255, 30))     # 降低网格线不透明度
            axis_x.setMinorGridLineVisible(True)
            axis_x.setMinorGridLineColor(QColor(255, 255, 255, 15))
            axis_x.setLabelsFont(QFont("Segoe UI", 9))
            # axis_x.setTitleText("数据点")                          # 添加轴标题
            axis_x.setTitleFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            axis_x.setTitleBrush(QColor("#E5E9F0"))
            
            # Y轴美化
            axis_y = QValueAxis()
            axis_y.setRange(-10, 10)
            axis_y.setLabelFormat("%d")
            axis_y.setLabelsColor(QColor("#E5E9F0").lighter(110))  # 稍微提亮标签
            axis_y.setGridLineVisible(True)
            axis_y.setGridLineColor(QColor(255, 255, 255, 30))     # 降低网格线不透明度
            axis_y.setMinorGridLineVisible(True)
            axis_y.setMinorGridLineColor(QColor(255, 255, 255, 15))
            axis_y.setLabelsFont(QFont("Segoe UI", 9))
            # axis_y.setTitleText("数值")                            # 添加轴标题
            axis_y.setTitleFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            axis_y.setTitleBrush(QColor("#E5E9F0"))
            
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
            
            # 美化线条
            if isinstance(series, QLineSeries):
                pen = series.pen()
                pen.setWidth(2)                                  # 增加线宽
                series.setPen(pen)
            
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
            chart_view.setStyleSheet("""
                background   : transparent;
                border-radius: 14px;                               /* 增加边框圆角 */
                margin       : 2px;                                /* 添加边距 */
            """)
            # Fix the height for each chart to reduce space on TestPage
            chart_view.setMaximumHeight(300)

            # 鼠标悬停显示数据点值
            def show_tooltip(point, state, key=key):
                if state:
                    QToolTip.showText(QCursor.pos(), f"{chart_titles[key]}: {int(point.y())}")
                else:
                    QToolTip.hideText()
            series.hovered.connect(show_tooltip)

            self.charts[key] = chart
            top_layout.addWidget(chart_view)
        return top_widget

    def create_test_area(self):
        bottom_left = QWidget()
        bottom_left.setStyleSheet("background-color: rgba(45, 52, 54,  0.15); ")
        bottom_left_layout = QVBoxLayout(bottom_left)
        bottom_left_layout.setContentsMargins(0, 0, 0, 0)
        bottom_left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        form_splitter = QSplitter(Qt.Orientation.Vertical)
        form_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 上部分 - 数据表格
        top_table = QWidget()
        top_table_layout = QVBoxLayout(top_table)
        top_table_layout.setContentsMargins(5, 5, 5, 5)
        top_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.data_table = TableWidget()
        self.data_table.setColumnCount(10)
        self.data_table.setHorizontalHeaderLabels(['Master', 'Slave', 'NLOS', 'RSSI', 'Speed','X', 'Y', 'Z', 'Auth', 'Trans'])
        
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.data_table.setAlternatingRowColors(True)           # 斑马纹
        self.data_table.setBorderVisible(True)                  # 边框线
        self.data_table.setBorderRadius(8)                      # 圆角表头
        top_table_layout.addWidget(self.data_table)

        # 下部分 - 闸机动画区域
        bottom_space = QWidget()
        bottom_space.setStyleSheet("background: rgba(255, 255, 255, 0.05); border-radius: 10px;")
        bottom_layout = QVBoxLayout(bottom_space)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        
        
        # 创建闸机动画组件
        self.gate_animation = SubwayGateAnimation()
        bottom_layout.addWidget(self.gate_animation)
        

        form_splitter.addWidget(top_table)
        form_splitter.addWidget(bottom_space)
        form_splitter.setSizes([120, 300])

        bottom_left_layout.addWidget(form_splitter)
        return bottom_left
    
    def on_display_key_press(self, event):
        """处理显示区域的键盘事件"""
        if event.key() == Qt.Key.Key_Space:
            self.auto_scroll.setChecked(not self.auto_scroll.isChecked())
        QTextEdit.keyPressEvent(self.serial_display, event)
    
    def on_search_text_changed(self, text):
        """Handle SearchLineEdit text changes"""
        if not text:
            self.clear_search_highlights()
            return
        
        # Auto search as user types
        self.perform_search(text)
    
    def on_search_triggered(self, text=""):
        """Handle SearchLineEdit search signal (Enter key)"""
        if not text:
            text = self.search_line.text()
        if text:
            # Add to search history
            self.search_line.add_to_history(text)
            self.perform_search(text)
    
    def on_search_cleared(self):
        """Handle SearchLineEdit clear signal"""
        self.clear_current_line_highlight()
        self.search_count_label.setText("0/0")
        self.current_search_text = ""
    
    def perform_search(self, text):
        """Perform search in serial display"""
        if not text:
            self.search_count_label.setText("0/0")
            self.clear_current_line_highlight()
            self.current_search_text = ""
            return
            
        content = self.serial_display.toPlainText()
        if not content:
            self.search_count_label.setText("0/0")
            self.clear_current_line_highlight()
            self.current_search_text = ""
            return
            
        # Store current search text for dynamic updates
        self.current_search_text = text
        
        # Find all occurrences
        positions = []
        start = 0
        while True:
            pos = content.find(text, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        total_matches = len(positions)
        if not positions:
            self.search_count_label.setText("0/0")
            self.clear_current_line_highlight()
            return
            
        # Store search results for navigation
        self.search_positions = positions
        self.search_text_length = len(text)
        self.current_search_index = 0
        
        # Move to first match and highlight current line
        self.move_to_search_match(0)
        
        # Update count label
        self.search_count_label.setText(f"1/{total_matches}")
    
    def move_to_search_match(self, index):
        """Move to specific search match and highlight the line"""
        if not hasattr(self, 'search_positions') or not self.search_positions:
            return
            
        if index < 0 or index >= len(self.search_positions):
            return
            
        pos = self.search_positions[index]
        cursor = self.serial_display.textCursor()
        cursor.setPosition(pos)
        
        # Move to beginning of line
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        line_start = cursor.position()
        
        # Move to end of line
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        line_end = cursor.position()
        
        # Clear previous line highlight
        self.clear_current_line_highlight()
        
        # Highlight entire line with background color
        cursor.setPosition(line_start)
        cursor.setPosition(line_end, QTextCursor.MoveMode.KeepAnchor)
        
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#cf91cf"))  # Light purple background for current line
        cursor.mergeCharFormat(fmt)
        
        # Position cursor at the search match
        cursor.setPosition(pos)
        cursor.setPosition(pos + self.search_text_length, QTextCursor.MoveMode.KeepAnchor)
        self.serial_display.setTextCursor(cursor)
        self.serial_display.ensureCursorVisible()
        
        # Store current highlight for clearing later
        self.current_line_start = line_start
        self.current_line_end = line_end
        
    def clear_current_line_highlight(self):
        """Clear current line highlight"""
        if (hasattr(self, 'current_line_start') and hasattr(self, 'current_line_end') and 
            self.current_line_start is not None and self.current_line_end is not None):
            cursor = self.serial_display.textCursor()
            cursor.setPosition(self.current_line_start)
            cursor.setPosition(self.current_line_end, QTextCursor.MoveMode.KeepAnchor)
            
            # Clear formatting by setting default format
            fmt = QTextCharFormat()
            fmt.setBackground(QColor())  # Clear background color
            cursor.mergeCharFormat(fmt)
            
            # Reset stored positions
            self.current_line_start = None
            self.current_line_end = None
    
    def search_previous(self):
        """Move to previous search match"""
        if not hasattr(self, 'search_positions') or not self.search_positions:
            return
            
        self.current_search_index = (self.current_search_index - 1) % len(self.search_positions)
        self.move_to_search_match(self.current_search_index)
        self.search_count_label.setText(f"{self.current_search_index + 1}/{len(self.search_positions)}")
    
    def search_next(self):
        """Move to next search match"""
        if not hasattr(self, 'search_positions') or not self.search_positions:
            return
            
        self.current_search_index = (self.current_search_index + 1) % len(self.search_positions)
        self.move_to_search_match(self.current_search_index)
        self.search_count_label.setText(f"{self.current_search_index + 1}/{len(self.search_positions)}")
    
    def highlight_search_matches(self, positions, length):
        """Highlight search matches in the text"""
        cursor = self.serial_display.textCursor()
        
        # Clear previous highlights
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        cursor.mergeCharFormat(fmt)
        
        for pos in positions:
            cursor.setPosition(pos)
            cursor.setPosition(pos + length, QTextCursor.MoveMode.KeepAnchor)
            
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#c3dd8c"))
            fmt.setForeground(QColor("#000000"))
            cursor.mergeCharFormat(fmt)
    
    def clear_search_highlights(self):
        """Clear all search highlights"""
        cursor = self.serial_display.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        cursor.mergeCharFormat(fmt)
        cursor.clearSelection()
        self.serial_display.setTextCursor(cursor)
    
    def on_search_text_changed2(self, text):
        """Handle SearchLineEdit text changes for COM2"""
        if not text:
            self.clear_search_highlights2()
            return
        
        # Auto search as user types
        self.perform_search2(text)
    
    def on_search_triggered2(self, text=""):
        """Handle SearchLineEdit search signal (Enter key) for COM2"""
        if not text:
            text = self.search_line2.text()
        if text:
            # Add to search history
            self.search_line2.add_to_history(text)
            self.perform_search2(text)
    
    def on_search_cleared2(self):
        """Handle SearchLineEdit clear signal for COM2"""
        self.clear_current_line_highlight2()
        self.search_count_label2.setText("0/0")
        self.current_search_text2 = ""
    
    def perform_search2(self, text):
        """Perform search in serial display for COM2"""
        if not text:
            self.search_count_label2.setText("0/0")
            self.clear_current_line_highlight2()
            self.current_search_text2 = ""
            return
            
        content = self.serial_display2.toPlainText()
        if not content:
            self.search_count_label2.setText("0/0")
            self.clear_current_line_highlight2()
            self.current_search_text2 = ""
            return
            
        # Store current search text for dynamic updates
        self.current_search_text2 = text
        
        # Find all occurrences
        positions = []
        start = 0
        while True:
            pos = content.find(text, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        total_matches = len(positions)
        if not positions:
            self.search_count_label2.setText("0/0")
            self.clear_current_line_highlight2()
            return
            
        # Store search results for navigation
        self.search_positions2 = positions
        self.search_text_length2 = len(text)
        self.current_search_index2 = 0
        
        # Move to first match and highlight current line
        self.move_to_search_match2(0)
        
        # Update count label
        self.search_count_label2.setText(f"1/{total_matches}")
    
    def move_to_search_match2(self, index):
        """Move to specific search match and highlight the line for COM2"""
        if not hasattr(self, 'search_positions2') or not self.search_positions2:
            return
            
        if index < 0 or index >= len(self.search_positions2):
            return
            
        pos = self.search_positions2[index]
        cursor = self.serial_display2.textCursor()
        cursor.setPosition(pos)
        
        # Move to beginning of line
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        line_start = cursor.position()
        
        # Move to end of line
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        line_end = cursor.position()
        
        # Clear previous line highlight
        self.clear_current_line_highlight2()
        
        # Highlight entire line with background color
        cursor.setPosition(line_start)
        cursor.setPosition(line_end, QTextCursor.MoveMode.KeepAnchor)
        
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#d8bfd8"))  # Light purple background for current line
        cursor.mergeCharFormat(fmt)
        
        # Position cursor at the search match
        cursor.setPosition(pos)
        cursor.setPosition(pos + self.search_text_length2, QTextCursor.MoveMode.KeepAnchor)
        self.serial_display2.setTextCursor(cursor)
        self.serial_display2.ensureCursorVisible()
        
        # Store current highlight for clearing later
        self.current_line_start2 = line_start
        self.current_line_end2 = line_end
        
    def clear_current_line_highlight2(self):
        """Clear current line highlight for COM2"""
        if (hasattr(self, 'current_line_start2') and hasattr(self, 'current_line_end2') and 
            self.current_line_start2 is not None and self.current_line_end2 is not None):
            cursor = self.serial_display2.textCursor()
            cursor.setPosition(self.current_line_start2)
            cursor.setPosition(self.current_line_end2, QTextCursor.MoveMode.KeepAnchor)
            
            # Clear formatting by setting default format
            fmt = QTextCharFormat()
            fmt.setBackground(QColor())  # Clear background color
            cursor.mergeCharFormat(fmt)
            
            # Reset stored positions
            self.current_line_start2 = None
            self.current_line_end2 = None
    
    def search_previous2(self):
        """Move to previous search match for COM2"""
        if not hasattr(self, 'search_positions2') or not self.search_positions2:
            return
            
        self.current_search_index2 = (self.current_search_index2 - 1) % len(self.search_positions2)
        self.move_to_search_match2(self.current_search_index2)
        self.search_count_label2.setText(f"{self.current_search_index2 + 1}/{len(self.search_positions2)}")
    
    def search_next2(self):
        """Move to next search match for COM2"""
        if not hasattr(self, 'search_positions2') or not self.search_positions2:
            return
            
        self.current_search_index2 = (self.current_search_index2 + 1) % len(self.search_positions2)
        self.move_to_search_match2(self.current_search_index2)
        self.search_count_label2.setText(f"{self.current_search_index2 + 1}/{len(self.search_positions2)}")
    
    def update_search_results(self):
        """Update search results when new data is added"""
        if hasattr(self, 'current_search_text') and self.current_search_text:
            # Store current position before updating
            current_index = getattr(self, 'current_search_index', 0)
            current_position = None
            
            # If we have a current match, store its position for reference
            if hasattr(self, 'search_positions') and self.search_positions and current_index < len(self.search_positions):
                current_position = self.search_positions[current_index]
            
            # Re-perform search to get updated positions
            content = self.serial_display.toPlainText()
            positions = []
            start = 0
            while True:
                pos = content.find(self.current_search_text, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            
            self.search_positions = positions
            total_matches = len(positions)
            
            if total_matches > 0:
                # Try to maintain current position relative to content
                if current_position is not None:
                    # Find the closest match to the previous position
                    best_index = 0
                    min_distance = abs(positions[0] - current_position)
                    for i, pos in enumerate(positions):
                        distance = abs(pos - current_position)
                        if distance < min_distance:
                            min_distance = distance
                            best_index = i
                    self.current_search_index = best_index
                else:
                    # Maintain current index if possible
                    if current_index < total_matches:
                        self.current_search_index = current_index
                    else:
                        self.current_search_index = total_matches - 1
                
                self.search_count_label.setText(f"{self.current_search_index + 1}/{total_matches}")
            else:
                self.search_count_label.setText("0/0")
                self.current_search_index = 0
    
    def update_search_results2(self):
        """Update search results when new data is added for COM2"""
        if hasattr(self, 'current_search_text2') and self.current_search_text2:
            # Store current position before updating
            current_index = getattr(self, 'current_search_index2', 0)
            current_position = None
            
            # If we have a current match, store its position for reference
            if hasattr(self, 'search_positions2') and self.search_positions2 and current_index < len(self.search_positions2):
                current_position = self.search_positions2[current_index]
            
            # Re-perform search to get updated positions
            content = self.serial_display2.toPlainText()
            positions = []
            start = 0
            while True:
                pos = content.find(self.current_search_text2, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            
            self.search_positions2 = positions
            total_matches = len(positions)
            
            if total_matches > 0:
                # Try to maintain current position relative to content
                if current_position is not None:
                    # Find the closest match to the previous position
                    best_index = 0
                    min_distance = abs(positions[0] - current_position)
                    for i, pos in enumerate(positions):
                        distance = abs(pos - current_position)
                        if distance < min_distance:
                            min_distance = distance
                            best_index = i
                    self.current_search_index2 = best_index
                else:
                    # Maintain current index if possible
                    if current_index < total_matches:
                        self.current_search_index2 = current_index
                    else:
                        self.current_search_index2 = total_matches - 1
                
                self.search_count_label2.setText(f"{self.current_search_index2 + 1}/{total_matches}")
            else:
                self.search_count_label2.setText("0/0")
                self.current_search_index2 = 0

    def highlight_search_matches2(self, positions, length):
        """Highlight search matches in the text for COM2"""
        cursor = self.serial_display2.textCursor()
        
        # Clear previous highlights
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        cursor.mergeCharFormat(fmt)
        
        for pos in positions:
            cursor.setPosition(pos)
            cursor.setPosition(pos + length, QTextCursor.MoveMode.KeepAnchor)
            
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#c3dd8c"))
            fmt.setForeground(QColor("#000000"))
            cursor.mergeCharFormat(fmt)
    
    def clear_search_highlights2(self):
        """Clear all search highlights for COM2"""
        cursor = self.serial_display2.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        cursor.mergeCharFormat(fmt)
        cursor.clearSelection()
        self.serial_display2.setTextCursor(cursor)
    
    # Removed on_find_result method - using SearchLineEdit instead

    def refresh_ports(self):
        """刷新可用串口列表，使用注册表方式获取所有串口，包括虚拟串口"""
        try:
            import winreg
            ports = []
            
            # 方法1：从注册表获取串口信息
            try:
                path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                
                for i in range(256):
                    try:
                        val = winreg.EnumValue(key, i)
                        # val[1]是串口名称，如COM1
                        ports.append(val[1])
                    except:
                        break
                
                winreg.CloseKey(key)
                # print(f"注册表方式找到串口: {ports}")
                
            except Exception as reg_error:
                print(f"注册表方式获取串口失败: {str(reg_error)}")
            
            # 如果两种方式都没找到串口
            if not ports:
                print("未找到任何串口")
                ports = []
            
            # 检查串口列表是否有变化
            if set(ports) == set(self.current_ports):
                return
                
            current_port = self.port_combo.currentText()
            
            self.current_ports = ports
            self.port_combo.clear()
            for port in ports:
                self.port_combo.addItem(port)
            
            # 恢复之前选择的串口
            if current_port:
                index = self.port_combo.findText(current_port)
                if index >= 0:
                    self.port_combo.setCurrentIndex(index)
                    
            print(f"最终串口列表: {ports}")
                    
        except Exception as e:
            print(f"获取串口列表失败: {str(e)}")
            # 出错时尝试使用原来的pyserial方式作为后备
            try:
                from serial.tools import list_ports
                ports = [port.device for port in list_ports.comports()]
                self.current_ports = ports
                self.port_combo.clear()
                for port in ports:
                    self.port_combo.addItem(port)
            except:
                self.current_ports = []

    def toggle_port(self):
        """切换串口开关状态"""
        if self.toggle_btn.isChecked():
            try:
                # Clear time log data when opening new serial connection
                self.time_log_data.clear()
                
                # 创建串口对象
                self.serial_port = serial.Serial(
                    port     = self.port_combo.currentText(),
                    baudrate = int(self.baud_combo.currentText()),
                    bytesize = self.data_bits,
                    parity   = self.parity,
                    stopbits = self.stop_bits,
                    timeout  = 0.1
                )
                
                # 创建并启动读取线程
                self.serial_thread = SerialReadThread(self.serial_port)
                self.serial_thread.data_received.connect(self.handle_serial_data)
                self.serial_thread.connection_lost.connect(self.handle_serial_connection_lost)
                # 根据当前输出格式设置是否按换行分割（STR: True, HEX: False）
                try:
                    self.serial_thread.set_split_on_newline(self.output_format_str)
                except Exception:
                    pass
                self.serial_thread.start()
                
                current_time      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                port_name         = self.port_combo.currentText().replace(":", "_")
                csv_log_filename  = f"[{port_name}] {current_time}.csv"
                text_log_filename = f"[{port_name}] {current_time}.log"

                # 确保 logger 实例及其目录属性存在
                if hasattr(self.logger, 'csv_log_dir') and hasattr(self.logger, 'text_log_dir'):
                    self.current_csv_log_file_path = os.path.join(self.logger.csv_log_dir, csv_log_filename)
                    self.current_text_log_file_path = os.path.join(self.logger.text_log_dir, text_log_filename)
                    self.logger.create_logger("data", csv_log_filename, "csv") # 创建 CSV 日志
                    header_str = ",".join(self.csv_title)
                    self.log_worker.add_log_task("data", "info", header_str)
                    self.logger.create_logger("UwbLog", text_log_filename, "text") # 创建 Text 日志
                    self.open_csv_log_file_btn.setEnabled(True) # 启用按钮
                    self.open_text_log_file_btn.setEnabled(True)
                else:
                    # 如果无法获取 log_dir，则禁用按钮并打印警告
                    print("警告: Logger 对象缺少 csv_log_dir 或 text_log_dir 属性，'打开日志文件'功能可能不可用。")
                    self.current_csv_log_file_path  = None
                    self.current_text_log_file_path = None
                    self.open_csv_log_file_btn.setEnabled(False)
                
                # Update button style to connected state
                self.update_port_button_style(self.toggle_btn, True)
                
            except Exception as e:
                error_msg = f"打开串口失败：{str(e)}\n"
                error_msg += f"串口: {self.port_combo.currentText()}\n"
                error_msg += f"波特率: {self.baud_combo.currentText()}\n"
                error_msg += f"异常类型: {type(e).__name__}"
                print(f"COM1串口异常详情: {error_msg}")  # 添加控制台输出用于调试
                QMessageBox.critical(self, "错误", error_msg)
                
                # 确保在异常时清理可能已创建的资源
                try:
                    if hasattr(self, 'serial_thread') and self.serial_thread is not None:
                        self.serial_thread.stop()
                        self.serial_thread = None
                    if hasattr(self, 'serial_port') and self.serial_port is not None:
                        self.serial_port.close()
                        self.serial_port = None
                except:
                    pass  # 忽略清理时的异常
                
                self.toggle_btn.setChecked(False)  # Reset switch state on error
                self.update_port_button_style(self.toggle_btn, False)  # Reset button style
                return
        else:
            # 关闭串口
            try:
                if hasattr(self, 'serial_thread') and self.serial_thread is not None:
                    self.serial_thread.stop()
                    self.serial_thread = None
                if hasattr(self, 'serial_port') and self.serial_port is not None:
                    self.serial_port.close()
                    self.serial_port = None
                
                # Update button style to disconnected state
                self.update_port_button_style(self.toggle_btn, False)
                
            except Exception as e:
                print(f"关闭串口时发生错误: {str(e)}")
                # 即使出错也要重置状态
                if hasattr(self, 'serial_thread'):
                    self.serial_thread = None
                if hasattr(self, 'serial_port'):
                    self.serial_port = None
                # Update button style to disconnected state
                self.update_port_button_style(self.toggle_btn, False)
    
    def open_current_csv_file(self):
        """使用系统默认应用打开当前的日志文件"""
        if self.current_csv_log_file_path and os.path.exists(self.current_csv_log_file_path):
            try:
                os.startfile(self.current_csv_log_file_path) # Windows specific
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开日志文件：\n{e}")
        else:
            QMessageBox.information(self, "提示", "当前没有活动的日志文件或文件不存在。")
    
    def open_current_text_log_file(self):
        """使用系统默认应用打开当前的 Text 日志文件"""
        if self.current_text_log_file_path and os.path.exists(self.current_text_log_file_path):
            try:
                os.startfile(self.current_text_log_file_path) # Windows specific
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开 Text 日志文件：\n{e}")
        else:
            QMessageBox.information(self, "提示", "当前没有活动的 Text 日志文件或文件不存在。")
    
    def open_current_text_log_file2(self):
        if self.current_text_log_file_path2 and os.path.exists(self.current_text_log_file_path2):
            try:
                os.startfile(self.current_text_log_file_path2) # Windows specific
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开 Text 日志文件：\n{e}")
        else:
            QMessageBox.information(self, "提示", "当前没有活动的 Text 日志文件或文件不存在。")

    def open_log_folder(self):
        """使用系统文件浏览器打开日志文件夹"""
        log_dir = getattr(self.logger, 'log_dir', None)
        if log_dir and os.path.isdir(log_dir):
            try:
                os.startfile(log_dir) # Windows specific
                return 
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开日志目录 '{log_dir}'：\n{e}")

        # 如果 logger 没有 log_dir 或目录不存在，可以尝试打开程序运行目录下的 'UWBLogs' 文件夹
        fallback_dir = os.path.join(os.path.dirname(__file__), 'UWBLogs') 
        if os.path.isdir(fallback_dir):
             try:
                os.startfile(fallback_dir)
             except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开备选日志目录 '{fallback_dir}'：\n{e}")
        else:
            QMessageBox.warning(self, "错误", "无法确定日志目录，主目录和备选目录均未找到。")
    
    def update_chart(self, chart_key, value):
        """更新图表（在主线程中执行）"""
        try:
            series = self.series[chart_key]
            data_list = self.uwb_data[chart_key]
            
            # 如果点数超过100，移除最旧的点
            if series.count() >= 100:
                series.remove(0)
            
            # 更新所有点的X坐标
            for i in range(series.count()):
                old_point = series.at(i)
                series.replace(i, QPointF(i, old_point.y()))
            
            # 添加新点
            series.append(len(data_list) - 1, value)
            
            # 更新Y轴范围
            if data_list:
                min_val = min(data_list)
                max_val = max(data_list)
                margin  = (max_val - min_val) * 0.1 if max_val != min_val else 1.0
                chart   = self.charts[chart_key]
                y_axis  = chart.axes(Qt.Orientation.Vertical)[0]
                y_axis.setRange(min_val - margin, max_val + margin)
            
            data = self.uwb_data.get(chart_key, [])
            chart = self.charts[chart_key]

            if data:
                mean = sum(data) / len(data)
                std = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
                display_key = "RSSI" if chart_key == "rssi" else chart_key.upper()
                title = f"{display_key} | Avg: {mean:.1f} | Std: {std:.1f}"
            else:
                mean = 0
                std = 0
                title = chart_key.upper()
            chart.setTitle(title)

            # 将实时统计推送到测试页（Avg/Std/RSSI）
            try:
                if hasattr(self, 'testInterface') and self.testInterface:
                    if not hasattr(self, '_test_metrics'):
                        self._test_metrics = {'slave': (0.0, 0.0), 'master': (0.0, 0.0), 'rssi': 0.0}
                    # 根据chart_key更新对应指标
                    if chart_key == 'slave':
                        self._test_metrics['slave'] = (mean, std)
                    elif chart_key == 'master':
                        self._test_metrics['master'] = (mean, std)
                    elif chart_key == 'rssi':
                        # 使用最新值作为RSSI即可
                        self._test_metrics['rssi'] = data[-1] if data else 0.0
                    a0_avg, a0_std = self._test_metrics['slave']
                    a1_avg, a1_std = self._test_metrics['master']
                    a1_rssi = self._test_metrics['rssi']
                    self.testInterface.update_realtime_data(a0_avg, a0_std, a1_avg, a1_std, a1_rssi)
            except Exception:
                pass

            n = len(data)
            # ===== 均值线 =====
            if not hasattr(self, "mean_series"):
                self.mean_series = {}
            if chart_key not in self.mean_series:
                from PyQt6.QtCharts import QLineSeries
                mean_series = QLineSeries()
                mean_series.setColor(QColor(255, 255, 255))  # 紫色
                mean_series.setPen(QPen(QColor(255, 255, 255), 3, Qt.PenStyle.DashLine))  # 实线加粗
                chart.addSeries(mean_series)
                mean_series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
                mean_series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
                self.mean_series[chart_key] = mean_series
            else:
                mean_series = self.mean_series[chart_key]
            mean_series.clear()
            if n > 1:
                mean_series.append(0, mean)
                mean_series.append(n-1, mean)
            # ===== 标准差带 =====
            if not hasattr(self, "std_area"):
                self.std_area = {}
            if chart_key not in self.std_area:
                from PyQt6.QtCharts import QLineSeries, QAreaSeries
                upper = QLineSeries()
                lower = QLineSeries()
                area = QAreaSeries(upper, lower)
                area.setColor(QColor(0, 120, 255, 60))  # 蓝色半透明
                area.setPen(QPen(QColor(0, 120, 255, 120), 1))
                chart.addSeries(area)
                area.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
                area.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
                self.std_area[chart_key] = (upper, lower, area)
            else:
                upper, lower, area = self.std_area[chart_key]
            upper.clear()
            lower.clear()
            for i in range(n):
                upper.append(i, mean + std)
                lower.append(i, mean - std)

        except Exception as e:
            print(f"Error updating chart: {str(e)}")

    
    def show_time_log_dialog(self):
        """Show time log dialog with beautiful UI in separate thread"""
        # Use QTimer.singleShot to run dialog creation in next event loop iteration
        # This prevents blocking the main UI thread
        QTimer.singleShot(0, self._create_time_log_dialog)
    
    def _create_time_log_dialog(self):
        """Create and show time log dialog"""
        self.time_log_dialog = QDialog(self)
        self.time_log_dialog.setWindowTitle("⏰ Time Log")
        self.time_log_dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        # Increase dialog size for better visibility
        self.time_log_dialog.resize(900, 600)
        
        # Center the dialog
        parent_geometry = self.geometry()
        dialog_geometry = self.time_log_dialog.geometry()
        x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
        y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
        self.time_log_dialog.move(x, y)
        
        layout = QVBoxLayout(self.time_log_dialog)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Create text display area
        self.time_log_text_display = TextEdit()
        self.time_log_text_display.setReadOnly(True)
        self.time_log_text_display.setFont(QFont("Consolas", 13))
        
        self.last_time_log_count = 0
        
        self.refresh_time_log_display()
        
        layout.addWidget(self.time_log_text_display)
        
        self.time_log_dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a5568, stop:1 #2d3748);
                border-radius: 12px;
            }
        """)
        
        # Set fixed window opacity for transparency
        self.time_log_dialog.setWindowOpacity(0.99)
        
        # Override window flags to customize title bar
        self.time_log_dialog.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )
        
        # Setup auto-refresh timer
        self.time_log_refresh_timer = QTimer()
        self.time_log_refresh_timer.timeout.connect(self.refresh_time_log_display)
        self.time_log_refresh_timer.start(1000)  # Refresh every 1 second
        
        # Connect dialog close event to stop timer
        self.time_log_dialog.finished.connect(self.stop_time_log_refresh)
        
        self.time_log_dialog.show()  # Use show() instead of exec() to avoid blocking
    
    def load_historical_time_logs(self):
        """Load historical time logs from existing data buffer"""
        try:
            # Check if data_buffer exists and has content
            if hasattr(self, 'data_buffer') and self.data_buffer:
                for entry in self.data_buffer:
                    if "@@@ Time of" in entry:
                        # Use current timestamp for historical entries since original timestamp is not available
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_entry = f"[{timestamp}] {entry.strip()}"
                        self.time_log_data.append(log_entry)
                
                # Keep only the latest 1000 entries
                if len(self.time_log_data) > 1000:
                    self.time_log_data = self.time_log_data[-1000:]
                    
                print(f"Loaded {len(self.time_log_data)} historical time log entries")
        except Exception as e:
            print(f"Error loading historical time logs: {e}")
    

    def refresh_time_log_display(self):
        """Refresh time log display only when new data is available"""
        if hasattr(self, 'time_log_text_display') and self.time_log_text_display:
            current_count = len(self.time_log_data)
            
            # Only refresh if there's new data or it's the first time
            if not hasattr(self, 'last_time_log_count') or current_count != self.last_time_log_count:
                if self.time_log_data:
                    content = "\n".join([f"{entry}" for entry in self.time_log_data])
                    self.time_log_text_display.setPlainText(content)
                    # Auto scroll to bottom to show latest entries
                    scrollbar = self.time_log_text_display.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                else:
                    self.time_log_text_display.setPlainText("暂无时间日志记录\n\n等待接收包含 '@@@ Time of' 的数据...")
                
                # Update the last count
                self.last_time_log_count = current_count
    
    def stop_time_log_refresh(self):
        """Stop the time log refresh timer"""
        if hasattr(self, 'time_log_refresh_timer'):
            self.time_log_refresh_timer.stop()
    
    def toggle_input_size2(self):
        """Toggle between small and large input boxes for COM2"""
        if self.is_expanded2:
            self.large_send_edit2.setVisible(False) 
            self.expand_btn2.setIcon(FIF.UP)
            # Reset splitter sizes to original
            if hasattr(self.splitter2, 'setSizes'):
                self.splitter2.setSizes([2000, 100])
            self.is_expanded2 = False
        else:
            self.large_send_edit2.setVisible(True)
            self.expand_btn2.setIcon(FIF.DOWN )
            if hasattr(self.splitter2, 'setSizes'):
                self.splitter2.setSizes([2000, 500])
            self.is_expanded2 = True

    def toggle_send_mode2(self):
        """Toggle between HEX and STR sending modes for COM2"""
        if self.send_judge2.isChecked():
            self.send_judge2.setText("HEX")
            placeholder = "Enter hex data."
        else:
            self.send_judge2.setText("STR")
            placeholder = "Enter string data."
        
        self.send_line_edit2.setPlaceholderText(placeholder)
        self.large_send_edit2.setPlaceholderText(placeholder)

    def com2_send_data(self):
        """Send data through COM2 port based on selected mode"""
        try:
            # Check if serial port is available and open
            if not hasattr(self, 'serial2') or not self.serial2.is_open:
                InfoBar.error(
                    title='发送失败',
                    content='COM2串口未打开！',
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
            
            # Get text from active input box
            if self.is_expanded2:
                text = self.large_send_edit2.toPlainText().strip()
            else:
                text = self.send_line_edit2.text().strip()
                
            if not text:
                InfoBar.warning(
                    title='输入警告',
                    content='请输入要发送的数据！',
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            if self.send_judge2.isChecked():  # HEX mode
                # Remove spaces and convert hex string to bytes
                hex_string = text.replace(' ', '').replace('0x', '')
                if len(hex_string) % 2 != 0:
                    InfoBar.error(
                        title='格式错误',
                        content='无效的十六进制格式！长度必须为偶数。',
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    return
                data = bytes.fromhex(hex_string)
            else:  # STR mode
                data = text.encode('utf-8')
            
            self.serial2.write(data)
            InfoBar.success(
                    title='发送成功',
                    content='数据已成功发送！',
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
            )
            
        except Exception as e:
            InfoBar.error(
                title='发送失败',
                content=f'发送数据失败: {str(e)}',
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def toggle_input_size(self):
        if self.is_expanded:
            self.large_send_edit.setVisible(False)
            self.expand_btn.setIcon(FIF.UP)
            if hasattr(self.splitter, 'setSizes'):
                self.splitter.setSizes([2000, 100])
            self.is_expanded = False
        else:
            self.large_send_edit.setVisible(True)
            self.expand_btn.setIcon(FIF.DOWN )
            if hasattr(self.splitter, 'setSizes'):
                self.splitter.setSizes([2000, 500])
            self.is_expanded = True

    def toggle_send_mode(self):
        """Toggle between HEX and STR sending modes"""
        if self.send_judge.isChecked():
            self.send_judge.setText("HEX")
            placeholder = "Enter hex data (e.g., FF AA BB CC)"
        else:
            self.send_judge.setText("STR")
            placeholder = "Enter string data"
        
        # Update placeholder for both input boxes
        self.send_line_edit.setPlaceholderText(placeholder)
        self.large_send_edit.setPlaceholderText(placeholder)

    def toggle_output_format(self):
        """Toggle output format between STR and HEX for COM1"""
        self.output_format_str = not self.output_format_str
        if self.output_format_str:
            self.output_format_btn.setText("STR")
            self.output_format_btn.setToolTip("当前: STR格式，点击切换到HEX格式")
        else:
            self.output_format_btn.setText("HEX")
            self.output_format_btn.setToolTip("当前: HEX格式，点击切换到STR格式")
        
        # 同步更新串口读取线程的分割策略（STR: 按\n分割；HEX: 不分割）
        if hasattr(self, 'serial_thread') and self.serial_thread:
            try:
                self.serial_thread.set_split_on_newline(self.output_format_str)
            except Exception:
                pass
        
        # Refresh display with new format
        self.refresh_display_format()

    def toggle_output_format2(self):
        """Toggle output format between STR and HEX for COM2"""
        self.output_format_str2 = not self.output_format_str2
        if self.output_format_str2:
            self.output_format_btn2.setText("STR")
            self.output_format_btn2.setToolTip("当前: STR格式，点击切换到HEX格式")
        else:
            self.output_format_btn2.setText("HEX")
            self.output_format_btn2.setToolTip("当前: HEX格式，点击切换到STR格式")
        
        # 同步更新串口读取线程的分割策略（STR: 按\n分割；HEX: 不分割）
        if hasattr(self, 'serial_thread2') and self.serial_thread2:
            try:
                self.serial_thread2.set_split_on_newline(self.output_format_str2)
            except Exception:
                pass
        
        # Refresh display with new format
        self.refresh_display_format2()

    def refresh_display_format(self):
        """Refresh COM1 display area with current format"""
        # This function can be used to refresh the display when format changes
        # For now, it will only affect new incoming data
        pass

    def refresh_display_format2(self):
        """Refresh COM2 display area with current format"""
        # This function can be used to refresh the display when format changes
        # For now, it will only affect new incoming data
        pass

    def format_data_for_display(self, data, is_str_format=True):
        """Format data for display based on selected format"""
        try:
            if is_str_format:
                # STR format - decode as text
                if isinstance(data, bytes):
                    return data.decode('utf-8', errors='ignore')
                else:
                    return str(data)
            else:
                # HEX format - convert to hex string without any line break interpretation
                if isinstance(data, bytes):
                    # Convert each byte to 2-digit hex, separated by space
                    hex_parts = []
                    for byte in data:
                        hex_parts.append(f"{byte:02X}")
                    # Join with spaces without adding a newline to avoid misinterpreting 0A/0D as line breaks
                    return ' '.join(hex_parts)
                    
                elif isinstance(data, str):
                    # Convert string to bytes first, then to hex
                    return self.format_data_for_display(data.encode('utf-8'), is_str_format=False)
                else:
                    return str(data) + '\n'
        except Exception as e:
            print(f"Error formatting data: {str(e)}")
            return str(data) + '\n'

    def com1_send_data(self):
        """Send data through COM1 port based on selected mode"""
        try:
            # Check if serial port is available and open
            if not hasattr(self, 'serial_port') or not self.serial_port.is_open:
                InfoBar.error(
                    title='发送失败',
                    content='COM1串口未打开！',
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
            
            # Get text from active input box
            if self.is_expanded:
                text = self.large_send_edit.toPlainText().strip()
            else:
                text = self.send_line_edit.text().strip()
                
            if not text:
                InfoBar.warning(
                    title='输入警告',
                    content='请输入要发送的数据！',
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            if self.send_judge.isChecked():  # HEX mode
                # Remove spaces and convert hex string to bytes
                hex_string = text.replace(' ', '').replace('0x', '')
                if len(hex_string) % 2 != 0:
                    InfoBar.error(
                        title='格式错误',
                        content='无效的十六进制格式！长度必须为偶数。',
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    return
                data = bytes.fromhex(hex_string)
            else:  # STR mode
                data = text.encode('utf-8')
            
            self.serial_port.write(data)
            InfoBar.success(
                    title='发送成功',
                    content='数据已成功发送！',
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
            )
            
        except Exception as e:
            InfoBar.error(
                title='发送失败',
                content=f'发送数据失败: {str(e)}',
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    # BM: COM1 data handle
    def handle_serial_data(self, data):
        try:
            # Apply format conversion based on current setting
            if hasattr(self, 'output_format_str') and not self.output_format_str:
                # HEX format - format data and add line break at the end
                formatted_data = self.format_data_for_display(data, is_str_format=False)
                text = formatted_data  # Don't add \n here, let format_data_for_display handle it
            else:
                # STR format (default)
                text = data.decode('utf-8')
            
            self.log_worker.add_log_task("UwbLog", "info", text.strip())
            text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
            self.data_buffer.append(text)
            
            # Only process special patterns in STR mode
            if not hasattr(self, 'output_format_str') or self.output_format_str:
                # Collect time log data containing '@@@ Time of'
                if "@@@ Time of" in text:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"{text.strip()}"
                    self.time_log_data.append(log_entry)
                    # Keep only the latest 1000 entries to prevent memory issues
                    if len(self.time_log_data) > 1000:
                        self.time_log_data = self.time_log_data[-1000:]

                if "Write Card End" in text:
                    #"@@@ Time of Write Card End     = 00:14:520  │ 80D7 │  710 ms"
                    print("open door")
                    match = re.search(r"│\s*([0-9A-Fa-f]+)\s*│\s*(\d+)\s*ms", text)
                    if match:
                        address = match.group(1)
                        transaction_time = match.group(2)
                    
                    if hasattr(self, 'Address_label') and self.Address_label is not None:
                        self.Address_label.setText(f"{address}  -")
                    
                    if hasattr(self, 'Transaction_time_label') and self.Transaction_time_label is not None:
                        self.Transaction_time_label.setText(f"{transaction_time}ms")
                    
                    if hasattr(self, 'gate_animation') and self.gate_animation is not None:
                        self.gate_animation.trigger_gate_animation()
            if "@POSITION" in text:
                # print(f'接收到原始数据：{repr(text)}')
                try:
                    # Fix unquoted hex values in JSON (e.g., "mac": F4A6 -> "mac": "F4A6")
                    fixed_text = re.sub(r'"mac":\s*([A-Fa-f0-9]+)(?=\s*[,}])', r'"mac": "\1"', text)
                    
                    # Fix unquoted Link values (hex values like 3B5D)
                    fixed_text = re.sub(r'"Link":\s*([A-Fa-f0-9]+)(?=\s*[,}])', r'"Link": "\1"', fixed_text)
                    
                    # Fix unquoted CardNo values (long numbers without quotes)
                    fixed_text = re.sub(r'"CardNo":\s*([0-9A-Fa-f]+)(?=\s*[,}])', r'"CardNo": "\1"', fixed_text)
                    
                    # Fix empty values in JSON - handle various empty patterns
                    # Pattern 1: "CardNo": , -> "CardNo": null,
                    fixed_text = re.sub(r'"(CardNo|Balance)":\s*,', r'"\1": null,', fixed_text)
                    # Pattern 2: "CardNo": } -> "CardNo": null}
                    fixed_text = re.sub(r'"(CardNo|Balance)":\s*}', r'"\1": null}', fixed_text)
                    # Pattern 3: "CardNo":  , (with extra spaces) -> "CardNo": null,
                    fixed_text = re.sub(r'"(CardNo|Balance)":\s+,', r'"\1": null,', fixed_text)
                    # Pattern 4: Handle any field with empty value followed by comma or brace
                    fixed_text = re.sub(r'"([^"]+)":\s*([,}])', r'"\1": null\2', fixed_text)
                    
                    json_data = json.loads(fixed_text)
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    print(f"原始数据: {text}")
                    return
                # 提取用户坐标和MAC地址
                user_x = float(json_data.get('User-X', 0))
                user_y = float(json_data.get('User-Y', 0))
                user_z = float(json_data.get('User-Z', 0))
                user_mac = json_data.get('mac', 'default')  # 获取用户MAC地址
                
                # 提取卡号和余额信息
                card_no = json_data.get('CardNo')
                balance_raw = json_data.get('Balance')
                balance = None
                if balance_raw is not None:
                    try:
                        # 将余额从分转换为元（除以100）
                        balance = float(balance_raw) / 100.0
                    except (ValueError, TypeError):
                        balance = None
                
                new_red_length = int(json_data.get('RedAreaH', 0)) / 2
                new_blue_length = int(json_data.get('BlueAreaH', 0))
                refresh_needed = (getattr(self, 'red_length', None) != new_red_length) or (getattr(self, 'blue_length', None) != new_blue_length)
                self.red_length = new_red_length
                self.blue_length = new_blue_length

                # 仅当值发生变化时刷新位置视图
                if hasattr(self, 'position_view') and refresh_needed:
                    # print("refresh areas")
                    self.position_view.refresh_areas()
                
                # Map JSON keys to chart keys
                key_mapping = {
                    'master'   : 'Master',
                    'slave'    : 'Slave',
                    'nlos'     : 'nLos',
                    'rssi'     : 'RSSI',
                    'speed'    : 'Speed'
                }
                
                # Update data with correct key mapping
                for chart_key, json_key in key_mapping.items():
                    try:
                        value = int(json_data.get(json_key, 0))
                        self.uwb_data[chart_key].append(value)

                        if len(self.uwb_data[chart_key]) > 100:
                            self.uwb_data[chart_key] = self.uwb_data[chart_key][-100:]
                        
                        self.chart_thread.add_data(chart_key, value)
                            
                    except (ValueError, TypeError):
                        continue

                # 解析状态监控数据
                link_value = json_data.get('Link', 'FFFF')
                user_value = json_data.get('User', 0)
                auth_value = json_data.get('Auth', 0)
                trans_value = json_data.get('Trans', 0)
                dtpml_value = json_data.get('Dtpml', 0)
                
                # 更新状态卡片
                if hasattr(self, 'status_panel'):
                    self.update_status_card("LINK", link_value=link_value)
                    self.update_status_card("USER", used_value=user_value)
                    self.update_status_card("AUTH", used_value=auth_value)
                    self.update_status_card("TRANS", used_value=trans_value)
                    self.update_status_card("DTPML", used_value=dtpml_value)

                # Log data
                data_values = [
                    json_data.get('Master', 0),
                    json_data.get('Slave', 0),
                    json_data.get('nLos', 0),
                    json_data.get('RSSI', 0),
                    json_data.get('Speed', 0),
                    json_data.get('User-X', 0),
                    json_data.get('User-Y', 0),
                    json_data.get('User-Z', 0),
                    auth_value,
                    trans_value
                ]
                
                # 写入CSV
                csv_data = ",".join(str(val) for val in data_values)
                self.log_worker.add_log_task("data", "info", csv_data)
                
                # 缓存表格数据，延后批量插入
                if not hasattr(self, 'pending_table_rows'):
                    self.pending_table_rows = []
                self.pending_table_rows.append(data_values)

                # 更新多用户位置显示
                if hasattr(self, 'position_view'):
                    # 直接使用单用户更新方法，避免不必要的循环开销
                    self.position_view.update_position(user_x, user_y, user_mac)
                    
                    # 更新用户卡号和余额信息
                    if card_no is not None or balance is not None:
                        self.position_view.user_manager.update_user_card_info(user_mac, card_no, balance)
                    
                    # 定期清理不活跃的用户（每100次更新检查一次）
                    if not hasattr(self, '_cleanup_counter'):
                        self._cleanup_counter = 0
                    self._cleanup_counter += 1
                    if self._cleanup_counter >= 100:
                        self.position_view.user_manager.remove_inactive_users(timeout_seconds=30.0)
                        self._cleanup_counter = 0
                        
        except Exception as e:
            print(f"Error processing serial data: {str(e)}")

    def handle_serial_connection_lost(self, error_msg):
        """Handle serial connection lost for COM1"""
        try:
            # Update UI status to indicate disconnection
            # self.toggle_btn.setText("打开串口")
            
            # Clean up serial resources
            if hasattr(self, 'serial_thread'):
                self.serial_thread.stop()
                self.serial_thread = None
            if hasattr(self, 'serial_port'):
                self.serial_port.close()
                self.serial_port = None
                
            # Show warning message
            # QMessageBox.warning(self, "串口连接丢失", f"COM1串口连接意外断开: {error_msg}")
        except Exception as e:
            print(f"处理串口连接丢失错误: {str(e)}")

    def update_display(self):
        """更新显示区域"""
        if self.data_buffer:
            cursor         = self.serial_display.textCursor()
            scrollbar      = self.serial_display.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # Apply log level filtering
            filtered_buffer = []
            for message in self.data_buffer:
                if not self.should_filter_log_message(message):
                    filtered_buffer.append(message)
            
            if not filtered_buffer:
                self.data_buffer.clear()
                return
            
            text = ''.join(filtered_buffer)
            
            # 如果选中了时间戳选项，为每行添加时间戳
            if self.timestamp.isChecked():
                # 在HEX模式下，避免使用splitlines()，因为它会将0A字节当作换行符
                if hasattr(self, 'output_format_str') and not self.output_format_str:
                    # HEX模式：将整个文本作为一个整体添加时间戳，并在末尾补一个换行用于分隔每个数据块
                    timestamp = QDateTime.currentDateTime().toString('[yyyy-MM-dd hh:mm:ss.zzz] ')
                    text = timestamp + text + '\n'
                else:
                    # STR模式：正常使用splitlines()
                    lines = text.splitlines(True) 
                    timestamp = QDateTime.currentDateTime().toString('[yyyy-MM-dd hh:mm:ss.zzz] ')
                    text = ''.join(timestamp + line for line in lines)
            else:
                # 未开启时间戳，但HEX模式下也需要在每个块末尾补换行，避免所有数据拼在一行
                if hasattr(self, 'output_format_str') and not self.output_format_str:
                    text = text + '\n'
            
            self.serial_display.setUpdatesEnabled(False)
            cursor.movePosition(QTextCursor.MoveOperation.End)
            insert_pos = cursor.position()
            cursor.insertText(text)
            self.data_buffer.clear()
            self.serial_display.setUpdatesEnabled(True)

            if self.highlight_config: 
                doc       = self.serial_display.document()
                start_pos = insert_pos
                end_pos   = insert_pos + len(text)
                block     = doc.findBlock(start_pos)

                if not block.isValid(): 
                    block = doc.begin()

                while block.isValid() and block.position() < end_pos:
                    block_text  = block.text()
                    block_start = block.position()

                    for keyword, color in self.highlight_config.items():
                        if not keyword: continue 

                        highlight_fmt = QTextCharFormat()
                        highlight_fmt.setBackground(color) 
                        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
                        text_color = QColor("#000000") if luminance > 0.5 else QColor("#FFFFFF")
                        highlight_fmt.setForeground(text_color)
                        highlight_fmt.setFontWeight(QFont.Weight.Bold)

                        idx = block_text.find(keyword)
                        while idx != -1:
                            abs_pos = block_start + idx
                            if abs_pos >= start_pos and abs_pos + len(keyword) <= end_pos:
                                highlight_cursor = QTextCursor(doc)
                                highlight_cursor.setPosition(abs_pos)
                                highlight_cursor.setPosition(abs_pos + len(keyword), QTextCursor.MoveMode.KeepAnchor)
                                highlight_cursor.mergeCharFormat(highlight_fmt)
                            idx = block_text.find(keyword, idx + len(keyword))
                    block = block.next()
            
            if self.auto_scroll.isChecked():
                scrollbar.setValue(current_scroll)
            else:
                scrollbar.setValue(scrollbar.maximum())
            
            # Update search results if there's an active search
            self.update_search_results()

        if hasattr(self, 'pending_table_rows') and len(self.pending_table_rows) >= 5:
            for data_values in self.pending_table_rows:
                row_position = self.data_table.rowCount()
                self.data_table.insertRow(row_position)
                for col, value in enumerate(data_values):
                    self.data_table.setItem(row_position, col, QTableWidgetItem(str(value)))
                if self.data_table.rowCount() > 100:
                    self.data_table.removeRow(0)
            self.data_table.scrollToBottom()
            self.pending_table_rows.clear()
    
    def update_display2(self):
        """更新显示区域2"""
        if self.data_buffer2:
            cursor         = self.serial_display2.textCursor()
            scrollbar      = self.serial_display2.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            # Apply log level filtering
            filtered_buffer = []
            for message in self.data_buffer2:
                if not self.should_filter_log_message(message):
                    filtered_buffer.append(message)
            
            if not filtered_buffer:
                self.data_buffer2.clear()
                return
            
            text = ''.join(filtered_buffer)
            
            # 如果选中了时间戳选项，为每行添加时间戳
            if self.timestamp2.isChecked():
                # 在HEX模式下，避免使用splitlines()，因为它会将0A字节当作换行符
                if hasattr(self, 'output_format_str2') and not self.output_format_str2:
                    # HEX模式：将整个文本作为一个整体添加时间戳，并在末尾补一个换行用于分隔每个数据块
                    timestamp = QDateTime.currentDateTime().toString('[yyyy-MM-dd hh:mm:ss.zzz] ')
                    text = timestamp + text + '\n'
                else:
                    # STR模式：正常使用splitlines()
                    lines     = text.splitlines(True)
                    timestamp = QDateTime.currentDateTime().toString('[yyyy-MM-dd hh:mm:ss.zzz] ')
                    text      = ''.join(timestamp + line for line in lines)
            else:
                # 未开启时间戳，但HEX模式下也需要在每个块末尾补换行，避免所有数据拼在一行
                if hasattr(self, 'output_format_str2') and not self.output_format_str2:
                    text = text + '\n'
            
            self.serial_display2.setUpdatesEnabled(False)
            cursor.movePosition(QTextCursor.MoveOperation.End)
            insert_pos = cursor.position()
            cursor.insertText(text)
            self.data_buffer2.clear()
            self.serial_display2.setUpdatesEnabled(True)

            # 处理高亮
            if self.highlight_config:
                doc       = self.serial_display2.document()
                start_pos = insert_pos
                end_pos   = insert_pos + len(text)
                block     = doc.findBlock(start_pos)

                if not block.isValid():
                    block = doc.begin()

                while block.isValid() and block.position() < end_pos:
                    block_text  = block.text()
                    block_start = block.position()
                    for keyword, color in self.highlight_config.items():
                        if not keyword:
                            continue
                        highlight_fmt = QTextCharFormat()
                        highlight_fmt.setBackground(color)
                        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
                        text_color = QColor("#000000") if luminance > 0.5 else QColor("#FFFFFF")
                        highlight_fmt.setForeground(text_color)
                        highlight_fmt.setFontWeight(QFont.Weight.Bold)
                        
                        idx = block_text.find(keyword)
                        while idx != -1:
                            abs_pos = block_start + idx
                            if abs_pos >= start_pos and abs_pos + len(keyword) <= end_pos:
                                highlight_cursor = QTextCursor(doc)
                                highlight_cursor.setPosition(abs_pos)
                                highlight_cursor.setPosition(abs_pos + len(keyword), QTextCursor.MoveMode.KeepAnchor)
                                highlight_cursor.setCharFormat(highlight_fmt)
                            idx = block_text.find(keyword, idx + len(keyword))
                    block = block.next()
            
            if self.auto_scroll2.isChecked():
                scrollbar.setValue(current_scroll)
            else:
                scrollbar.setValue(scrollbar.maximum())
            
            # Update search results if there's an active search
            self.update_search_results2()

    def toggle_theme(self):
        self.background_image_index = (self.background_image_index + 1) % len(self.background_images)
        self.background_image = self.background_images[self.background_image_index]
        # 切换背景图片并刷新
        background_path = Path(__file__).parent / self.background_image
        if background_path.exists():
            background = QPixmap(str(background_path))
            self.background_cache = background.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.last_window_size = self.size()
        self._save_unified_config()
        self.update()
    
    def apply_theme(self):   # BM: THEME
        theme = self.current_theme
        self.setStyleSheet(f"""
            MSFluentWindow {{
                background-color: transparent;
            }}
            QMainWindow {{
                background-color: transparent;
            }}
            QWidget {{
                background-color: rgba(33, 42, 54, 0.397);
                color           : {theme['text']};
            }}
            QScrollBar:vertical {{
                background   : transparent;
                width        : 5px;
                margin       : 2px 0 2px 0;
                border-radius: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3da9fc, stop:1 #1e293b
                );
                min-height   : 24px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #90caf9, stop:1 #3da9fc
                );
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height    : 0;
                background: none;
                border    : none;
            }}
            QScrollBar:horizontal {{
                background   : transparent;
                height       : 5px;
                margin       : 0 2px 0 2px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3da9fc, stop:1 #1e293b
                );
                min-width    : 24px;
                border-radius: 0px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #90caf9, stop:1 #3da9fc
                );
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width     : 0;
                background: none;
                border    : none;
            }}
            QSplitter::handle {{
                background: transparent;
                border    : none;
                min-height: 5px;
            }}
            QSplitter::handle:vertical {{
                height: 5px;
            }}
            QSplitter::handle:horizontal {{
                width: 5px;
            }}
        """)

    def show_protocol_parse_dialog(self):
        """Show TLV protocol parsing dialog - Dark themed input dialog"""
        QTimer.singleShot(0, self._create_tlv_input_dialog)
    
    def _create_tlv_input_dialog(self): # BM: create tlv input dialog
        self.input_dialog = QDialog(self)
        # Remove title bar and window decorations
        self.input_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.input_dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.input_dialog.resize(450, 200)
        
        # Center the dialog
        parent_geometry = self.geometry()
        dialog_geometry = self.input_dialog.geometry()
        x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
        y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
        self.input_dialog.move(x, y)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 52, 54, 0.95);
                border-radius: 12px;
                border: 1px solid rgba(116, 125, 140, 0.3);
            }
        """)
        
        layout = QVBoxLayout(self.input_dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        
        # Inner layout
        inner_layout = QVBoxLayout(main_widget)
        inner_layout.setContentsMargins(15, 15, 15, 15)
        inner_layout.setSpacing(15)
        
        self.protocol_input = TextEdit()
        self.protocol_input.setMinimumHeight(100)
        self.protocol_input.setFont(QFont("Consolas", 11))
        self.protocol_input.setPlaceholderText("")
        
        inner_layout.addWidget(self.protocol_input)
        
        # Button layout - only confirm and cancel
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = PushButton("取消")
        cancel_btn.setFont(QFont("Microsoft YaHei", 10))
        cancel_btn.clicked.connect(self.input_dialog.close)
        
        confirm_btn = PrimaryPushButton("确认")
        confirm_btn.setFont(QFont("Microsoft YaHei", 10))
        confirm_btn.clicked.connect(self._proceed_to_tlv_parse)

        
        dcs_btn = PushButton("DCS")
        dcs_btn.setFont(QFont("Microsoft YaHei", 10))
        dcs_btn.clicked.connect(self._calculate_dcs)
        
        # Add 0x format button
        format_0x_btn = PushButton("0x")
        format_0x_btn.setFont(QFont("Microsoft YaHei", 10))
        format_0x_btn.clicked.connect(self._format_with_0x)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(format_0x_btn)
        button_layout.addWidget(dcs_btn)
        button_layout.addWidget(confirm_btn)
        inner_layout.addLayout(button_layout)
        
        # Make dialog draggable
        self.input_dialog.mousePressEvent = self._dialog_mouse_press
        self.input_dialog.mouseMoveEvent = self._dialog_mouse_move
        
        self.input_dialog.show()
    
    def _dialog_mouse_press(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.input_dialog.frameGeometry().topLeft()
            event.accept()
    
    def _dialog_mouse_move(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.input_dialog.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def _proceed_to_tlv_parse(self):
        """Proceed to TLV parsing step after input"""
        input_text = self.protocol_input.toPlainText().strip()
        if not input_text:
            # Show error message
            error_label = QLabel("请输入TLV协议数据")
            error_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            return
        
        # Store input text and close input dialog
        self.stored_protocol_input = input_text
        self.input_dialog.close()
        
        # Show TLV parsing result dialog
        QTimer.singleShot(100, self._create_tlv_result_dialog)
    
    def _calculate_dcs(self):
        """Calculate DCS (Data Check Sum) for hex string input"""
        input_text = self.protocol_input.toPlainText().strip()
        if not input_text:
            # Show error message in a simple dialog
            msg = QMessageBox(self)
            msg.setWindowTitle("错误")
            msg.setText("请输入十六进制数据")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()
            return
        
        try:
            # Clean and validate hex string
            clean_str = input_text.replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "").upper()
            
            # Validate hex string
            if not all(c in "0123456789ABCDEF" for c in clean_str):
                raise ValueError("输入包含非十六进制字符")
            
            if len(clean_str) % 2 != 0:
                raise ValueError("十六进制字符串长度必须为偶数")
            
            # Convert to byte array and calculate checksum
            bytes_data = [int(clean_str[i:i+2], 16) for i in range(0, len(clean_str), 2)]
            
            # Calculate sum (only keep lowest byte)
            checksum = sum(bytes_data) & 0xFF
            
            # Calculate DCS (checksum + dcs = 0x00, so dcs = 0x100 - checksum)
            dcs = (0x100 - checksum) & 0xFF
            
            # Add DCS result to the input field
            current_text = self.protocol_input.toPlainText()
            result_text = f"∑: 0x{checksum:02X}   DCS: 0x{dcs:02X}"
            
            # Add result on a new line
            if not current_text.endswith('\n'):
                current_text += '\n'
            current_text += result_text
            
            self.protocol_input.setPlainText(current_text)
            
            # Move cursor to end and show status
            cursor = self.protocol_input.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.protocol_input.setTextCursor(cursor)
            
            # Show brief status message using InfoBar instead of statusBar
            InfoBar.success(
                title="DCS计算完成",
                content=f"∑=0x{checksum:02X}, DCS=0x{dcs:02X}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            # Show error message
            msg = QMessageBox(self)
            msg.setWindowTitle("计算错误")
            msg.setText(f"DCS计算失败: {str(e)}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()
    
    def _copy_dcs_value(self, dcs_value, button):
        """Copy DCS value to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(dcs_value)
        
        # Show brief confirmation
        original_text = button.text()
        button.setText("已复制!")
        QTimer.singleShot(1000, lambda: button.setText(original_text))
    
    def _format_with_0x(self):
        """Format input data with 0x prefix"""
        try:
            # Get current text from input field
            current_text = self.protocol_input.toPlainText().strip()
            if not current_text:
                return
            
            # Remove existing spaces and format
            numbers = current_text.replace(" ", "").replace("0x", "").replace(",", "")
            
            # Validate hex characters
            if not all(c in '0123456789ABCDEFabcdef' for c in numbers):
                # Show error message
                msg = QMessageBox(self)
                msg.setWindowTitle("格式错误")
                msg.setText("输入包含非十六进制字符，请检查输入数据")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.exec()
                return
            
            # Format numbers in pairs with 0x prefix
            formatted_numbers = [numbers[i:i+2] for i in range(0, len(numbers), 2)]
            formatted_numbers = [f"0x{num.upper()}" for num in formatted_numbers]
            result = ",".join(formatted_numbers)
            
            # Update the input field with formatted result
            self.protocol_input.setPlainText(result)
            
            # Show length information using InfoBar instead of statusBar
            byte_count = len(numbers) // 2
            InfoBar.success(
                title="格式化完成",
                content=f"已格式化为0x前缀格式，共 {byte_count} 字节",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            # Show error message
            msg = QMessageBox(self)
            msg.setWindowTitle("格式化错误")
            msg.setText(f"数据格式化失败: {str(e)}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()
    
    
    def _create_tlv_result_dialog(self):
        """Create and show TLV parsing result dialog (second step) - Dark themed"""
        self.result_dialog = QDialog(self)
        # Remove title bar and window decorations
        self.result_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.result_dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.result_dialog.resize(650, 500)
        
        # Center the dialog
        parent_geometry = self.geometry()
        dialog_geometry = self.result_dialog.geometry()
        x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
        y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
        self.result_dialog.move(x, y)
        
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(44, 62, 80, 0.98),
                    stop:1 rgba(52, 73, 94, 0.98));
                border-radius: 10px;
                border: 1px solid rgba(149, 165, 166, 0.3);
            }
        """)
        
        layout = QVBoxLayout(self.result_dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        
        # Inner layout
        inner_layout = QVBoxLayout(main_widget)
        inner_layout.setContentsMargins(10, 10, 10, 10)
        inner_layout.setSpacing(10)
        
        # Parse and display results
        try:
            result_html = self.parse_tlv_protocol(self.stored_protocol_input)
            
            # Create dark themed result display
            result_widget = TextEdit()
            result_widget.setReadOnly(True)
            result_widget.setFont(QFont("Consolas", 11))
            result_widget.setHtml(result_html)
            
        except Exception as e:
            result_widget = QLabel(f"TLV解析错误: {str(e)}")
        
        inner_layout.addWidget(result_widget)
        
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        back_btn = PushButton("重新输入")
        back_btn.setFont(QFont("Microsoft YaHei", 9))
        back_btn.clicked.connect(self._back_to_input)
        
        copy_btn = PrimaryPushButton("复制结果")
        copy_btn.setFont(QFont("Microsoft YaHei", 9))
        copy_btn.clicked.connect(self._copy_tlv_result)
        
        cancel_btn = PushButton("取消")
        cancel_btn.setFont(QFont("Microsoft YaHei", 9))
        cancel_btn.clicked.connect(self.result_dialog.close)

        
        action_layout.addWidget(back_btn)
        action_layout.addStretch()
        action_layout.addWidget(copy_btn)
        action_layout.addWidget(cancel_btn)
        inner_layout.addLayout(action_layout)
        
        # Make dialog draggable
        self.result_dialog.mousePressEvent = self._result_dialog_mouse_press
        self.result_dialog.mouseMoveEvent = self._result_dialog_mouse_move
        
        self.result_dialog.show()
    
    def _result_dialog_mouse_press(self, event):
        """Handle mouse press for dragging result dialog"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.result_drag_position = event.globalPosition().toPoint() - self.result_dialog.frameGeometry().topLeft()
            event.accept()
    
    def _result_dialog_mouse_move(self, event):
        """Handle mouse move for dragging result dialog"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'result_drag_position'):
            self.result_dialog.move(event.globalPosition().toPoint() - self.result_drag_position)
            event.accept()
    
    def _back_to_input(self):
        """Go back to input dialog"""
        self.result_dialog.close()
        QTimer.singleShot(100, self._create_tlv_input_dialog)
    
    def _copy_tlv_result(self):
        """Copy TLV parsing result to clipboard - only data (length + data)"""
        if hasattr(self, 'stored_protocol_input'):
            try:
                # Parse the protocol to get structured data
                clean_str = self.stored_protocol_input.replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "").upper()
                
                # Validate hex string
                if not all(c in "0123456789ABCDEF" for c in clean_str):
                    return
                
                if len(clean_str) % 2 != 0:
                    return
                
                # Convert to byte array
                try:
                    bytes_data = [int(clean_str[i:i+2], 16) for i in range(0, len(clean_str), 2)]
                except ValueError:
                    return
                
                if len(bytes_data) < 1:
                    return
                
                packet_count = bytes_data[0]
                current_pos = 1
                copy_data = []
                
                # Extract only length and data for each packet
                packet_lines = []
                for i in range(packet_count):
                    if current_pos >= len(bytes_data):
                        break
                    
                    packet_line = []
                    
                    # Check if we have at least 2 bytes for length
                    if current_pos + 1 >= len(bytes_data):
                        if current_pos < len(bytes_data):
                            # Only one byte available for length
                            packet_line.append(f"{bytes_data[current_pos]:02X}")
                        if packet_line:
                            packet_lines.append(' '.join(packet_line))
                        break
                    
                    # Read 2-byte length
                    length_low = bytes_data[current_pos]
                    length_high = bytes_data[current_pos + 1]
                    data_length = (length_high << 8) | length_low
                    current_pos += 2
                    
                    # Add length bytes to packet line
                    packet_line.append(f"{length_low:02X}{length_high:02X}")
                    
                    # Check if we have enough data
                    if current_pos + data_length > len(bytes_data):
                        # Not enough data, extract what we have
                        available_data = bytes_data[current_pos:] if current_pos < len(bytes_data) else []
                        if available_data:
                            data_hex = ''.join(f'{b:02X}' for b in available_data)
                            packet_line.append(data_hex)
                        packet_lines.append(' '.join(packet_line))
                        break
                    
                    # Extract complete data
                    packet_data = bytes_data[current_pos:current_pos + data_length]
                    current_pos += data_length
                    
                    if packet_data:
                        data_hex = ''.join(f'{b:02X}' for b in packet_data)
                        packet_line.append(data_hex)
                    
                    # Add this packet's line to the result
                    packet_lines.append(' '.join(packet_line))
                
                # Join all packet lines with newlines
                result_text = '\n'.join(packet_lines)
                
                clipboard = QApplication.clipboard()
                clipboard.setText(result_text)
                
                # Show brief confirmation
                sender = self.sender()
                original_text = sender.text()
                sender.setText("已复制!")
                QTimer.singleShot(1000, lambda: sender.setText(original_text))
            except Exception as e:
                pass
    
    def clear_protocol_input(self):
        """Clear protocol input field"""
        if hasattr(self, 'protocol_input'):
            self.protocol_input.clear()
    
    def parse_tlv_protocol(self, protocol_str):  # BM: Parse TLV
        """Parse TLV protocol string - Standard TLV format"""
        # Remove spaces and convert to uppercase
        clean_str = protocol_str.replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "").upper()
        
        # Validate hex string
        if not all(c in "0123456789ABCDEF" for c in clean_str):
            raise ValueError("输入包含非十六进制字符")
        
        if len(clean_str) % 2 != 0:
            raise ValueError("十六进制字符串长度必须为偶数")
        
        # Convert to byte array
        try:
            bytes_data = [int(clean_str[i:i+2], 16) for i in range(0, len(clean_str), 2)]
        except ValueError:
            raise ValueError("十六进制字符串格式错误")
        
        if len(bytes_data) < 1:
            raise ValueError("数据长度不足")
        
        result = []
        # Clean container without background colors
        result.append("<div style='font-family: Segoe UI, Arial, sans-serif; color: #ffffff; margin: 0; padding: 0;'>")
        
        # Original data block - simple and clean
        original_hex = ''.join(f'{b:02X}' for b in bytes_data)
        result.append(f"""
            <div style='
                padding: 10px;
                margin-bottom: 10px;
                border: 2px solid #e9c707;
            '>
                <div style='
                    color: #2dbaf1;
                    font-weight: 600;
                    font-size: 15px;
                    margin-bottom: 3px;
                '>原始数据</div>
                <div style='
                    color: #e9c707;
                    font-family: Consolas, Monaco, Courier New, monospace;
                    font-size: 14px;
                    word-break: break-all;
                    line-height: 1.0;
                    padding: 10px;
                    border: 1px solid #666666;
                    margin-bottom: 15px;
                '>{original_hex}</div>
            </div>
        """)
        
        # Parse TLV format: first byte = number of packets, then each packet = 2 bytes length + data
        if len(bytes_data) < 1:
            raise ValueError("数据长度不足，至少需要1个字节表示包数量")
        
        packet_count = bytes_data[0]
        
        current_pos = 1
        parsed_packets = []
        incomplete_data = False  # Flag to track if data is incomplete
        
        for i in range(packet_count):
            if current_pos >= len(bytes_data):
                # No more data available, but don't raise error
                incomplete_data = True
                break
            
            # Check if we have at least 2 bytes for length
            if current_pos + 1 >= len(bytes_data):
                # Incomplete length field, parse what we have
                incomplete_data = True
                if current_pos < len(bytes_data):
                    # Only one byte available for length
                    length_low = bytes_data[current_pos]
                    parsed_packets.append({
                        'index': i + 1,
                        'length': None,  # Unknown length
                        'length_bytes': (length_low, None),
                        'data': [],
                        'incomplete': True,
                        'error': '长度字段不完整'
                    })
                break
            
            # Read 2-byte length (little-endian: low byte first, then high byte)
            length_low = bytes_data[current_pos]
            length_high = bytes_data[current_pos + 1]
            data_length = (length_high << 8) | length_low
            current_pos += 2
            
            # Check if we have enough data
            if current_pos + data_length > len(bytes_data):
                # Not enough data, extract what we have
                incomplete_data = True
                available_data = bytes_data[current_pos:] if current_pos < len(bytes_data) else []
                parsed_packets.append({
                    'index': i + 1,
                    'length': data_length,
                    'length_bytes': (length_low, length_high),
                    'data': available_data,
                    'incomplete': True,
                    'expected_length': data_length,
                    'actual_length': len(available_data)
                })
                break
            
            # Extract data
            packet_data = bytes_data[current_pos:current_pos + data_length]
            current_pos += data_length
            
            parsed_packets.append({
                'index': i + 1,
                'length': data_length,
                'length_bytes': (length_low, length_high),
                'data': packet_data,
                'incomplete': False
            })
        
        # Add warning message if data is incomplete
        if incomplete_data:
            result.append(f"""
                <div style='
                    padding: 10px;
                    margin-bottom: 10px;
                    border: 2px solid #ff6b6b;
                    background-color: rgba(255, 107, 107, 0.1);
                '>
                    <div style='
                        color: #ff6b6b;
                        font-weight: 600;
                        font-size: 15px;
                        margin-bottom: 3px;
                    '>⚠️ 数据不完整警告</div>
                    <div style='
                        color: #ffcc02;
                        font-size: 14px;
                    '>协议包数据长度不足，已解析可用部分</div>
                </div>
            """)
        
        # Display each packet as a simple block
        for i, packet in enumerate(parsed_packets):
            # Determine border color based on completeness
            border_color = "#ff6b6b" if packet.get('incomplete', False) else "#0080ff"
            
            result.append(f"""
                <div style='
                    margin-bottom: 1px;
                    border: 2px solid {border_color};
                '>
                    <div style='
                        padding: 16px 5px;
                        border-bottom: 1px solid #666666;
                    '>
                        <div style='
                            color: #2dbaf1;
                            font-weight: 600;
                            font-size: 15px;
                        '>第{packet['index']}包{' (不完整)' if packet.get('incomplete', False) else ''}</div>
                    </div>
                    
                    <div style='padding: 20px;'>
                        <div style='margin-bottom: 1px;'>
            """)
            
            # Display length bytes with special handling for incomplete data
            if packet.get('incomplete', False) and 'error' in packet:
                # Case: incomplete length field
                length_byte_1 = packet['length_bytes'][0] if packet['length_bytes'][0] is not None else '??'
                length_byte_2 = packet['length_bytes'][1] if packet['length_bytes'][1] is not None else '??'
                result.append(f"""
                                <span style='color: #ff6b6b; font-family: Consolas, Monaco, Courier New, monospace; font-weight: 600; font-size: 16px;'>{length_byte_1:02X if isinstance(length_byte_1, int) else length_byte_1}{length_byte_2 if length_byte_2 == '??' else f'{length_byte_2:02X}'}</span>
                                <span style='color: #ff6b6b; font-size: 12px; margin-left: 10px;'>({packet['error']})</span>
                """)
            elif packet.get('incomplete', False):
                # Case: incomplete data
                result.append(f"""
                                <span style='color: #ff6b6b; font-family: Consolas, Monaco, Courier New, monospace; font-weight: 600; font-size: 16px;'>{packet['length_bytes'][0]:02X}{packet['length_bytes'][1]:02X}</span>
                                <span style='color: #ff6b6b; font-size: 12px; margin-left: 10px;'>(期望 {packet['expected_length']} 字节，实际 {packet['actual_length']} 字节)</span>
                """)
            else:
                # Case: complete data
                result.append(f"""
                                <span style='color: #0080ff; font-family: Consolas, Monaco, Courier New, monospace; font-weight: 600; font-size: 16px;'>{packet['length_bytes'][0]:02X}{packet['length_bytes'][1]:02X}</span>
                """)
            
            result.append("""
                            </div>
                        </div>
                        <div>
            """)
            
            # Display data content
            if packet['data']:
                data_hex = ''.join(f'{b:02X}' for b in packet['data'])
                data_color = "#ff9999" if packet.get('incomplete', False) else "#e9c707"
                result.append(f"""
                                <div style='
                                    font-family: Consolas, Monaco, Courier New, monospace;
                                    color: {data_color};
                                    font-size: 14px;
                                    word-break: break-all;
                                    line-height: 1.0;
                                    margin-bottom: 15px;
                                '>{data_hex}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """)
            else:
                no_data_text = "数据不完整" if packet.get('incomplete', False) else "暂无数据"
                result.append(f"""
                                <div style='
                                    color: #999999;
                                    font-style: italic;
                                    text-align: center;
                                    font-size: 14px;
                                    padding: 8px;
                                '>{no_data_text}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """)
        
        result.append("</div>")
        
        return "".join(result)

    def create_settings_page(self): # BM: Setting Page
        settings_page = ScrollArea()
        settings_page.setObjectName("Settings")
        
        view = QWidget()
        vBoxLayout = QVBoxLayout(view)
        vBoxLayout.setContentsMargins(20, 20, 20, 20)
        vBoxLayout.setSpacing(20)
        
        self.appearanceGroup = SettingCardGroup('外观设置', view)
        
        self.themeCard = PushSettingCard(
            text='深色',
            icon=FIF.BRUSH,
            title='应用主题',
            content='深色主题已启用'
        )
        self.themeCard.clicked.connect(self.onThemeCardClicked)
        
        self.backgroundCard = PushSettingCard(
            text='切换背景',
            icon=FIF.PHOTO,
            title='背景图片',
        )
        self.backgroundCard.clicked.connect(self.on_background_toggle)
        self.appearanceGroup.addSettingCard(self.themeCard)
        self.appearanceGroup.addSettingCard(self.backgroundCard)
        
        # 背景透明度进度条（0~100）
        opacityRow = QWidget(view)
        opacityLayout = QHBoxLayout(opacityRow)
        opacityLayout.setContentsMargins(0, 0, 0, 0)
        opacityLayout.setSpacing(12)
        self.opacityLabel = BodyLabel('背景透明度')
        self.opacitySlider = QSlider(Qt.Orientation.Horizontal)
        self.opacitySlider.setRange(0, 100)
        current_opacity = int(getattr(self, 'background_opacity', 1.0) * 100)
        self.opacitySlider.setValue(current_opacity)
        self.opacityValueLabel = BodyLabel(f"{current_opacity}%")
        self.opacitySlider.valueChanged.connect(self.on_opacity_slider_changed)
        opacityLayout.addWidget(self.opacityLabel)
        opacityLayout.addWidget(self.opacitySlider, 1)
        opacityLayout.addWidget(self.opacityValueLabel)
        
        self.applicationGroup = SettingCardGroup('应用设置', view)
        
        self.logLevelCard = OptionsSettingCard(
            configItem=self.config.logLevelItem,
            icon=FIF.FILTER,
            title='LOG LEVEL',
            content='设置显示的Log级别',
            texts=['ALL', 'MIN']
        )
        self.logLevelCard.optionChanged.connect(self.on_log_level_changed)
        
        self.highlightCard = PushSettingCard(
            text='配置高亮',
            icon=FIF.PALETTE,
            title='高亮配置',
            content='配置关键字高亮显示的颜色和样式'
        )
        self.highlightCard.clicked.connect(self.open_highlight_config_dialog)
        
        self.helpCard = PushSettingCard(
            text='查看帮助',
            icon=FIF.HELP,
            title='帮助支持',
            content='获取应用使用帮助和支持信息'
        )
        self.helpCard.clicked.connect(self.show_help_dialog)
        
        # About card
        self.aboutCard = PushSettingCard(
            text='关于应用',
            icon=FIF.INFO,
            title='关于UWBDash',
            content='查看应用版本和开发信息'
        )
        self.aboutCard.clicked.connect(self.show_about_dialog)
        
        self.applicationGroup.addSettingCard(self.logLevelCard)
        self.applicationGroup.addSettingCard(self.highlightCard)
        self.applicationGroup.addSettingCard(self.helpCard)
        self.applicationGroup.addSettingCard(self.aboutCard)
        
        # About group
        self.aboutGroup = SettingCardGroup('关于', view)
        
        # Version info card
        self.versionCard = PushSettingCard(
            text='检查更新',
            icon=FIF.UPDATE,
            title='版本信息',
            content=f'{APP_NAME}_{APP_VERSION}'
        )
        self.versionCard.clicked.connect(self.checkUpdate)
        
        # Project homepage card
        self.homepageCard = HyperlinkCard(
            url='https://ximing766.github.io/my-project-doc/',
            text='访问项目主页',
            icon=FIF.LINK,
            title='项目主页',
            content='访问GitHub项目页面获取更多信息'
        )
        
        self.aboutGroup.addSettingCard(self.versionCard)
        self.aboutGroup.addSettingCard(self.homepageCard)
        
        # Layout setup
        vBoxLayout.addWidget(self.appearanceGroup)
        vBoxLayout.addWidget(opacityRow)
        vBoxLayout.addSpacing(10)
        vBoxLayout.addWidget(self.applicationGroup)
        vBoxLayout.addSpacing(10)
        vBoxLayout.addWidget(self.aboutGroup)
        vBoxLayout.addStretch(1)
        
        settings_page.setWidget(view)
        settings_page.setWidgetResizable(True)
        settings_page.setStyleSheet('QScrollArea{background: transparent; border: none}')
        
        return settings_page
    
    def onThemeCardClicked(self):
        """Theme card clicked slot"""
        try:
            # Cycle through themes
            current_theme = 'dark' if isDarkTheme() else 'light'
            if current_theme == 'light':
                setTheme(Theme.DARK)
                self.themeCard.button.setText('深色')
                self.themeCard.setContent('深色主题已启用')
                theme_name = '深色'
            else:
                setTheme(Theme.LIGHT)
                self.themeCard.button.setText('浅色')
                self.themeCard.setContent('浅色主题已启用')
                theme_name = '浅色'
                
            InfoBar.success(
                title='主题已切换',
                content=f'已切换到{theme_name}主题',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except RuntimeError as e:
            # Handle the dictionary changed size during iteration error
            print(f"Theme switching error: {e}")
            InfoBar.error(
                title='主题切换失败',
                content='主题切换时发生错误，请稍后重试',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
    def checkUpdate(self):
        """Check for updates"""
        InfoBar.info(
            title='检查更新',
            content='当前已是最新版本',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def on_background_toggle(self):
        """Handle background image toggle from settings page"""
        try:
            # Use backgrounds from config.json instead of hardcoded list
            if not self.background_images:
                # Fallback to default if no backgrounds configured
                self.background_images = [
                    "pic\\D_1.jpg",
                    "pic\\D_2.jpg",
                    "pic\\D_3.png",
                    "pic\\D_4.jpg",
                    "pic\\D_5.jpg",
                    "pic\\D_6.png",
                    "pic\\D_7.jpg",
                    "pic\\D_8.jpg",
                    "pic\\D_9.jpg",
                    "pic\\D10.jpg",
                    "pic\\D_11.jpg",
                    "pic\\L_1.png"
                ]
            
            current_index = self.background_images.index(self.background_image) if self.background_image in self.background_images else 0
            next_index = (current_index + 1) % len(self.background_images)
            self.background_image = self.background_images[next_index]
            
            # Save configuration
            self._save_unified_config()
            
            # Clear background cache to force reload
            self.background_cache = None
            
            # Update the display
            self.update()
            
            # Show success message
            InfoBar.success(
                title='背景已切换',
                content=f'٩(•̤̀ᵕ•̤́๑)ᵒᵏᵎᵎᵎᵎ',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            print(f"Background toggle error: {e}")
            InfoBar.error(
                title='背景切换失败',
                content='背景切换时发生错误，请检查图片文件',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def on_opacity_slider_changed(self, value: int):
        """从设置页滑块更新背景透明度 (0~100)"""
        try:
            self.background_opacity = max(0.0, min(1.0, value / 100.0))
            if hasattr(self, 'opacityValueLabel'):
                self.opacityValueLabel.setText(f"{int(self.background_opacity * 100)}%")
            # 保存配置并刷新界面
            self._save_unified_config()
            self.update()
        except Exception as e:
            print(f"更新背景透明度失败: {e}")

    def on_quick_send_selected(self, text):
        """Handle quick send selection for COM1"""
        if text and text in self.quick_send_data:
            # Always add to LineEdit first, then check if expanded for TextEdit
            self.send_line_edit.setText(self.quick_send_data[text])
            # If expanded, also add to large text edit
            if self.is_expanded:
                self.large_send_edit.setPlainText(self.quick_send_data[text])

    def on_quick_send_selected2(self, text):
        """Handle quick send selection for COM2"""
        if text and text in self.quick_send_data:
            self.send_line_edit2.setText(self.quick_send_data[text])
            if self.is_expanded2:
                self.large_send_edit2.setPlainText(self.quick_send_data[text])

    def show_quick_send_config(self):
        """Show quick send configuration dialog"""
        dialog = QuickSendConfigDialog(self.quick_send_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.quick_send_data = dialog.get_config()
            self.update_quick_send_combo()
            self.save_quick_send_config()

    def update_quick_send_combo(self):
        if hasattr(self, 'quick_send_combo'):
            self.quick_send_combo.clear()
            for key in self.quick_send_data.keys():
                self.quick_send_combo.addItem(key)
        if hasattr(self, 'quick_send_combo2'):
            self.quick_send_combo2.clear()
            for key in self.quick_send_data.keys():
                self.quick_send_combo2.addItem(key)
    
    def load_quick_send_config(self):
        if hasattr(self, 'quick_send_data'):
            self.update_quick_send_combo()
        else:
            self.quick_send_data = {}

    def save_quick_send_config(self):
        """Save quick send configuration to unified config file"""
        try:
            self._save_unified_config()
        except Exception as e:
            print(f"Failed to save quick send config: {e}")

class ThemeManager:
    # 📌📁❌🔸
    LIGHT_THEME = {
        "nav_bg"      : "rgba(248, 249, 250,  0.35)",
        "nav_item"    : "#c29500",
        "nav_selected": "rgba(218, 237, 244, 1)",
        "accent"      : "#4a90e2",
        "bg"          : "rgba(223, 238, 240, 0.35)",
        "text"        : "#2d3436",
        "title_bg"    : "#424e54"
    }

    DARK_THEME = {
        "nav_bg"      : "rgba(45, 52, 54,  0.35)",
        "nav_item"    : "#c29500",
        "nav_selected": "rgba(74, 74, 74,  0.35)",
        "accent"      : "#6c5ce797",
        "bg"          : "rgba(53, 59, 64, 0.35)",
        "text"        : "#f8f9fa",
        "title_bg"    : "#01285600"
    }

class HighlightConfigDialog(QDialog):
    """配置高亮关键字和颜色的对话框"""
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置高亮关键字")
        self.setMinimumWidth(450)
        self.config = current_config.copy() # 使用传入配置的副本

        layout = QVBoxLayout(self)

        # 表格显示关键字和颜色
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["关键字", "颜色预览", "颜色值 (Hex)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 100)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # 禁止直接编辑
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # 按钮区域
        button_layout = QHBoxLayout()
        add_btn = PrimaryPushButton("添加")
        add_btn.clicked.connect(self.add_keyword)
        edit_btn = PushButton("编辑")
        edit_btn.clicked.connect(self.edit_keyword)
        remove_btn = PushButton("删除")
        remove_btn.clicked.connect(self.remove_keyword)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # OK / Cancel 按钮
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

        self.populate_table()

    def populate_table(self):
        """用当前配置填充表格"""
        self.table.setRowCount(0) # 清空表格
        for keyword, color in self.config.items():
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            # 关键字
            self.table.setItem(row_position, 0, QTableWidgetItem(keyword))

            color_label = QLabel()
            color_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #555;") # 直接设置背景色和边框
            self.table.setCellWidget(row_position, 1, color_label)

            # 颜色值
            hex_color = color.name().upper()
            self.table.setItem(row_position, 2, QTableWidgetItem(hex_color))

    def add_keyword(self):
        keyword, ok = QInputDialog.getText(self, "添加关键字", "输入关键字:")
        if ok and keyword:
            color = QColorDialog.getColor(Qt.GlobalColor.yellow, self, "选择高亮颜色")
            if color.isValid():
                self.config[keyword] = color
                self.populate_table()

    def edit_keyword(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要编辑的行。")
            return

        row         = selected_rows[0].row()
        old_keyword = self.table.item(row, 0).text()
        old_color   = self.config[old_keyword]

        new_keyword, ok = QInputDialog.getText(self, "编辑关键字", "输入新关键字:", QLineEdit.EchoMode.Normal, old_keyword)
        if not ok or not new_keyword:
            return 

        new_color = QColorDialog.getColor(old_color, self, "选择新的高亮颜色")
        if not new_color.isValid():
            return 

        if old_keyword != new_keyword:
            del self.config[old_keyword]
        self.config[new_keyword] = new_color
        self.populate_table()

    def remove_keyword(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的行。")
            return

        row = selected_rows[0].row()
        keyword = self.table.item(row, 0).text()

        reply = QMessageBox.question(self, "确认删除", f"确定要删除关键字 '{keyword}' 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            del self.config[keyword]
            self.populate_table()

    def get_config(self):
        return self.config

class QuickSendConfigDialog(QDialog):
    """Quick send configuration dialog"""
    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置快捷发送")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.config = current_config.copy()

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["名称", "数据"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 150)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        add_btn = PrimaryPushButton("添加")
        add_btn.clicked.connect(self.add_item)
        edit_btn = PushButton("编辑")
        edit_btn.clicked.connect(self.edit_item)
        remove_btn = PushButton("删除")
        remove_btn.clicked.connect(self.remove_item)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

        self.populate_table()

    def populate_table(self):
        """Populate table with current config"""
        self.table.setRowCount(len(self.config))
        for row, (key, value) in enumerate(self.config.items()):
            self.table.setItem(row, 0, QTableWidgetItem(key))
            self.table.setItem(row, 1, QTableWidgetItem(value))

    def add_item(self):
        """Add new key-value pair"""
        dialog = QuickSendItemDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            key, value = dialog.get_data()
            if key and key not in self.config:
                self.config[key] = value
                self.populate_table()
            elif key in self.config:
                InfoBar.warning(
                    title='重复的名称',
                    content='该名称已存在，请使用其他名称',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )

    def edit_item(self):
        """Edit selected item"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            key_item = self.table.item(current_row, 0)
            value_item = self.table.item(current_row, 1)
            if key_item and value_item:
                old_key = key_item.text()
                dialog = QuickSendItemDialog(self, old_key, value_item.text())
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    new_key, new_value = dialog.get_data()
                    if new_key:
                        # Remove old key if changed
                        if old_key != new_key and old_key in self.config:
                            del self.config[old_key]
                        self.config[new_key] = new_value
                        self.populate_table()

    def remove_item(self):
        """Remove selected item"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            key_item = self.table.item(current_row, 0)
            if key_item:
                key = key_item.text()
                if key in self.config:
                    del self.config[key]
                    self.populate_table()

    def get_config(self):
        """Get current configuration"""
        return self.config

class QuickSendItemDialog(QDialog):
    """Dialog for adding/editing quick send items"""
    def __init__(self, parent=None, key="", value=""):
        super().__init__(parent)
        self.setWindowTitle("快捷发送项")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(BodyLabel("名称:"))
        self.key_edit = LineEdit()
        self.key_edit.setText(key)
        self.key_edit.setPlaceholderText("输入显示名称")
        key_layout.addWidget(self.key_edit)
        layout.addLayout(key_layout)

        # Value input
        value_layout = QHBoxLayout()
        value_layout.addWidget(BodyLabel("数据:"))
        self.value_edit = LineEdit()
        self.value_edit.setText(value)
        value_layout.addWidget(self.value_edit)
        layout.addLayout(value_layout)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

    def get_data(self):
        """Get key and value"""
        return self.key_edit.text().strip(), self.value_edit.text().strip()

class LogWorker(QThread):
    def __init__(self, logger):
        super().__init__()
        self.logger    = logger
        self.log_queue = queue.Queue()
        
    def add_log_task(self, log_type, level, message):
        self.log_queue.put(("log", log_type, level, message))
        
    def run(self):
        while True:
            try:
                task = self.log_queue.get(timeout=1)
                if task[0] == "log":
                    _, log_type, level, message = task
                    self.logger.log_to(log_type, level, message)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Log thread error: {str(e)}")

class ChartUpdateThread(QThread):
    update_chart = pyqtSignal(str, int)  # 发送图表更新信号
    
    def __init__(self):
        super().__init__()
        self.running    = True
        self.data_queue = queue.Queue()
    
    def add_data(self, chart_key, value):
        self.data_queue.put((chart_key, value))
    
    def stop(self):
        self.running = False
    
    def run(self):
        while self.running:
            try:
                chart_key, value = self.data_queue.get(timeout=0.1)
                self.update_chart.emit(chart_key, value)
            except queue.Empty:
                continue

class FindThread(QThread):
    result_ready = pyqtSignal(int, int, list)  # 当前索引, 总数, 所有匹配位置

    def __init__(self, text, keyword, current_pos, forward):
        super().__init__()
        self.text        = text
        self.keyword     = keyword
        self.current_pos = current_pos
        self.forward     = forward

    def run(self):
        positions = []
        idx       = self.text.find(self.keyword)
        while idx != -1:
            positions.append(idx)
            idx = self.text.find(self.keyword, idx + len(self.keyword))
        total = len(positions)
        current = 0
        if total > 0:
            # 定位到下一个/上一个
            if self.forward:
                for i, pos in enumerate(positions):
                    if pos > self.current_pos:
                        current = i
                        break
                else:
                    current = 0  # 循环到第一个
            else:
                for i in reversed(range(total)):
                    if positions[i] < self.current_pos:
                        current = i
                        break
                else:
                    current = total - 1  # 循环到最后一个
        self.result_ready.emit(current, total, positions)

class SubwayGateAnimation(QWidget):
    """地铁闸机开门关门动画组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setMinimumSize(300, 200)
        
        self.gate_state = "closed"  # closed, opening, open, closing
        self.left_door_angle = 0    # 左门角度 (0-90)
        self.right_door_angle = 0   # 右门角度 (0-90)
        self.display_scale = 1.0    # 显示缩放因子，用于扩展模式
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        
        self.animation_speed = 3.5  # 帧 (increased by 1/3 for faster animation)
        self.open_duration = 2000   # 开门保持时间(ms)
        self.open_timer = QTimer()
        self.open_timer.timeout.connect(self.start_closing)
        self.open_timer.setSingleShot(True)
        
        self.glow_intensity = 0.0  # 发光强度
        self.scan_line_pos = 0     # 扫描线位置
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self.update_particles)
        self.particles = []        # 粒子列表
        self.frame_count = 0       # 帧计数器
        
    def set_display_scale(self, scale):
        """设置显示缩放因子"""
        self.display_scale = scale
        self.update()
        
    def trigger_gate_animation(self):
        """触发闸机开门动画"""
        if self.gate_state == "closed":
            self.gate_state = "opening"
            self.animation_timer.start(16)  # ~60fps
            self.glow_intensity = 1.0       # 开始发光效果
            self.particle_timer.start(100)  # 10fps
            self.generate_particles()       # 生成粒子特效
            
    def update_animation(self):
        """更新动画帧"""
        import math
        
        if self.gate_state == "opening":
            # 使用缓动函数使动画更流畅
            progress = self.left_door_angle / 90.0
            eased_progress = 1 - math.pow(1 - progress, 3)  # ease-out cubic
            
            self.left_door_angle += self.animation_speed
            self.right_door_angle += self.animation_speed
            
            # 发光效果渐强
            self.glow_intensity = min(1.0, self.glow_intensity + 0.05)
            
            if self.left_door_angle >= 90:
                self.left_door_angle = 90
                self.right_door_angle = 90
                self.gate_state = "open"
                self.animation_timer.stop()
                self.open_timer.start(self.open_duration)
                
        elif self.gate_state == "closing":
            self.left_door_angle -= self.animation_speed
            self.right_door_angle -= self.animation_speed
            
            # 发光效果渐弱
            self.glow_intensity = max(0.0, self.glow_intensity - 0.03)
            
            if self.left_door_angle <= 0:
                self.left_door_angle = 0
                self.right_door_angle = 0
                self.gate_state = "closed"
                self.animation_timer.stop()
                self.particle_timer.stop()
                self.glow_intensity = 0.0
                
        # 更新扫描线位置
        self.scan_line_pos = (self.scan_line_pos + 2) % self.height()
        self.frame_count += 1
        
        self.update()
        
    def start_closing(self):
        """开始关门动画"""
        self.gate_state = "closing"
        self.animation_timer.start(16)
        self.generate_particles()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        self.draw_tech_background(painter)
        
        # 计算中心位置
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # 绘制闸机框架
        self.draw_tech_frame(painter, center_x, center_y)
        
        # 绘制闸机门
        self.draw_gate_doors(painter, center_x, center_y)
        
        if self.gate_state != "closed":
            self.draw_particles(painter)
            self.draw_scan_lines(painter)
            if self.glow_intensity > 0:
                self.draw_glow_effect(painter, center_x, center_y)
        
    def draw_gate_doors(self, painter, center_x, center_y):
        """绘制横向地铁闸机门"""
        # 应用显示缩放
        door_width = int(80 * self.display_scale)   # 横向门的宽度
        door_height = int(15 * self.display_scale)  # 横向门的高度
        
        import math
        
        # 计算门的横向偏移（基于角度）
        left_offset = math.sin(math.radians(self.left_door_angle)) * (60 * self.display_scale)
        right_offset = math.sin(math.radians(self.right_door_angle)) * (60 * self.display_scale)
        
        # 绘制左右两扇横向门
        for door_side in ['left', 'right']:
            if door_side == 'left':
                door_x = int(center_x - door_width - left_offset)
                door_y = center_y - door_height // 2
            else:
                door_x = int(center_x + right_offset)
                door_y = center_y - door_height // 2
            
            # 创建门的渐变效果（横向渐变）
            door_gradient = QLinearGradient(door_x, door_y, door_x + door_width, door_y)
            
            if self.gate_state in ["open", "opening"]:
                # 开启状态 - 蓝绿渐变
                door_gradient.setColorAt(0, QColor(0, 180, 255, 220))
                door_gradient.setColorAt(0.5, QColor(0, 220, 180, 240))
                door_gradient.setColorAt(1, QColor(0, 255, 150, 240))
                border_color = QColor(0, 255, 200, 200)
            else:
                # 关闭状态 - 深蓝灰渐变
                door_gradient.setColorAt(0, QColor(108, 92, 231, 220))
                door_gradient.setColorAt(0.5, QColor(74, 74, 74, 240))
                door_gradient.setColorAt(1, QColor(53, 59, 64, 240))
                border_color = QColor(108, 92, 231, 150)
            
            painter.setBrush(door_gradient)
            painter.setPen(QPen(border_color, int(2 * self.display_scale)))
            
            # 绘制横向门体
            door_rect = QRect(door_x, door_y, door_width, door_height)
            corner_radius = int(6 * self.display_scale)
            painter.drawRoundedRect(door_rect, corner_radius, corner_radius)
            
            # 横向中央线
            line_margin = int(10 * self.display_scale)
            painter.setPen(QPen(QColor(255, 255, 255, 120), max(1, int(1 * self.display_scale))))
            painter.drawLine(door_x + line_margin, door_y + door_height // 2, door_x + door_width - line_margin, door_y + door_height // 2)
            
            # 绘制门端传感器
            sensor_size = int(8 * self.display_scale)
            if door_side == 'left':
                sensor_x = door_x + door_width - sensor_size // 2
            else:
                sensor_x = door_x - sensor_size // 2
            sensor_y = center_y - sensor_size // 2
            
            # 传感器发光效果
            sensor_gradient = QLinearGradient(sensor_x, sensor_y, sensor_x + sensor_size, sensor_y + sensor_size)
            if self.gate_state in ["open", "opening"]:
                sensor_gradient.setColorAt(0, QColor(0, 255, 200, 255))
                sensor_gradient.setColorAt(1, QColor(0, 150, 255, 200))
            else:
                sensor_gradient.setColorAt(0, QColor(108, 92, 231, 255))
                sensor_gradient.setColorAt(1, QColor(74, 74, 74, 200))
                
            painter.setBrush(sensor_gradient)
            painter.setPen(QPen(QColor(255, 255, 255, 180), max(1, int(1 * self.display_scale))))
            painter.drawEllipse(sensor_x, sensor_y, sensor_size, sensor_size)
            
            # 传感器中心点
            center_size = int(4 * self.display_scale)
            center_offset = int(2 * self.display_scale)
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(sensor_x + center_offset, sensor_y + center_offset, center_size, center_size)
            
            # 绘制门的阴影效果
            shadow_offset = int(2 * self.display_scale)
            shadow_color = QColor(0, 0, 0, 60)
            painter.setBrush(shadow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            shadow_rect = QRect(door_x, door_y + shadow_offset, door_width, door_height)
            painter.drawRoundedRect(shadow_rect, corner_radius, corner_radius)
        
    def draw_tech_background(self, painter):
        """绘制高科技背景"""
        import math
        
        # 动态深色渐变背景
        bg_gradient = QLinearGradient(0, 0, self.width(), self.height())
        
        # 根据状态调整背景色调
        if self.gate_state in ["open", "opening"]:
            bg_gradient.setColorAt(0, QColor(10, 25, 35, 180))
            bg_gradient.setColorAt(0.3, QColor(15, 35, 45, 200))
            bg_gradient.setColorAt(0.7, QColor(20, 40, 50, 200))
            bg_gradient.setColorAt(1, QColor(10, 25, 35, 180))
            grid_color = QColor(0, 180, 255, 40)
        else:
            bg_gradient.setColorAt(0, QColor(45, 52, 54, 180))
            bg_gradient.setColorAt(0.3, QColor(53, 59, 64, 200))
            bg_gradient.setColorAt(0.7, QColor(74, 74, 74, 200))
            bg_gradient.setColorAt(1, QColor(45, 52, 54, 180))
            grid_color = QColor(108, 92, 231, 40)
        
        painter.setBrush(bg_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # 绘制动态网格背景（应用缩放）
        grid_size = int(25 * self.display_scale)
        grid_alpha = int(30 + 20 * math.sin(self.frame_count * 0.05))
        grid_line_width = max(1, int(1 * self.display_scale))
        painter.setPen(QPen(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), grid_alpha), grid_line_width))
        
        # 垂直网格线
        for x in range(0, self.width(), grid_size):
            # 添加闪烁效果
            line_alpha = int(grid_alpha + 30 * math.sin(self.frame_count * 0.1 + x * 0.01))
            painter.setPen(QPen(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), max(0, min(255, line_alpha))), grid_line_width))
            painter.drawLine(x, 0, x, self.height())
            
        # 水平网格线
        for y in range(0, self.height(), grid_size):
            line_alpha = int(grid_alpha + 30 * math.sin(self.frame_count * 0.1 + y * 0.01))
            painter.setPen(QPen(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), max(0, min(255, line_alpha))), grid_line_width))
            painter.drawLine(0, y, self.width(), y)
        
        # 绘制数据流线条（应用缩放）
        flow_line_width = max(1, int(2 * self.display_scale))
        painter.setPen(QPen(grid_color, flow_line_width))
        flow_speed = 3
        flow_spacing = int(50 * self.display_scale)
        flow_y_spacing = int(40 * self.display_scale)
        flow_y_start = int(30 * self.display_scale)
        for i in range(5):
            flow_x = (self.frame_count * flow_speed + i * flow_spacing) % (self.width() + 100) - 50
            flow_y = flow_y_start + i * flow_y_spacing
            if flow_y < self.height():
                # 数据流点（应用缩放）
                dot_spacing = int(15 * self.display_scale)
                dot_size = int(4 * self.display_scale)
                dot_height = int(2 * self.display_scale)
                for j in range(8):
                    dot_x = flow_x - j * dot_spacing
                    if 0 <= dot_x <= self.width():
                        dot_alpha = int(200 * (1 - j / 8.0))
                        painter.setBrush(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), dot_alpha))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawEllipse(dot_x - dot_size//2, flow_y - dot_height//2, dot_size, dot_height)
    
    def draw_tech_frame(self, painter, center_x, center_y):
        """绘制闸机框架"""
        import math
        
        # 动态颜色根据状态变化
        if self.gate_state in ["open", "opening"]:
            primary_color = QColor(0, 180, 255)
            secondary_color = QColor(0, 255, 200)
            accent_color = QColor(0, 255, 150)
        else:
            primary_color = QColor(74, 74, 74)
            secondary_color = QColor(108, 92, 231)
            accent_color = QColor(53, 59, 64)
        
        # 绘制底座平台（应用缩放）
        base_width = int(200 * self.display_scale)
        base_height = int(20 * self.display_scale)
        base_y_offset = int(60 * self.display_scale)
        base_half_width = int(100 * self.display_scale)
        
        base_gradient = QLinearGradient(center_x - base_half_width, center_y + base_y_offset, 
                                       center_x + base_half_width, center_y + base_y_offset + base_height)
        base_gradient.setColorAt(0, QColor(40, 50, 70, 200))
        base_gradient.setColorAt(0.5, QColor(60, 70, 90, 240))
        base_gradient.setColorAt(1, QColor(40, 50, 70, 200))
        
        painter.setBrush(base_gradient)
        painter.setPen(QPen(primary_color, int(2 * self.display_scale)))
        base_radius = int(10 * self.display_scale)
        painter.drawRoundedRect(center_x - base_half_width, center_y + base_y_offset, 
                               base_width, base_height, base_radius, base_radius)
        
        # 立柱尺寸（应用缩放）
        pillar_width = int(25 * self.display_scale)
        pillar_height = int(140 * self.display_scale)
        pillar_y_offset = int(70 * self.display_scale)
        pillar_radius = int(8 * self.display_scale)
        left_pillar_x = int(center_x - 90 * self.display_scale)
        right_pillar_x = int(center_x + 65 * self.display_scale)
        
        # 左侧立柱 
        left_pillar_gradient = QLinearGradient(left_pillar_x, center_y - pillar_y_offset, 
                                              left_pillar_x + pillar_width, center_y + pillar_y_offset)
        left_pillar_gradient.setColorAt(0, QColor(80, 100, 140, 220))
        left_pillar_gradient.setColorAt(0.3, QColor(100, 120, 160, 250))
        left_pillar_gradient.setColorAt(0.7, QColor(90, 110, 150, 250))
        left_pillar_gradient.setColorAt(1, QColor(70, 90, 130, 220))
        
        painter.setBrush(left_pillar_gradient)
        painter.setPen(QPen(primary_color, int(3 * self.display_scale)))
        painter.drawRoundedRect(left_pillar_x, center_y - pillar_y_offset, 
                               pillar_width, pillar_height, pillar_radius, pillar_radius)
        
        # 右侧立柱 
        right_pillar_gradient = QLinearGradient(right_pillar_x, center_y - pillar_y_offset, 
                                               right_pillar_x + pillar_width, center_y + pillar_y_offset)
        right_pillar_gradient.setColorAt(0, QColor(80, 100, 140, 220))
        right_pillar_gradient.setColorAt(0.3, QColor(100, 120, 160, 250))
        right_pillar_gradient.setColorAt(0.7, QColor(90, 110, 150, 250))
        right_pillar_gradient.setColorAt(1, QColor(70, 90, 130, 220))
        
        painter.setBrush(right_pillar_gradient)
        painter.setPen(QPen(primary_color, int(3 * self.display_scale)))
        painter.drawRoundedRect(right_pillar_x, center_y - pillar_y_offset, 
                               pillar_width, pillar_height, pillar_radius, pillar_radius)
        
        # 装饰线条 
        glow_alpha = int(100 + 30 * math.sin(self.frame_count * 0.1))
        painter.setPen(QPen(QColor(secondary_color.red(), secondary_color.green(), secondary_color.blue(), glow_alpha), max(1, int(1 * self.display_scale))))
        
        # 立柱中央线条（应用缩放）
        line_offset_x = int(77 * self.display_scale)
        line_offset_y = int(50 * self.display_scale)
        painter.drawLine(center_x - line_offset_x, center_y - line_offset_y, center_x - line_offset_x, center_y + line_offset_y)
        painter.drawLine(center_x + line_offset_x, center_y - line_offset_y, center_x + line_offset_x, center_y + line_offset_y)
        
        # 在立柱顶部绘制状态指示LED（应用缩放）
        led_size = int(6 * self.display_scale)
        led_y_offset = int(60 * self.display_scale)
        led_positions = [(center_x - line_offset_x, center_y - led_y_offset), (center_x + line_offset_x, center_y - led_y_offset)]
        
        for i, (led_x, led_y) in enumerate(led_positions):
            # LED发光效果
            if self.gate_state in ["open", "opening"]:
                led_color = accent_color
                led_alpha = 255
            elif self.gate_state == "closing":
                led_color = QColor(255, 200, 0)  # 黄色警告
                led_alpha = 200
            else:
                led_color = QColor(100, 100, 100)
                led_alpha = 100
                
            painter.setBrush(QColor(led_color.red(), led_color.green(), led_color.blue(), led_alpha))
            painter.setPen(QPen(QColor(255, 255, 255, 150), max(1, int(1 * self.display_scale))))
            painter.drawEllipse(led_x - led_size//2, led_y - led_size//2, led_size, led_size)
        
        # 绘制传感器阵列（应用缩放）
        sensor_offset_x = int(82 * self.display_scale)
        sensor_offset_y = int(30 * self.display_scale)
        sensor_positions = [
            (center_x - sensor_offset_x, center_y - sensor_offset_y),
            (center_x - sensor_offset_x, center_y),
            (center_x - sensor_offset_x, center_y + sensor_offset_y),
            (center_x + sensor_offset_x, center_y - sensor_offset_y),
            (center_x + sensor_offset_x, center_y),
            (center_x + sensor_offset_x, center_y + sensor_offset_y)
        ]
        
        for i, (sx, sy) in enumerate(sensor_positions):
            # 传感器闪烁效果
            blink_alpha = int(100 + 100 * math.sin(self.frame_count * 0.15 + i * 0.5))
            sensor_color = QColor(accent_color.red(), accent_color.green(), accent_color.blue(), blink_alpha)
            
            painter.setBrush(sensor_color)
            painter.setPen(QPen(QColor(255, 255, 255, 180), max(1, int(1 * self.display_scale))))
            # 应用缩放的传感器大小
            sensor_size = int(6 * self.display_scale)
            sensor_half_size = int(3 * self.display_scale)
            painter.drawEllipse(sx - sensor_half_size, sy - sensor_half_size, sensor_size, sensor_size)
    
    def draw_scan_lines(self, painter):
        """绘制扫描线效果"""
        import math
        
        # 根据状态调整扫描线颜色
        if self.gate_state in ["open", "opening"]:
            scan_color = QColor(0, 255, 200)
        else:
            scan_color = QColor(255, 150, 100)
        
        # 主扫描线 - 水平移动（应用缩放）
        scan_alpha = int(120 + 80 * math.sin(self.frame_count * 0.15))
        main_line_width = max(1, int(3 * self.display_scale))
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), scan_alpha), main_line_width))
        
        # 主扫描线
        main_scan_y = self.scan_line_pos
        painter.drawLine(0, main_scan_y, self.width(), main_scan_y)
        
        # 副扫描线
        secondary_scan_y = (self.scan_line_pos + self.height()//2) % self.height()
        secondary_line_width = max(1, int(2 * self.display_scale))
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), scan_alpha//2), secondary_line_width))
        painter.drawLine(0, secondary_scan_y, self.width(), secondary_scan_y)
        
        # 垂直扫描线 - 左右移动
        vertical_scan_x = (self.frame_count * 3) % (self.width() + 100) - 50
        if 0 <= vertical_scan_x <= self.width():
            vertical_line_width = max(1, int(2 * self.display_scale))
            painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), scan_alpha//3), vertical_line_width))
            painter.drawLine(vertical_scan_x, 0, vertical_scan_x, self.height())
        
        # 雷达扫描效果（圆形）（应用缩放）
        center_x = self.width() // 2
        center_y = self.height() // 2
        base_radar_radius = int((50 + 30 * math.sin(self.frame_count * 0.08)) * self.display_scale)
        
        radar_line_width = max(1, int(2 * self.display_scale))
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), 60), radar_line_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - base_radar_radius, center_y - base_radar_radius, 
                           base_radar_radius * 2, base_radar_radius * 2)
        
        # 雷达扫描臂
        radar_angle = (self.frame_count * 4) % 360
        radar_end_x = center_x + base_radar_radius * math.cos(math.radians(radar_angle))
        radar_end_y = center_y + base_radar_radius * math.sin(math.radians(radar_angle))
        
        radar_arm_width = max(1, int(3 * self.display_scale))
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), 150), radar_arm_width))
        painter.drawLine(center_x, center_y, int(radar_end_x), int(radar_end_y))
        
        # 扫描点效果（应用缩放）
        for i in range(3):
            point_radius = int((20 + i * 15) * self.display_scale)
            point_alpha = int(100 - i * 30)
            point_line_width = max(1, int(1 * self.display_scale))
            painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), point_alpha), point_line_width))
            painter.drawEllipse(int(radar_end_x) - point_radius, int(radar_end_y) - point_radius,
                               point_radius * 2, point_radius * 2)
    
    def draw_glow_effect(self, painter, center_x, center_y):
        """绘制发光效果"""
        import math
        
        # 创建径向渐变发光（应用缩放）
        glow_radius = int(100 * self.glow_intensity * self.display_scale)
        glow_gradient = QLinearGradient(center_x - glow_radius, center_y - glow_radius,
                                       center_x + glow_radius, center_y + glow_radius)
        
        if self.gate_state in ["open", "opening"]:
            glow_color = QColor(0, 255, 150, int(50 * self.glow_intensity))
        else:
            glow_color = QColor(255, 100, 100, int(50 * self.glow_intensity))
            
        glow_gradient.setColorAt(0, glow_color)
        glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(glow_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - glow_radius), int(center_y - glow_radius),
                   int(glow_radius * 2), int(glow_radius * 2))
    
    def generate_particles(self):
        """生成粒子特效"""
        import random
        
        for _ in range(15):
            particle = {
                'x': random.randint(0, self.width()),
                'y': random.randint(0, self.height()),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'life': random.uniform(0.5, 1.0),
                'size': random.uniform(2 * self.display_scale, 5 * self.display_scale)  # 应用缩放
            }
            self.particles.append(particle)
    
    def update_particles(self):
        """更新粒子状态"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.02
            
            if (particle['life'] <= 0 or 
                particle['x'] < 0 or particle['x'] > self.width() or
                particle['y'] < 0 or particle['y'] > self.height()):
                self.particles.remove(particle)
        
        self.update()
    
    def draw_particles(self, painter):
        """绘制粒子效果"""
        for particle in self.particles:
            alpha = int(255 * particle['life'])
            if self.gate_state in ["open", "opening"]:
                color = QColor(0, 255, 150, alpha)
            else:
                color = QColor(255, 100, 100, alpha)
                
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(particle['x']), int(particle['y']),
                               int(particle['size']), int(particle['size']))
        
    

class SerialReadThread(QThread):
    data_received = pyqtSignal(bytes)
    connection_lost = pyqtSignal(str)  # Add signal for connection lost
    
    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running     = False
        # 是否按换行符分割数据（STR模式：True；HEX模式：False）
        self.split_on_newline = True
        self.delimiter = b"\n"
    
    def set_split_on_newline(self, enable: bool):
        self.split_on_newline = bool(enable)
        
    def run(self):
        self.running = True
        buffer       = bytearray()
        while self.running and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    # 等待一小段时间，让数据完整到达
                    time.sleep(0.05)
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if not data:
                        pass
                    elif self.split_on_newline:
                        # 行模式：按换行符分包（保留换行符）
                        buffer.extend(data)
                        while self.delimiter in buffer:
                            line_end = buffer.find(self.delimiter)
                            # 提取完整的行（包括换行符）
                            line = bytes(buffer[:line_end + 1])
                            buffer = buffer[line_end + 1:]
                            if line.strip():  # 忽略空行
                                self.data_received.emit(line)
                    else:
                        # 原始模式：不按换行符分包，直接发送数据块
                        self.data_received.emit(data)
            except Exception as e:
                print(f"串口读取错误: {str(e)}")
                self.connection_lost.emit(str(e))  # Emit signal when connection is lost
                break
            time.sleep(0.01)  # 降低CPU占用
            
    def stop(self):
        self.running = False
        self.wait()

class Particle:
    def __init__(self, bounds_rect):
        self.bounds = bounds_rect
        self.reset()

    def reset(self):
        self.pos = QPointF(random.uniform(0, self.bounds.width()),
                         random.uniform(0, self.bounds.height()))
        # 粒子速度
        self.vel = QPointF(random.uniform(-0.5, 0.5), random.uniform(-0.8, -1.8))

        self.color = QColor(random.randint(100, 200), 
                          random.randint(100, 200), 
                          random.randint(200, 255), 
                          random.randint(30, 120))
        # 粒子尺寸
        self.size = random.uniform(3.0, 6.0)

    def update(self):
        self.pos += self.vel
        if not self.bounds.contains(self.pos):
            self.pos = QPointF(random.uniform(0, self.bounds.width()), self.bounds.height() -1)
            self.vel = QPointF(random.uniform(-0.5, 0.5), random.uniform(-0.8, -1.8))

class TestPage(QWidget):
    """UWB多测试点双锚点参数测试页面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        # 基础15个点位坐标（相对闸机中心）
        self.base_points = [
            (0, -40), (0, 0), (1, 10), (0, 10), (-1, 10),
            (1, 60), (0, 60), (-1, 60), (1, 110), (0, 110),
            (-1, 110), (1, 160), (0, 160), (-1, 160), (0, 210)
        ]
        self.A0_Anchor = [0, 0, 0]      # Slave锚点坐标
        self.A1_Anchor = [0, 0, 0]      # Master锚点坐标
        self.test_points = {}           # 生成的测试点字典
        self.point_distances = {'A': {}, 'B': {}}  # 标准距离缓存
        self.csv_path = Path(__file__).parent / "test_log.csv"
        self.init_ui()
        self.update_test_points()

    

    def on_point_changed(self):
        """当点位序号或高度切换时，仅刷新Res显示（使用实时均值）"""
        self.update_res_labels()

    def append_csv_log(self):
        """生成并追加一行CSV日志（无限追加），文件名可配置"""
        # 文件名处理（优先使用顶部配置栏的输入）
        file_name = (getattr(self, 'log_name_edit', None).text() if getattr(self, 'log_name_edit', None) else self.csv_path.name).strip()
        if not file_name.lower().endswith('.csv'):
            file_name += '.csv'
        self.csv_path = Path(__file__).parent / file_name

        # 当前点位与高度
        idx = self.point_index_spin.value()
        height_group = 'A' if self.height_combo.currentIndex() == 0 else 'B'
        height_str = '80 cm' if height_group == 'A' else '150 cm'
        key = f"{height_group}{idx}"
        dists = self.point_distances.get(height_group, {}).get(str(idx), {})
        std_a0 = dists.get('D0', dists.get('D_A0', 0))
        std_a1 = dists.get('D1', dists.get('D_A1', 0))

        # 实时均值/方差/RSSI
        a0_avg = getattr(self, '_a0_avg', 0.0)
        a1_avg = getattr(self, '_a1_avg', 0.0)
        try:
            a0_rssi = float(self.a0_rssi_edit.text())
        except Exception:
            a0_rssi = 0.0
        a1_rssi = getattr(self, '_a1_rssi', 0.0)
        a0_std = float(self.a0_std_label.text().split(':')[-1]) if hasattr(self, 'a0_std_label') else 0.0
        a1_std = float(self.a1_std_label.text().split(':')[-1]) if hasattr(self, 'a1_std_label') else 0.0

        # Res = 标准值 - 平均值
        a0_res = std_a0 - a0_avg
        a1_res = std_a1 - a1_avg

        row = [
            key, height_str,
            f"{a0_avg:.1f}", f"{a0_std:.1f}", f"{a0_res:.1f}", f"{a0_rssi:.0f}",
            f"{a1_avg:.1f}", f"{a1_std:.1f}", f"{a1_res:.1f}", f"{a1_rssi:.0f}"
        ]

        header = ['Point', 'Height', 'A0_Avg', 'A0_Std', 'A0_Res', 'A0_RSSI',
                  'A1_Avg', 'A1_Std', 'A1_Res', 'A1_RSSI']

        rows = []
        if self.csv_path.exists():
            with open(self.csv_path, newline='', encoding='utf-8') as f:
                rows = list(csv.reader(f))
        if not rows or rows[0] != header:
            rows = [header]
        rows.append(row)
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        InfoBar.success("已记录", f"点位{key}已追加到日志，共{len(rows)-1}条", parent=self, duration=1500)

    def init_ui(self):      # BM: 测试页面
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        if hasattr(self.parent_window, 'chart_widget'):
            # 创建图表容器
            chart_container = QWidget()
            chart_container_layout = QVBoxLayout(chart_container)
            chart_container_layout.setContentsMargins(0, 0, 0, 0)
            chart_container_layout.setSpacing(0)
            chart_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            # 保存引用，便于后续在页面切换时动态重挂载图表
            self.chart_container = chart_container
            self.chart_container_layout = chart_container_layout
            
            # 从主窗口获取图表部件并重新设置父对象
            chart_widget = self.parent_window.chart_widget
            if chart_widget.parent():
                chart_widget.setParent(None)  # 先移除原父对象
            chart_container_layout.addWidget(chart_widget)
            chart_widget.show()
            
            # Add chart container compactly and move content upward
            chart_container.setFixedHeight(300)
            root.addWidget(chart_container, alignment=Qt.AlignmentFlag.AlignTop) 

        # Top: test config bar (true single-row layout; no sub-layouts)
        config_card = CardWidget()
        config_card.setObjectName("configCard")
        config_layout = QHBoxLayout(config_card)
        config_layout.setSpacing(10)
        config_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        config_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Width (cm)
        width_label = QLabel("宽度")
        width_label.setStyleSheet("background:transparent")
        self.gate_width_edit = LineEdit()
        self.gate_width_edit.setText("100")
        self.gate_width_edit.textChanged.connect(self.update_test_points)

        # Height (cm)
        height_label = QLabel("高度")
        height_label.setStyleSheet("background:transparent")
        self.gate_height_edit = LineEdit()
        self.gate_height_edit.setText("90")
        self.gate_height_edit.textChanged.connect(self.update_test_points)

        # Point index
        point_index_label = QLabel("点位序号:")
        point_index_label.setStyleSheet("background:transparent")
        self.point_index_spin = SpinBox()
        self.point_index_spin.setRange(0, 14)
        self.point_index_spin.setValue(7)
        self.point_index_spin.valueChanged.connect(self.on_point_changed)

        # Point height
        point_height_label = QLabel("点位高度:")
        point_height_label.setStyleSheet("background:transparent")
        self.height_combo = ComboBox()
        self.height_combo.addItems(["0.8", "1.5"])
        self.height_combo.currentIndexChanged.connect(self.on_point_changed)

        # 日志名与操作
        self.log_name_edit = LineEdit()
        self.log_name_edit.setText(self.csv_path.name)
        self.log_name_edit.setClearButtonEnabled(True)
        self.log_name_edit.setMaximumWidth(200)
        log_btn_top = PrimaryPushButton("Log")
        log_btn_top.setFixedHeight(34)
        log_btn_top.clicked.connect(self.append_csv_log)

        # COM1开关与清除按钮
        self.com1_switch = SwitchButton()
        self.com1_switch.setOffText("COM1 OFF")
        self.com1_switch.setOnText("COM1 ON")
        self.com1_switch.checkedChanged.connect(self.on_com1_switch_changed)

        self.clear_test_btn = PushButton("CLEAR")
        self.clear_test_btn.clicked.connect(self.clear_test_data)

        # Add all widgets directly to the single-row layout
        config_layout.addWidget(width_label)
        config_layout.addWidget(self.gate_width_edit)
        config_layout.addWidget(height_label)
        config_layout.addWidget(self.gate_height_edit)
        config_layout.addWidget(point_index_label)
        config_layout.addWidget(self.point_index_spin)
        config_layout.addWidget(point_height_label)
        config_layout.addWidget(self.height_combo)
        config_layout.addWidget(self.log_name_edit, 1)
        config_layout.addWidget(log_btn_top)
        config_layout.addWidget(self.com1_switch)
        config_layout.addWidget(self.clear_test_btn)

        # 内容：A0（Slave）信息卡片
        a0_card = CardWidget()
        a0_layout = QVBoxLayout(a0_card)

        a0_title = QLabel("A0")
        a0_title.setStyleSheet("background-color: transparent; color: #E5E9F0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;")
        self.a0_avg_label = QLabel("Avg: 0.0")
        self.a0_avg_label.setStyleSheet("color: #9CDCFE; font-weight: 600; background-color: transparent; padding: 4px 8px; letter-spacing: 0.3px;")
        self.a0_std_label = QLabel("Std: 0.0")
        self.a0_std_label.setStyleSheet("color: #C18AFF; font-weight: 600; background-color: transparent; padding: 4px 8px; letter-spacing: 0.3px;")
        self.a0_rssi_edit = LineEdit()
        self.a0_res_label = QLabel("Res: 0.0")
        self.a0_res_label.setObjectName("resBadgeA0")
        # Res progress bar for A0
        self.a0_res_bar = QProgressBar()
        self.a0_res_bar.setRange(0, 100)
        self.a0_res_bar.setValue(0)
        self.a0_res_bar.setTextVisible(False)
        self.a0_res_bar.setFixedHeight(12)
        self.a0_res_bar.setStyleSheet(
            "QProgressBar {"
            "background-color: rgba(255,255,255,0.06);"
            "border: none;"
            "border-radius: 6px; padding: 2px;}"
            "QProgressBar::chunk {"
            "background-color: #22c55e;"
            "border: none;"
            "border-radius: 6px;}"
        )

        a0_layout.addWidget(a0_title)
        a0_layout.addWidget(self.a0_avg_label)
        a0_layout.addWidget(self.a0_std_label)
        # RSSI标签与输入框同一行
        rssi_row = CardWidget()
        rssi_layout = QHBoxLayout(rssi_row)
        self.a0_rssi_title = QLabel("RSSI:")
        self.a0_rssi_title.setStyleSheet("color: #FFB86C;  background-color: transparent;")
        rssi_layout.addWidget(self.a0_rssi_title)
        rssi_layout.addWidget(self.a0_rssi_edit, 1)
        a0_layout.addWidget(rssi_row)
        a0_layout.addWidget(self.a0_res_label)
        a0_layout.addWidget(self.a0_res_bar)
        a0_layout.addStretch()

        # 内容：A1（Master）信息卡片
        a1_card = CardWidget()
        a1_layout = QVBoxLayout(a1_card)

        a1_title = QLabel("A1")
        a1_title.setStyleSheet("background-color: transparent; color: #E5E9F0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;")

        # A1 metrics labels (use QLabel with color accents)
        self.a1_avg_label = QLabel("Avg: 0.0")
        self.a1_avg_label.setStyleSheet("color: #9CDCFE; font-weight: 600; background-color: transparent; padding: 4px 8px; letter-spacing: 0.3px;")
        self.a1_std_label = QLabel("Std: 0.0")
        self.a1_std_label.setStyleSheet("color: #C18AFF; font-weight: 600; background-color: transparent; padding: 4px 8px; letter-spacing: 0.3px;")
        self.a1_rssi_label = QLabel("RSSI: 0.0")
        self.a1_rssi_label.setStyleSheet("color: #FFB86C; font-weight: 600; background-color: transparent; padding: 4px 8px; letter-spacing: 0.3px;")
        self.a1_res_label = QLabel("Res: 0.0")
        self.a1_res_label.setObjectName("resBadgeA1")
        # Res progress bar for A1
        self.a1_res_bar = QProgressBar()
        self.a1_res_bar.setRange(0, 100)
        self.a1_res_bar.setValue(0)
        self.a1_res_bar.setTextVisible(False)
        self.a1_res_bar.setFixedHeight(12)
        self.a1_res_bar.setStyleSheet(
            "QProgressBar {"
            "background-color: rgba(255,255,255,0.06);"
            "border: none;"
            "border-radius: 6px; padding: 2px;}"
            "QProgressBar::chunk {"
            "background-color: #22c55e;"
            "border: none;"
            "border-radius: 6px;}"
        )

        a1_layout.addWidget(a1_title)
        a1_layout.addWidget(self.a1_avg_label)
        a1_layout.addWidget(self.a1_std_label)
        a1_layout.addWidget(self.a1_rssi_label)
        a1_layout.addWidget(self.a1_res_label)
        a1_layout.addWidget(self.a1_res_bar)
        a1_layout.addStretch()

        # 两卡片横向布局并限制尺寸，减少留白并居中
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        cards_layout.addWidget(a0_card)
        cards_layout.addWidget(a1_card)
        a0_card.setMinimumSize(360, 180)   # BM:测试页面框架大小
        a1_card.setMinimumSize(360, 180)
        a0_card.setMaximumSize(420, 280)
        a1_card.setMaximumSize(420, 280)

        # 顶部设置栏：拉满宽度
        config_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._style_card(config_card)
        root.addWidget(config_card, alignment=Qt.AlignmentFlag.AlignTop)

        # 使用容器居中卡片区并限制总宽度
        cards_container = QWidget()
        cards_container.setLayout(cards_layout)
        cards_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        root.addWidget(cards_container, alignment=Qt.AlignmentFlag.AlignTop)

        # 添加垂直伸缩空间，吸收剩余空间，防止组件被拉伸
        root.addStretch()
        
        # 设置卡片样式
        self._style_card(a0_card)
        self._style_card(a1_card)
        self.a0_res_label.setStyleSheet(
            "QLabel#resBadgeA0 {"
            "background-color: transparent;"
            "color: #9CDCFE; padding: 6px 10px;"
            "font-weight: 600; letter-spacing: 0.3px;}"
        )
        self.a1_res_label.setStyleSheet(
            "QLabel#resBadgeA1 {"
            "background-color: transparent;"
            "color: #A7F3D0; padding: 6px 10px;"
            "font-weight: 600; letter-spacing: 0.3px;}"
        )

    def _style_card(self, card: QWidget):
        """Apply modern card style and drop shadow"""
        try:
            card.setStyleSheet(
                """
                QWidget {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 rgba(44, 54, 68, 0.85),
                        stop:1 rgba(31, 41, 55, 0.75));
                    border: 1px solid rgba(180, 200, 220, 0.10);
                    border-radius: 16px;
                }
                """
            )
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 120))
            card.setGraphicsEffect(shadow)
        except Exception:
            pass

    def _update_res_bar(self, bar: QProgressBar, value: float, std_value: float):
        """Update progress bar range, value and color for residual visualization.
        Args:
            bar: target progress bar
            value: residual value (can be negative)
            std_value: standard deviation used to scale the max range
        """
        try:
            # Use absolute residual, and set a more generous max range to avoid early saturation
            base = 100.0
            dyn = (std_value * 6.0) if std_value and std_value > 0 else base
            max_val = int(max(base, dyn))
            val = int(min(abs(value), max_val))
            bar.setRange(0, max_val)
            bar.setValue(val)
            # Map value to color bands: green -> orange -> red
            ratio = 0.0 if max_val == 0 else min(1.0, val / max_val)
            if ratio < 0.33:
                color_hex = "#22c55e"  # green
            elif ratio < 0.66:
                color_hex = "#f59e0b"  # amber
            else:
                color_hex = "#ef4444"  # red
            bar.setStyleSheet(
                f"QProgressBar {{background-color: rgba(255,255,255,0.06); border: none; border-radius: 6px; padding: 2px;}}"
                f"QProgressBar::chunk {{background-color: {color_hex}; border: none; border-radius: 6px;}}"
            )
        except Exception:
            pass

    def create_gate_group(self):
        # 无标题容器，宽/高单位采用厘米
        group = QWidget()
        layout = QFormLayout(group)
        layout.setSpacing(8)

        self.gate_width_edit = LineEdit()
        self.gate_width_edit.setText("100")
        self.gate_width_edit.textChanged.connect(self.update_test_points)

        self.gate_height_edit = LineEdit()
        self.gate_height_edit.setText("90")
        self.gate_height_edit.textChanged.connect(self.update_test_points)

        layout.addRow("宽度", self.gate_width_edit)
        layout.addRow("高度", self.gate_height_edit)
        return group

    def create_point_group(self):
        group = QWidget()
        layout = QFormLayout(group)
        layout.setSpacing(8)

        self.point_index_spin = SpinBox()
        self.point_index_spin.setRange(0, 14)
        self.point_index_spin.setValue(7)
        self.point_index_spin.valueChanged.connect(self.on_point_changed)

        self.height_combo = ComboBox()
        self.height_combo.addItems(["0.8", "1.5"])
        self.height_combo.currentIndexChanged.connect(self.on_point_changed)

        layout.addRow("点位序号:", self.point_index_spin)
        layout.addRow("点位高度:", self.height_combo)
        return group

    def update_test_points(self):
        """根据闸机宽高重新计算所有测试点与标准距离"""
        try:
            width_cm = int(self.gate_width_edit.text())
            height_cm = int(self.gate_height_edit.text())
        except ValueError:
            return
        self.A0_Anchor = [-width_cm / 2, 0, height_cm]
        self.A1_Anchor = [ width_cm / 2, 0, height_cm]

        # （A0-A14为0.8m高，B0-B14为1.5m高）
        self.test_points = {}
        for i, (x, y) in enumerate(self.base_points):
            x_pos = (x * (width_cm / 2)) if x != 0 else 0
            self.test_points[f"A{i}"] = [x_pos, y, 80]
            self.test_points[f"B{i}"] = [x_pos, y, 150]

        self.point_distances = {'A': {}, 'B': {}}
        for name, coord in self.test_points.items():
            dist_A0 = math.sqrt(
                (coord[0] - self.A0_Anchor[0]) ** 2 +
                (coord[1] - self.A0_Anchor[1]) ** 2 +
                (coord[2] - self.A0_Anchor[2]) ** 2
            )
            dist_A1 = math.sqrt(
                (coord[0] - self.A1_Anchor[0]) ** 2 +
                (coord[1] - self.A1_Anchor[1]) ** 2 +
                (coord[2] - self.A1_Anchor[2]) ** 2
            )
            group = name[0]  # 'A'或'B'
            idx = name[1:]   # '0'~'14'
            self.point_distances[group][idx] = {
                'D_A0': round(dist_A0),
                'D_A1': round(dist_A1)
            }
        print(self.point_distances)
        self.on_point_changed()

    def on_point_changed(self):
        """当点位或高度变化时刷新Res值"""
        self.update_res_labels()

    def update_res_labels(self):
        """根据当前选中点位与实时数据计算Res"""
        idx = self.point_index_spin.value()
        height_group = "A" if self.height_combo.currentIndex() == 0 else "B"
        key = f"{height_group}{idx}"

        # 标准距离
        std_A0 = self.point_distances[height_group].get(str(idx), {}).get('D_A0', 0)
        std_A1 = self.point_distances[height_group].get(str(idx), {}).get('D_A1', 0)

        # 使用缓存的实时数据
        avg_A0 = getattr(self, '_a0_avg', 0.0)
        avg_A1 = getattr(self, '_a1_avg', 0.0)

        res_A0 = std_A0 - avg_A0
        res_A1 = std_A1 - avg_A1

        self.a0_res_label.setText(f"Res: {res_A0:.1f}")
        self.a1_res_label.setText(f"Res: {res_A1:.1f}")
        # Update progress bars to visualize deviation
        try:
            a0_std = float(self.a0_std_label.text().split(':')[-1]) if hasattr(self, 'a0_std_label') else 0.0
        except Exception:
            a0_std = 0.0
        try:
            a1_std = float(self.a1_std_label.text().split(':')[-1]) if hasattr(self, 'a1_std_label') else 0.0
        except Exception:
            a1_std = 0.0
        self._update_res_bar(self.a0_res_bar, res_A0, a0_std)
        self._update_res_bar(self.a1_res_bar, res_A1, a1_std)

    def append_csv_log(self):
        """追加一行测试记录到CSV（无限追加，文件名可配置）"""
        headers = ['Point', 'Height', 'A0_Avg', 'A0_Std', 'A0_Res', 'A0_RSSI',
                   'A1_Avg', 'A1_Std', 'A1_Res', 'A1_RSSI']

        file_name = (getattr(self, 'log_name_edit', None).text() if getattr(self, 'log_name_edit', None) else self.csv_path.name).strip()
        if not file_name.lower().endswith('.csv'):
            file_name += '.csv'
        self.csv_path = Path(__file__).parent / file_name

        idx = self.point_index_spin.value()
        height_group = 'A' if self.height_combo.currentIndex() == 0 else 'B'
        height_str = '0.8' if height_group == 'A' else '1.5'
        point_name = f"{idx}"

        try:
            a0_rssi = float(self.a0_rssi_edit.text())
        except Exception:
            a0_rssi = 0.0

        a0_avg = getattr(self, '_a0_avg', 0.0)
        a1_avg = getattr(self, '_a1_avg', 0.0)
        a1_rssi = getattr(self, '_a1_rssi', 0.0)
        a0_std = float(self.a0_std_label.text().split(':')[-1]) if hasattr(self, 'a0_std_label') else 0.0
        a1_std = float(self.a1_std_label.text().split(':')[-1]) if hasattr(self, 'a1_std_label') else 0.0

        # 标准距离
        std_A0 = self.point_distances.get(height_group, {}).get(str(idx), {}).get('D_A0', 0)
        std_A1 = self.point_distances.get(height_group, {}).get(str(idx), {}).get('D_A1', 0)
        a0_res = std_A0 - a0_avg
        a1_res = std_A1 - a1_avg

        row = [point_name, height_str,
               f"{a0_avg:.1f}", f"{a0_std:.1f}", f"{a0_res:.1f}", f"{a0_rssi:.0f}",
               f"{a1_avg:.1f}", f"{a1_std:.1f}", f"{a1_res:.1f}", f"{a1_rssi:.0f}"]

        # 读写CSV（不做数量限制）
        rows = []
        if self.csv_path.exists():
            with open(self.csv_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
        if not rows or rows[0] != headers:
            rows = [headers]
        rows.append(row)

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        InfoBar.success("已记录", f"点位{point_name}已追加到日志，共{len(rows)-1}条", parent=self, duration=1500)

    def update_realtime_data(self, a0_avg, a0_std, a1_avg, a1_std, a1_rssi):
        """供外部调用，刷新实时数据并更新Res"""
        # 更新显示
        self.a0_avg_label.setText(f"Avg: {a0_avg:.1f}")
        self.a0_std_label.setText(f"Std: {a0_std:.1f}")
        self.a1_avg_label.setText(f"Avg: {a1_avg:.1f}")
        self.a1_std_label.setText(f"Std: {a1_std:.1f}")
        self.a1_rssi_label.setText(f"RSSI: {a1_rssi}")
        # 更新内部缓存，用于后续计算Res
        self._a0_avg = a0_avg
        self._a1_avg = a1_avg
        self._a1_rssi = a1_rssi
        self.update_res_labels()

    def clear_test_data(self):
        """清空所有测试数据，重置Avg/Std、RSSI、Res和图表内容"""
        # 重置显示值
        self.a0_avg_label.setText("Avg: 0.0")
        self.a0_std_label.setText("Std: 0.0")
        self.a0_rssi_edit.setText("0.0")
        self.a0_res_label.setText("Res: 0.0")
        self.a1_avg_label.setText("Avg: 0.0")
        self.a1_std_label.setText("Std: 0.0")
        self.a1_rssi_label.setText("RSSI: 0.0")
        self.a1_res_label.setText("Res: 0.0")
        
        # 重置进度条
        self.a0_res_bar.setValue(0)
        self.a1_res_bar.setValue(0)
        
        # 重置内部缓存
        self._a0_avg = 0.0
        self._a1_avg = 0.0
        self._a1_rssi = 0.0
        
        # 清空图表数据（如果图表存在）
        if hasattr(self.parent_window, 'chart_widget') and self.parent_window.chart_widget:
            # chart_widget是包含多个图表的容器，我们需要访问其中的charts字典
            if hasattr(self.parent_window, 'charts') and self.parent_window.charts:
                # 清空所有系列数据
                for chart in self.parent_window.charts.values():
                    for series in chart.series():
                        if hasattr(series, 'clear'):
                            series.clear()
                        elif hasattr(series, 'removePoints'):
                            series.removePoints(0, series.count())
            else:
                # 如果无法访问charts，尝试直接通过chart_widget的子控件获取图表
                chart_widget = self.parent_window.chart_widget
                if hasattr(chart_widget, 'layout') and chart_widget.layout():
                    # 遍历布局中的所有图表视图
                    for i in range(chart_widget.layout().count()):
                        item = chart_widget.layout().itemAt(i)
                        if item and item.widget():
                            chart_view = item.widget()
                            if hasattr(chart_view, 'chart'):
                                chart = chart_view.chart()
                                if chart:
                                    for series in chart.series():
                                        if hasattr(series, 'clear'):
                                            series.clear()
                                        elif hasattr(series, 'removePoints'):
                                            series.removePoints(0, series.count())
        
        InfoBar.success("已清空", "测试数据已重置", parent=self, duration=1500)

    def on_com1_switch_changed(self, is_checked):
        """COM1开关切换处理"""
        if is_checked:
            # 调用父窗口的toggle_port方法开启COM1
            if hasattr(self.parent_window, 'toggle_btn') and hasattr(self.parent_window, 'toggle_port'):
                # 设置按钮状态为选中，然后调用toggle_port
                if not self.parent_window.toggle_btn.isChecked():
                    self.parent_window.toggle_btn.setChecked(True)
                    # toggle_port会在按钮状态改变时自动调用
                InfoBar.success("COM1", "COM1端口已开启", parent=self, duration=1500)
        else:
            # 调用父窗口的toggle_port方法关闭COM1
            if hasattr(self.parent_window, 'toggle_btn') and hasattr(self.parent_window, 'toggle_port'):
                # 设置按钮状态为未选中，然后调用toggle_port
                if self.parent_window.toggle_btn.isChecked():
                    self.parent_window.toggle_btn.setChecked(False)
                    # toggle_port会在按钮状态改变时自动调用
                InfoBar.info("COM1", "COM1端口已关闭", parent=self, duration=1500)


class ParticleEffectWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.particles = []
        self.num_particles = 100
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles_and_repaint)
        self._particles_initialized = False

    def _initialize_particles(self):
        if self.width() > 0 and self.height() > 0:
            bounds = QRectF(0, 0, self.width(), self.height())
            self.particles = [Particle(bounds) for _ in range(self.num_particles)]
            self._particles_initialized = True

    def start_animation(self):
        if not self.isVisible():
            return
        if not self._particles_initialized and self.width() > 0 and self.height() > 0:
            self._initialize_particles()
        if self._particles_initialized and not self.timer.isActive():
            self.timer.start(30)

    def stop_animation(self):
        self.timer.stop()

    def update_particles_and_repaint(self):
        if not self.isVisible() or not self._particles_initialized:
            self.stop_animation()
            return
        for p in self.particles:
            p.update()
        self.update()

    def paintEvent(self, event):
        if not self._particles_initialized:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self.particles:
            painter.setBrush(p.color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(p.pos, p.size, p.size)
        super().paintEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() > 0 and self.height() > 0:
            new_bounds = QRectF(0, 0, self.width(), self.height())
            if not self._particles_initialized:
                self._initialize_particles()
            else:
                for p in self.particles:
                    p.bounds = new_bounds
                    if not new_bounds.contains(p.pos):
                        p.reset()
            if self.isVisible() and not self.timer.isActive():
                self.start_animation()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_animation()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.stop_animation()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better transparency support
    
    window = MainWindow()
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    def show_main_window():
        try:
            window.showMaximized()   # Show window in fullscreen mode by default
            window.raise_()          # Bring window to front
            window.activateWindow()  # Activate window
        except Exception as e:
            print(f"Error showing main window: {e}")

    splash.finished.connect(show_main_window)
    
    def check_splash_closed():
        if not splash.isVisible():
            show_main_window()
            fallback_timer.stop()
    
    fallback_timer = QTimer()
    fallback_timer.timeout.connect(check_splash_closed)
    fallback_timer.start(500)  
    
    sys.exit(app.exec())
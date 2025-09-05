# 标准库导入
import sys
import os
import json
import re
import datetime
import time
import queue
import random
from pathlib import Path
# 串口通信
import serial
# Qt核心模块
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QUrl, QTimer,
    QDateTime, QThread, QMargins, QPointF,
    pyqtSignal, QObject, QPointF, QRectF,
    QEvent, QRect
)
# Qt界面模块
from PyQt6.QtWidgets import *
# Qt图形和绘制
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QTextCursor,
    QPixmap, QPainter, QIcon, QCursor,
    QClipboard, QIntValidator, QPen,
    QLinearGradient, QTextCharFormat,
    QTextOption, QTextDocument
)
# Qt图表模块
from PyQt6.QtCharts import (
    QChart, QChartView,
    QLineSeries, QValueAxis
)
# 自定义模块
from log import Logger

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

class MainWindow(QMainWindow):
    """
    UWBDash 主窗口类
    
    这是一个基于 PyQt6 的 UWB 数据可视化工具。主要功能包括:
    - 双串口数据接收和显示
    - UWB 数据实时图表展示
    - 自定义主题切换
    - 日志记录功能
    """
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        icon_path = Path(__file__).parent / "logo.ico"
        app_path  = Path(os.getcwd())
        print(f"app_path: {app_path}")
        self.setWindowIcon(QIcon(str(icon_path)))
        self.current_theme               = ThemeManager.DARK_THEME
        self.config_path                 = Path(__file__).parent / "config.json"
        self._load_background_config()
        self.logger                      = Logger(app_path=str(app_path))
        self.csv_title                   = ['Master', 'Slave', 'NLOS', 'RSSI', 'Speed','X', 'Y', 'Z', 'Auth', 'Trans']
        self.highlight_config_path       = str(Path(__file__).parent / "highlight_config.json")
        self.highlight_config            = self.load_highlight_config()
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

        self.highlight_config_timer = QTimer()
        self.highlight_config_timer.timeout.connect(self.reload_highlight_config)
        self.highlight_config_timer.start(10000)

        
        self.uwb_data = {
            'master'   : [],
            'slave'    : [],
            'nlos'     : [],
            'lift_deep': [],
            'speed'    : [],
        }

        self.base_points = [
            (0, -40), (0, 0), (1, 10), (0, 10), (-1, 10),
            (1, 60), (0, 60), (-1, 60), (1, 110), (0, 110),
            (-1, 110), (1, 160), (0, 160), (-1, 160), (0, 210)
        ]

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |         # 无边框
            Qt.WindowType.WindowMinimizeButtonHint |    # 允许最小化
            Qt.WindowType.WindowMaximizeButtonHint      # 允许最大化
        )
        self.init_ui()

    
    def paintEvent(self, event):
        if not self.background_cache or self.size() != self.last_window_size:
            size = self.size()
            background_path = Path(__file__).parent / self.background_image
            if not background_path.exists(): # Fallback if current image is somehow invalid
                print(f"Warning: Background image {self.background_image} not found. Falling back to default.")
                if self.background_images:
                    self.background_image = self.background_images[0]
                    self._save_background_config() # Save the fallback
                    background_path = Path(__file__).parent / self.background_image
                else: # Ultimate fallback if list is also empty (should not happen with proper config loading)
                    # You might want to handle this case more gracefully, e.g., by not drawing a background
                    # or using a solid color. For now, let's assume config loading ensures a valid image.
                    print("Error: No background images available.")
                    return # Or handle error appropriately

            background = QPixmap(str(background_path))
            self.background_cache = background.scaled(
                size, 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.last_window_size = size
            
        painter = QPainter(self) 
        painter.setOpacity(1)
        x = (self.width() - self.background_cache.width()) // 2
        y = (self.height() - self.background_cache.height()) // 2
        painter.drawPixmap(x, y, self.background_cache)
    
    def _load_background_config(self):
        default_images = [
            "pic/person1.jpg", "pic/city1.jpg", "pic/carton1.jpg",
            "pic/landscape1.jpg", "pic/person2.jpg", "pic/landscape2.jpg"
        ]
        default_current_image = default_images[0] if default_images else None

        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f) 
                self.background_images = config_data.get("background_images", default_images)
                self.background_image = config_data.get("current_background_image", default_current_image)
                if not self.background_images: # Ensure list is not empty
                    self.background_images = default_images
                if self.background_image not in self.background_images and self.background_images:
                    self.background_image = self.background_images[0]
                elif not self.background_images:
                     self.background_image = None # No images available

                # Ensure current_background_image is valid and exists in the list
                if self.background_image not in self.background_images:
                    self.background_image = self.background_images[0] if self.background_images else default_current_image
                
                # Initialize background_image_index based on the loaded current_background_image
                if self.background_image and self.background_image in self.background_images:
                    self.background_image_index = self.background_images.index(self.background_image)
                else:
                    self.background_image_index = 0 # Default to first image if current is invalid or not found
                    if self.background_images: # If there are images, set current to the first one
                        self.background_image = self.background_images[0]
                    else: # If no images at all, set current to None
                        self.background_image = None

            else:
                self.background_images = default_images
                self.background_image = default_current_image
                self.background_image_index = 0
                self._save_background_config() # Create config file with defaults
        except Exception as e:
            print(f"Error loading background config: {e}. Using defaults.")
            self.background_images = default_images
            self.background_image = default_current_image
            self.background_image_index = 0
            # Attempt to save defaults if loading failed, to fix a potentially corrupt file
            self._save_background_config()
        
        # Final check to ensure background_image is set if list is not empty
        if not self.background_image and self.background_images:
            self.background_image = self.background_images[0]
            self.background_image_index = 0

    def _save_background_config(self):
        config_data = {
            "background_images": self.background_images,
            "current_background_image": self.background_image
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving background config: {e}")
    
    def load_highlight_config(self):
        try:
            with open(self.highlight_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 将颜色字符串转为 QColor
            return {k: QColor(v) for k, v in data.items()}
        except Exception as e:
            print(f"加载高亮配置失败: {e}")
            # 默认配置
            return {
                "APP     :ERROR"     : QColor("#ff7f7f"),
                "APP     :INFO"      : QColor("#8ccfff"),
                "APP     :WARN"      : QColor("#ffd280"),
                "gCapSessionHandle"  : QColor("#00ff7f"),
                "gDtxSessionHandle"  : QColor("#b9f309"),
                "gMrmSessionHandle"  : QColor("#ffaaff"),
                "AuthenticationState": QColor("#3daaea"),
                "APP_HIFTask"        : QColor("#34a7b2"),
            }

    def reload_highlight_config(self):
        # 将当前的 self.highlight_config 写回到 JSON 文件
        try:
            data = {k: v.name() for k, v in self.highlight_config.items()}
            with open(self.highlight_config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存高亮配置失败: {e}")

    def init_ui(self):
        title_bar = self.create_title_bar()
        self.setGeometry(100, 100, 800, 700)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav_container = self.create_nav_bar()
        self.nav_list.currentRowChanged.connect(self.switch_page)

        self.stacked_widget = QStackedWidget()
        self.create_pages()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
                border    : none;
                min-height: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
        """)
        
        splitter.addWidget(nav_container)
        splitter.addWidget(self.stacked_widget)
        splitter.setStretchFactor(1, 1)  
        splitter.setSizes([80,500])

        main_layout.addWidget(title_bar)
        main_layout.addWidget(splitter)  
        
        self.apply_theme()
        self.nav_list.setCurrentRow(0)

    def create_nav_bar(self):
        nav_container = QWidget()
        nav_container.setMinimumWidth(65)  
        nav_container.setMaximumWidth(300) 
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.nav_list = QListWidget()
        self.nav_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # nav_items = ["COM 1", "COM 2", "CHART", "Parking"] 
        nav_items = ["COM 1", "COM 2", "CHART"] 
        for item in nav_items:
            list_item = QListWidgetItem(item)
            list_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            list_item.setSizeHint(QSize(65, 50))
            list_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.nav_list.addItem(list_item)

        self.theme_btn = QPushButton(" 🌓 ")
        # self.theme_btn.setFixedHeight(45)
        self.theme_btn.setStyleSheet(f"background: {self.current_theme['bg']}; border-radius: 0px;")
        self.theme_btn.clicked.connect(self.toggle_theme)

        nav_layout.addWidget(self.nav_list)
        nav_layout.addWidget(self.theme_btn)
        return nav_container
    
    def mousePressEvent(self, event):
        idx = self.stacked_widget.currentIndex()
        count = self.stacked_widget.count()
        # print(f"count: {count} idx: {idx}")
        if event.button() == Qt.MouseButton.XButton2:  
            new_idx = (idx - 1) % count
            self.stacked_widget.setCurrentIndex(new_idx)
            self.nav_list.setCurrentRow(new_idx)
            # print(f"New_idx: {new_idx}")
        elif event.button() == Qt.MouseButton.XButton1:  
            new_idx = (idx + 1) % count
            self.stacked_widget.setCurrentIndex(new_idx)
            self.nav_list.setCurrentRow(new_idx)
            # print(f"New_idx: {new_idx}")
        else:
            super().mousePressEvent(event)
    
    def wheelEvent(self, event):
        current_idx = self.stacked_widget.currentIndex()
        # 检测滚轮方向（正值表示向上滚动）
        delta = event.angleDelta().y()
        
        if current_idx == 0:  # COM 1 页面
            if delta > 0:  # 向上滚动
                self.auto_scroll.setChecked(True)  
            elif delta < 0 and not self.auto_scroll.isChecked():  # 向下滚动且自动滚动未启用
                # 可选：在这里添加额外的向下滚动逻辑
                pass
        elif current_idx == 1:  # COM 2 页面
            if delta > 0:  # 向上滚动
                self.auto_scroll2.setChecked(True)  
            elif delta < 0 and not self.auto_scroll2.isChecked():  # 向下滚动且自动滚动未启用
                # 可选：在这里添加额外的向下滚动逻辑
                pass
                
        # 调用父类方法以保持正常的滚动行为
        super().wheelEvent(event)

    def eventFilter(self, obj, event):
        if (obj == self.serial_display or obj == self.serial_display2) and event.type() == QEvent.Type.Wheel:
            # print(f"Event type: {event.type()}")
            self.wheelEvent(event)
            return True # 阻止事件进一步传播
        return super().eventFilter(obj, event)

    def create_title_bar(self):
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(5)

        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_pos = event.globalPosition().toPoint()
        
        def mouseMoveEvent(event):
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
                self.drag_pos = event.globalPosition().toPoint()
        
        # 将事件处理器绑定到标题栏
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent  = mouseMoveEvent

        title_bar.setAttribute(Qt.WidgetAttribute.WA_MouseTracking)
        
        self.title_label = QLabel("UWBDash")
        self.title_label.setObjectName("titleLabel")
        
        help_btn = QPushButton("Help")
        help_btn.setStyleSheet("background: transparent; border: none;color:#c29500;font-weight:bold;")
        help_btn.clicked.connect(self.show_help_dialog)
        
        about_btn = QPushButton("About")
        about_btn.setStyleSheet("background: transparent; border: none;color:#c29500;font-weight:bold;")
        about_btn.clicked.connect(self.show_about_dialog)

        btn_size = QSize(20, 20)
        
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(btn_size)
        minimize_btn.clicked.connect(self.showMinimized)
        
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(btn_size)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        close_btn = QPushButton("❌")
        close_btn.setFixedSize(btn_size)
        close_btn.clicked.connect(self.close)

        control_btns = [minimize_btn, self.maximize_btn, close_btn]
        for btn in control_btns:
            btn.setStyleSheet("""
                QPushButton {
                    border    : none;
                    font-size : 10px;
                    padding   : 5px;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
        close_btn.setStyleSheet(close_btn.styleSheet() + """
            QPushButton:hover {
                background-color: #ff4444;
            }
        """)

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(help_btn)
        title_layout.addWidget(about_btn)
        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(close_btn)
        
        return title_bar
    
    def show_help_dialog(self):
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("UWBDash Help")
        help_dialog.setFixedSize(500, 400)

        layout = QVBoxLayout(help_dialog)

        title_label = QLabel("UWBDash Help Guide")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #c29500;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a scroll area for the content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Add help sections
        sections = [
            ("Basic Controls", [
                "• Click and drag the title bar to move the window",
                "• Ctrl + F to open the search box",
                "• Select the message box and press Space to stop the scrolling"
            ]),
            ("Data Visualization", [
                "• Slave anchor needs to be connected for transmitting json data",
                "• Real-time UWB positioning data display",
                "• Interactive charts for key param monitoring",
            ]),
            ("Configuration", [
                "• Set up serial port parameters in the settings panel",
                "• Customize highlight colors for different message types"
            ]),
            ("Logging", [
                "• A log file will be created automatically in the app directory when the '打开串口' button is clicked every time",
            ])
        ]

        for section_title, items in sections:
            section_label = QLabel(section_title)
            section_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #666; margin-top: 10px;")
            scroll_layout.addWidget(section_label)

            for item in items:
                item_label = QLabel(item)
                # item_label.setStyleSheet("font-size: 12px; color: #333; margin-left: 20px;")
                item_label.setWordWrap(True)
                scroll_layout.addWidget(item_label)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(title_label)
        layout.addWidget(scroll)

        # Add OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(help_dialog.accept)
        layout.addWidget(ok_button)
        help_dialog.exec()

    def show_about_dialog(self):
        QMessageBox.about(self, "关于", "UWBDash APP\nCardShare@QLL")
    
    def open_highlight_config_dialog(self):
        dialog = HighlightConfigDialog(self.highlight_config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.highlight_config = dialog.get_config()


    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")

    def create_pages(self):
        COM1_page  = self.create_COM_page()
        COM2_page  = self.create_COM_page2()
        Chart_page = self.create_Chart_page()
        Parking_page = self.create_parking_page()

        self.stacked_widget.addWidget(COM1_page)
        self.stacked_widget.addWidget(COM2_page)
        self.stacked_widget.addWidget(Chart_page)
        self.stacked_widget.addWidget(Parking_page)
    
    def create_COM_page2(self):
        COM2_page = QWidget()
        layout = QVBoxLayout(COM2_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        top_widget = QWidget()
        top_widget.setStyleSheet("background: rgba(36, 42, 56, 0.2);")
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)
        
        self.port_combo2 = QComboBox()
        self.port_combo2.setMinimumWidth(120)

        self.baud_combo2 = QComboBox()
        self.baud_combo2.addItems(['9600', '115200', '230400', '460800', '3000000'])
        self.baud_combo2.setCurrentText('3000000')
        self.baud_combo2.setStyleSheet(self.port_combo2.styleSheet())

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 0, 10, 0)
        status_layout.setSpacing(5)
        self.status_indicator2 = QLabel("●")
        self.status_indicator2.setStyleSheet("color: red; font-size: 16px;background:rgba(36, 42, 56, 0);")
        status_layout.addWidget(self.status_indicator2)

        self.toggle_btn2 = QPushButton("打开串口")
        self.toggle_btn2.setFixedWidth(90)
        self.toggle_btn2.clicked.connect(self.toggle_port2)

        line_top_1 = QFrame()
        line_top_1.setFrameShape(QFrame.Shape.VLine)
        line_top_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")
        
        max_lines_label = QLabel("最大行数")
        max_lines_label.setStyleSheet("background: rgba(36, 42, 56, 0);")
        self.max_lines_spin2 = QSpinBox()
        self.max_lines_spin2.setRange(50000, 300000)
        self.max_lines_spin2.setValue(150000)
        self.max_lines_spin2.setSingleStep(10000)
        self.max_lines_spin2.valueChanged.connect(self.update_max_lines2)
        self.current_lines_label2 = QLabel("当前行数: 0")
        self.current_lines_label2.setStyleSheet("background: rgba(36, 42, 56, 0);")
        
        line_top_2 = QFrame()
        line_top_2.setFrameShape(QFrame.Shape.VLine)
        line_top_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        self.Address_label_2 = QLabel("0000  -")
        self.Address_label_2.setStyleSheet("background:rgba(36, 42, 56, 0);")
       
        self.Transaction_time_label_2 = QLabel("0000ms")
        self.Transaction_time_label_2.setStyleSheet("background:rgba(36, 42, 56, 0);")
        
        top_layout.addWidget(self.port_combo2)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.baud_combo2)
        top_layout.addSpacing(10)
        top_layout.addWidget(status_widget)
        top_layout.addWidget(self.toggle_btn2)
        top_layout.addSpacing(20)
        top_layout.addWidget(line_top_1)
        top_layout.addSpacing(20)
        top_layout.addWidget(max_lines_label)
        top_layout.addWidget(self.max_lines_spin2)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.current_lines_label2)
        top_layout.addSpacing(20)
        top_layout.addWidget(line_top_2)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.Address_label_2)
        top_layout.addSpacing(5)
        top_layout.addWidget(self.Transaction_time_label_2)
        top_layout.addStretch()

        layout.addWidget(top_widget)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
                border    : none;
                min-height: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
        """)
        
        self.create_display_area2(splitter)
    
        bottom_widget = QWidget()
        # bottom_widget.setStyleSheet("background: rgba(36, 42, 56, 0.8);")
        bottom_layout = QHBoxLayout(bottom_widget)
        
        self.clear_btn2 = QPushButton("清屏")
        self.clear_btn2.setFixedWidth(80)
        self.clear_btn2.clicked.connect(self.serial_display2.clear)

        self.config_highlight_btn2 = QPushButton("高亮")
        self.config_highlight_btn2.setFixedWidth(80)
        self.config_highlight_btn2.clicked.connect(self.open_highlight_config_dialog)

        self.timestamp2 = QCheckBox("🕒 时间戳")
        self.timestamp2.setObjectName("timestamp")
        self.timestamp2.setToolTip("每行前添加时间戳")
        self.timestamp2.setChecked(True)
        self.auto_scroll2 = QCheckBox("📌 自动滚动")
        self.auto_scroll2.setObjectName("autoScroll")
        self.auto_scroll2.setChecked(False)
        self.auto_scroll2.setToolTip("锁定滚动条到底部")

        line_bottom_1 = QFrame()
        line_bottom_1.setFrameShape(QFrame.Shape.VLine)
        line_bottom_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        line_bottom_2 = QFrame()
        line_bottom_2.setFrameShape(QFrame.Shape.VLine)
        line_bottom_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        # 日志相关按钮
        self.open_text_log_file_btn2 = QPushButton("📄TEXT")
        self.open_text_log_file_btn2.setFixedWidth(75)
        self.open_text_log_file_btn2.setToolTip("打开当前Text日志文件")
        self.open_text_log_file_btn2.clicked.connect(self.open_current_text_log_file2)
        self.open_text_log_file_btn2.setEnabled(False)

        self.open_log_folder_btn2 = QPushButton("📁")
        self.open_log_folder_btn2.setFixedWidth(60)
        self.open_log_folder_btn2.setToolTip("打开日志文件夹")
        self.open_log_folder_btn2.clicked.connect(self.open_log_folder)

        bottom_layout.addWidget(self.clear_btn2)
        bottom_layout.addWidget(self.config_highlight_btn2)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(line_bottom_1)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.timestamp2)
        bottom_layout.addWidget(self.auto_scroll2)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(line_bottom_2)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.open_text_log_file_btn2)
        bottom_layout.addWidget(self.open_log_folder_btn2)
        bottom_layout.addStretch()
        
        splitter.addWidget(bottom_widget)
        splitter.setSizes([2000, 100])  
        
        layout.addWidget(splitter)
        
        self.port_scan_timer2 = QTimer()
        self.port_scan_timer2.timeout.connect(self.refresh_ports2)
        self.port_scan_timer2.start(1000)
        self.refresh_ports2()
        
        return COM2_page
    
    def update_max_lines2(self, value):
        self.serial_display2.document().setMaximumBlockCount(value)
    
    def update_current_lines2(self):
        current_count = self.serial_display2.document().blockCount()
        self.current_lines_label2.setText(f"当前行数: {current_count}")
        max_lines = self.serial_display2.document().maximumBlockCount()
        if current_count >= max_lines:
            self.serial_display2.clear()

    def create_display_area2(self, layout):
        self.serial_display2 = QTextEdit()
        self.serial_display2.setReadOnly(True)
        self.serial_display2.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # 确保能接收键盘事件
        self.serial_display2.installEventFilter(self) # 安装事件过滤器
        self.serial_display2.document().setMaximumBlockCount(150000)  # 限制最大行数
        self.serial_display2.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # 自动换行
        self.serial_display2.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)  # 允许在任何位置换行
        
        self.serial_display2.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_display2.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_display2.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        font = QFont("Microsoft YaHei", 12)
        self.serial_display2.setFont(font)
        
        self.serial_display2.setStyleSheet("""
            QTextEdit {
                background-color          : rgba(36, 42, 56, 0.177);
                border                    : 1.5px solid #3a4a5c;
                border-radius             : 16px;
                padding                   : 12px;
                color                     : {theme['text']};
                font-size                 : 15px;
                font-family               : 'JetBrains Mono', 'Consolas', 'Microsoft YaHei', monospace;
                selection-background-color: #088bef;
                selection-color           : #ffffff;

            }
            QTextEdit:focus {
                border          : 1.5px solid #477faa;
                background-color: rgba(36, 42, 56, 0.5);
            }
            QScrollBar:vertical {
                background   : transparent;
                width        : 10px;
                margin       : 2px 0 2px 0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3da9fc, stop:1 #1e293b
                );
                min-height   : 24px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #90caf9, stop:1 #3da9fc
                );
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height    : 0;
                background: none;
                border    : none;
            }
        """)
        
        self.serial_display2.document().blockCountChanged.connect(self.update_current_lines2)
        self.update_current_lines2()

        self.find_dialog2 = QDialog(self)
        self.find_dialog2.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.find_dialog2.setFixedSize(300, 48)
        self.find_dialog2.setStyleSheet("""
            QDialog {
                background-color: rgba(45, 52, 54, 0.95);
                border          : 1px solid rgba(255, 255, 255, 0.1);
                border-radius   : 10px;
            }
        """)

        find_layout = QHBoxLayout(self.find_dialog2)
        find_layout.setContentsMargins(6, 6, 6, 6)
        find_layout.setSpacing(6)

        self.find_input2 = QLineEdit()
        self.find_input2.setPlaceholderText("输入搜索内容")
        self.find_input2.textChanged.connect(self.update_find_count2)
        self.count_label2 = QLabel("0/0")

        from PyQt6.QtWidgets import QToolButton
        self.prev_btn2 = QToolButton()
        self.prev_btn2.setArrowType(Qt.ArrowType.UpArrow)
        self.prev_btn2.clicked.connect(lambda: self.find_text2(False))
        self.next_btn2 = QToolButton()
        self.next_btn2.setArrowType(Qt.ArrowType.DownArrow)
        self.next_btn2.clicked.connect(lambda: self.find_text2(True))

        self.close_find_btn2 = QToolButton()
        self.close_find_btn2.setText("✕")
        self.close_find_btn2.clicked.connect(self.find_dialog2.close)
        self.close_find_btn2.setStyleSheet("font-size: 16px; color: #fff; background: transparent; border: none;")

        find_layout.addWidget(self.find_input2)
        find_layout.addWidget(self.count_label2)
        find_layout.addWidget(self.prev_btn2)
        find_layout.addWidget(self.next_btn2)
        find_layout.addWidget(self.close_find_btn2)

        self.serial_display2.keyPressEvent = self.on_display_key_press2
        # self.serial_display2.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        layout.addWidget(self.serial_display2)
    
    
    def on_display_key_press2(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.auto_scroll2.setChecked(not self.auto_scroll2.isChecked())
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_F:
                cursor = self.serial_display2.textCursor()
                selected_text = cursor.selectedText()
                self.show_find_dialog2()
                if selected_text:
                    self.find_input2.setText(selected_text)
                    self.find_input2.selectAll()
                event.accept()
                return
        
        QTextEdit.keyPressEvent(self.serial_display2, event)
    
    def show_find_dialog2(self):
        display_rect = self.serial_display2.rect()
        display_pos = self.serial_display2.mapToGlobal(display_rect.topRight())
        dialog_x = display_pos.x() - self.find_dialog2.width() - 10  # 距离右边界10像素
        dialog_y = display_pos.y() + 10  # 距离顶部10像素
        self.find_dialog2.move(dialog_x, dialog_y)
        
        self.find_dialog2.show()
        self.find_input2.setFocus()
        self.find_input2.selectAll()
        
    
    def update_find_count2(self):
        """增量更新查找结果计数"""
        text    = self.find_input2.text()
        content = self.serial_display2.toPlainText()
        
        # 增量缓存：只对新增内容查找
        if not hasattr(self, '_find_count_cache2'):
            self._find_count_cache2 = {'text': '', 'content_len': 0, 'count': 0}
        cache = self._find_count_cache2

        if not text:
            self.count_label2.setText("0/0")
            cache['text']        = ''
            cache['content_len'] = 0
            cache['count']       = 0
            return

        if text != cache['text']:
            count = content.count(text)
            cache['text']        = text
            cache['content_len'] = len(content)
            cache['count']       = count
        else:
            old_len = cache['content_len']
            if len(content) > old_len:
                new_part  = content[old_len:]
                count_new = new_part.count(text)
                cache['count']       += count_new
                cache['content_len']  = len(content)
            elif len(content) < old_len:
                count                = content.count(text)
                cache['count']       = count
                cache['content_len'] = len(content)

        count = cache['count']
        
        # 获取当前选中的位置
        current = 0
        cursor  = self.serial_display2.textCursor()
        if cursor.hasSelection():
            sel_text = cursor.selectedText()
            if sel_text == text:
                pos     = cursor.position() - len(text)
                current = content[:pos].count(text) + 1
        
        self.count_label2.setText(f"{current}/{count}")

    def find_text2(self, forward=True):
        """增量查找文本"""
        text = self.find_input2.text()
        if not text:
            return
        
        # 终止上一个查找线程
        if hasattr(self, 'find_thread2') and self.find_thread2.isRunning():
            self.find_thread2.terminate()
            self.find_thread2.wait()
        
        doc = self.serial_display2.document()
        current_format = doc.defaultTextOption()

        self.auto_scroll2.setChecked(True)

        content = self.serial_display2.toPlainText()
        cursor = self.serial_display2.textCursor()
        cur_pos = cursor.selectionStart() if cursor.hasSelection() else cursor.position()

        # 启动查找线程
        self.find_thread2 = FindThread(content, text, cur_pos, forward)
        self.find_thread2.result_ready.connect(self.on_find_result2)
        self.find_thread2.start()

    def on_find_result2(self, current, total, positions):
        # 定位并高亮当前匹配项
        pos = positions[current]
        length = len(self.find_input2.text())
        cursor = self.serial_display2.textCursor()
        cursor.setPosition(pos)
        cursor.setPosition(pos + length, QTextCursor.MoveMode.KeepAnchor)
        self.serial_display2.setTextCursor(cursor)

        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#ffaaff"))
        fmt.setForeground(QColor("#000000"))
        fmt.setFontWeight(QFont.Weight.Bold)
        cursor.mergeCharFormat(fmt)

        self._last_highlight2 = (pos, length)
        self.count_label2.setText(f"{current+1}/{total}")
    
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
        if self.toggle_btn2.text() == "打开串口":
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
                self.serial_thread2.start()
                
                self.toggle_btn2.setText("关闭串口")
                self.status_indicator2.setStyleSheet("color: green;background:rgba(36,36,36,0);")
                
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
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"打开串口失败: {str(e)}")
        else:
            try:
                if hasattr(self, 'serial_thread2') and self.serial_thread2:
                    self.serial_thread2.stop()
                    self.serial_thread2 = None

                if hasattr(self, 'serial2') and self.serial2:
                    self.serial2.close()
                    self.serial2 = None
                
                self.toggle_btn2.setText("打开串口")
                self.status_indicator2.setStyleSheet("color: red;background:rgba(36,36,36,0);")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"关闭串口失败: {str(e)}")
    
    def handle_serial_2_data(self, data):
        try:
            text = data.decode('utf-8', errors='ignore')
            self.log_worker.add_log_task("UwbLog2", "info", text.strip())
            text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
            self.data_buffer2.append(text)

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
        
    def create_COM_page(self):
        COM1_page = QWidget()
        layout = QVBoxLayout(COM1_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        top_widget = QWidget()
        top_widget.setStyleSheet("background: rgba(36, 42, 56, 0.2);")
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '115200', '230400', '460800', '3000000'])
        self.baud_combo.setCurrentText('3000000')
        self.baud_combo.setStyleSheet(self.port_combo.styleSheet())

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 0, 10, 0)
        status_layout.setSpacing(5)
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: red; font-size: 16px;background:rgba(36, 42, 56, 0);")
        status_layout.addWidget(self.status_indicator)

        self.toggle_btn = QPushButton("打开串口")
        self.toggle_btn.setFixedWidth(90)
        self.toggle_btn.clicked.connect(self.toggle_port)

        line_top_1 = QFrame()
        line_top_1.setFrameShape(QFrame.Shape.VLine)
        line_top_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")
        
        max_lines_label = QLabel("最大行数") 
        max_lines_label.setStyleSheet("background:rgba(36, 42, 56, 0);")
        
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(50000, 300000)
        self.max_lines_spin.setValue(150000)
        self.max_lines_spin.setSingleStep(10000)
        self.max_lines_spin.valueChanged.connect(self.update_max_lines)
        self.current_lines_label = QLabel("当前行数: 0")
        self.current_lines_label.setStyleSheet("background:rgba(36, 42, 56, 0);")

        line_top_2 = QFrame()
        line_top_2.setFrameShape(QFrame.Shape.VLine)
        line_top_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_top_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        self.Address_label = QLabel("0000  -")
        self.Address_label.setStyleSheet("background:rgba(36, 42, 56, 0);")
       
        self.Transaction_time_label = QLabel("0000ms")
        self.Transaction_time_label.setStyleSheet("background:rgba(36, 42, 56, 0);")

        top_layout.addWidget(self.port_combo)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.baud_combo)
        top_layout.addSpacing(10)
        top_layout.addWidget(status_widget)
        top_layout.addWidget(self.toggle_btn)
        top_layout.addSpacing(20)
        top_layout.addWidget(line_top_1)
        top_layout.addSpacing(20)
        top_layout.addWidget(max_lines_label)
        top_layout.addWidget(self.max_lines_spin)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.current_lines_label)
        top_layout.addSpacing(20)
        top_layout.addWidget(line_top_2)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.Address_label)
        top_layout.addSpacing(5)
        top_layout.addWidget(self.Transaction_time_label)

        top_layout.addStretch()

        layout.addWidget(top_widget)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
                border    : none;
                min-height: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
        """)
        
        self.create_display_area(splitter)
        
        bottom_widget = QWidget()
        # bottom_widget.setStyleSheet("background: rgba(36, 42, 56, 0.25);")
        bottom_layout = QHBoxLayout(bottom_widget)
        
        self.clear_btn = QPushButton("清屏")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.clicked.connect(self.serial_display.clear)

        self.config_highlight_btn = QPushButton("高亮")
        self.config_highlight_btn.setFixedWidth(80)
        self.config_highlight_btn.clicked.connect(self.open_highlight_config_dialog)

        self.timestamp = QCheckBox("🕒 时间戳")
        self.timestamp.setObjectName("timestamp")
        self.timestamp.setToolTip("每行前添加时间戳")
        self.timestamp.setChecked(True)
        self.auto_scroll = QCheckBox("📌 自动滚动")
        self.auto_scroll.setObjectName("autoScroll")
        self.auto_scroll.setChecked(False)
        self.auto_scroll.setToolTip("锁定滚动条到底部")

        line_bottom_1 = QFrame()
        line_bottom_1.setFrameShape(QFrame.Shape.VLine)
        line_bottom_1.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_1.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        line_bottom_2 = QFrame()
        line_bottom_2.setFrameShape(QFrame.Shape.VLine)
        line_bottom_2.setFrameShadow(QFrame.Shadow.Sunken)
        line_bottom_2.setStyleSheet("color: #66abf5; background: #4a90e2; min-width:1px;")

        # 日志相关按钮
        self.open_csv_log_file_btn = QPushButton("📄CSV")
        self.open_csv_log_file_btn.setFixedWidth(75)
        self.open_csv_log_file_btn.setToolTip("打开当前CSV日志文件")
        self.open_csv_log_file_btn.clicked.connect(self.open_current_csv_file)
        self.open_csv_log_file_btn.setEnabled(False)

        self.open_text_log_file_btn = QPushButton("📄TEXT")
        self.open_text_log_file_btn.setFixedWidth(75)
        self.open_text_log_file_btn.setToolTip("打开当前Text日志文件")
        self.open_text_log_file_btn.clicked.connect(self.open_current_text_log_file)
        self.open_text_log_file_btn.setEnabled(False)

        self.open_log_folder_btn = QPushButton("📁")
        self.open_log_folder_btn.setFixedWidth(60)
        self.open_log_folder_btn.setToolTip("打开日志文件夹")
        self.open_log_folder_btn.clicked.connect(self.open_log_folder)

        bottom_layout.addWidget(self.clear_btn)
        bottom_layout.addWidget(self.config_highlight_btn)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(line_bottom_1)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.timestamp)
        bottom_layout.addWidget(self.auto_scroll)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(line_bottom_2)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.open_csv_log_file_btn)
        bottom_layout.addWidget(self.open_text_log_file_btn)
        bottom_layout.addWidget(self.open_log_folder_btn)
        bottom_layout.addStretch()
        
        splitter.addWidget(bottom_widget)
        splitter.setSizes([2000, 100])  # 设置初始大小比例
        
        layout.addWidget(splitter)
        
        # 设置自动扫描定时器
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
        self.current_lines_label.setText(f"当前行数: {current_count}")
        # 如果当前行数等于最大行数，自动清除
        max_lines = self.serial_display.document().maximumBlockCount()
        if current_count >= max_lines:
            self.serial_display.clear()

    def create_display_area(self, layout):
        """创建数据显示区域"""
        self.serial_display = QTextEdit()
        self.serial_display.setReadOnly(True)
        self.serial_display.document().setMaximumBlockCount(150000)  # 限制最大行数
        self.serial_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # 自动换行
        self.serial_display.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)  # 允许在任何位置换行
        self.serial_display.installEventFilter(self) # 安装事件过滤器
        
        # 优化显示性能
        self.serial_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.serial_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # 设置字体和样式
        font = QFont("Microsoft YaHei", 12)
        self.serial_display.setFont(font)
        
        self.serial_display.setStyleSheet("""
            QTextEdit {
                background-color          : rgba(36, 42, 56, 0.177);
                border                    : 1.5px solid #3a4a5c;
                border-radius             : 16px;
                padding                   : 12px;
                color                     : {theme['text']};
                font-size                 : 15px;
                font-family               : 'JetBrains Mono', 'Consolas', 'Microsoft YaHei', monospace;
                selection-background-color: #088bef;
                selection-color           : #ffffff;

            }
            QTextEdit:focus {
                border          : 1.5px solid #477faa;
                background-color: rgba(36, 42, 56, 0.5);
            }
        """)
        
        # 更新初始行数显示
        self.serial_display.document().blockCountChanged.connect(self.update_current_lines)
        self.update_current_lines()

        # 查找框相关
        self.find_dialog = QDialog(self)
        self.find_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.find_dialog.setFixedSize(300, 48)
        self.find_dialog.setStyleSheet("""
            QDialog {
                background-color: rgba(45, 52, 54, 0.95);
                border          : 1px solid rgba(255, 255, 255, 0.1);
                border-radius   : 10px;
            }
        """)

        find_layout = QHBoxLayout(self.find_dialog)
        find_layout.setContentsMargins(6, 6, 6, 6)
        find_layout.setSpacing(6)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("输入搜索内容")
        self.find_input.textChanged.connect(self.update_find_count)
        self.count_label = QLabel("0/0")

        # 上下箭头按钮
        from PyQt6.QtWidgets import QToolButton
        self.prev_btn = QToolButton()
        self.prev_btn.setArrowType(Qt.ArrowType.UpArrow)
        self.prev_btn.clicked.connect(lambda: self.find_text(False))
        self.next_btn = QToolButton()
        self.next_btn.setArrowType(Qt.ArrowType.DownArrow)
        self.next_btn.clicked.connect(lambda: self.find_text(True))

        # 关闭按钮
        self.close_find_btn = QToolButton()
        self.close_find_btn.setText("✕")
        self.close_find_btn.clicked.connect(self.find_dialog.close)
        self.close_find_btn.setStyleSheet("font-size: 16px; color: #fff; background: transparent; border: none;")

        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.count_label)
        find_layout.addWidget(self.prev_btn)
        find_layout.addWidget(self.next_btn)
        find_layout.addWidget(self.close_find_btn)

        # 添加鼠标事件处理
        self.serial_display.wheelEvent = self.on_display_wheel
        self.serial_display.keyPressEvent = self.on_display_key_press
        self.font_size = 12  # 初始字体大小
        
        layout.addWidget(self.serial_display)

    def create_Chart_page(self):
        Chart_page = QWidget()
        layout = QVBoxLayout(Chart_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
                border    : none;
                min-height: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
        """)
        chart_widget = self.create_chart_area()
        main_splitter.addWidget(chart_widget)

        canvas_splitter = QSplitter(Qt.Orientation.Horizontal)
        canvas_splitter.setStyleSheet("""
            QSplitter::handle {
                background: transparent;
                border    : none;
                min-height: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
        """)

        table_widget = self.create_test_area()  # 这里包含了表格和预留区域
        canvas_splitter.addWidget(table_widget)
        position_widget = self.create_position_area()
        canvas_splitter.addWidget(position_widget)

        canvas_splitter.setSizes([100, 100])
        main_splitter.addWidget(canvas_splitter)
        main_splitter.setSizes([100, 200])

        layout.addWidget(main_splitter)
        return Chart_page
    
    def create_position_area(self):
        bottom_right = QWidget()
        bottom_right_layout = QVBoxLayout(bottom_right)
        bottom_right_layout.setContentsMargins(5, 5, 5, 5)
        self.position_view = PositionView(self)
        bottom_right_layout.addWidget(self.position_view)
        # 初始化时刷新红蓝区域
        self.position_view.refresh_areas()
        print("create_position_area")
        return bottom_right
    
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
            'lift_deep': 'RSSI',
            'speed'    : 'Speed'
        }
        for key, title in chart_titles.items():
            series = QLineSeries()
            colors = {
                'master'   : QColor("#FF6B6B"),
                'slave'    : QColor("#4ECDC4"),
                'nlos'     : QColor("#45B7D1"),
                'lift_deep': QColor("#68ecae"),
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

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(10)
        self.data_table.setHorizontalHeaderLabels([
            'Master', 'Slave', 'NLOS', 'RSSI', 'Speed',
            'X', 'Y', 'Z', 'Auth', 'Trans'
        ])
        
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        top_table_layout.addWidget(self.data_table)

        # 下部分 - 闸机动画区域
        bottom_space = QWidget()
        bottom_space.setStyleSheet("background: rgba(255, 255, 255, 0.05); border-radius: 10px;")
        bottom_layout = QVBoxLayout(bottom_space)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加标题
        
        # 创建闸机动画组件
        self.gate_animation = SubwayGateAnimation()
        bottom_layout.addWidget(self.gate_animation)
        
        # 添加控制按钮
        # control_layout = QHBoxLayout()
        
        # self.trigger_btn = QPushButton("触发开门")
        # self.trigger_btn.clicked.connect(self.gate_animation.trigger_gate_animation)
        
        # control_layout.addStretch()
        # control_layout.addWidget(self.trigger_btn)
        # control_layout.addStretch()
        
        # bottom_layout.addLayout(control_layout)

        form_splitter.addWidget(top_table)
        form_splitter.addWidget(bottom_space)
        form_splitter.setSizes([100, 300])

        bottom_left_layout.addWidget(form_splitter)
        return bottom_left
    
    def create_parking_page(self):
        """Create parking fee page"""
        parking_page = QWidget()
        parking_page.setStyleSheet("background: rgba(36, 42, 56, 0);")
        
        main_layout = QVBoxLayout(parking_page)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)
        
        # Simplified title
        title_label = QLabel("🚗 Parking Fee")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #4a90e2;
                background: transparent;
                margin-bottom: 20px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 简化的内容区域 - 去掉边框
        content_widget = QWidget()
        # content_widget.setMaximumWidth(700)
        content_widget.setMinimumWidth(600)
        content_widget.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.98);
                border-radius: 15px;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 简化的输入字段样式 - 去掉边框
        input_style = """
            QLineEdit {
                font-size: 16px;
                padding: 14px 18px;
                border: none;
                border-radius: 8px;
                background: rgba(74, 144, 226, 0.08);
                color: #2c3e50;
            }
            QLineEdit:focus {
                background: rgba(74, 144, 226, 0.15);
            }
        """
        
        # 创建输入字段组合函数
        def create_input_group(icon, label_text, placeholder, default_value):
            group_layout = QVBoxLayout()
            group_layout.setSpacing(6)
            
            label = QLabel(f"{icon} {label_text}")
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    color: #34495e;
                    background: transparent;
                }
            """)
            
            input_field = QLineEdit()
            input_field.setPlaceholderText(placeholder)
            input_field.setText(default_value)
            input_field.setStyleSheet(input_style)
            
            group_layout.addWidget(label)
            group_layout.addWidget(input_field)
            return group_layout, input_field
        
        # Create input fields
        plate_layout, self.plate_input = create_input_group(
            "🚙", "License Plate", "e.g.: 粤B12345", "粤B12345")
        content_layout.addLayout(plate_layout)
        
        amount_layout, self.amount_input = create_input_group(
            "💰", "Parking Fee", "e.g.: 15.50", "15.50")
        content_layout.addLayout(amount_layout)
        
        # Entry time display - simplified style
        time_label = QLabel("🕐 Entry Time")
        time_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #34495e;
                background: transparent;
            }
        """)
        
        self.entry_time_display = QLabel()
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")
        self.entry_time_display.setText(current_time)
        self.entry_time_display.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 14px 18px;
                border-radius: 8px;
                background: rgba(52, 152, 219, 0.1);
                color: #2c3e50;
            }
        """)
        
        content_layout.addWidget(time_label)
        content_layout.addWidget(self.entry_time_display)
        
        # Simplified send button
        self.send_parking_btn = QPushButton("Confirm Payment")
        self.send_parking_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 16px;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 10px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background: #357abd;
            }
            QPushButton:pressed {
                background: #2968a3;
            }
        """)
        self.send_parking_btn.clicked.connect(self.send_parking_data)
        content_layout.addWidget(self.send_parking_btn)
        
        # Simplified status display
        self.status_label = QLabel("Ready to send")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                padding: 8px;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 6px;
                color: #7f8c8d;
                text-align: center;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        # 居中显示内容
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(content_widget)
        center_layout.addStretch()
        
        main_layout.addLayout(center_layout)
        main_layout.addStretch()
        
        return parking_page
    
    def send_parking_data(self):
        """Send parking fee data in hexadecimal format"""
        try:
            # Get input data
            plate_number = self.plate_input.text().strip()
            amount = self.amount_input.text().strip()
            
            # Validate required fields
            if not plate_number or not amount:
                self.status_label.setText("License plate and amount are required")
                self.status_label.setStyleSheet("""
                    QLabel {
                        font-size: 13px;
                        padding: 8px;
                        background: rgba(231, 76, 60, 0.1);
                        border-radius: 6px;
                        color: #e74c3c;
                        text-align: center;
                    }
                """)
                return
            
            # Convert data to hexadecimal format
            hex_data = self.convert_to_hex_protocol(plate_number, amount)
            
            # Check if COM2 serial port is connected
            if hasattr(self, 'serial2') and self.serial2 and self.serial2.is_open:
                # Send hexadecimal data
                hex_bytes = bytes.fromhex(hex_data)
                self.serial2.write(hex_bytes)
                
                self.status_label.setText(f"{plate_number}  :  ${amount}\nHex: {hex_data}")
                self.status_label.setStyleSheet("""
                    QLabel {
                        font-size: 13px;
                        padding: 8px;
                        background: rgba(46, 204, 113, 0.1);
                        border-radius: 6px;
                        color: #27ae60;
                        text-align: center;
                    }
                """)
                    
            else:
                self.status_label.setText("COM2 port not connected")
                self.status_label.setStyleSheet("""
                    QLabel {
                        font-size: 13px;
                        padding: 8px;
                        background: rgba(231, 76, 60, 0.1);
                        border-radius: 6px;
                        color: #e74c3c;
                        text-align: center;
                    }
                """)
                
        except Exception as e:
            self.status_label.setText(f"Send failed: {str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    padding: 8px;
                    background: rgba(231, 76, 60, 0.1);
                    border-radius: 6px;
                    color: #e74c3c;
                    text-align: center;
                }
            """)
            print(f"Parking fee data send error: {str(e)}")
    
    def convert_to_hex_protocol(self, plate_number, amount):
        """
        Convert parking data to hexadecimal protocol format
        
        New Protocol format:
        [Header/Preamble(3)] [Length(2)] [SADDR(6)] [TADDR(6)] [SNQ(1)] [cmd_type(1)] [result(1)] [apdu_count(1)] [data(N)] [DCS(1)] [End(1)]
        
        Args:
            plate_number (str): License plate number (supports Chinese characters, e.g., "粤B12345")
            amount (str): Parking fee amount (e.g., "15.50")
            
        Returns:
            str: Hexadecimal string ready to send to MCU
            
        Example:
            Input: plate_number="粤B12345", amount="15.50"
            - Plate UTF-8 bytes: [0xE7, 0xB2, 0xA4, 0x42, 0x31, 0x32, 0x33, 0x34, 0x35] (9 bytes)
            - Amount in cents: 1550 (0x060E)
            - Data: E7B2A442313233343506OE
        """
        try:
            # 1. Header/Preamble (fixed)
            header_preamble = "0000FF"
            
            # 2. Convert plate number to UTF-8 bytes then to hex
            # This handles Chinese characters properly (e.g., "粤B12345")
            plate_bytes = plate_number.encode('utf-8')
            plate_hex = plate_bytes.hex().upper()
            
            # 3. Convert amount to cents (multiply by 100) then to 2-byte hex
            # e.g., "15.50" -> 1550 -> "060E"
            amount_cents = int(float(amount) * 100)
            amount_hex = f"{amount_cents:04X}"
            
            # 4. Build data field (plate + amount)
            data_field = plate_hex + amount_hex
            
            # 5. Fixed protocol fields
            saddr = "05FFFFFFFFFF"      # SADDR
            taddr = "06FFFFFFFFFF"      # TADDR  
            snq = "01"                  # SNQ
            cmd_type = "C2"             # cmd_type
            result = "00"               # result
            apdu_count = "01"           # apdu_count
            
            # 6. Calculate total data length (little endian)
            # Length includes: SADDR(6) + TADDR(6) + SNQ(1) + cmd_type(1) + result(1) + apdu_count(1) + data(N)
            total_data_length = 6 + 6 + 1 + 1 + 1 + 1 + len(data_field)//2
            length_hex = f"{total_data_length:02X}00"  # Little endian format
            
            # 7. Build payload for DCS calculation (everything except Header/Preamble and Length)
            payload_for_dcs = saddr + taddr + snq + cmd_type + result + apdu_count + data_field
            
            # 8. Calculate DCS (checksum)
            # DCS calculation: sum of all bytes from SADDR to data, then DCS = 0x100 - (sum & 0xFF)
            dcs_sum = 0
            for i in range(0, len(payload_for_dcs), 2):
                dcs_sum += int(payload_for_dcs[i:i+2], 16)
            dcs = (0x100 - (dcs_sum & 0xFF)) & 0xFF
            dcs_hex = f"{dcs:02X}"
            
            # 9. End byte
            end_byte = "00"
            
            # 10. Assemble complete protocol
            complete_hex = header_preamble + length_hex + payload_for_dcs + dcs_hex + end_byte
            
            return complete_hex
            
        except Exception as e:
            print(f"Error converting to hex protocol: {str(e)}")
            # Fallback to simple format if conversion fails
            return f"ERROR{str(e)[:10]}".encode('utf-8').hex().upper()
    
    def on_display_wheel(self, event):
        """处理显示区域的鼠标滚轮事件"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.font_size = min(self.font_size + 1, 24)  # 增大字体，最大24
            else:
                self.font_size = max(self.font_size - 1, 8)   # 减小字体，最小8
            
            # 更新字体大小
            self.serial_display.setStyleSheet(f"""
                QTextEdit {{
                    background-color: rgba(0, 0, 0, 0.2);
                    border          : 1px solid rgba(255, 255, 255, 0.1);
                    border-radius   : 10px;
                    padding         : 10px;
                    color           : #fafafa;
                    font-family     : 'Consolas', 'Courier New', monospace;
                    font-size       : {self.font_size}px;
                }}
            """)
        else:
            # 调用原始的滚轮事件处理
            QTextEdit.wheelEvent(self.serial_display, event)
    
    def on_display_key_press(self, event):
        """处理显示区域的键盘事件"""
        if event.key() == Qt.Key.Key_Space:
            self.auto_scroll.setChecked(not self.auto_scroll.isChecked())
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            # 计算查找框显示在serial_display右上角
            parent_pos = self.serial_display.mapToGlobal(self.serial_display.rect().topRight())
            dlg_geom = self.find_dialog.geometry()

            cursor = self.serial_display.textCursor()
            selected_text = cursor.selectedText()
            # 让查找框右上角与显示区右上角对齐
            self.find_dialog.move(parent_pos.x() - dlg_geom.width(), parent_pos.y())
            self.find_dialog.show()
            self.find_input.setFocus()
            self.find_input.selectAll()
            self.auto_scroll.setChecked(True)
            if selected_text:
                self.find_input.setText(selected_text)
        # 调用原始的键盘事件处理
        QTextEdit.keyPressEvent(self.serial_display, event)
    
    def update_find_count(self):
        """增量更新查找结果计数"""
        text = self.find_input.text()
        content = self.serial_display.toPlainText()
        # 增量缓存：只对新增内容查找
        if not hasattr(self, '_find_count_cache'):
            self._find_count_cache = {'text': '', 'content_len': 0, 'count': 0}
        cache = self._find_count_cache

        if not text:
            self.count_label.setText("0/0")
            cache['text']        = ''
            cache['content_len'] = 0
            cache['count']       = 0
            return

        if text != cache['text']:
            # 关键字变了，重新全量查找
            count = content.count(text)
            cache['text']        = text
            cache['content_len'] = len(content)
            cache['count']       = count
        else:
            # 关键字没变，只查找新增部分
            old_len = cache['content_len']
            if len(content) > old_len:
                new_part              = content[old_len:]
                count_new             = new_part.count(text)
                cache['count']       += count_new
                cache['content_len']  = len(content)
            # 如果内容被清空或减少，重新全量查找
            elif len(content) < old_len:
                count                = content.count(text)
                cache['count']       = count
                cache['content_len'] = len(content)

        count   = cache['count']
        current = 0
        # 获取当前选中的位置
        cursor = self.serial_display.textCursor()
        if cursor.hasSelection():
            sel_text = cursor.selectedText()
            if sel_text == text:
                pos     = cursor.position() - len(text)
                current = content[:pos].count(text) + 1
        self.count_label.setText(f"{current}/{count}")
    
    def find_text(self, forward=True):
        text = self.find_input.text()
        if not text:
            return
        
        # 终止上一个查找线程
        if hasattr(self, 'find_thread') and self.find_thread.isRunning():
            self.find_thread.terminate()
            self.find_thread.wait()
        
        self.auto_scroll.setChecked(True)

        content = self.serial_display.toPlainText()
        cursor  = self.serial_display.textCursor()
        cur_pos = cursor.selectionStart() if cursor.hasSelection() else cursor.position()

        # 启动查找线程
        self.find_thread = FindThread(content, text, cur_pos, forward)
        self.find_thread.result_ready.connect(self.on_find_result)
        self.find_thread.start()
    
    def on_find_result(self, current, total, positions):
        # 定位并高亮当前匹配项
        pos    = positions[current]
        length = len(self.find_input.text())
        cursor = self.serial_display.textCursor()
        cursor.setPosition(pos)
        cursor.setPosition(pos + length, QTextCursor.MoveMode.KeepAnchor)
        self.serial_display.setTextCursor(cursor)

        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#c3dd8c"))
        fmt.setForeground(QColor("#000000"))
        fmt.setFontWeight(QFont.Weight.Bold)
        cursor.mergeCharFormat(fmt)

        self._last_highlight = (pos, length)
        self.count_label.setText(f"{current+1}/{total}")

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
        if self.toggle_btn.text() == "打开串口":
            try:
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
                self.serial_thread.start()
                
                # 更新UI状态
                self.toggle_btn.setText("关闭串口")
                self.status_indicator.setStyleSheet("color: green;background:rgba(36,36,36,0);")

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
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开串口失败：{str(e)}")
                self.current_csv_log_file_path  = None 
                self.current_text_log_file_path = None
                self.open_csv_log_file_btn.setEnabled(False)
                return
        else:
            # 关闭串口
            if hasattr(self, 'serial_thread'):
                self.serial_thread.stop()
            if hasattr(self, 'serial_port'):
                self.serial_port.close()
            
            # 更新UI状态
            self.toggle_btn.setText("打开串口")
            self.status_indicator.setStyleSheet("color: red;background:rgba(36,42,56,0);")
    
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
                display_key = "RSSI" if chart_key == "lift_deep" else chart_key.upper()
                title = f"{display_key} | Avg: {mean:.1f} | Std: {std:.1f}"
            else:
                mean = 0
                std = 0
                title = chart_key.upper()
            chart.setTitle(title)

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

    # @time_decorator
    def handle_serial_data(self, data):
        try:
            text = data.decode('utf-8')
            
            self.log_worker.add_log_task("UwbLog", "info", text.strip())
            text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
            self.data_buffer.append(text)

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
                    json_data = json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    return
                # 提取用户坐标
                user_x = float(json_data.get('User-X', 0))
                user_y = float(json_data.get('User-Y', 0))
                user_z = float(json_data.get('User-Z', 0))
                
                new_red_length = int(json_data.get('RedAreaH', 0)) / 2
                new_blue_length = int(json_data.get('BlueAreaH', 0))
                refresh_needed = (getattr(self, 'red_length', None) != new_red_length) or (getattr(self, 'blue_length', None) != new_blue_length)
                self.red_length = new_red_length
                self.blue_length = new_blue_length

                # 仅当值发生变化时刷新位置视图
                if hasattr(self, 'position_view') and refresh_needed:
                    print("refresh areas")
                    self.position_view.refresh_areas()
                
                # Map JSON keys to chart keys
                key_mapping = {
                    'master'   : 'Master',
                    'slave'    : 'Slave',
                    'nlos'     : 'nLos',
                    'lift_deep': 'LiftDeep',
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

                # Log data
                data_values = [
                    json_data.get('Master', 0),
                    json_data.get('Slave', 0),
                    json_data.get('nLos', 0),
                    json_data.get('LiftDeep', 0),
                    json_data.get('Speed', 0),
                    json_data.get('User-X', 0),
                    json_data.get('User-Y', 0),
                    json_data.get('User-Z', 0),
                    json_data.get('Auth', 0),
                    json_data.get('Trans', 0)
                ]
                
                # 写入CSV
                csv_data = ",".join(str(val) for val in data_values)
                self.log_worker.add_log_task("data", "info", csv_data)
                
                # 缓存表格数据，延后批量插入
                if not hasattr(self, 'pending_table_rows'):
                    self.pending_table_rows = []
                self.pending_table_rows.append(data_values)

                # 更新用户位置显示（仅当有明显偏移时）
                if hasattr(self, 'position_view'):
                    last_pos = getattr(self.position_view, "current_position", None)
                    threshold = 2  # 例如5米或5像素，根据你的scale调整
                    if last_pos is None or ((user_x - last_pos[0]) ** 2 + (user_y - last_pos[1]) ** 2) ** 0.5 > threshold:
                        self.position_view.update_position(user_x, user_y)
                        
        except Exception as e:
            print(f"Error processing serial data: {str(e)}")

    def update_display(self):
        """更新显示区域"""
        if self.data_buffer:
            cursor         = self.serial_display.textCursor()
            scrollbar      = self.serial_display.verticalScrollBar()
            current_scroll = scrollbar.value()
            
            text = ''.join(self.data_buffer)
            
            # 如果选中了时间戳选项，为每行添加时间戳
            if self.timestamp.isChecked():
                lines = text.splitlines(True) 
                timestamp = QDateTime.currentDateTime().toString('[yyyy-MM-dd hh:mm:ss.zzz] ')
                text = ''.join(timestamp + line for line in lines)
            
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

            # 更新查找计数
            if self.find_dialog.isVisible():
                self.update_find_count()
            
            if self.auto_scroll.isChecked():
                scrollbar.setValue(current_scroll)
            else:
                scrollbar.setValue(scrollbar.maximum())

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
            text           = ''.join(self.data_buffer2)
            
            # 如果选中了时间戳选项，为每行添加时间戳
            if self.timestamp2.isChecked():
                lines     = text.splitlines(True)
                timestamp = QDateTime.currentDateTime().toString('[yyyy-MM-dd hh:mm:ss.zzz] ')
                text      = ''.join(timestamp + line for line in lines)
            
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

            # 更新查找计数
            if self.find_dialog2.isVisible():
                self.update_find_count2()
            
            if self.auto_scroll2.isChecked():
                scrollbar.setValue(current_scroll)
            else:
                scrollbar.setValue(scrollbar.maximum())

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
        self._save_background_config()
        self.update()
    
    def apply_theme(self):
        theme = self.current_theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['bg']};
            }}
            QWidget#titleBar {{
                background-color: {theme['title_bg']} !important;
            }}
            QLabel#titleLabel {{
                color           : #C29500;              /* 固定字体颜色 */
                font-weight     : bold;
                background-color: {theme['title_bg']};  /* 继承标题栏背景色 */
            }}
            QWidget {{
                background-color: {theme['bg']};
                color           : {theme['text']};
            }}
            QListWidget {{
                background-color: {theme['nav_bg']};
                border          : none;
            }}
            QListWidget::item {{
                color      : {theme['nav_item']};
                border-left: 4px solid transparent;
            }}
            QListWidget::item:selected {{
                background-color: {theme['nav_selected']};
                border-left     : 4px solid {theme['accent']};
            }}
            QComboBox:hover {{
                background: rgba(90, 110, 140, 0.604);
                border: 1px solid {theme['accent']};
            }}
            QPushButton {{
                background   : rgba(90, 110, 140, 0.33);
                color        : {theme['text']};
                border       : 1px solid rgba(90, 110, 140, 0.18);
                padding      : 4px 12px;
                border-radius: 8px;
                font-size    : 13px;
            }}
            QPushButton:hover {{

                border: 1px solid {theme['accent']};
            }}
            QLineEdit {{
                background   : rgba(255, 255, 255, 0.35);
                border       : 1px solid rgba(0, 0, 0, 0.35);
                border-radius: 15px;
                font-size    : 14px;
                padding      : 8px;
            }}
            QScrollBar:vertical {{
                background   : rgba(36, 42, 56, 0.08);
                width        : 12px;
                margin       : 4px 0 4px 0;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a90e2, stop:1 #1e293b
                );
                min-height   : 28px;
                border-radius: 6px;
                border       : 1px solid #3da9fc;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #90caf9, stop:1 #3da9fc
                );
                border: 1.5px solid #66abf5;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height    : 0;
                background: none;
                border    : none;
            }}
            QScrollBar:horizontal {{
                background   : rgba(36, 42, 56, 0.08);
                height       : 12px;
                margin       : 0 4px 0 4px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a90e2, stop:1 #1e293b
                );
                min-width    : 28px;
                border-radius: 6px;
                border       : 1px solid #3da9fc;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #90caf9, stop:1 #3da9fc
                );
                border: 1.5px solid #66abf5;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width     : 0;
                background: none;
                border    : none;
            }}
            QCheckBox {{
                color    : {theme['text']};
                spacing  : 5px;
                padding  : 2px;
                font-size: 12px;
            }}
            QCheckBox::indicator {{
                width        : 16px;
                height       : 16px;
                border       : 1px solid #a0a4ad;
                border-radius: 4px;
                background   : transparent;
            }}
            QCheckBox::indicator:hover {{
                border    : 1px solid {theme['accent']};
                background: rgba(90, 110, 140, 0.10);
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme['accent']};
                border          : 1px solid {theme['accent']};
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {theme['accent']};
                border          : 1px solid {theme['accent']};
            }}
            QCheckBox::indicator:checked:disabled {{
                background-color: #cccccc;
                border          : 1px solid #cccccc;
            }}
        """)
        if hasattr(self, "data_table"):
            self.data_table.setAlternatingRowColors(True)
            self.data_table.setStyleSheet(f"""
                QTableWidget {{
                    background                : transparent;
                    border                    : 1.5px solid #3a4a5c;
                    border-radius             : 14px;
                    selection-background-color: {theme['accent']};
                    selection-color           : #fff;
                    alternate-background-color: rgba(255,255,255,0.08);
                    font-size                 : 13px;
                    font-family               : 'JetBrains Mono', 'Consolas', 'Microsoft YaHei', monospace;
                    color                     : {theme['text']};
                }}
                QHeaderView::section {{
                    background             : {theme['nav_bg']};
                    color                  : {theme['nav_item']};
                    border                 : none;
                    padding                : 8px 5px;
                    font-weight            : bold;
                    font-size              : 13px;
                    border-top-left-radius : 10px;
                    border-top-right-radius: 10px;
                }}
                QTableWidget::item {{
                    color     : {theme['text']};
                    border    : none;
                    background: transparent;
                    font-size : 13px;
                }}
                QTableWidget::item:selected {{
                    background: {theme['accent']};
                    color     : #fff;
                }}
                QTableWidget::item:hover {{
                    background: rgba(76, 175, 255, 0.18);
                }}
                QTableWidget::viewport {{
                    background: transparent;
                }}
                QTableCornerButton::section {{
                    background            : {theme['nav_bg']};
                    border                : none;
                    border-top-left-radius: 10px;
                }}
            """)
            self.data_table.setShowGrid(False)
        
    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        if index != 0:  
            self.find_dialog.close()
        if index != 1:
            self.find_dialog2.close()

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
        add_btn       = QPushButton("添加")
        add_btn.clicked.connect(self.add_keyword)
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_keyword)
        remove_btn = QPushButton("删除")
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

class PositionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_position = None
        self.last_position    = None
        self.scale            = 2
        self.origin_offset_y  = -200
        self.main_window      = parent  # 保存主窗口引用
        
        # 创建静态内容缓存
        self.static_content   = None
        
        # 滤波和异常值检测相关参数
        self.position_history = []  # 存储最近的位置历史
        self.history_max_size = 3   # 历史记录最大长度
        self.max_jump_distance = 50  # 最大允许跳变距离
        self.smoothing_factor = 0.5  # 平滑因子 (0-1)，越小越平滑
        
    def draw_static_content(self, painter, center_x, center_y):
        # 获取动态长度值
        red_height = int(self.main_window.red_length * self.scale) if self.main_window.red_length != 0 else 100
        blue_height = int(self.main_window.blue_length ) if self.main_window.blue_length != 0 else 300
        print(f'red_height: {red_height}, blue_height: {blue_height}')
        
        # 红色感应区（从原点开始向下）
        red_gradient = QLinearGradient(center_x, center_y, center_x, center_y + red_height)
        red_gradient.setColorAt(0, QColor(255, 0, 0, 70))  # 增加红色透明度
        red_gradient.setColorAt(1, QColor(255, 0, 0, 80))
        painter.setBrush(red_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(int(center_x - 100), int(center_y), 200, red_height)
        
        # 蓝色区域（紧接红色区域，不重叠）
        blue_start_y = center_y + red_height
        blue_rect_height = blue_height - red_height if blue_height > red_height else blue_height
        blue_gradient = QLinearGradient(center_x, blue_start_y, center_x, blue_start_y + blue_rect_height)
        blue_gradient.setColorAt(0, QColor(0, 140, 255, 100))  # 增加蓝色透明度和饱和度
        blue_gradient.setColorAt(1, QColor(0, 140, 255, 70))
        painter.setBrush(blue_gradient)
        painter.drawRect(int(center_x - 100), int(blue_start_y), 200, blue_rect_height)
        
        # 绘制闸机（左侧）
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.setBrush(QColor("#444444"))
        painter.drawRect(int(center_x - 100), int(center_y - 40), 20, 80)  # 修改为-100
        # 闸机装饰
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawLine(int(center_x - 95), int(center_y - 30), int(center_x - 85), int(center_y - 30))  # 对应调整装饰线
        painter.drawLine(int(center_x - 95), int(center_y), int(center_x - 85), int(center_y))
        painter.drawLine(int(center_x - 95), int(center_y + 30), int(center_x - 85), int(center_y + 30))
        
        # 绘制闸机（右侧）
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.setBrush(QColor("#444444"))
        painter.drawRect(int(center_x + 80), int(center_y - 40), 20, 80)  # 修改为+80，考虑闸机宽度20
        # 闸机装饰
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawLine(int(center_x + 85), int(center_y - 30), int(center_x + 95), int(center_y - 30))  # 对应调整装饰线
        painter.drawLine(int(center_x + 85), int(center_y), int(center_x + 95), int(center_y))
        painter.drawLine(int(center_x + 85), int(center_y + 30), int(center_x + 95), int(center_y + 30))
        
        # 绘制坐标轴
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawLine(0, int(center_y), self.width(), int(center_y))
        painter.drawLine(int(center_x), 0, int(center_x), self.height())
        
        # 绘制原点（红色）
        painter.setPen(QPen(QColor("#FF0000"), 2))
        painter.setBrush(QColor("#FF0000"))
        painter.drawEllipse(int(center_x) - 2, int(center_y) - 2, 4, 4)
        
    def create_static_content(self):
        """创建静态内容缓存"""
        self.static_content = QPixmap(self.size())
        self.static_content.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(self.static_content)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取窗口中心
        center_x = self.width() / 2
        center_y = self.height() / 2 + self.origin_offset_y
        
        # 绘制静态内容
        self.draw_static_content(painter, center_x, center_y)
        painter.end()
        
    def update_position(self, x, y):
        """更新位置并触发重绘，包含滤波和异常值检测"""
        # 如果是第一个点，直接接受
        if self.current_position is None:
            self.current_position = (x, y)
            self.position_history.append((x, y))
            self.update()
            return
            
        # 计算与上一个点的距离
        last_x, last_y = self.current_position
        distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
        
        # 异常值检测 - 如果距离太大，可能是异常值
        if distance > self.max_jump_distance:
            print(f"异常值检测: 距离 {distance:.1f} 超过阈值 {self.max_jump_distance}")
            
            # 限制移动距离，沿着相同方向但限制距离
            direction_x = (x - last_x) / distance if distance > 0 else 0
            direction_y = (y - last_y) / distance if distance > 0 else 0

            x = last_x + direction_x * self.max_jump_distance
            y = last_y + direction_y * self.max_jump_distance

            distance_new = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
        
        # 移动平均滤波
        if self.position_history:
            # 添加当前点到历史
            self.position_history.append((x, y))
            
            # 保持历史记录在指定长度内
            if len(self.position_history) > self.history_max_size:
                self.position_history.pop(0)
            
            # 计算历史点的平均位置
            avg_x = sum(pos[0] for pos in self.position_history) / len(self.position_history)
            avg_y = sum(pos[1] for pos in self.position_history) / len(self.position_history)
            
            # 应用平滑因子 - 在当前测量值和平均值之间插值
            smoothed_x = x * self.smoothing_factor + avg_x * (1 - self.smoothing_factor)
            smoothed_y = y * self.smoothing_factor + avg_y * (1 - self.smoothing_factor)
            
            # 更新位置
            self.last_position = self.current_position
            self.current_position = (smoothed_x, smoothed_y)
        else:
            # 如果没有历史记录，直接使用当前值
            self.last_position = self.current_position
            self.current_position = (x, y)
            self.position_history.append((x, y))
        
        self.update()
        
    def refresh_areas(self):
        """刷新红蓝区域，当长度值变化时调用"""
        self.static_content = None  # 清除缓存
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 如果静态内容不存在或窗口大小改变，重新创建
        if self.static_content is None or \
           self.static_content.size() != self.size():
            self.create_static_content()
        
        # 绘制静态内容
        painter.drawPixmap(0, 0, self.static_content)
            
        # 如果没有位置数据，到此结束
        if not self.current_position:
            return
            
        # 获取窗口中心（用于动态内容）
        center_x = self.width() / 2
        center_y = self.height() / 2 + self.origin_offset_y
        
        # 绘制动态内容（位置点和轨迹）
        x, y = self.current_position
        screen_x = center_x + x * self.scale
        screen_y = center_y + y * self.scale

        # 绘制坐标文本背景
        coord_text = f"X: {int(x)}, Y: {int(y)}"
        bg_rect = painter.fontMetrics().boundingRect(coord_text)
        bg_rect.adjust(-15, -5, 15, 5)  # 扩大背景区域
        bg_rect.moveTopLeft(QPoint(10, 5))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 120))  # 半透明黑色背景
        painter.drawRoundedRect(bg_rect, 5, 5)  # 圆角矩形背景
        
        # 绘制坐标文本
        painter.setPen(QPen(QColor("#ffffff"), 2))  # 白色文本
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))  # 加粗字体
        painter.drawText(15, 23, coord_text)
        
        if self.last_position:
            last_x, last_y = self.last_position
            last_screen_x = center_x + last_x * self.scale
            last_screen_y = center_y + last_y * self.scale
            
            # 使用渐变色绘制轨迹
            gradient = QLinearGradient(last_screen_x, last_screen_y, screen_x, screen_y)
            gradient.setColorAt(0, QColor(180, 120, 220, 25))  # 起点颜色（浅紫色较淡）
            gradient.setColorAt(1, QColor(180, 120, 220, 200))  # 终点颜色（浅紫色较深）
            
            pen = QPen()
            pen.setBrush(gradient)
            pen.setWidth(5)  # 增加线条宽度
            painter.setPen(pen)
            painter.drawLine(int(last_screen_x), int(last_screen_y), 
                           int(screen_x), int(screen_y))
        
        # 绘制当前位置点
        painter.setPen(QPen(QColor("#b478dc"), 2))
        painter.setBrush(QColor(180, 120, 220, 255))
        painter.drawEllipse(int(screen_x) - 6, int(screen_y) - 6, 12, 12)  # 增大点的大小

class SubwayGateAnimation(QWidget):
    """地铁闸机开门关门动画组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setMinimumSize(300, 200)
        
        self.gate_state = "closed"  # closed, opening, open, closing
        self.left_door_angle = 0    # 左门角度 (0-90)
        self.right_door_angle = 0   # 右门角度 (0-90)
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        
        self.animation_speed = 2.5  # 帧
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
        door_width = 80   # 横向门的宽度
        door_height = 15  # 横向门的高度
        
        import math
        
        # 计算门的横向偏移（基于角度）
        left_offset = math.sin(math.radians(self.left_door_angle)) * 60
        right_offset = math.sin(math.radians(self.right_door_angle)) * 60
        
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
            painter.setPen(QPen(border_color, 2))
            
            # 绘制横向门体
            door_rect = QRect(door_x, door_y, door_width, door_height)
            painter.drawRoundedRect(door_rect, 6, 6)
            
            # 横向中央线
            painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
            painter.drawLine(door_x + 10, door_y + door_height // 2, door_x + door_width - 10, door_y + door_height // 2)
            
            # 绘制门端传感器
            sensor_size = 8
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
            painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
            painter.drawEllipse(sensor_x, sensor_y, sensor_size, sensor_size)
            
            # 传感器中心点
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(sensor_x + 2, sensor_y + 2, 4, 4)
            
            # 绘制门的阴影效果
            shadow_offset = 2
            shadow_color = QColor(0, 0, 0, 60)
            painter.setBrush(shadow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            shadow_rect = QRect(door_x, door_y + shadow_offset, door_width, door_height)
            painter.drawRoundedRect(shadow_rect, 6, 6)
        
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
        
        # 绘制动态网格背景
        grid_size = 25
        grid_alpha = int(30 + 20 * math.sin(self.frame_count * 0.05))
        painter.setPen(QPen(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), grid_alpha), 1))
        
        # 垂直网格线
        for x in range(0, self.width(), grid_size):
            # 添加闪烁效果
            line_alpha = int(grid_alpha + 30 * math.sin(self.frame_count * 0.1 + x * 0.01))
            painter.setPen(QPen(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), max(0, min(255, line_alpha))), 1))
            painter.drawLine(x, 0, x, self.height())
            
        # 水平网格线
        for y in range(0, self.height(), grid_size):
            line_alpha = int(grid_alpha + 30 * math.sin(self.frame_count * 0.1 + y * 0.01))
            painter.setPen(QPen(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), max(0, min(255, line_alpha))), 1))
            painter.drawLine(0, y, self.width(), y)
        
        # 绘制数据流线条
        painter.setPen(QPen(grid_color, 2))
        flow_speed = 3
        for i in range(5):
            flow_x = (self.frame_count * flow_speed + i * 50) % (self.width() + 100) - 50
            flow_y = 30 + i * 40
            if flow_y < self.height():
                # 数据流点
                for j in range(8):
                    dot_x = flow_x - j * 15
                    if 0 <= dot_x <= self.width():
                        dot_alpha = int(200 * (1 - j / 8.0))
                        painter.setBrush(QColor(grid_color.red(), grid_color.green(), grid_color.blue(), dot_alpha))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawEllipse(dot_x - 2, flow_y - 1, 4, 2)
    
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
        
        # 绘制底座平台
        base_gradient = QLinearGradient(center_x - 100, center_y + 60, center_x + 100, center_y + 80)
        base_gradient.setColorAt(0, QColor(40, 50, 70, 200))
        base_gradient.setColorAt(0.5, QColor(60, 70, 90, 240))
        base_gradient.setColorAt(1, QColor(40, 50, 70, 200))
        
        painter.setBrush(base_gradient)
        painter.setPen(QPen(primary_color, 2))
        painter.drawRoundedRect(center_x - 100, center_y + 60, 200, 20, 10, 10)
        
        # 左侧立柱 
        left_pillar_gradient = QLinearGradient(center_x - 90, center_y - 70, center_x - 70, center_y + 70)
        left_pillar_gradient.setColorAt(0, QColor(80, 100, 140, 220))
        left_pillar_gradient.setColorAt(0.3, QColor(100, 120, 160, 250))
        left_pillar_gradient.setColorAt(0.7, QColor(90, 110, 150, 250))
        left_pillar_gradient.setColorAt(1, QColor(70, 90, 130, 220))
        
        painter.setBrush(left_pillar_gradient)
        painter.setPen(QPen(primary_color, 3))
        painter.drawRoundedRect(center_x - 90, center_y - 70, 25, 140, 8, 8)
        
        # 右侧立柱 
        right_pillar_gradient = QLinearGradient(center_x + 65, center_y - 70, center_x + 90, center_y + 70)
        right_pillar_gradient.setColorAt(0, QColor(80, 100, 140, 220))
        right_pillar_gradient.setColorAt(0.3, QColor(100, 120, 160, 250))
        right_pillar_gradient.setColorAt(0.7, QColor(90, 110, 150, 250))
        right_pillar_gradient.setColorAt(1, QColor(70, 90, 130, 220))
        
        painter.setBrush(right_pillar_gradient)
        painter.setPen(QPen(primary_color, 3))
        painter.drawRoundedRect(center_x + 65, center_y - 70, 25, 140, 8, 8)
        
        # 装饰线条 
        glow_alpha = int(100 + 30 * math.sin(self.frame_count * 0.1))
        painter.setPen(QPen(QColor(secondary_color.red(), secondary_color.green(), secondary_color.blue(), glow_alpha), 1))
        
        # 立柱中央线条
        painter.drawLine(center_x - 77, center_y - 50, center_x - 77, center_y + 50)
        painter.drawLine(center_x + 77, center_y - 50, center_x + 77, center_y + 50)
        
        # 在立柱顶部绘制状态指示LED
        led_size = 6
        led_positions = [(center_x - 77, center_y - 60), (center_x + 77, center_y - 60)]
        
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
            painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
            painter.drawEllipse(led_x - led_size//2, led_y - led_size//2, led_size, led_size)
        
        # 绘制传感器阵列
        sensor_positions = [
            (center_x - 82, center_y - 30),
            (center_x - 82, center_y),
            (center_x - 82, center_y + 30),
            (center_x + 82, center_y - 30),
            (center_x + 82, center_y),
            (center_x + 82, center_y + 30)
        ]
        
        for i, (sx, sy) in enumerate(sensor_positions):
            # 传感器闪烁效果
            blink_alpha = int(100 + 100 * math.sin(self.frame_count * 0.15 + i * 0.5))
            sensor_color = QColor(accent_color.red(), accent_color.green(), accent_color.blue(), blink_alpha)
            
            painter.setBrush(sensor_color)
            painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
            painter.drawEllipse(sx - 3, sy - 3, 6, 6)
    
    def draw_scan_lines(self, painter):
        """绘制扫描线效果"""
        import math
        
        # 根据状态调整扫描线颜色
        if self.gate_state in ["open", "opening"]:
            scan_color = QColor(0, 255, 200)
        else:
            scan_color = QColor(255, 150, 100)
        
        # 主扫描线 - 水平移动
        scan_alpha = int(120 + 80 * math.sin(self.frame_count * 0.15))
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), scan_alpha), 3))
        
        # 主扫描线
        main_scan_y = self.scan_line_pos
        painter.drawLine(0, main_scan_y, self.width(), main_scan_y)
        
        # 副扫描线
        secondary_scan_y = (self.scan_line_pos + self.height()//2) % self.height()
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), scan_alpha//2), 2))
        painter.drawLine(0, secondary_scan_y, self.width(), secondary_scan_y)
        
        # 垂直扫描线 - 左右移动
        vertical_scan_x = (self.frame_count * 3) % (self.width() + 100) - 50
        if 0 <= vertical_scan_x <= self.width():
            painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), scan_alpha//3), 2))
            painter.drawLine(vertical_scan_x, 0, vertical_scan_x, self.height())
        
        # 雷达扫描效果（圆形）
        center_x = self.width() // 2
        center_y = self.height() // 2
        radar_radius = int(50 + 30 * math.sin(self.frame_count * 0.08))
        
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), 60), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - radar_radius, center_y - radar_radius, 
                           radar_radius * 2, radar_radius * 2)
        
        # 雷达扫描臂
        radar_angle = (self.frame_count * 4) % 360
        radar_end_x = center_x + radar_radius * math.cos(math.radians(radar_angle))
        radar_end_y = center_y + radar_radius * math.sin(math.radians(radar_angle))
        
        painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), 150), 3))
        painter.drawLine(center_x, center_y, int(radar_end_x), int(radar_end_y))
        
        # 扫描点效果
        for i in range(3):
            point_radius = 20 + i * 15
            point_alpha = int(100 - i * 30)
            painter.setPen(QPen(QColor(scan_color.red(), scan_color.green(), scan_color.blue(), point_alpha), 1))
            painter.drawEllipse(int(radar_end_x) - point_radius, int(radar_end_y) - point_radius,
                               point_radius * 2, point_radius * 2)
    
    def draw_glow_effect(self, painter, center_x, center_y):
        """绘制发光效果"""
        import math
        
        # 创建径向渐变发光
        glow_radius = 100 * self.glow_intensity
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
                'size': random.uniform(2, 5)
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
    
    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running     = False
        
    def run(self):
        self.running = True
        buffer       = bytearray()
        while self.running and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    # 等待一小段时间，让数据完整到达
                    time.sleep(0.05)
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        buffer.extend(data)
                        # 检查是否有完整的行
                        while b'\n' in buffer:
                            line_end = buffer.find(b'\n')
                            # 提取完整的行（包括换行符）
                            line = bytes(buffer[:line_end + 1])
                            buffer = buffer[line_end + 1:]
                            if line.strip():  # 忽略空行
                                self.data_received.emit(line)
            except Exception as e:
                print(f"串口读取错误: {str(e)}")
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
    app.setStyle("Fusion")  # 使用Fusion样式更好支持透明效果
    window = MainWindow()
    window.show()
    # 在显示窗口后设置最大化状态
    window.setWindowState(Qt.WindowState.WindowMaximized)
    window.maximize_btn.setText("❐")
    sys.exit(app.exec())

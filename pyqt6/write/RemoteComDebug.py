import sys
import os
import ctypes
import time
import serial
from ctypes import wintypes
import win32clipboard
import win32con
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint, QUrl, QTimer, QDateTime, QThread
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor, QPixmap, QPainter, QIcon, QCursor, QClipboard, QIntValidator

class MainWindow(QMainWindow):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_theme = ThemeManager.DARK_THEME
        self.drag_pos = QPoint()
        self.server_serial_thread = None
        self.client_serial_thread = None
        
        # 添加串口实例变量
        self.server_serial = None
        self.client_serial = None
        self.root_path = os.path.dirname(__file__) + "/PIC"
        self.setWindowIcon(QIcon(os.path.join(self.root_path, "my.ico")))
        self.image_files = ['bg.png', 'my.png', 'my.png', 'my.png']
        self.background_image = QPixmap(os.path.join(self.root_path,self.image_files[0])) 
        if self.background_image.isNull():
            print(f"图片加载失败 {os.path.join(self.root_path,self.image_files[0])}")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.WindowMinimizeButtonHint |  # 允许最小化
            Qt.WindowType.WindowMaximizeButtonHint  # 允许最大化
        )
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Remote COM Debug Tool")
        self.setGeometry(100, 100, 800, 600)

        title_bar = self.create_title_bar()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏
        nav_container = self.create_nav_bar()
        self.nav_list.currentRowChanged.connect(self.switch_page)

        # 右侧堆栈窗口
        self.stacked_widget = QStackedWidget()
        self.create_pages()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(nav_container)
        splitter.addWidget(self.stacked_widget)
        splitter.setStretchFactor(1, 1)  # 设置堆栈窗口可以拉伸
        splitter.setSizes([80,500])

        main_layout.addWidget(title_bar)
        main_layout.addWidget(splitter)  
        
        self.apply_theme()
        self.nav_list.setCurrentRow(0)

    def create_nav_bar(self):
        nav_container = QWidget()
        nav_container.setMinimumWidth(65)  # 允许拉伸的最小宽度
        nav_container.setMaximumWidth(300)  # 限制最大宽度
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.nav_list = QListWidget()
        self.nav_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        nav_items = ["Server", "Client"] 
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

    def create_title_bar(self):
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet(f"background-color: {self.current_theme['title_bg']};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(5)

        # 启用鼠标追踪
        title_bar.setAttribute(Qt.WidgetAttribute.WA_MouseTracking)
        
        # 标题和图标
        self.title_label = QLabel("Modern App")
        self.title_label.setStyleSheet("color: #C29500; font-weight: bold;")

        # 窗口控制按钮
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

        # 统一按钮样式
        control_btns = [minimize_btn, self.maximize_btn, close_btn]
        for btn in control_btns:
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    font-size: 10px;
                    padding: 5px;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
        # 特殊处理关闭按钮的悬停效果
        close_btn.setStyleSheet(close_btn.styleSheet() + """
            QPushButton:hover {
                background-color: #ff4444;
            }
        """)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(self.maximize_btn)
        title_layout.addWidget(close_btn)
        
        return title_bar

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")

    def create_pages(self):
        server_page = self.create_server_page()
        client_page = self.create_client_page()
        
        self.stacked_widget.addWidget(server_page)
        self.stacked_widget.addWidget(client_page)
        
        # 在两个页面都创建完成后刷新串口列表
        self.refresh_serial_ports()

    def create_client_page(self):
        """创建客户端页面"""
        client_page = QWidget()
        layout = QVBoxLayout(client_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 添加标题
        title_label = self.create_page_title("客户端 - 接收远程数据并转发到本地串口")
        
        # 创建主分割容器
        main_container = QSplitter(Qt.Orientation.Horizontal)
        
        # 添加到主布局
        layout.addWidget(title_label)
        layout.addWidget(main_container)
        
        return client_page

    def create_server_page(self):
        """创建服务器页面"""
        server_page = QWidget()
        layout = QVBoxLayout(server_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 添加标题
        title_label = self.create_page_title("服务器 - 接收本地串口数据并转发到远程")
        
        # 创建主分割容器
        main_container = QSplitter(Qt.Orientation.Horizontal)
        
        # 创建左右两侧部件
        left_widget = self.create_server_left_panel()
        right_widget = self.create_server_right_panel()
        
        # 添加到主分割器
        main_container.addWidget(left_widget)
        main_container.addWidget(right_widget)
        main_container.setSizes([400, 400])
        
        # 添加到主布局
        layout.addWidget(title_label)
        layout.addWidget(main_container)
        
        return server_page

    def create_page_title(self, text):
        """创建页面标题"""
        title_label = QLabel(text)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFixedHeight(30)
        return title_label

    def create_server_left_panel(self):
        """创建服务器页面左侧面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 创建串口配置组
        serial_group = self.create_server_serial_config()
        # 创建数据接收组
        receive_group = self.create_server_receive_area()
        
        left_layout.addWidget(serial_group)
        left_layout.addWidget(receive_group)
        
        return left_widget

    def create_server_serial_config(self):
        """创建服务器串口配置组"""
        serial_group = QGroupBox("本地串口配置")
        serial_layout = QFormLayout(serial_group)
        
        self.server_port_combo = QComboBox()
        self.server_baud_combo = QComboBox()
        for baud in ["9600", "115200", "460800", "3000000"]:
            self.server_baud_combo.addItem(baud)
        self.server_baud_combo.setCurrentText("460800")
        
        self.server_serial_btn = QPushButton("打开串口")
        self.server_serial_status = QLabel("关闭")
        self.server_serial_status.setStyleSheet("color: red;")
        
        serial_btn_layout = QHBoxLayout()
        serial_btn_layout.addWidget(self.server_serial_btn)
        serial_btn_layout.addWidget(self.server_serial_status)
        
        serial_layout.addRow("串口:", self.server_port_combo)
        serial_layout.addRow("波特率:", self.server_baud_combo)
        serial_layout.addRow("", serial_btn_layout)

        # 连接信号
        self.server_serial_btn.clicked.connect(self.toggle_server_serial)
        
        return serial_group

    def create_server_receive_area(self):
        """创建服务器数据接收区域"""
        receive_group = QGroupBox("串口数据接收")
        receive_layout = QVBoxLayout(receive_group)
        
        self.server_serial_data = QTextEdit()
        self.server_serial_data.setReadOnly(True)
        self.server_serial_data.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.server_serial_data.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        receive_control_layout = QHBoxLayout()
        self.server_clear_btn = QPushButton("清除")
        self.server_hex_display = QCheckBox("HEX显示")
        self.server_hex_display.setChecked(True)
        receive_control_layout.addWidget(self.server_hex_display)
        receive_control_layout.addWidget(self.server_clear_btn)
        
        receive_layout.addWidget(self.server_serial_data)
        receive_layout.addLayout(receive_control_layout)
        
        return receive_group

    def create_server_right_panel(self):
        """创建服务器页面右侧面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 创建远程服务配置组
        remote_group = self.create_server_remote_config()
        
        right_layout.addWidget(remote_group)
        
        return right_widget

    def create_server_remote_config(self):
        """创建服务器远程配置组"""
        remote_group = QGroupBox("远程服务配置")
        remote_layout = QFormLayout(remote_group)
        
        self.server_host_input = QLineEdit("0.0.0.0")
        self.server_port_input = QLineEdit("8888")
        self.server_port_input.setValidator(QIntValidator(1, 65535))
        
        remote_layout.addRow("监听地址:", self.server_host_input)
        remote_layout.addRow("监听端口:", self.server_port_input)
        
        self.server_start_btn = QPushButton("启动服务")
        self.server_status = QLabel("未启动")
        self.server_status.setStyleSheet("color: red;")
        
        server_btn_layout = QHBoxLayout()
        server_btn_layout.addWidget(self.server_start_btn)
        server_btn_layout.addWidget(self.server_status)
        remote_layout.addRow("", server_btn_layout)
        
        return remote_group

    def refresh_serial_ports(self):
        """刷新可用串口列表"""
        import serial.tools.list_ports
        current_server = self.server_port_combo.currentText() if self.server_port_combo.count() > 0 else ""
        self.server_port_combo.clear()
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            self.server_port_combo.addItem(port.device)
            
        if current_server and self.server_port_combo.findText(current_server) >= 0:
            self.server_port_combo.setCurrentText(current_server)
    
    def toggle_server_serial(self):
        """切换服务端串口状态"""
        if self.server_serial_btn.text() == "打开串口":
            try:
                port = self.server_port_combo.currentText()
                if not port:
                    raise Exception("请选择串口")
                    
                baud = int(self.server_baud_combo.currentText())
                self.server_serial = serial.Serial(
                    port=port,
                    baudrate=baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.1
                )
                
                if not self.server_serial.is_open:
                    self.server_serial.open()
                
                self.server_serial_btn.setText("关闭串口")
                self.server_serial_status.setText("已打开")
                self.server_serial_status.setStyleSheet("color: green;")

                # 创建并启动读取线程
                self.server_serial_thread = SerialReadThread(self.server_serial)
                self.server_serial_thread.data_received.connect(self.on_server_data_received)
                self.server_serial_thread.start()
                
            except Exception as e:
                if self.server_serial:
                    self.server_serial.close()
                    self.server_serial = None
                QMessageBox.warning(self, "错误", f"打开串口失败: {str(e)}")
        else:
            try:
                # 停止读取线程
                if self.server_serial_thread:
                    self.server_serial_thread.stop()
                    self.server_serial_thread = None

                if self.server_serial:
                    self.server_serial.close()
                    self.server_serial = None
                
                self.server_serial_btn.setText("打开串口")
                self.server_serial_status.setText("关闭")
                self.server_serial_status.setStyleSheet("color: red;")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"关闭串口失败: {str(e)}")
    
    def on_server_data_received(self, data):
        """处理服务端接收到的串口数据"""
        try:
            if self.server_hex_display.isChecked():
                # HEX显示
                hex_str = ' '.join([f"{b:02X}" for b in data]) + '\n'  # 添加换行符
                print("接收数据(HEX):", ' '.join([f"{b:02X}" for b in data]))
                self.server_serial_data.moveCursor(QTextCursor.MoveOperation.End)
                self.server_serial_data.insertPlainText(hex_str)
            else:
                # 文本显示
                try:
                    text = data.decode('utf-8')
                except UnicodeDecodeError:
                    text = data.decode('gbk', errors='ignore')
                self.server_serial_data.moveCursor(QTextCursor.MoveOperation.End)
                self.server_serial_data.insertPlainText(text + '\n')  # 添加换行符
            
            # 自动滚动到底部
            self.server_serial_data.moveCursor(QTextCursor.MoveOperation.End)
        except Exception as e:
            print(f"数据处理错误: {str(e)}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
    
    def toggle_theme(self):
        self.current_theme = ThemeManager.DARK_THEME if \
            self.current_theme == ThemeManager.LIGHT_THEME else ThemeManager.LIGHT_THEME
        self.apply_theme()
        self.theme_btn.setStyleSheet(f"background: {self.current_theme['bg']}; border-radius: 0px;")
    
    def apply_theme(self):
        theme = self.current_theme
        self.title_label.setStyleSheet(f"color: {theme['nav_item']}; font-weight: bold;")
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['bg']};
            }}
            QWidget {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}
            QListWidget {{
                background-color: {theme['nav_bg']};
                border: none;
            }}
            QListWidget::item {{
                color: {theme['nav_item']};
                border-left: 4px solid transparent;
            }}
            QListWidget::item:selected {{
                background-color: {theme['nav_selected']};
                border-left: 4px solid {theme['accent']};
            }}
            QPushButton {{
                background: {theme['accent']};
                color: white;
                border: none;
                padding: 9px;
                border-radius: 10px;
            }}
            QLineEdit {{
                background: rgba(255, 255, 255, 0.35);
                border: 1px solid rgba(0, 0, 0, 0.35);
                border-radius: 15px;
                font-size: 14px;
                padding: 8px;
            }}
            QScrollBar:vertical {{
                background: rgba(25, 55, 80, 0.486);
                width: 10px;
                border: none;
                margin: 0px 0px 0px 0px;
            }}
        """)
        
    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

class ThemeManager:
    # 📌📁❌🔸
    LIGHT_THEME = {
        "nav_bg": "rgba(248, 249, 250,  0.35)",
        "nav_item": "#c29500",
        "nav_selected": "rgba(233, 236, 239,  0.35)",
        "accent": "#4a90e2",
        "bg": "rgba(255, 255, 255,  0.35)",
        "text": "#2d3436",
        "title_bg": "#f8f9fa"
    }

    DARK_THEME = {
        "nav_bg": "rgba(45, 52, 54,  0.35)",
        "nav_item": "#dfe6e9",
        "nav_selected": "rgba(74, 74, 74,  0.35)",
        "accent": "#6c5ce7",
        "bg": "rgba(53, 59, 64, 0.35)",
        "text": "#f8f9fa",
        "title_bg": "#2d3436"
    }

class SerialReadThread(QThread):
    data_received = pyqtSignal(bytes)
    
    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = False
        
    def run(self):
        self.running = True
        while self.running and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    # 等待一小段时间，让数据完整到达
                    time.sleep(0.05)
                    # 一次性读取所有数据
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        self.data_received.emit(data)
            except Exception as e:
                print(f"串口读取错误: {str(e)}")
                break
            time.sleep(0.01)  # 降低CPU占用
            
    def stop(self):
        self.running = False
        self.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion样式更好支持透明效果
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

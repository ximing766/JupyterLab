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
        
        nav_items = ["Page 1", "Page 2"] 
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
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(5)

        # 启用鼠标追踪
        title_bar.setAttribute(Qt.WidgetAttribute.WA_MouseTracking)
        
        # 标题和图标
        self.title_label = QLabel("Modern App")
        self.title_label.setObjectName("titleLabel")

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

    def create_client_page(self):
        client_page = QWidget()
        layout = QVBoxLayout(client_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title_label = self.create_page_title("Page 2")
        
        main_container = QSplitter(Qt.Orientation.Horizontal)
        
        # 创建位置显示区域
        position_widget = QWidget()
        position_widget.setMinimumSize(400, 300)
        position_widget.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border-radius: 10px;")
        
        # 创建标签显示坐标
        self.position_label = QLabel("位置: (0, 0)")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_label.setStyleSheet("font-size: 14px; color: #c29500;")
        self.position_label.setFixedHeight(30)  # 固定高度
        self.position_label.setMaximumWidth(150)  # 限制最大宽度
        
        # 创建自定义位置指示器
        self.position_indicator = PositionIndicator()
        
        # 垂直布局放置标签和指示器
        position_layout = QVBoxLayout(position_widget)
        position_layout.addWidget(self.position_label)
        position_layout.addWidget(self.position_indicator)
        
        # 创建定时器模拟位置更新
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.start(50)  # 每100ms更新一次
        
        main_container.addWidget(position_widget)
        
        # 添加到主布局
        layout.addWidget(title_label)
        layout.addWidget(main_container)
        
        return client_page
    
    def update_position(self):
        # 这里模拟接收新的位置数据
        # 实际应用中，这里应该是从实际数据源获取位置
        import random
        x = random.randint(0, 100)
        y = random.randint(0, 100)
        self.position_label.setText(f"位置: ({x}, {y})")
        self.position_indicator.update_position(x, y)

    

    def create_server_page(self):
        server_page = QWidget()
        layout = QVBoxLayout(server_page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title_label = self.create_page_title("Page 1")
        
        # 创建主分割容器
        main_container = QSplitter(Qt.Orientation.Horizontal)
        
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
        # 移除单独的title_label样式设置
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['bg']};
            }}
            QWidget#titleBar {{
                background-color: {theme['title_bg']} !important;
            }}
            QLabel#titleLabel {{
                color: #C29500;  /* 固定字体颜色 */
                font-weight: bold;
                background-color: {theme['title_bg']};  /* 继承标题栏背景色 */
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
        "nav_selected": "rgba(218, 237, 244, 1)",
        "accent": "#4a90e2",
        "bg": "rgba(223, 238, 240, 0.35)",
        "text": "#2d3436",
        "title_bg": "#424e54"
    }

    DARK_THEME = {
        "nav_bg": "rgba(45, 52, 54,  0.35)",
        "nav_item": "#c29500",
        "nav_selected": "rgba(74, 74, 74,  0.35)",
        "accent": "#6c5ce7",
        "bg": "rgba(53, 59, 64, 0.35)",
        "text": "#f8f9fa",
        "title_bg": "#01285600"
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
                    time.sleep(0.05)
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

class PositionIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.setMinimumSize(300, 200)
        self.background = None  # 添加背景缓存
        
    def resizeEvent(self, event):
        # 当窗口大小改变时重新创建背景
        self.background = QPixmap(self.size())
        self.background.fill(Qt.GlobalColor.transparent)
        self.drawGrid()
    
    def drawGrid(self):
        # 绘制网格到背景缓存中
        painter = QPainter(self.background)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景网格
        painter.setPen(QColor(100, 100, 100, 50))
        for i in range(0, self.width(), 20):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 20):
            painter.drawLine(0, i, self.width(), i)
        painter.end()
    
    def update_position(self, x, y):
        self.x = x
        self.y = y
        self.update()
    
    def paintEvent(self, event):
        if self.background is None:
            self.resizeEvent(None)
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制缓存的背景
        painter.drawPixmap(0, 0, self.background)
        
        # 只绘制位置指示点
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#c29500"))
        x_pos = self.x * self.width() / 100
        y_pos = self.y * self.height() / 100
        painter.drawEllipse(int(x_pos)-5, int(y_pos)-5, 10, 10)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion样式更好支持透明效果
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

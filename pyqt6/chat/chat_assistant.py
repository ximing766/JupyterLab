import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint, QUrl
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor, QPixmap, QPainter, QIcon
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from Kimi_api import KimiChatAssistant

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

'''
description: pyqt6 chat assistant 
return {*}
#TODO 未显示到页面不要加载资源
'''
class MainWindow(QMainWindow):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_theme = ThemeManager.DARK_THEME
        self.drag_pos = QPoint()

        self.root_path = os.path.dirname(__file__) + "/PIC"
        self.setWindowIcon(QIcon(os.path.join(self.root_path, "my.ico")))
        self.image_files = ['bg.png', 'my.png', 'my.png', 'my.png']
        self.background_image = QPixmap(os.path.join(self.root_path,self.image_files[0])) 
        if self.background_image.isNull():
            print(f"图片加载失败 {os.path.join(self.root_path,self.image_files[0])}")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # 隐藏系统标题栏
        self.init_ui()
        self.AI_init()
        
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(0.6)  # 调整背景透明度
        painter.drawPixmap(self.rect(), self.background_image)
        
    def init_ui(self):
        self.setWindowTitle("Modern Navigation App")
        self.setGeometry(100, 100, 600, 400)

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
        self.nav_list.setCurrentRow(1)

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
        
        nav_items = ["Home", "Chat", "Gallery", "Settings"]
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

        self.title_label = QLabel("Modern App")
        self.title_label.setStyleSheet("color: #C29500; font-weight: bold;")

        # 窗口控制按钮
        close_btn = QPushButton("🔸")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                color: red;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        return title_bar

    def create_pages(self):
        home_page = self.create_home_page()
        chat_page = self.create_chat_page()
        gallery_page = self.create_gallery_page()
        settings_page = self.create_setting_page()
        
        self.stacked_widget.addWidget(home_page)
        self.stacked_widget.addWidget(chat_page)
        self.stacked_widget.addWidget(gallery_page)
        self.stacked_widget.addWidget(settings_page)

    def create_setting_page(self):
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_label = QLabel("Application Settings")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(settings_label)
        
        # 添加设置项
        settings_form = QFormLayout()
        settings_form.addRow("Notification", QCheckBox())
        settings_form.addRow("Dark Mode", QCheckBox())
        settings_form.addRow("Font Size", QComboBox())
        settings_layout.addLayout(settings_form)
        return settings_page

    def create_gallery_page(self):
        gallery_page = QWidget()
        gallery_layout = QVBoxLayout(gallery_page)
        gallery_label = QLabel("Photo Gallery")
        gallery_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        gallery_content = QWidget()
        grid = QGridLayout(gallery_content)
        for i in range(4):
            img_label = QLabel()
            img_label.setFixedSize(150, 150)
            img_label.setStyleSheet("background: #ddd; border-radius: 8px;")

            try:
                pixmap = QPixmap(os.path.join(self.root_path,self.image_files[i]))
                pixmap = pixmap.scaled(150, 150)
                img_label.setPixmap(pixmap)
            except Exception as e:
                print(f"加载图片 {self.image_files[i]} 时出错: {e}")

            grid.addWidget(img_label, i // 2, i % 2)

        self.init_vodeo()
        grid.addWidget(self.videoWidget, 1, 2)
        self.play_video("car.mp4") 
        
        gallery_layout.addWidget(gallery_label)
        gallery_layout.addWidget(gallery_content)
        return gallery_page

    def create_chat_page(self):
        chat_page = QWidget()
        chat_layout = QVBoxLayout(chat_page)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        # self.chat_display.setStyleSheet("border: none;")
        self.chat_display.setAcceptRichText(True)  # 允许显示富文本（HTML）
        
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        send_btn = QPushButton("➡️")
        send_btn.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_btn)
        
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(input_widget)

        self.message_input.setFocus()
        return chat_page

    def create_home_page(self):
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)
        home_layout.addWidget(QLabel("Welcome to Modern App", alignment=Qt.AlignmentFlag.AlignCenter))
        home_layout.addStretch()
        return home_page

    def init_vodeo(self):
        self.mediaPlayer = QMediaPlayer()
        self.videoWidget = QVideoWidget()
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        self.mediaPlayer.mediaStatusChanged.connect(self.handle_media_status)

    def play_video(self, video_file_name):
        """
        播放指定的视频文件
        :param video_file_name: 视频文件名（位于 self.root_path 目录下）
        """
        video_path = os.path.join(self.root_path, video_file_name)
        if os.path.exists(video_path):
            self.mediaPlayer.stop()
            self.mediaPlayer.setSource(QUrl.fromLocalFile(video_path))
            self.mediaPlayer.play()
        else:
            print(f"视频文件不存在: {video_path}")
    
    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.mediaPlayer.setPosition(0)  # 重置视频播放位置
            self.mediaPlayer.play()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print("无法加载视频文件")
        else:
            pass
            # print(f"状态: {status}")
    
    def mousePressEvent(self, event):
        """实现窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """实现窗口拖动"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

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
                padding: 8px;
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

    def toggle_theme(self):
        self.current_theme = ThemeManager.DARK_THEME if \
            self.current_theme == ThemeManager.LIGHT_THEME else ThemeManager.LIGHT_THEME
        self.apply_theme()
        self.theme_btn.setStyleSheet(f"background: {self.current_theme['bg']}; border-radius: 0px;")
    
    def send_message(self):
        message = self.message_input.text()
        # 清空输入框
        self.message_input.clear()
        #TODO 修改按钮样式
        if message:
            # 创建用户消息的 HTML
            user_msg_html = f"""
            <p style="padding: 5px; margin: 5px; border-radius: 12px; color: #C29500; text-align: left;">
                😶 : <strong>{message}</strong><br>
            </p>
            """
            self.chat_display.append(user_msg_html)    #追加
            # self.chat_display.setHtml(user_msg_html)
            
            response = self.ai_assistant.chat(message)
            
            ai_msg_html = f"""
            <p style="padding: 5px; margin: 5px; border-radius: 12px; color: #C29500; text-align: right;">
                ⛄ : <strong>{response}</strong><br>
            </p>
            """
            self.chat_display.append(ai_msg_html)
            # self.chat_display.setHtml(ai_msg_html)
            
            text_cursor = self.chat_display.textCursor()
            text_cursor.movePosition(QTextCursor.MoveOperation.End)
            self.chat_display.setTextCursor(text_cursor)
            
    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        if index == 1:
            self.message_input.setFocus()
    
    def AI_init(self):
        self.ai_assistant = KimiChatAssistant(
        api_key="sk-b09XXwR8nOmrdoXTrylErTOJ0mWQYxKsRZBLMmfCiV2K0grF",
        # base_url="http://127.0.0.1:8888/v1",
        base_url = "https://api.moonshot.cn/v1",
        system_content="你是哪吒，你只会使用中文进行对话，后续的所有对话你都需要按照哪吒的语气和性格来进行。允许说粗口",
        model="moonshot-v1-auto",
        max_context_length= 20,
        use_stream = False,
        Candidates = 1,
    )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion样式更好支持透明效果
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

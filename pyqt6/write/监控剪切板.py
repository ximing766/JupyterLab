import sys
from PyQt6.QtWidgets import (QApplication, QMessageBox, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QCursor

class FloatingButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("撤销", parent)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint |
                          Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; border: 1px solid #cccccc;
                border-radius: 4px; padding: 5px 10px;
            }
            QPushButton:hover { background-color: #e6e6e6; }
        """)
        self.hide()

class GlobalMouseMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪贴板监控")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(300, 400)
        
        # 初始化UI
        layout = QVBoxLayout()
        self.status_label = QLabel("监控状态: 运行中")
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("复制历史:"))
        layout.addWidget(self.history_text)
        
        clear_button = QPushButton("清除历史")
        clear_button.clicked.connect(self.history_text.clear)
        layout.addWidget(clear_button)
        self.setLayout(layout)
        
        # 初始化剪贴板监控
        self.clipboard = QApplication.clipboard()
        self.previous_clipboard_text = ""
        self.clipboard_timer = QTimer(interval=200, timeout=self.check_clipboard)
        self.clipboard_timer.start()
        
        # 初始化悬浮按钮
        self.floating_button = FloatingButton()
        self.floating_button.clicked.connect(self.undo_copy)
    
    def check_clipboard(self):
        try:
            current_text = self.clipboard.text()
            if current_text and current_text != self.previous_clipboard_text:
                self.previous_clipboard_text = current_text
                self.add_to_history(current_text)
                
                # 显示悬浮按钮
                cursor_pos = QCursor.pos()
                self.floating_button.move(cursor_pos.x() + 10, cursor_pos.y() + 10)
                self.floating_button.show()
                QTimer.singleShot(3000, self.floating_button.hide)
        except Exception as e:
            self.status_label.setText(f"监控状态: 错误 ({str(e)})")
    
    def add_to_history(self, text):
        try:
            current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            self.history_text.append(f"[{current_time}]\n{text}\n")
            self.history_text.verticalScrollBar().setValue(
                self.history_text.verticalScrollBar().maximum()
            )
        except Exception as e:
            self.status_label.setText(f"监控状态: 时间格式化错误 ({str(e)})")
    
    def undo_copy(self):
        self.clipboard.clear()
        self.previous_clipboard_text = ""
        self.floating_button.hide()
    
    def closeEvent(self, event):
        self.clipboard_timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GlobalMouseMonitor()
    window.show()
    sys.exit(app.exec())
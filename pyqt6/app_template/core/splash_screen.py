# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from qfluentwidgets import (Theme, setTheme, PushButton, LineEdit, ComboBox, TableWidget,ToolButton,
                           BodyLabel, ProgressBar)
import os
import sys

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window

class SplashScreen(Window):
    finished = pyqtSignal()
    def __init__(self, app_name="Application", logo_path=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.logo_path = logo_path
        self.progress = 0
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the splash screen UI"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(400, 300)
        
        # Create a central widget with background
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        
        # Create layout for central widget
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo label
        self.logo_label = BodyLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo()
        
        # App name label
        self.name_label = BodyLabel(self.app_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.name_label.setFont(font)
        
        # Status label
        self.status_label = BodyLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        # Add widgets to layout
        layout.addWidget(self.logo_label)
        layout.addWidget(self.name_label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        
        # Set central widget as main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.central_widget)
        
        # Set background color and styling for the central widget
        self.central_widget.setStyleSheet("""
            QWidget#centralWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a7dbdf, stop:1 #a075ca);
            }
        """)

        self.center_window()
        
    def load_logo(self):
        """Load and set the logo image"""
        if self.logo_path and os.path.exists(self.logo_path):
            pixmap = QPixmap(self.logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
            else:
                self.logo_label.setText("📱")
                font = QFont()
                font.setPointSize(48)
                self.logo_label.setFont(font)
        else:
            self.logo_label.setText("📱")
            font = QFont()
            font.setPointSize(48)
            self.logo_label.setFont(font)
    
    def center_window(self):
        """Center the splash screen on the screen"""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def show_splash(self):
        """Show the splash screen"""
        self.show()
    
    def start_loading(self, duration=3000):
        """Start the loading animation"""
        self.progress = 0
        self.progress_bar.setValue(0)
        
        # Simple progress timer
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(duration // 100)  # 100 steps
    
    def update_progress(self):
        """Update progress bar"""
        self.progress += 1
        if self.progress >= 100:
            self.progress = 100
            self.progress_timer.stop()
            self.status_label.setText("Ready!")
            # Close splash screen after progress is complete with a small delay
            QTimer.singleShot(500, self.close_splash)
        
        self.progress_bar.setValue(self.progress)
        
        # Update status text
        if self.progress < 30:
            self.status_label.setText("Loading...")
        elif self.progress < 70:
            self.status_label.setText("Initializing...")
        elif self.progress < 95:
            self.status_label.setText("Almost ready...")
        else:
            self.status_label.setText("Ready!")
    
    def set_status(self, text):
        """Set custom status text"""
        self.status_label.setText(text)
    
    def set_progress(self, value):
        """Set custom progress value (0-100)"""
        self.progress = max(0, min(100, value))
        self.progress_bar.setValue(self.progress)
    
    def close_splash(self):
        """Close the splash screen"""
        self.finished.emit()
        self.close()
    
    def closeEvent(self, event):
        """Handle close event"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        self.finished.emit()
        super().closeEvent(event)


def show_splash_screen(app_name="Application", logo_path=None, duration=3000):
    """Simple convenience function to show splash screen"""
    splash = SplashScreen(app_name, logo_path)
    splash.show_splash()
    splash.start_loading(duration)
    return splash

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = show_splash_screen("Test App", "assets/logo.ico")
    sys.exit(app.exec())
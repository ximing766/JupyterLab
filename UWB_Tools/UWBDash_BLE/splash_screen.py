# -*- coding: utf-8 -*-
"""
Splash Screen Module for UWB Dashboard

This module contains the SplashScreen class that displays a startup animation
with logo and loading progress for the UWB Dashboard application.
"""

import random
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QApplication
from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QPen
from qfluentwidgets import CardWidget, BodyLabel, ProgressBar, SubtitleLabel, CaptionLabel


class SplashScreen(CardWidget):
    """Startup splash screen with logo and loading animation"""
    
    # Signal emitted when splash screen is finished
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set window size and center it
        self.setFixedSize(400, 350)
        self.center_on_screen()
        
        # Load logo
        self.logo_path = Path(__file__).parent / "logo.png"
        self.logo_pixmap = QPixmap(str(self.logo_path)) if self.logo_path.exists() else None
        
        # Animation properties
        self.opacity = 0.0
        self.progress = 0
        self.fade_in_complete = False
        self.is_closing = False
        
        # Setup timers for animations - Accelerated by 1/3
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.fade_in_animation)
        self.fade_timer.start(13)  # Faster animation: ~77 FPS for smoother and quicker fade
        
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
        # Setup UI elements
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the splash screen UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo container
        logo_container = CardWidget()
        logo_container.setFixedHeight(150)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo label
        self.logo_label = BodyLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.logo_pixmap:
            scaled_logo = self.logo_pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        else:
            self.logo_label.setText("UWB")
            self.logo_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #00D4FF;")
        
        logo_layout.addWidget(self.logo_label)
        layout.addWidget(logo_container)
        
        # App title
        self.title_label = SubtitleLabel("UWB Dashboard")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #FFFFFF;
            margin: 10px 0;
        """)
        layout.addWidget(self.title_label)
        
        # Loading text
        self.loading_label = CaptionLabel("正在启动...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            font-size: 14px;
            color: #CCCCCC;
            margin: 5px 0;
        """)
        layout.addWidget(self.loading_label)
        
        # Progress bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        # qfluentwidgets ProgressBar has built-in styling, remove custom stylesheet
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
    def center_on_screen(self):
        """Center the splash screen on the screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def paintEvent(self, event):
        """Custom paint event for background and effects"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set opacity
        painter.setOpacity(self.opacity)
        
        # Draw background with gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(30, 30, 40, 240))
        gradient.setColorAt(0.5, QColor(20, 25, 35, 250))
        gradient.setColorAt(1, QColor(15, 20, 30, 240))
        
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(100, 150, 200, 100), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 15, 15)
        
        # Draw subtle border glow
        glow_pen = QPen(QColor(0, 212, 255, int(50 * self.opacity)), 3)
        painter.setPen(glow_pen)
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 13, 13)
        
    def fade_in_animation(self):
        """Handle fade-in animation"""
        if self.opacity < 1.0:
            self.opacity += 0.075  # Faster fade-in: increased from 0.05 to 0.075
            self.update()
        else:
            self.fade_timer.stop()
            self.fade_in_complete = True
            # Start progress animation after fade-in is complete
            self.progress_timer.start(33)  # Faster progress updates: reduced from 50ms to 33ms
            
    def update_progress(self):
        """Update loading progress"""
        if self.progress < 100 and not self.is_closing:
            # Simulate loading with faster variable speed
            if self.progress < 30:
                self.progress += random.randint(3, 6)
            elif self.progress < 70:
                self.progress += random.randint(2, 4)
            else:
                self.progress += random.randint(2, 3)
                
            self.progress = min(self.progress, 100)
            self.progress_bar.setValue(self.progress)
            
            # Update loading text based on progress
            if self.progress < 30:
                self.loading_label.setText("正在初始化...")
            elif self.progress < 60:
                self.loading_label.setText("正在加载组件...")
            elif self.progress < 90:
                self.loading_label.setText("正在准备界面...")
            else:
                self.loading_label.setText("即将完成...")
        else:
            self.progress_timer.stop()
            if not self.is_closing:
                self.is_closing = True
                # Reduced delay before closing: from 500ms to 300ms
                QTimer.singleShot(300, self.fade_out_and_close)
            
    def fade_out_and_close(self):
        """Handle fade-out animation and close"""
        if not hasattr(self, 'fade_out_timer'):
            self.fade_out_timer = QTimer()
            self.fade_out_timer.timeout.connect(self.fade_out_step)
            self.fade_out_timer.start(10)  # Faster fade-out: reduced from 15ms to 10ms
    
    def fade_out_step(self):
        """Single step of fade-out animation"""
        if self.opacity > 0:
            self.opacity -= 0.1  # Faster fade-out: increased from 0.08 to 0.1
            self.update()
        else:
            self.fade_out_timer.stop()
            # Emit finished signal before closing
            self.finished.emit()
            # Reduced final delay: from 100ms to 50ms
            QTimer.singleShot(50, self.close)
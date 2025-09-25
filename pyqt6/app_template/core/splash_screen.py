from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPixmap, QFont
from qfluentwidgets import isDarkTheme
import os


class SplashScreen(QWidget):
    """Generic splash screen for PyQt6 applications using qfluentwidgets"""
    
    finished = pyqtSignal()
    
    def __init__(self, app_name="Application", logo_path=None, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.logo_path = logo_path
        self.progress = 0
        self.startup_text = "Starting..."
        
        self.init_ui()
        self.setup_animation()
        
    def init_ui(self):
        """Initialize the splash screen UI"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 300)
        
        # Center the window
        self.center_window()
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo label
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_logo()
        
        # App name label
        self.name_label = QLabel(self.app_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.name_label.setFont(font)
        
        # Status label
        self.status_label = QLabel(self.startup_text)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        # Add widgets to layout
        layout.addWidget(self.logo_label)
        layout.addWidget(self.name_label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Apply theme-based styling
        self.apply_theme_style()
        
    def load_logo(self):
        """Load and set the logo image"""
        if self.logo_path and os.path.exists(self.logo_path):
            pixmap = QPixmap(self.logo_path)
            if not pixmap.isNull():
                # Scale the logo to fit
                scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
            else:
                # Default logo placeholder
                self.logo_label.setText("📱")
                font = QFont()
                font.setPointSize(48)
                self.logo_label.setFont(font)
        else:
            # Default logo placeholder
            self.logo_label.setText("📱")
            font = QFont()
            font.setPointSize(48)
            self.logo_label.setFont(font)
    
    def apply_theme_style(self):
        """Apply theme-based styling"""
        if isDarkTheme():
            # Dark theme colors
            text_color = "#FFFFFF"
            bg_start = "#2D2D30"
            bg_end = "#1E1E1E"
            progress_color = "#0078D4"
        else:
            # Light theme colors
            text_color = "#000000"
            bg_start = "#F0F0F0"
            bg_end = "#FFFFFF"
            progress_color = "#0078D4"
        
        # Set text colors
        self.name_label.setStyleSheet(f"color: {text_color};")
        self.status_label.setStyleSheet(f"color: {text_color};")
        
        # Set progress bar style
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {progress_color};
                border-radius: 5px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QProgressBar::chunk {{
                background-color: {progress_color};
                border-radius: 3px;
            }}
        """)
        
        # Store colors for painting
        self.bg_start_color = QColor(bg_start)
        self.bg_end_color = QColor(bg_end)
    
    def center_window(self):
        """Center the splash screen on the screen"""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def setup_animation(self):
        """Setup fade in/out animations"""
        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_animation.finished.connect(self.close)
        
        # Progress timer
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
    def paintEvent(self, event):
        """Custom paint event for gradient background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.bg_start_color)
        gradient.setColorAt(1, self.bg_end_color)
        
        # Draw rounded rectangle background
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
    
    def show_splash(self):
        """Show the splash screen with fade in animation"""
        self.show()
        self.fade_in_animation.start()
    
    def start_loading(self, duration=3000, steps=50):
        """Start the loading animation"""
        self.progress = 0
        self.progress_bar.setValue(0)
        
        # Calculate timer interval
        interval = duration // steps
        self.progress_step = 100 // steps
        
        self.progress_timer.start(interval)
        
        # Auto close after duration
        QTimer.singleShot(duration + 500, self.close_splash)
    
    def update_progress(self):
        """Update progress bar and status text"""
        self.progress += self.progress_step
        if self.progress >= 100:
            self.progress = 100
            self.progress_timer.stop()
            self.status_label.setText("Ready!")
        
        self.progress_bar.setValue(self.progress)
        
        # Update status text based on progress
        if self.progress < 30:
            self.status_label.setText("Initializing...")
        elif self.progress < 60:
            self.status_label.setText("Loading components...")
        elif self.progress < 90:
            self.status_label.setText("Finalizing...")
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
        """Close the splash screen with fade out animation"""
        self.fade_out_animation.start()
        self.finished.emit()
    
    def closeEvent(self, event):
        """Handle close event"""
        self.finished.emit()
        super().closeEvent(event)


# Example usage function
def show_splash_screen(app_name="Application", logo_path=None, duration=3000):
    """Convenience function to show splash screen"""
    splash = SplashScreen(app_name, logo_path)
    splash.show_splash()
    splash.start_loading(duration)
    return splash
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generic PyQt6 Application Template
A customizable application template using qfluentwidgets

Usage:
    python main.py

Features:
    - Splash screen with loading animation
    - Theme management (light/dark/auto)
    - Background image support
    - Navigation interface
    - Extensible page system
    - Settings management
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.main_window import MainWindow


def main():
    """Main application entry point"""
    # Enable high DPI scaling (PyQt6 compatible)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Generic App Template")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Your Organization")
    
    # Set application icon (optional)
    # app.setWindowIcon(QIcon("assets/icon.png"))
    
    # Create main window
    # You can customize the app name and logo path here
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = None
    
    window = MainWindow(
        app_name="Generic App Template",
        logo_path=logo_path
    )
    
    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
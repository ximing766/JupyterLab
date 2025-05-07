class ThemeManager:
    DARK_THEME = {
        "nav_bg": "rgba(45, 52, 54,  0.35)",
        "nav_item": "#c29500",
        "nav_selected": "rgba(74, 74, 74,  0.35)",
        "accent": "#6c5ce7",
        "bg": "rgba(53, 59, 64, 0.35)",
        "text": "#f8f9fa",
        "title_bg": "#01285600"
    }

    @staticmethod
    def get_stylesheet(theme):
        return f"""
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
                background   : rgba(90, 110, 140, 0.33);
                color        : {theme['text']};
                border       : 1px solid rgba(90, 110, 140, 0.18);
                padding      : 4px 12px;
                border-radius: 8px;
                font-size    : 13px;
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
        """
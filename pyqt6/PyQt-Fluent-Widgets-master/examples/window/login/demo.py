import sys
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QWidget, QSpacerItem, QSizePolicy
from qfluentwidgets import (setThemeColor, setTheme, Theme, SplitTitleBar, isDarkTheme,
                            BodyLabel, CheckBox, HyperlinkButton, LineEdit, PrimaryPushButton, InfoBar, InfoBarPosition)

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class PureCodeLoginWindow(Window):
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.setupWindow()
        
    def setupUI(self):
        """Create UI elements programmatically"""
        # Main horizontal layout
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        
        # Background image label (left side) - using background image
        self.label = QLabel()
        self.label.setText("")
        # Set background image from resource folder
        self.label.setStyleSheet("""
            QLabel {
                background-image: url(resource/images/background.jpg);
                background-repeat: no-repeat;
                background-position: center;
            }
        """)
        self.label.setScaledContents(True)
        self.horizontalLayout.addWidget(self.label)
        
        # Right panel widget
        self.widget = QWidget()
        # sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QSize(360, 0))
        self.widget.setMaximumSize(QSize(360, 16777215))
        self.widget.setStyleSheet("QLabel{ font: 13px 'Microsoft YaHei' }")
        
        # Right panel layout
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setContentsMargins(20, 20, 20, 20)
        self.verticalLayout_2.setSpacing(9)
        
        # Top spacer
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        
        # Logo label - using logo image from resource folder
        self.label_2 = QLabel()
        self.label_2.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QSize(100, 100))
        self.label_2.setMaximumSize(QSize(100, 100))
        # Set logo image from resource folder
        logo_pixmap = QPixmap("resource/images/logo.png")
        self.label_2.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_2.setStyleSheet("""
            QLabel {
                border-radius: 50px;
            }
        """)
        self.label_2.setScaledContents(True)
        self.verticalLayout_2.addWidget(self.label_2, 0, Qt.AlignHCenter)
        
        # Small spacer
        spacerItem1 = QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem1)
        
        # Username label
        self.label_5 = BodyLabel(self.widget)
        self.verticalLayout_2.addWidget(self.label_5)
        
        # Username input
        self.lineEdit_3 = LineEdit(self.widget)
        self.lineEdit_3.setClearButtonEnabled(True)
        self.verticalLayout_2.addWidget(self.lineEdit_3)
        
        # Password label
        self.label_6 = BodyLabel(self.widget)
        self.verticalLayout_2.addWidget(self.label_6)
        
        # Password input
        self.lineEdit_4 = LineEdit(self.widget)
        self.lineEdit_4.setEchoMode(LineEdit.Password)
        self.lineEdit_4.setClearButtonEnabled(True)
        self.verticalLayout_2.addWidget(self.lineEdit_4)
        
        # Small spacer
        spacerItem2 = QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem2)
        
        # Remember password checkbox
        self.checkBox = CheckBox(self.widget)
        self.checkBox.setChecked(True)
        self.verticalLayout_2.addWidget(self.checkBox)
        
        # Small spacer
        spacerItem3 = QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem3)
        
        # Login button
        self.pushButton = PrimaryPushButton(self.widget)
        self.pushButton.clicked.connect(self.handleLogin)  # Connect login function
        self.verticalLayout_2.addWidget(self.pushButton)
        
        # Small spacer
        spacerItem4 = QSpacerItem(20, 6, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem4)
        
        # Forgot password link
        self.pushButton_2 = HyperlinkButton(self.widget)
        self.verticalLayout_2.addWidget(self.pushButton_2)
        
        # Bottom spacer
        spacerItem5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem5)
        
        # Add right panel to main layout
        self.horizontalLayout.addWidget(self.widget)
        
        # Set text content
        self.retranslateUi()
        
    def retranslateUi(self):
        """Set text content for UI elements"""
        self.setWindowTitle("Form")
        self.label_5.setText("用户名")
        self.lineEdit_3.setPlaceholderText("example@example.com")
        self.label_6.setText("密码")
        self.lineEdit_4.setPlaceholderText("••••••••••••")
        self.checkBox.setText("记住密码")
        self.pushButton.setText("登录")
        self.pushButton_2.setText("找回密码")
        
    def setupWindow(self):
        """Setup window properties and effects"""
        setThemeColor('#28afe9')
        
        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()
        
        self.label.setScaledContents(False)
        self.setWindowTitle('PyQt-Fluent-Widget')
        
        self.setFixedSize(1000, 650)  # Fixed size
        
        # Title bar styling
        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI';
                padding: 0 4px;
                color: white
            }
        """)
        
        # Center window
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
    
    def handleLogin(self):
        """Handle login button click"""
        InfoBar.success(
            title='登录成功',
            content=f'欢迎 {username}！',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def resizeEvent(self, e):
        """Handle window resize event"""
        super().resizeEvent(e)
        # Since we're using gradient background, no need to handle image resizing
        
    def systemTitleBarRect(self, size):
        """Returns the system title bar rect, only works for macOS"""
        return QRect(size.width() - 75, 0, 75, size.height())


if __name__ == '__main__':
    # Enable DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    w = PureCodeLoginWindow()
    w.show()
    app.exec_()
import sys
import os
import qfluentwidgets
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QStackedWidget, QLabel, QFrame, QScrollArea, QSizePolicy)

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, NavigationWidget, qrouter,
    SubtitleLabel, setFont, SplashScreen, FluentIcon as FIF,
    MSFluentWindow, NavigationAvatarWidget, isDarkTheme, setTheme, Theme,
    PrimaryPushButton, PushButton, ToggleButton, RadioButton, CheckBox,
    ComboBox, LineEdit, TextEdit, SpinBox, DoubleSpinBox, Slider,
    SwitchButton, ProgressBar, ProgressRing, IndeterminateProgressRing,
    CardWidget, SimpleCardWidget, HeaderCardWidget, ElevatedCardWidget,
    ScrollArea, FluentStyleSheet, SettingCardGroup, SwitchSettingCard,
    FolderListSettingCard, OptionsSettingCard, PushSettingCard,
    HyperlinkCard, PrimaryPushSettingCard, ColorSettingCard,
    CustomColorSettingCard, RangeSettingCard, ComboBoxSettingCard,
    ExpandLayout, InfoBar, InfoBarPosition, StateToolTip, Flyout, FlyoutAnimationType,
    setTheme, Theme, setThemeColor, themeColor, qconfig
)


class HomeInterface(ScrollArea):
    """ Home interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('homeInterface')
        
        # Create main widget
        self.view = QWidget()
        self.vBoxLayout = QVBoxLayout(self.view)
        print(qfluentwidgets.__version__)   # 应 ≥ 1.7.0
        
        # Title
        self.titleLabel = SubtitleLabel('🏠 欢迎使用 Fluent Gallery', self)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setFont(self.titleLabel, 24)
        
        # Description
        self.descLabel = QLabel('这是一个基于 PyQt-Fluent-Widgets 构建的现代化应用模板\n'
                               '展示了各种精美的 Fluent Design 组件和布局', self)
        self.descLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.descLabel.setStyleSheet('color: rgb(96, 96, 96); font-size: 14px;')
        
        # Feature cards
        self.createFeatureCards()
        
        # Layout setup
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.descLabel)
        self.vBoxLayout.addSpacing(30)
        self.vBoxLayout.addLayout(self.cardLayout)
        self.vBoxLayout.addStretch(1)
        
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setStyleSheet('QScrollArea{background: transparent; border: none}')
        
    def createFeatureCards(self):
        """ Create feature cards with responsive layout """
        # Create responsive grid layout
        self.cardLayout = QGridLayout()
        self.cardLayout.setSpacing(20)
        self.cardLayout.setContentsMargins(20, 20, 20, 20)
        
        # Simplified card data - only keep one card
        cards_data = [
            {
                'title': '🎨 Fluent Design',
                'content': '现代化界面设计\n流畅的用户体验',
                'color': '#0078D4'
            }
        ]
        
        for i, card_data in enumerate(cards_data):
            card = self.createCard(card_data)
            # Use responsive positioning
            row = i // 2
            col = i % 2
            self.cardLayout.addWidget(card, row, col)
            
        # Add stretch to center the cards
        self.cardLayout.setRowStretch(1, 1)
        self.cardLayout.setColumnStretch(2, 1)
            
    def createCard(self, data):
        """ Create a responsive feature card """
        card = ElevatedCardWidget()
        card.setMinimumSize(200, 150)
        card.setMaximumSize(400, 200)
        
        layout = QVBoxLayout(card)
        
        # Title with responsive font size
        title = QLabel(data['title'])
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f'font-size: 16px; font-weight: bold; color: {data["color"]};')
        
        # Content with responsive font size
        content = QLabel(data['content'])
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.setStyleSheet('color: rgb(96, 96, 96); font-size: 12px; line-height: 1.5;')
        content.setWordWrap(True)
        
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(content)
        layout.addStretch(1)
        
        # Set size policy for responsive behavior
        from PyQt6.QtWidgets import QSizePolicy
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        return card


class ComponentsInterface(ScrollArea):
    """ Components showcase interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('componentsInterface')
        
        # Create main widget
        self.view = QWidget()
        self.vBoxLayout = QVBoxLayout(self.view)
        
        # Title
        self.titleLabel = SubtitleLabel('🧩 核心组件', self)
        setFont(self.titleLabel, 24)
        
        # Create only essential component group
        self.createEssentialGroup()
        
        # Layout setup
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.essentialGroup)
        self.vBoxLayout.addStretch(1)
        
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setStyleSheet('QScrollArea{background: transparent; border: none}')
        
    def createEssentialGroup(self):
        """ Create essential components group """
        self.essentialGroup = SettingCardGroup('核心组件展示', self.view)
        
        # Essential components layout
        essentialLayout = QVBoxLayout()
        
        # Button section
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(QLabel('按钮:'))
        primaryBtn = PrimaryPushButton('主要按钮', self)
        primaryBtn.clicked.connect(lambda: self.showMessage('主要按钮被点击!'))
        buttonLayout.addWidget(primaryBtn)
        buttonLayout.addStretch(1)
        
        # Input section
        inputLayout = QHBoxLayout()
        inputLayout.addWidget(QLabel('输入:'))
        lineEdit = LineEdit(self)
        lineEdit.setPlaceholderText('输入文本...')
        inputLayout.addWidget(lineEdit)
        inputLayout.addStretch(1)
        
        essentialLayout.addLayout(buttonLayout)
        essentialLayout.addSpacing(10)
        essentialLayout.addLayout(inputLayout)
        
        # Add to group
        essentialWidget = QWidget()
        essentialWidget.setLayout(essentialLayout)
        self.essentialGroup.addSettingCard(essentialWidget)
        
    def showMessage(self, message):
        """ Show info bar message """
        InfoBar.success(
            title='操作成功',
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )


class SettingsInterface(ScrollArea):
    """ Settings interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('settingsInterface')
        
        # Create main widget
        self.view = QWidget()
        self.vBoxLayout = QVBoxLayout(self.view)
        
        # Title
        self.titleLabel = SubtitleLabel('⚙️ 应用设置', self)
        setFont(self.titleLabel, 24)
        
        # Create simplified setting groups
        self.createAppearanceGroup()
        self.createAboutGroup()
        
        # Layout setup
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.appearanceGroup)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.aboutGroup)
        self.vBoxLayout.addStretch(1)
        
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setStyleSheet('QScrollArea{background: transparent; border: none}')
        
    def createAppearanceGroup(self):
        """ Create appearance settings group """
        self.appearanceGroup = SettingCardGroup('外观设置', self.view)
        
        # Theme setting using PushSettingCard with ComboBox
        self.themeCard = PushSettingCard(
            text='浅色',
            icon=FIF.BRUSH,
            title='应用主题',
            content='选择应用的主题模式'
        )
        self.themeCard.clicked.connect(self.onThemeCardClicked)
        
        # Color setting using PushSettingCard
        self.colorCard = PushSettingCard(
            text='Windows 蓝',
            icon=FIF.PALETTE,
            title='主题色',
            content='当前主题色: Windows 蓝'
        )
        self.colorCard.clicked.connect(self.onColorChanged)
        
        self.appearanceGroup.addSettingCard(self.themeCard)
        self.appearanceGroup.addSettingCard(self.colorCard)
    def createAboutGroup(self):
        """ Create about group """
        self.aboutGroup = SettingCardGroup('关于', self.view)
        
        # Version info
        self.versionCard = PushSettingCard(
            text='检查更新',
            icon=FIF.UPDATE,
            title='版本信息',
            content='Fluent Gallery v1.0.0'
        )
        self.versionCard.clicked.connect(self.checkUpdate)
        
        # Help card
        self.helpCard = HyperlinkCard(
            url='https://github.com/zhiyiYo/PyQt-Fluent-Widgets',
            text='访问项目主页',
            icon=FIF.HELP,
            title='帮助支持',
            content='获取更多帮助和支持信息'
        )
        
        self.aboutGroup.addSettingCard(self.versionCard)
        self.aboutGroup.addSettingCard(self.helpCard)
        
    def onThemeCardClicked(self):
        """ Theme card clicked slot """
        # Cycle through themes
        current_theme = 'dark' if isDarkTheme() else 'light'
        if current_theme == 'light':
            setTheme(Theme.DARK)
            self.themeCard.setContent('深色主题已启用')
            theme_name = '深色'
        else:
            setTheme(Theme.LIGHT)
            self.themeCard.setContent('浅色主题已启用')
            theme_name = '浅色'
            
        InfoBar.success(
            title='主题已切换',
            content=f'已切换到{theme_name}主题',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def onColorChanged(self):
        """ Color changed slot """
        # Predefined theme colors
        colors = [
            ('#0078D4', 'Windows 蓝'),
            ('#107C10', '自然绿'),
            ('#D13438', '活力红'),
            ('#FF8C00', '橙色'),
            ('#7B68EE', '紫色'),
            ('#20B2AA', '青色'),
            ('#FF1493', '粉色'),
            ('#32CD32', '柠檬绿')
        ]
        
        # Get current theme color
        current_color = themeColor()
        current_index = 0
        
        # Find current color index
        for i, (color, _) in enumerate(colors):
            if current_color.name().upper() == color:
                current_index = i
                break
        
        # Switch to next color
        next_index = (current_index + 1) % len(colors)
        next_color, color_name = colors[next_index]
        
        # Set new theme color
        setThemeColor(next_color)
        
        # Update card text
        self.colorCard.setContent(f'当前主题色: {color_name}')
        
        InfoBar.success(
            title='主题色已更改',
            content=f'已切换到{color_name}主题色',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def checkUpdate(self):
        """ Check for updates """
        InfoBar.info(
            title='检查更新',
            content='当前已是最新版本',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )


class MainWindow(MSFluentWindow):
    """ Main window """

    def __init__(self):
        super().__init__()
        self.initWindow()
        self.initNavigation()
        self.setMinimumSize(800, 600)  # Set minimum size for better responsive behavior
        
    def initWindow(self):
        """ Initialize window """
        self.resize(1000, 700)
        self.setWindowTitle('Fluent Gallery - 现代化应用模板')
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        
        # Center window
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        
    def initNavigation(self):
        """ Initialize navigation """
        # Create interfaces
        self.homeInterface = HomeInterface(self)
        self.componentsInterface = ComponentsInterface(self)
        self.settingsInterface = SettingsInterface(self)
        
        # Add interfaces to navigation
        self.addSubInterface(self.homeInterface, FIF.HOME, '首页')
        self.addSubInterface(self.componentsInterface, FIF.APPLICATION, '组件')
        
        # Add settings with correct parameter order
        self.addSubInterface(self.settingsInterface, FIF.SETTING, '设置', position=NavigationItemPosition.BOTTOM)
        
        # Set default interface
        self.stackedWidget.setCurrentWidget(self.homeInterface)
        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())


def main():
    """ Main function """
    # Enable high DPI scaling for PyQt6
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # Set theme and colors for better readability
    setTheme(Theme.LIGHT)  # Force light theme for better text visibility
    setThemeColor('#0078d4')  # Microsoft blue for better contrast
    
    # Apply custom stylesheet to ensure light background
    app.setStyleSheet("""
        QWidget {
            background-color: #f5f5f5;
            color: #333333;
        }
        QScrollArea {
            background-color: #ffffff;
            border: none;
        }
        QLabel {
            color: #333333;
            background-color: transparent;
        }
        QFrame {
            background-color: #ffffff;
            color: #333333;
        }
    """)
    
    # Create main window
    window = MainWindow()
    
    # Create splash screen
    splashScreen = SplashScreen(QIcon(':/qfluentwidgets/images/logo.png'), window)
    splashScreen.setIconSize(QSize(106, 106))
    splashScreen.raise_()
    
    # Show splash screen
    splashScreen.show()
    app.processEvents()
    
    # Simulate loading time
    import time
    time.sleep(1.5)
    
    # Show main window and close splash screen
    window.show()
    splashScreen.finish()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
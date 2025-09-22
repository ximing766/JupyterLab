# Generic PyQt6 Application Template

一个基于 PyQt6 和 qfluentwidgets 的通用应用程序模板，提供现代化的用户界面和可扩展的架构。

## 特性

- 🚀 **启动动画**: 优雅的启动画面，支持自定义logo和应用名称
- 🎨 **主题管理**: 支持亮色/暗色/自动主题切换
- 🖼️ **背景图片**: 可自定义背景图片，支持多种图片格式
- 🧭 **导航界面**: 基于 qfluentwidgets 的现代导航栏
- 📄 **页面系统**: 可扩展的页面管理系统
- ⚙️ **设置管理**: 完整的配置管理和持久化
- 🔧 **易于扩展**: 模块化设计，方便添加新功能

## 项目结构

```
app_template/
├── assets/                 # 资源文件
│   └── PIC/               # 背景图片文件夹
├── config/                # 配置管理
│   ├── config_manager.py  # 配置管理器
│   └── theme_manager.py   # 主题管理器
├── core/                  # 核心组件
│   ├── main_window.py     # 主窗口
│   └── splash_screen.py   # 启动画面
├── pages/                 # 页面组件
│   ├── __init__.py
│   ├── base_page.py       # 基础页面类
│   ├── page_manager.py    # 页面管理器
│   ├── placeholder_page.py # 占位页面
│   └── settings_page.py   # 设置页面
├── main.py               # 应用入口
└── README.md            # 说明文档
```

## 快速开始

### 环境要求

- Python 3.8+
- PyQt6
- qfluentwidgets

### 安装依赖

```bash
pip install PyQt6 qfluentwidgets
```

### 运行应用

```bash
python main.py
```

## 自定义应用

### 1. 修改应用信息

在 `main.py` 中修改应用名称、版本等信息：

```python
window = MainWindow(
    app_name="你的应用名称",
    logo_path="path/to/your/logo.png"
)
```

### 2. 添加新页面

创建新的页面类，继承自 `BasePage`：

```python
from pages.base_page import BasePage
from PyQt6.QtWidgets import QLabel
from qfluentwidgets import FluentIcon

class MyCustomPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("我的页面", FluentIcon.HOME, parent)
    
    def init_content(self):
        """初始化页面内容"""
        label = QLabel("这是我的自定义页面")
        self.content_layout.addWidget(label)
    
    def on_page_activated(self):
        """页面激活时调用"""
        print("我的页面被激活了")
```

然后在主窗口中注册页面：

```python
# 在 MainWindow 的 create_default_pages 方法中添加
self.page_manager.register_page(
    "my_page",
    "我的页面",
    FluentIcon.HOME,
    MyCustomPage
)
```

### 3. 自定义主题

在设置页面中可以添加自定义主题，或者直接修改 `theme_manager.py`：

```python
# 添加自定义主题
self.theme_manager.add_custom_theme("my_theme", {
    "primary_color": "#FF6B6B",
    "background_color": "#F8F9FA",
    "text_color": "#2C3E50"
})
```

### 4. 添加背景图片

将图片文件放入 `assets/PIC/` 文件夹，应用会自动检测并在设置中提供选择。

## 配置文件

应用会在用户目录下创建配置文件：
- Windows: `%APPDATA%/YourApp/config.json`
- macOS: `~/Library/Application Support/YourApp/config.json`
- Linux: `~/.config/YourApp/config.json`

配置文件包含：
- 主题设置
- 背景图片设置
- 窗口大小和位置
- 其他用户偏好设置

## API 参考

### MainWindow

主窗口类，应用的核心容器。

```python
class MainWindow(QMainWindow):
    def __init__(self, app_name="Application", logo_path=None, parent=None)
```

**参数:**
- `app_name`: 应用名称
- `logo_path`: logo文件路径
- `parent`: 父窗口

### BasePage

所有页面的基类。

```python
class BasePage(QWidget):
    def __init__(self, title, icon, parent=None)
```

**方法:**
- `init_content()`: 初始化页面内容（需要重写）
- `on_page_activated()`: 页面激活时调用
- `on_page_deactivated()`: 页面停用时调用
- `save_state()`: 保存页面状态
- `restore_state()`: 恢复页面状态

### PageManager

页面管理器，负责页面的注册和管理。

```python
class PageManager:
    def register_page(self, page_id, title, icon, page_class, **kwargs)
    def get_page(self, page_id)
    def set_page_enabled(self, page_id, enabled)
    def set_page_visible(self, page_id, visible)
```

## 扩展示例

### 添加数据库支持

```python
# 在 config/ 目录下创建 database.py
import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        # 初始化数据库表
        pass
```

### 添加网络功能

```python
# 在 core/ 目录下创建 network.py
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl, pyqtSignal, QObject

class NetworkManager(QObject):
    data_received = pyqtSignal(bytes)
    
    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
```

## 常见问题

### Q: 如何修改启动画面的持续时间？

A: 在 `MainWindow` 的 `show_splash_screen` 方法中修改 `duration` 参数：

```python
self.splash_screen.start_loading(duration=3000)  # 3秒
```

### Q: 如何禁用某个页面？

A: 使用 `PageManager` 的方法：

```python
self.page_manager.set_page_enabled("page_id", False)
```

### Q: 如何添加自定义图标？

A: 使用 qfluentwidgets 提供的图标或自定义图标：

```python
from qfluentwidgets import FluentIcon
# 或者
from PyQt6.QtGui import QIcon
custom_icon = QIcon("path/to/icon.png")
```

## 许可证

本项目基于 MIT 许可证开源。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个模板！

## 更新日志

### v1.0.0
- 初始版本发布
- 基础功能实现
- 启动动画
- 主题管理
- 页面系统
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
│   ├── example_page.py    # 示例页面
│   ├── page_manager.py    # 页面管理器
│   └── settings_page.py   # 设置页面
├── main.py               # 应用入口
└── README.md            # 说明文档
```


## SDK 使用指南

### 1. 创建自定义应用

#### 基本应用创建

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt6.QtWidgets import QApplication
from core.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow(
        app_name="我的应用",
        logo_path="path/to/logo.png"  # 可选
    )
    
    # 显示窗口
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

### 2. 页面创建与管理

#### 创建自定义页面

继承 `BasePage` 类来创建自定义页面：

```python
from pages.base_page import BasePage
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QPushButton
from qfluentwidgets import FluentIcon as FIF

class MyCustomPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("my_page", parent)  # page_id 必须唯一
    
    def init_content(self):
        """初始化页面内容 - 必须重写此方法"""
        # 添加标题
        title = QLabel("我的自定义页面")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout.addWidget(title)
        
        # 添加按钮
        button = QPushButton("点击我")
        button.clicked.connect(self.on_button_clicked)
        self.layout.addWidget(button)
    
    def on_button_clicked(self):
        self.show_info("提示", "按钮被点击了！")
    
    def on_activate(self):
        """页面激活时调用 - 可选重写"""
        print(f"页面 {self.page_id} 被激活")
    
    def on_deactivate(self):
        """页面停用时调用 - 可选重写"""
        print(f"页面 {self.page_id} 被停用")
```

#### 注册页面的两种方式

**方式1: 使用页面管理器注册（推荐）**

```python
# 在 main.py 中
from pages.my_custom_page import MyCustomPage

def main():
    app = QApplication(sys.argv)
    window = MainWindow("我的应用")
    
    # 注册页面
    window.page_manager.register_page(
        page_id="my_page",
        title="我的页面",
        page_class=MyCustomPage,
        icon=FIF.HOME,
        tooltip="这是我的自定义页面",
        order=1  # 页面显示顺序
    )
    
    window.show()
    return app.exec()
```

**方式2: 直接添加页面实例**

```python
# 在 main.py 中
def main():
    app = QApplication(sys.argv)
    window = MainWindow("我的应用")
    
    # 创建页面实例
    my_page = MyCustomPage(window)
    
    # 添加到导航
    window.add_page(
        page_id="my_page",
        page_widget=my_page,
        icon=FIF.HOME,
        title="我的页面"
    )
    
    window.show()
    return app.exec()
```

### 3. 页面管理器 API

#### PageManager 主要方法

```python
# 注册页面
page_manager.register_page(
    page_id: str,           # 页面唯一标识
    title: str,             # 页面标题
    page_class: Type[BasePage],  # 页面类
    icon=None,              # 页面图标
    tooltip: str = "",      # 工具提示
    enabled: bool = True,   # 是否启用
    visible: bool = True,   # 是否可见
    order: int = 0          # 显示顺序
) -> bool

# 获取页面实例
page_manager.get_page_instance(page_id: str, *args, **kwargs) -> BasePage

# 导航到页面
page_manager.navigate_to_page(page_id: str, *args, **kwargs) -> bool

# 设置页面状态
page_manager.set_page_enabled(page_id: str, enabled: bool) -> bool
page_manager.set_page_visible(page_id: str, visible: bool) -> bool

# 获取页面信息
page_manager.get_all_pages() -> Dict[str, PageInfo]
page_manager.get_visible_pages() -> Dict[str, PageInfo]
page_manager.get_current_page_id() -> str
```

### 4. 主题管理

#### 使用主题管理器

```python
# 获取主题管理器
theme_manager = window.theme_manager

# 设置主题
theme_manager.set_theme("dark")  # "light" 或 "dark"

# 获取当前主题
current_theme = theme_manager.get_current_theme_id()

# 监听主题变化
theme_manager.theme_changed.connect(self.on_theme_changed)

def on_theme_changed(self, theme_name):
    print(f"主题已切换到: {theme_name}")
```

#### 在页面中应用主题

```python
class MyPage(BasePage):
    def apply_theme(self):
        """应用主题样式 - 可选重写"""
        super().apply_theme()
        
        # 根据当前主题设置样式
        if self.parent().theme_manager.get_current_theme_id() == "dark":
            self.setStyleSheet("background-color: #2b2b2b; color: white;")
        else:
            self.setStyleSheet("background-color: white; color: black;")
```

### 5. 配置管理

#### 使用配置管理器

```python
# 获取配置管理器
config_manager = window.config_manager

# 保存配置
config_manager.set_value("my_setting", "my_value")
config_manager.save_config()

# 读取配置
value = config_manager.get_value("my_setting", default_value="default")

# 监听配置变化
config_manager.config_changed.connect(self.on_config_changed)
```

### 6. 页面间通信

#### 使用信号槽机制

```python
class PageA(BasePage):
    # 定义信号
    data_sent = pyqtSignal(str)
    
    def send_data(self):
        self.data_sent.emit("Hello from Page A")

class PageB(BasePage):
    def init_content(self):
        super().init_content()
        
        # 连接其他页面的信号
        page_a = self.parent().page_manager.get_page_instance("page_a")
        if page_a:
            page_a.data_sent.connect(self.on_data_received)
    
    def on_data_received(self, data):
        print(f"收到数据: {data}")
```

### 7. 高级功能

#### 自定义启动画面

```python
def main():
    app = QApplication(sys.argv)
    
    window = MainWindow(
        app_name="我的应用",
        logo_path="assets/logo.png"
    )
    
    # 自定义启动画面持续时间
    window.splash_screen.start_loading(duration=3000)  # 3秒
    
    window.show()
    return app.exec()
```

#### 添加自定义背景

```python
# 将背景图片放入 assets/PIC/ 目录
# 应用会自动检测并在设置页面中提供选择
```

## 完整示例

以下是一个完整的自定义应用示例：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import pyqtSignal
from qfluentwidgets import FluentIcon as FIF
from core.main_window import MainWindow
from pages.base_page import BasePage

class DataPage(BasePage):
    """数据展示页面"""
    
    def __init__(self, parent=None):
        super().__init__("data", parent)
    
    def init_content(self):
        title = QLabel("数据管理")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(title)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在这里输入数据...")
        self.layout.addWidget(self.text_edit)
        
        save_btn = QPushButton("保存数据")
        save_btn.clicked.connect(self.save_data)
        self.layout.addWidget(save_btn)
    
    def save_data(self):
        data = self.text_edit.toPlainText()
        if data:
            # 保存到配置
            config_manager = self.parent().config_manager
            config_manager.set_value("user_data", data)
            config_manager.save_config()
            self.show_success("保存成功", "数据已保存")
        else:
            self.show_warning("警告", "请输入数据")
    
    def on_activate(self):
        # 页面激活时加载数据
        config_manager = self.parent().config_manager
        data = config_manager.get_value("user_data", "")
        self.text_edit.setPlainText(data)

def main():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow(
        app_name="数据管理应用",
        logo_path="assets/logo.png"
    )
    
    # 注册自定义页面
    window.page_manager.register_page(
        page_id="data",
        title="数据管理",
        page_class=DataPage,
        icon=FIF.DATABASE,
        tooltip="管理应用数据",
        order=1
    )
    
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

## 常见问题

### Q: 如何在页面间传递数据？

A: 使用信号槽机制或通过配置管理器：

```python
# 方法1: 信号槽
class PageA(BasePage):
    data_changed = pyqtSignal(dict)
    
    def send_data(self):
        self.data_changed.emit({"key": "value"})

# 方法2: 配置管理器
config_manager.set_value("shared_data", data)
```

### Q: 如何自定义页面图标？

A: 使用 qfluentwidgets 提供的图标或自定义图标：

```python
from qfluentwidgets import FluentIcon as FIF
from PyQt6.QtGui import QIcon

# 使用内置图标
icon = FIF.HOME

# 使用自定义图标
icon = QIcon("path/to/icon.png")
```

### Q: 如何禁用或隐藏页面？

A: 使用页面管理器的方法：

```python
# 禁用页面
window.page_manager.set_page_enabled("page_id", False)

# 隐藏页面
window.page_manager.set_page_visible("page_id", False)
```

## 许可证

本项目基于 MIT 许可证开源。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个模板！
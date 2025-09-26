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

## 用户管理系统

本应用模板集成了完整的用户管理系统，提供用户认证、权限控制和用户数据管理功能。

### 系统架构

用户管理系统采用分层架构设计：

```
用户管理系统架构
├── 用户界面层 (UI Layer)
│   ├── LoginDialog - 登录对话框
│   ├── UserManagementPage - 用户管理页面
│   └── UserDialog - 用户信息编辑对话框
├── 业务逻辑层 (Business Layer)
│   ├── UserManager - 用户管理器
│   ├── UserSession - 用户会话管理
│   └── PageManager - 页面权限管理
└── 数据存储层 (Data Layer)
    ├── User Model - 用户数据模型
    └── ConfigManager - 配置和数据持久化
```

### 核心组件

#### 1. UserManager (用户管理器)

**位置**: `user/user_manager.py`

**主要功能**:
- 用户认证和登录管理
- 用户注册和创建
- 密码哈希和验证
- 用户数据持久化
- 用户配置文件管理

**核心方法**:
```python
class UserManager:
    def login(username: str, password: str) -> bool
    def logout() -> None
    def create_user(username: str, password: str, role: str = 'user') -> bool
    def delete_user(username: str) -> bool
    def update_user(username: str, **kwargs) -> bool
    def get_all_users() -> List[Dict]
    def is_logged_in() -> bool
    def get_current_user() -> Optional[Dict]
```

#### 2. UserSession (用户会话)

**功能**:
- 维护当前登录用户状态
- 权限验证和角色检查
- 会话安全管理

**权限系统**:
```python
class UserSession:
    def is_authenticated() -> bool      # 检查用户是否已认证
    def is_admin() -> bool             # 检查是否为管理员
    def has_permission(permission: str) -> bool  # 检查特定权限
```

#### 3. User Model (用户数据模型)

**用户属性**:
```python
User = {
    'username': str,        # 用户名 (唯一)
    'password_hash': str,   # 密码哈希值
    'role': str,           # 用户角色 ('admin' | 'user')
    'created_at': str,     # 创建时间
    'last_login': str,     # 最后登录时间
    'is_active': bool,     # 账户状态
    'email': str,          # 邮箱 (可选)
    'full_name': str       # 全名 (可选)
}
```

### 认证流程

#### 登录流程
1. **用户输入**: 用户在LoginDialog中输入用户名和密码
2. **密码验证**: UserManager使用bcrypt验证密码哈希
3. **会话建立**: 验证成功后创建UserSession
4. **权限加载**: 根据用户角色加载相应权限
5. **界面更新**: 主窗口根据用户权限更新可用页面

#### 权限控制
- **页面级权限**: 通过PageManager的`required_role`属性控制
- **功能级权限**: 在页面内部通过`UserSession.is_admin()`等方法控制
- **动态权限**: 支持运行时权限检查和界面更新

### 用户管理功能

#### 管理员功能
- 查看所有用户列表
- 创建新用户账户
- 编辑用户信息
- 删除用户账户
- 重置用户密码
- 修改用户角色

#### 普通用户功能
- 查看个人信息
- 修改个人密码
- 更新个人资料

### 安全特性

#### 密码安全
- 使用bcrypt进行密码哈希
- 支持密码强度验证
- 防止密码明文存储

#### 会话安全
- 自动会话超时
- 登录状态验证
- 防止未授权访问

#### 数据保护
- 用户数据加密存储
- 敏感信息脱敏显示
- 操作日志记录

### 使用示例

#### 基本用户管理
```python
# 初始化用户管理器
user_manager = UserManager()

# 用户登录
if user_manager.login("admin", "password"):
    print("登录成功")
    
    # 检查权限
    if user_manager.session.is_admin():
        print("管理员权限")
    
    # 创建新用户
    user_manager.create_user("newuser", "password123", "user")
    
    # 获取所有用户
    users = user_manager.get_all_users()
    
    # 登出
    user_manager.logout()
```

#### 页面权限控制
```python
# 在页面中检查权限
class AdminPage(BasePage):
    def init_content(self):
        # 检查管理员权限
        if not self.parent().user_manager.session.is_admin():
            return
        
        # 初始化管理员界面
        self.setup_admin_ui()
```

## 数据库策略

本应用采用基于JSON文件的轻量级数据存储策略，通过ConfigManager实现数据持久化和配置管理。

### 存储架构

```
数据存储结构
├── config/                    # 配置目录
│   ├── config.json           # 主配置文件
│   ├── users/                # 用户配置目录
│   │   ├── admin.json        # 管理员配置
│   │   └── user1.json        # 用户个人配置
│   └── data/                 # 应用数据目录
│       ├── users.json        # 用户数据
│       └── app_data.json     # 应用数据
```

### 配置管理器 (ConfigManager)

**位置**: `config/config_manager.py`

#### 核心功能
- **多层配置**: 支持全局配置和用户个人配置
- **配置合并**: 自动合并默认配置和用户配置
- **实时保存**: 配置变更时自动持久化
- **用户隔离**: 每个用户拥有独立的配置空间
- **类型安全**: 支持多种数据类型的配置项

#### 配置分类

##### 1. 应用配置 (App Config)
```json
{
  "app": {
    "name": "应用名称",
    "version": "1.0.0",
    "settings": {
      "language": "chinese",
      "auto_save": true,
      "startup_page": "home"
    }
  }
}
```

##### 2. 主题配置 (Theme Config)
```json
{
  "theme": {
    "current_theme": "dark",
    "themes": {
      "dark": {
        "primary_color": "#0078d4",
        "background_color": "#202020",
        "text_color": "#ffffff"
      },
      "light": {
        "primary_color": "#0078d4",
        "background_color": "#ffffff",
        "text_color": "#000000"
      }
    }
  }
}
```

##### 3. 背景配置 (Background Config)
```json
{
  "background": {
    "enabled": true,
    "current_image": "background1.jpg",
    "current_index": 0,
    "available_images": [
      "background1.jpg",
      "background2.jpg"
    ],
    "opacity": 0.8
  }
}
```

### 数据持久化策略

#### 1. 文件存储
- **格式**: JSON格式，便于读写和调试
- **编码**: UTF-8编码，支持多语言
- **结构**: 层次化结构，便于管理和扩展

#### 2. 用户数据隔离
```python
# 用户特定配置路径
user_config_path = config_dir / "users" / f"{username}.json"

# 全局配置路径
global_config_path = config_dir / "config.json"
```

#### 3. 配置合并机制
```python
def _merge_configs(self, default: Dict, user: Dict) -> Dict:
    """递归合并用户配置和默认配置"""
    result = default.copy()
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = self._merge_configs(result[key], value)
        else:
            result[key] = value
    return result
```

### 数据管理API

#### 基本操作
```python
# 获取配置管理器
config_manager = ConfigManager()

# 读取配置
value = config_manager.get_value("app.settings.language", "english")

# 保存配置
config_manager.set_value("app.settings.language", "chinese")
config_manager.save_config()

# 主题管理
config_manager.set_theme("dark")
current_theme = config_manager.get_current_theme()

# 背景管理
config_manager.set_background_image("new_background.jpg")
config_manager.set_background_enabled(True)
```

#### 用户配置管理
```python
# 设置当前用户
config_manager.set_current_user("username")

# 用户配置自动隔离
config_manager.set_value("personal.preference", "value")  # 保存到用户配置

# 重置配置
config_manager.reset_to_defaults()
```

### 数据安全

#### 1. 数据备份
- 配置变更前自动创建备份
- 支持配置回滚和恢复
- 定期清理过期备份文件

#### 2. 错误处理
```python
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
except (json.JSONDecodeError, IOError) as e:
    print(f"配置加载失败: {e}")
    return default_config  # 返回默认配置
```

#### 3. 数据验证
- 配置项类型验证
- 必需字段检查
- 数据格式验证

### 扩展性设计

#### 1. 插件配置支持
```python
# 插件配置注册
config_manager.register_plugin_config("plugin_name", default_config)

# 插件配置访问
plugin_config = config_manager.get_plugin_config("plugin_name")
```

#### 2. 配置监听机制
```python
# 监听配置变化
config_manager.config_changed.connect(self.on_config_changed)

def on_config_changed(self, key: str, value: Any):
    print(f"配置 {key} 已更改为 {value}")
```

#### 3. 批量操作支持
```python
# 批量更新配置
updates = {
    "app.settings.language": "chinese",
    "theme.current_theme": "dark",
    "background.enabled": True
}
config_manager.batch_update(updates)
```

### 性能优化

#### 1. 延迟加载
- 配置文件按需加载
- 大型配置项延迟初始化
- 内存使用优化

#### 2. 缓存机制
- 频繁访问的配置项缓存
- 智能缓存失效
- 内存和磁盘缓存平衡

#### 3. 异步操作
```python
# 异步保存配置
async def save_config_async(self):
    await asyncio.to_thread(self._save_json_config, self.config_path, self._config)
```

### 迁移和升级

#### 配置版本管理
```json
{
  "config_version": "1.2.0",
  "migration_history": [
    {
      "from_version": "1.0.0",
      "to_version": "1.1.0",
      "migrated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 自动迁移机制
```python
def migrate_config(self, from_version: str, to_version: str):
    """自动迁移配置到新版本"""
    migration_rules = self.get_migration_rules(from_version, to_version)
    for rule in migration_rules:
        self.apply_migration_rule(rule)
```

## 许可证

本项目基于 MIT 许可证开源。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个模板！
# DK6 Flash Tool

基于PyQt6的现代化固件烧录工具，提供简洁的图形界面。

## 特性

- 🔌 自动检测COM端口
- 📁 支持BIN固件文件选择
- 💾 记忆最近使用的文件

## 打包

```bash
python -m nuitka --onefile --windows-disable-console --enable-plugin=pyqt6 --include-data-file=DK6.ico=DK6.ico --windows-icon-from-ico=DK6.ico --windows-company-name="DK6 Tools" --windows-product-name="DK6 Flash Tool" --windows-file-version="1.0.0.0" --windows-product-version="1.0.0" --windows-file-description="DK6 Firmware Flash Tool" main.py
```

## 快速开始

安装依赖：

```bash
pip install pyqt6 pyserial
```

运行程序：

```bash

```

## 使用

1. 选择COM端口
2. 选择固件文件
3. 点击Flash按钮

> 需要DK6Programmer.exe在PATH或同目录下

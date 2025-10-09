#### 单行命令（推荐）

```bash
python -m nuitka --standalone --windows-console-mode=disable --windows-icon-from-ico=compile_tool.ico --include-data-files=config.json=config.json --include-data-files=styles.qss=styles.qss --include-data-files=compile_tool.ico=compile_tool.ico --plugin-enable=pyqt6 --output-filename=UwbBuildTool.exe --windows-company-name="Cardshare@QLL" --windows-product-name="UWB Build Tool" --windows-file-version="1.0.0.0" --windows-product-version="1.0.0" --windows-file-description="UWB项目构建工具" --copyright="Copyright © 2025 Cardshare@QLL" main.py
```

### 命令参数说明
- `--onefile`: 生成单个可执行文件
- `--standalone`: 创建独立的可执行文件，包含所有依赖
- `--enable-plugin=pyqt6`: 启用PyQt6插件支持
- `--windows-disable-console`: 禁用控制台窗口
- `--windows-icon-from-ico=compile_tool.ico`: 设置应用程序图标
- `--include-data-dir=.=.`: 包含当前目录下的所有数据文件
- `--output-dir=dist`: 指定输出目录为dist
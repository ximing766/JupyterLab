我将为你创建一个名为 `build_lite.ps1` 的构建脚本，放置在 `e:\Work\Python\JupyterLab\UWB_Tools\build_tool` 目录下。

该脚本将基于参考文件 `UWB_Reader\build_lite.ps1` 进行适配，具体配置如下：

### 脚本配置详情
1.  **编译目标**: `main.py` (确认为程序入口)。
2.  **核心参数**:
    *   `--standalone` & `--onefile`: 生成单文件可执行程序。
    *   `--windows-console-mode=disable`: 运行时不显示控制台窗口。
    *   `--enable-plugin=pyqt6`: 启用 PyQt6 插件支持。
3.  **资源文件包含**:
    *   `compile_tool.ico`: 程序图标。
    *   `styles.qss`: 界面样式表。
    *   `config.json`: 默认配置文件（确保程序首次运行有默认配置）。
4.  **优化配置**:
    *   排除不必要的重型库：`numpy`, `scipy`, `pandas`, `matplotlib`, `PIL`, `IPython`（根据代码分析，这些未被直接使用，排除可显著减小体积）。
    *   使用 8 线程并行编译 (`--jobs=8`)。
    *   启用 Python 优化标志 (`-OO`)。

### 生成的文件
*   **路径**: `e:\Work\Python\JupyterLab\UWB_Tools\build_tool\build_lite.ps1`
*   **输出**: 编译成功后，可执行文件 `UwbBuildTool.exe` 将生成在 `output` 目录中。
# UWB Build Tool

## 简介
UWB Build Tool 是一个基于 Python/PyQt6 开发的图形化编译管理工具，专为 UWB (Ultra-Wideband) 嵌入式项目设计。它旨在简化编译流程，支持 MCUXpresso IDE 和 Make 两种构建模式，并提供了一键生成头文件、多通道固件管理等便捷功能。

## 核心作用
1. **多模式构建管理**：支持 Debug/Release 配置切换，以及不同的应用宏定义模式（如 INGATE_MASTER_TRANSIT）。
2. **双编译引擎**：
   - **IDE 模式**：调用 MCUXpresso IDE 的命令行工具 (`mcuxpressoidec.exe`) 进行构建，兼容原有 IDE 工程配置。
   - **Make 模式**：直接调用 `make` 命令进行快速构建，适合命令行或轻量级开发环境。
3. **固件自动化处理**：编译完成后自动根据配置（如单/双/三通道）重命名固件文件，便于版本管理和区分。
4. **配置持久化**：自动保存项目路径、最后使用的配置模式、窗口位置等用户习惯。

## 架构设计

### 模块划分
*   **UI 层 (`main.py`)**:
    *   基于 PyQt6 构建的主界面。
    *   提供项目选择、模式配置、编译控制等交互元素。
    *   使用 Fluent Design 风格组件 (`qfluentwidgets`) 提升视觉体验。
*   **逻辑层 (`build_thread.py`)**:
    *   **BuildThread**: 继承自 `QThread`，负责在后台执行耗时的编译任务，避免阻塞主界面。
    *   实现了对编译器输出流的实时捕获与过滤（`should_show_line`），仅展示关键信息（如错误、警告、最终结果）。
*   **配置层 (`config_manager.py`)**:
    *   负责 `config.json` 的读写。
    *   管理项目历史记录、构建宏定义映射表、UI 状态等。

### 工作流程
1.  **初始化**：启动时加载配置文件，恢复上次打开的项目和设置。
2.  **配置**：用户选择编译模式（如 Release）和功能宏（如 Master Anchor）。
3.  **构建**：
    *   点击构建按钮触发 `BuildThread`。
    *   线程根据模式组装命令行参数（Make 或 IDE CLI）。
    *   调用 `subprocess` 执行编译。
    *   实时回调 GUI 更新进度条和日志。
4.  **后处理**：编译成功后，脚本自动查找生成的 `.bin` 文件并按规则重命名（例如添加 `_S`, `_D` 等后缀）。

## 关键文件
- `main.py`: 程序入口与主窗口实现。
- `build_thread.py`: 编译逻辑核心，包含子进程管理和日志解析。
- `config_manager.py`: 配置数据管理。
- `build_lite.ps1`: 轻量级构建脚本（辅助）。

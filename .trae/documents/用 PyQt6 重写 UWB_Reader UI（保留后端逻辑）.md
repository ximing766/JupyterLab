# 目标
- 以 PyQt6 重写 `UWB_Reader` 的全部界面与交互，替代 tkinter/customtkinter。
- 不修改加密、APDU 处理、串口读写等业务逻辑；仅做 UI 适配与解耦。
- 合并进/出站 UI：顶部一栏进行双 Reader 的 COM 配置，下方并排日志；“Setting”独立页面。
- 去掉主题切换、更新日志按钮与 `/UwbReader.py#L282-283` 红字提示文案。

# 总体方案
- 将现有类的“业务逻辑”与“UI/变量绑定”分离：保留算法与串口流程，改为通过回调/信号与 PyQt UI 交互。
- 新增模块：
  - `uwb_service.py`：纯后端服务（串口+APDU+加密），提供方法：列口、连接/断开、发送、参数设置；通过回调输出日志/错误/状态。
  - `qt_main.py`：PyQt6 主窗口，完成界面与交互，订阅服务回调。
- 线程模型：沿用后端中的 `threading.Thread` 循环，向 UI 发射信号（通过回调转发到 `pyqtSignal`），避免 UI 卡顿与竞态。

# 界面设计
- 主窗口（`QMainWindow`，Fusion 风格 + 自定义浅色配色，稳定耐看）：
  - 顶部状态栏（单行，`QWidget+QGridLayout`）：
    - 进站 Reader：`QComboBox(COM)`、`QComboBox(波特率)`、`QPushButton(连接/断开)`、状态圆点（绿/灰）。
    - 出站 Reader：同上。
    - 右侧操作：`QCheckBox(Pin to Screen)` → 设置 `Qt.WindowStaysOnTopHint`；`QCheckBox(1E检查)` → 传给后端。
  - 下方日志区（`QSplitter` 水平分割）：
    - 左：`QPlainTextEdit`（ENTER Log），上方工具行：清空、保存、复制；自动滚动。
    - 右：`QPlainTextEdit`（EXIT Log），同上。
  - 底部状态栏：版本与连接状态提示；无任何“更新日志/主题”入口。
- Setting 页（`QTabWidget` 第二页“设置”）：
  - 分组 `QGroupBox`：进站参数（行业代码、线路代码、站点代码、金额输入）；出站参数（同）。
  - 字段与现有变量一一映射（参照 `UwbReader.py:175-236`）。

# 后端适配策略（不改业务）
- 参考点：
  - 串口连接与读线程：`connect_enter/exit`、`read_data_enter/exit`（`UwbReader.py:351-372, 513-562`）
  - APDU/加密流水：`ApduHandle`、`update_*`、`get_mac`（`UwbReader.py:430-512, 60-101, 397-428`）
- 变更仅限“UI耦合”部分：
  - 将 `messagebox.showerror(...)` 改为回调 `on_error(str)`（由 PyQt 弹窗或状态提示）。
  - 将 `show_in_text_area*` 改为回调 `on_enter_log/on_exit_log`（由 PyQt 文本框追加）。
  - 将 `self.port_var/self.baudrate_var/...` 改为纯 Python 成员（由 UI 传值），提供 setter：`set_enter_port/baud(...)`、`set_exit_port/baud(...)`。
  - `update_ports_periodically` 改为服务方法 + UI `QTimer(2s)` 更新下拉；逻辑沿用注册表方案（`UwbReader.py:616-673`）。
  - 删除 UI 专用项：`create_widgets`、主题切换与更新日志（`UwbReader.py:682-713, 714-721`），以及红字 `info_label`（`UwbReader.py:282-283`）。
- 其余算法、串口帧构造与校验保持完全一致。

# 交互与状态
- 连接流程：
  - 用户在顶部选择 COM/波特率，点“连接”；UI 调用 `service.connect_enter/exit(...)`，按钮与圆点切换为“已连接”。
  - 断开同理；异常通过回调推送到状态栏与消息框。
- 日志：
  - 后端在消费完成处仍产生日志文本（`send_*` 中），通过回调追加到对应 Log；支持“保存到文件”。
- E1 检查：
  - 顶部复选框 → `service.set_e1_check(True/False)`；逻辑仍在 `ApduHandle` 中执行。
- Pin to Screen：
  - 直接设置 `setWindowFlag(Qt.WindowStaysOnTopHint, checked)` 并 `show()` 刷新。

# 迁移步骤
1. 新建 `uwb_service.py`，复制后端逻辑，删去 tkinter/customtkinter 变量与 UI控件，加入回调接口与 setter；其余算法保持原样。
2. 新建 `qt_main.py`，按上述界面搭建；创建 `UwbService` 实例并绑定回调到 `pyqtSignal`，连接UI事件至 service 方法。
3. 移除旧 UI 功能：主题切换、更新日志、红字 info；不再依赖 `ttkbootstrap/customtkinter`。
4. 保留图标资源（`PIC/Delete.png`等）用于按钮；应用 Fusion 风格与统一浅色配色。
5. 启动入口：`python qt_main.py`；Windows11/PowerShell 运行；如需虚拟环境，先 `conda activate myenv`。

# 验证
- 串口可用性：端口热插拔更新；两路 Reader 可同时连接与独立断开；状态正确。
- APDU 流程：实卡/仿真串口回放均能触发 `C2` 分支、MAC 生成与 halt；日志正确显示金额与时间。
- E1 检查：开启时对进出站顺序进行拦截（沿用原逻辑）；关闭时不拦截。
- 稳定性：线程退出、窗口关闭（复用 `on_window_closing` 语义），无泄漏与崩溃；异常统一消息提示。

# 交付物
- `uwb_service.py`（后端服务，保留业务逻辑）
- `qt_main.py`（PyQt6 UI，现代化界面）
- 运行与使用说明（简短）

请确认以上方案；确认后我将开始实现、替换 UI，并进行端到端验证。
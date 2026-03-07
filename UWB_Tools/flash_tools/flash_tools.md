# UWB Flash Tools

## 简介
UWB Flash Tools 是一套用于 UWB 设备固件烧录和 OTA (Over-The-Air) 升级的工具集。包含图形化界面 (GUI) 和命令行 (CLI) 两个版本，支持通过串口 (UART) 对设备进行固件擦除、写入和校验。

## 核心作用
1. **串口烧录**：通过 PC 串口与 UWB 设备通信，执行固件更新。
2. **OTA 协议实现**：实现了自定义的 OTA 传输协议，包括握手、擦除扇区、分包传输数据、CRC 校验等。
3. **多固件类型支持**：支持 APP 固件和 SR150 (射频芯片) 固件的独立烧录。
4. **自动化脚本支持**：提供 CLI 版本，便于集成到自动化测试或产线脚本中。

## 架构设计

### 模块划分
*   **GUI 版本 (`OTA_Flash_Tool.py`)**:
    *   提供串口配置、文件选择、进度显示等图形界面。
    *   使用 `OTAWorker` 线程处理烧录任务，保持界面响应。
*   **CLI 版本 (`OTA_Flash_Tool_CLI.py`)**:
    *   基于 `argparse` 处理命令行参数。
    *   包含 `OTAClient` 类，封装了底层的串口通信和协议逻辑。
*   **通信协议**:
    *   **命令集**：RESET (0xCA), ERASE (0xCB), PROGRAM (0xCC), READ_HEADER (0xCD)。
    *   **校验机制**：使用 CRC32 校验固件完整性，XMODEM CRC 校验数据包传输。

### 核心流程 (OTA)
1.  **握手与连接**：打开指定串口。
2.  **预处理**：读取固件文件，添加自定义固件头（包含 Magic Number、版本、CRC32）。
3.  **擦除 (Erase Phase)**：发送擦除指令，清除 Flash 指定区域。
4.  **编程 (Program Phase)**：
    *   将固件切分为固定大小的数据包（默认 768 字节）。
    *   逐包发送并等待设备 ACK。
    *   支持传输超时重试。
5.  **校验 (Verification)**：读取设备端固件头信息与本地进行比对。

## 关键文件
- `OTA_Flash_Tool.py`: GUI 主程序。
- `OTA_Flash_Tool_CLI.py`: 命令行工具及核心协议实现 (`OTAClient`)。

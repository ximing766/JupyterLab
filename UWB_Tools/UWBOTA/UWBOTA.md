# UWB OTA (Android)

## 简介
UWB OTA 是一款 Android 移动端应用，专为通过蓝牙低功耗 (BLE) 技术对 UWB 设备进行固件升级而设计。它实现了完整的移动端 OTA 流程，支持 APP 固件和底层射频 (SR150) 固件的无线更新。

## 核心作用
1. **BLE 设备管理**：扫描、连接、断开 UWB 设备。
2. **无线固件升级**：
    *   支持 APP 固件 (External Flash App) 升级。
    *   支持 SR150 射频固件升级。
3. **APDU 协议通信**：通过 BLE 特征值发送符合 ISO7816/APDU 规范的指令包。
4. **进度可视化**：实时显示传输进度、速度和耗时。

## 架构设计

### 技术栈
*   **语言**: Kotlin
*   **UI 框架**: Android View Binding, Fragments
*   **异步处理**: Kotlin Coroutines (协程)

### 模块划分
*   **UI 层**:
    *   `MainActivity`: 应用入口与导航容器。
    *   `HomeFragment`: 主要操作界面，包含设备扫描和文件选择。
    *   `DeviceSelectionDialog`: 蓝牙设备扫描与选择弹窗。
*   **BLE 通信层 (`BleManager.kt`)**:
    *   封装 `BluetoothGatt` 操作。
    *   处理连接状态管理、服务发现、特征值写入 (Write) 和通知接收 (Notify)。
*   **业务逻辑层 (`OtaManager.kt`)**:
    *   **状态机**：管理 OTA 的各个阶段（准备 -> 擦除 -> 写入 -> 校验）。
    *   **流控**：控制数据包发送速率，处理重传机制。
*   **协议层 (`ApduProtocol.kt`)**:
    *   定义 OTA 相关的指令格式。
    *   负责数据的分包 (Chunking) 和组包。

### OTA 流程
1.  **扫描与连接**：用户选择目标 UWB 设备建立 BLE 连接。
2.  **文件准备**：加载手机存储中的 `.bin` 固件文件，计算 CRC32 并生成头部。
3.  **传输循环** (`OtaManager`):
    *   **Erase**：发送擦除指令，等待设备 ACK。
    *   **Program**：将固件切分为 128 字节的小块 (Chunk)，通过 BLE 特征值写入。
    *   **Verify**：发送校验指令，确认升级结果。
4.  **完成**：UI 提示升级成功或失败原因。

## 关键文件
- `BleManager.kt`: 蓝牙底层通信实现。
- `OtaManager.kt`: OTA 核心业务流程控制。
- `ApduProtocol.kt`: 协议封装。
- `MainActivity.kt`: 主界面逻辑。

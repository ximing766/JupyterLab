---
name: project_management
description: 管理当前项目下多个应用(UWBDash, UwbBuildTool, OTA_Flash_Tool, UWBReader)的运行与编译流程。当用户需要编译、构建或运行这些应用时触发。
---

# 工程管理 (Project Management)

## 描述
管理 JupyterLab 工程下多个 Python/PyQt6 应用的编译、构建和清理流程。确保在统一的虚拟环境 (`myenv`) 中执行标准化构建脚本。

## 使用场景
当用户需要对以下应用进行编译 (`build`) 或运行操作时：
1. **UWBDash**: `pyqt6\uwb`
2. **UwbBuildTool**: `UWB_Tools\build_tool`
3. **OTA_Flash_Tool**: `UWB_Tools\flash_tools`
4. **UWBReader**: `UWB_Tools\UWB_Reader`

## 指令

### 1. 环境准备
所有操作前必须激活 Conda 环境：
```powershell
conda activate myenv
```

### 2. 应用构建流程
根据目标应用，进入对应目录并执行 `build_lite.ps1`。

#### UWBDash
- **目录**: `e:\Work\Python\JupyterLab\pyqt6\uwb`
- **命令**:
  ```powershell
  cd e:\Work\Python\JupyterLab\pyqt6\uwb
  .\build_lite.ps1
  ```

#### UwbBuildTool
- **目录**: `e:\Work\Python\JupyterLab\UWB_Tools\build_tool`
- **命令**:
  ```powershell
  cd e:\Work\Python\JupyterLab\UWB_Tools\build_tool
  .\build_lite.ps1
  ```

#### OTA_Flash_Tool
- **目录**: `e:\Work\Python\JupyterLab\UWB_Tools\flash_tools`
- **命令**:
  ```powershell
  cd e:\Work\Python\JupyterLab\UWB_Tools\flash_tools
  .\build_lite.ps1

#### UWBReader
- **目录**: `e:\Work\Python\JupyterLab\UWB_Tools\UWB_Reader`
- **命令**:
  ```powershell
  cd e:\Work\Python\JupyterLab\UWB_Tools\UWB_Reader
  .\build_lite.ps1
  ```


## 示例

**用户**: "编译 UWBReader"
**执行步骤**:
1. 激活环境: `conda activate myenv`
2. 进入目录: `cd e:\Work\Python\JupyterLab\UWB_Tools\UWB_Reader`
3. 执行构建: `.\build_lite.ps1`
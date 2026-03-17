# UWBDash
UWB数据监控与可视化仪表盘。

## 核心功能
- **多串口监控**: 支持双路 COM 端口数据读取与解析。
- **实时绘图**: 动态展示 UWB 距离、RSSI、AoA/Pdoa 等参数。
- **灵活配置**: 支持背景自定义、日志保存及搜索历史记录。

## 脚本说明
- **[build_lite.ps1](file:///e:/Work/Python/JupyterLab/pyqt6/uwb/build_lite.ps1)**: 使用 Nuitka 进行精简打包，排除冗余库（numpy/scipy等）以减小体积，生成独立 EXE。
- **[release.ps1](file:///e:/Work/Python/JupyterLab/pyqt6/uwb/release.ps1)**: 自动化发布脚本。执行清理构建目录、压缩 `dist` 文件夹，并利用 GitHub CLI (`gh`) 创建版本并上传附件。

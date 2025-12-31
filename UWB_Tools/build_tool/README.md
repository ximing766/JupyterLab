```bash
python -m nuitka --standalone --windows-console-mode=disable --windows-icon-from-ico=compile_tool.ico --include-data-files=config.json=config.json --include-data-files=styles.qss=styles.qss --include-data-files=compile_tool.ico=compile_tool.ico --plugin-enable=pyqt6 --output-filename=UwbBuildTool.exe --windows-company-name="Cardshare@QLL" --windows-product-name="UWB Build Tool" --windows-file-version="1.0.0.0" --windows-product-version="1.0.0" --windows-file-description="UWB项目构建工具" --copyright="Copyright © 2025 Cardshare@QLL" main.py
```

mklink /J E:\mcux_ide D:\Software\MCUXPRESSO\router\MCUXpressoIDE_24.12.148\ide
该工程使用MCUXpressoIDE_24.12.148的make工具链进行编译


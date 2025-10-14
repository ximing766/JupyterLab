```bash
conda activate myenv
pip install nuitka pyqt6 pyserial

# 打包OTA Flash Tool
nuitka --standalone --onefile --windows-console-mode=disable --windows-icon-from-ico=DK6.ico --include-data-files=styles.qss=styles.qss --include-data-files=DK6.ico=DK6.ico --plugin-enable=pyqt6 --output-filename=OTA_Flash_Tool.exe --windows-company-name="Cardshare@QLL" --windows-product-name="OTA Flash Tool" --windows-file-version="1.0.0.0" --windows-product-version="1.0.0" --windows-file-description="UWB OTA烧录工具" --copyright="Copyright © 2025 Cardshare@QLL" OTA_Flash_Tool.py
`
```
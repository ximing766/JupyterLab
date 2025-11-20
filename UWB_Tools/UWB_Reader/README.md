### 优化版本（推荐）
```bash
python -m nuitka --standalone --onefile --windows-disable-console --enable-plugin=tk-inter --include-data-dir=PIC=PIC --include-data-dir=themes=themes --include-data-file=UWBReader.ico=UWBReader.ico --include-data-file=libRSCode.dll=libRSCode.dll --include-data-file=logo.png=logo.png --output-dir=output --windows-icon-from-ico=UWBReader.ico --assume-yes-for-downloads --show-progress --show-memory UwbReader.py
```




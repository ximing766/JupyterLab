```bash
python -m nuitka --standalone --onefile --windows-disable-console --enable-plugin=pyqt6 --include-qt-plugins=sensible,styles --include-data-file=UWBReader.ico=UWBReader.ico --include-data-file=logo.png=logo.png --output-dir=output --output-filename=UWBReader --windows-icon-from-ico=UWBReader.ico --assume-yes-for-downloads --jobs=8 --python-flag=-OO --nofollow-import-to=numpy,scipy,pandas,PySide6,matplotlib --show-progress --show-memory qt_main.py
```




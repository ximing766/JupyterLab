
```bash
python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=pyqt6 --windows-icon-from-ico=./logo.ico --include-data-dir=./pic=./pic --include-data-file=./highlight_config.json=./highlight_config.json --include-data-file=./logo.ico=./logo.ico --include-module=log --output-dir=../../output --product-name="UWBDash" --product-version="1.0.0" --file-version="1.0.0.0" --copyright="CardShare@QLL © 2025" --trademarks="UWBDash" UWBDash.py
```
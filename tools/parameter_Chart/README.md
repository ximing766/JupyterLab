# nuitka打包

- 进入虚拟环境，否则包很大

```
python -m nuitka --standalone --show-progress --show-memory --enable-plugin=pyqt6 --windows-icon-from-ico=logo.ico --include-data-dir=.venv/Lib/site-packages/pyecharts/datasets=pyecharts/datasets --output-dir=dist --output-filename=ParameterChart main.py
```

# Nuitka
uv pip install nuitka

# 进入uwb路径，虚拟环境pyqt6

# 打包
python -m nuitka --standalone --windows-disable-console --enable-plugin=pyqt6 --windows-icon-from-ico=./logo.ico --include-data-dir=./pic=./pic --include-data-file=./highlight_config.json=./highlight_config.json --include-data-file=./logo.ico=./logo.ico --include-module=log --output-dir=../../output UWBDash.py
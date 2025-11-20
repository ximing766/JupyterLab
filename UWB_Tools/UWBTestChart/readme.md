# UWB测试图表工具打包说明

* 进入myenv虚拟环境：   E:\Work\UWB\Code\UwbCOMCode\Test
* pip install nuitka

## 分离模式打包（推荐）

```bash
python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=tk-inter --include-data-file=uwb_layout_template.html=uwb_layout_template.html --output-dir=dist UWBTestChart.py
```

## onefile模式打包 (生产环境)

```
python -m nuitka --onefile --windows-console-mode=disable --enable-plugin=tk-inter --include-data-file=uwb_layout_template.html=uwb_layout_template.html --output-dir=dist UWBTestChart.py
```

## 使用说明

- 打包后在 `dist/UWBTestChart.dist/` 目录下找到可执行文件
- 运行前确保CSV数据文件格式正确
- 生成的HTML图表文件保存在同目录下

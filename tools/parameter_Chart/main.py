import sys
import os
import pandas as pd
import numpy as np
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QWidget, QFileDialog, QLabel, QListWidget, QListWidgetItem,
                             QProgressBar, QMessageBox, QSplitter, QFrame, QTableView,
                             QGroupBox, QComboBox, QTabWidget, QTextEdit, QSizePolicy, QStyleFactory)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QAbstractTableModel
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QColor, QFont

import pyecharts.options as opts
from pyecharts.charts import Line, Boxplot, Bar, Scatter
from pyecharts.globals import ThemeType

# 数据表格模型
class DataTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        
    def rowCount(self, parent=None):
        return len(self._data)
        
    def columnCount(self, parent=None):
        return len(self._data.columns)
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        elif role == Qt.ItemDataRole.BackgroundRole:
            if index.row() % 2 == 0:
                return QColor(248, 248, 248)
        return None
        
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section + 1)
        return None

# 数据处理线程
class DataProcessThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)
    
    def __init__(self, file_path, selected_columns, html_dir, chart_type):
        super().__init__()
        self.file_path = file_path
        self.selected_columns = selected_columns
        self.html_dir = html_dir
        self.chart_type = chart_type
        
    def run(self):
        try:
            # 根据文件扩展名读取数据
            file_ext = os.path.splitext(self.file_path)[1].lower()
            if file_ext == '.csv':
                data = pd.read_csv(self.file_path, sep=',', header=0)
            elif file_ext in ['.xlsx', '.xls']:
                data = pd.read_excel(self.file_path)
            else:
                self.error_signal.emit(f"不支持的文件格式: {file_ext}")
                return
                
            # 检查数据是否为空
            if data.empty:
                self.error_signal.emit("数据为空")
                return
                
            # 确保HTML目录存在
            os.makedirs(self.html_dir, exist_ok=True)
            
            # 生成的HTML文件路径列表
            html_files = []
            
            # 处理每个选定的列
            total_columns = len(self.selected_columns)
            
            # 初始进度
            self.progress_signal.emit(5)
            self.msleep(200)  # 延时200毫秒
            
            for i, column in enumerate(self.selected_columns):
                if column not in data.columns:
                    continue
                    
                # 开始处理当前列的进度 (5% 到 85%)
                start_progress = int(5 + (i / total_columns) * 80)
                self.progress_signal.emit(start_progress)
                self.msleep(300)  # 延时300毫秒
                
                # 根据图表类型创建图表
                if self.chart_type == "折线图":
                    html_path = self.create_line_chart(data, column)
                elif self.chart_type == "柱状图":
                    html_path = self.create_bar_chart(data, column)
                elif self.chart_type == "散点图":
                    html_path = self.create_scatter_chart(data, column)
                elif self.chart_type == "箱线图":
                    html_path = self.create_box_chart(data, column)
                else:
                    html_path = self.create_line_chart(data, column)
                    
                if html_path:
                    html_files.append(html_path)
                
                # 图表生成完成后更新进度
                end_progress = int(5 + ((i + 1) / total_columns) * 80)
                self.progress_signal.emit(end_progress)
                self.msleep(200)  # 延时200毫秒
                
            # 最终完成进度
            self.progress_signal.emit(95)
            self.msleep(300)
            self.progress_signal.emit(100)
            self.msleep(500)  # 完成后保持一段时间
            self.finished_signal.emit(html_files)
            
        except Exception as e:
            self.error_signal.emit(f"处理数据时出错: {str(e)}")
    
    def create_line_chart(self, data, column):
        try:
            x_data = list(range(len(data)))
            y_data = data[column].tolist()
            
            c = (
                Line(init_opts=opts.InitOpts(width="800px", height="500px", theme=ThemeType.MACARONS))
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(
                    series_name=column,
                    y_axis=y_data,
                    is_smooth=True,
                    areastyle_opts=opts.AreaStyleOpts(opacity=0.3),
                    label_opts=opts.LabelOpts(is_show=False),  # 隐藏数据点标签
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}"),
                    xaxis_opts=opts.AxisOpts(name="索引"),
                    yaxis_opts=opts.AxisOpts(name=column),
                    datazoom_opts=[opts.DataZoomOpts()],
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    toolbox_opts=opts.ToolboxOpts(is_show=True, 
                                                feature=opts.ToolBoxFeatureOpts(save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(background_color="white",pixel_ratio=3))),
                    visualmap_opts=opts.VisualMapOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_line.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"创建折线图时出错 {column}: {str(e)}")
            return None
    
    def create_bar_chart(self, data, column):
        try:
            x_data = list(range(len(data)))
            y_data = data[column].tolist()
            
            c = (
                Bar(init_opts=opts.InitOpts(width="800px", height="500px", theme=ThemeType.MACARONS))
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(series_name=column, y_axis=y_data, label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}"),
                    xaxis_opts=opts.AxisOpts(name="索引"),
                    yaxis_opts=opts.AxisOpts(name=column),
                    datazoom_opts=[opts.DataZoomOpts()],
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    toolbox_opts=opts.ToolboxOpts(is_show=True, 
                                                feature=opts.ToolBoxFeatureOpts(save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(background_color="white",pixel_ratio=3))),
                    visualmap_opts=opts.VisualMapOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_bar.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"创建柱状图时出错 {column}: {str(e)}")
            return None
    
    def create_scatter_chart(self, data, column):
        try:
            x_data = list(range(len(data)))
            y_data = data[column].tolist()
            scatter_data = list(zip(x_data, y_data))
            
            c = (
                Scatter(init_opts=opts.InitOpts(width="800px", height="500px", theme=ThemeType.MACARONS))
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(series_name=column, y_axis=y_data, label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}"),
                    xaxis_opts=opts.AxisOpts(name="索引"),
                    yaxis_opts=opts.AxisOpts(name=column),
                    datazoom_opts=[opts.DataZoomOpts()],
                    tooltip_opts=opts.TooltipOpts(trigger="item"),
                    toolbox_opts=opts.ToolboxOpts(is_show=True, 
                                                feature=opts.ToolBoxFeatureOpts(save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(background_color="white",pixel_ratio=3))),
                    visualmap_opts=opts.VisualMapOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_scatter.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"创建散点图时出错 {column}: {str(e)}")
            return None
    
    def create_box_chart(self, data, column):
        try:
            y_data = data[column].tolist()
            
            c = (
                Boxplot(init_opts=opts.InitOpts(width="800px", height="500px", theme=ThemeType.MACARONS))
                .add_xaxis([column])
                .add_yaxis(series_name=column, y_axis=[y_data], label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}"),
                    tooltip_opts=opts.TooltipOpts(trigger="item"),
                    toolbox_opts=opts.ToolboxOpts(is_show=True, 
                                                feature=opts.ToolBoxFeatureOpts(save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(background_color="white",pixel_ratio=3))),
                    visualmap_opts=opts.VisualMapOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_box.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"创建箱线图时出错 {column}: {str(e)}")
            return None

# 主窗口类
class ParameterChartApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_file = None
        self.data = None
        self.html_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HTML")
        os.makedirs(self.html_dir, exist_ok=True)
        
    def init_ui(self):
        # 设置窗口属性和样式
        self.setWindowTitle("参数报告生成")
        self.setGeometry(100, 100, 630, 350)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                color: #333333;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #495057;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357abd);
                border: 2px solid #357abd;
                color: white;
                border-radius: 8px;
                font-size: 12px;
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
                text-align: center;
                min-height: 12px;
                min-width: 50px;
                outline: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5ba0f2, stop:1 #4a90e2);
                border: 2px solid #4a90e2;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357abd, stop:1 #2968a3);
                border: 2px solid #2968a3;
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a0a0a0, stop:1 #808080);
                border: 2px solid #808080;
                color: #f0f0f0;
            }
            QPushButton:focus {
                border: 2px solid #66afe9;
            }
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 10px;
                background-color: white;
                color: #333333;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #6c757d;
            }
            QTableView {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                gridline-color: #dee2e6;
                color: #333333;
                selection-background-color: #e3f2fd;
            }
            QTableView::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTableView::item:selected {
                background-color: #e3f2fd;
                color: #333333;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
            QLabel {
                color: #333333;
            }
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 12px;
                color: #333333;
                background-color: #f8f9fa;
                height: 24px;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #28a745, stop:0.5 #20c997, stop:1 #17a2b8);
                border-radius: 6px;
                margin: 2px;
                border: none;
            }
            QProgressBar:chunk:disabled {
                background-color: #6c757d;
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 文件选择区域（极简紧凑布局）
        file_group = QGroupBox("文件选择")
        file_group.setMaximumHeight(60)  # 限制最大高度
        file_layout = QHBoxLayout(file_group)
        file_layout.setContentsMargins(5, 5, 5, 5)  # 减少边距
        file_layout.setSpacing(8)
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        
        self.browse_button = QPushButton("浏览")
        self.browse_button.setFixedSize(50, 20)  # 固定按钮大小
        self.browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.browse_button, 0)
        
        # 数据预览区域（核心位置，增大高度）
        preview_group = QGroupBox("数据预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        self.info_label = QLabel("请选择文件以查看数据信息")
        self.info_label.setStyleSheet("color: #6c757d; font-style: italic; font-size: 11px;")
        preview_layout.addWidget(self.info_label)
        
        self.table_view = QTableView()
        self.table_view.setMinimumHeight(250)  # 增加表格最小高度
        self.table_view.hide()
        preview_layout.addWidget(self.table_view)
        
        # 控制区域（紧凑布局）
        control_group = QGroupBox("图表设置")
        control_group.setMaximumHeight(80)  # 限制控制区域高度
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(8, 5, 8, 5)
        control_layout.setSpacing(5)
        
        # 列选择和图表类型在同一行
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(10)
        
        # 列选择（使用下拉框代替列表）
        settings_layout.addWidget(QLabel("选择列:"))
        self.columns_combo = QComboBox()
        self.columns_combo.setMinimumWidth(120)
        settings_layout.addWidget(self.columns_combo)
        
        settings_layout.addWidget(QLabel("图表类型:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["折线图", "柱状图", "散点图", "箱线图"])
        self.chart_type_combo.setMinimumWidth(100)
        settings_layout.addWidget(self.chart_type_combo)
        
        settings_layout.addStretch()
        control_layout.addLayout(settings_layout)
        
        # 生成按钮和进度条
        action_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("生成图表")
        self.generate_button.clicked.connect(self.generate_charts)
        self.generate_button.setEnabled(False)
        
        self.open_dir_button = QPushButton("\U0001F4C2")
        self.open_dir_button.clicked.connect(self.open_html_dir)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(24)
        
        action_layout.addWidget(self.generate_button)
        action_layout.addWidget(self.open_dir_button)
        action_layout.addWidget(self.progress_bar)
        
        control_layout.addLayout(action_layout)
        
        # 添加到主布局，设置拉伸因子
        main_layout.addWidget(file_group, 0)  # 文件选择区域不拉伸
        main_layout.addWidget(preview_group, 1)  # 预览区域占主要空间
        main_layout.addWidget(control_group, 0)  # 控制区域不拉伸
        
        # 创建中央窗口部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 设置拖放支持
        self.setAcceptDrops(True)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV或Excel文件", "", "数据文件 (*.csv *.xlsx *.xls)"
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        try:
            # 根据文件扩展名读取数据
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                self.data = pd.read_csv(file_path, sep=',', header=0)
            elif file_ext in ['.xlsx', '.xls']:
                self.data = pd.read_excel(file_path)
            else:
                QMessageBox.warning(self, "错误", f"不支持的文件格式: {file_ext}")
                return
            
            # 更新UI
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            
            # 更新列下拉框
            self.columns_combo.clear()
            self.columns_combo.addItems(self.data.columns.tolist())
            
            # 启用生成按钮
            self.generate_button.setEnabled(True)
            
            # 显示数据预览
            self.show_data_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件时出错: {str(e)}")
    
    def show_data_preview(self):
        if self.data is None:
            return
            
        # 更新信息标签
        info_text = f"文件: {os.path.basename(self.current_file)} | "
        info_text += f"行数: {len(self.data)} | "
        info_text += f"列数: {len(self.data.columns)}"
        self.info_label.setText(info_text)
        self.info_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        # 创建表格模型并设置到视图
        preview_data = self.data.head(10)  # 只显示前10行
        model = DataTableModel(preview_data)
        self.table_view.setModel(model)
        
        # 调整列宽
        self.table_view.resizeColumnsToContents()
        
        # 显示表格
        self.table_view.show()
    
    def generate_charts(self):
        # 获取选中的列
        selected_column = self.columns_combo.currentText()
        
        if not selected_column:
            QMessageBox.warning(self, "警告", "请选择一列进行可视化")
            return
        
        selected_columns = [selected_column]
        
        # 获取选中的图表类型
        chart_type = self.chart_type_combo.currentText()
        
        # 创建并启动数据处理线程
        self.thread = DataProcessThread(self.current_file, selected_columns, self.html_dir, chart_type)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.finished_signal.connect(self.show_results)
        self.thread.error_signal.connect(self.show_error)
        
        # 禁用生成按钮
        self.generate_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # 启动线程
        self.thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def show_results(self, html_files):
        # 重新启用生成按钮
        self.generate_button.setEnabled(True)
        # 重置进度条
        self.progress_bar.setValue(0)
        
        if not html_files:
            QMessageBox.warning(self, "警告", "没有生成任何图表")
            return
        
        # 显示成功消息并询问是否打开文件
        reply = QMessageBox.question(
            self, "成功", 
            f"已生成 {len(html_files)} 个图表，保存在 {self.html_dir} 目录\n\n是否在浏览器中打开查看？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 在系统默认浏览器中打开第一个HTML文件
            if html_files and os.path.exists(html_files[0]):
                webbrowser.open(f'file://{html_files[0]}')
                
            # 如果有多个文件，询问是否打开HTML目录
            if len(html_files) > 1:
                reply2 = QMessageBox.question(
                    self, "打开目录", 
                    f"还有 {len(html_files)-1} 个图表文件，是否打开HTML目录查看所有文件？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply2 == QMessageBox.StandardButton.Yes:
                    webbrowser.open(f'file://{self.html_dir}')
    
    def show_error(self, error_message):
        # 重新启用生成按钮
        self.generate_button.setEnabled(True)
        
        # 显示错误消息
        QMessageBox.critical(self, "错误", error_message)
    
    def open_html_dir(self):
        # 打开HTML目录
        if os.path.exists(self.html_dir):
            webbrowser.open(f'file://{self.html_dir}')
        else:
            QMessageBox.warning(self, "警告", "HTML目录不存在")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and len(urls) > 0:
            file_path = urls[0].toLocalFile()
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.csv', '.xlsx', '.xls']:
                self.load_file(file_path)

# 应用程序入口
def main():
    app = QApplication(sys.argv)
    window = ParameterChartApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

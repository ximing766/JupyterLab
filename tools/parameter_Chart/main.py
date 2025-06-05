import sys
import os
import pandas as pd
import numpy as np
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QWidget, QFileDialog, QLabel, QListWidget, QListWidgetItem,
                             QProgressBar, QMessageBox, QSplitter, QFrame, QTableView,
                             QGroupBox, QComboBox, QTabWidget, QTextEdit, QSizePolicy, QStyleFactory, QAbstractItemView, QHeaderView,
                             QDialog, QFormLayout, QSpinBox, QCheckBox, QColorDialog, QSlider)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QAbstractTableModel
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QColor, QFont

import pyecharts.options as opts
from pyecharts.charts import Line, Boxplot, Bar, Scatter
from pyecharts.globals import ThemeType

# Data table model
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

# Data processing thread
class DataProcessThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)
    
    def __init__(self, file_path, selected_columns, html_dir, chart_type, style_config):
        super().__init__()
        self.file_path = file_path
        self.selected_columns = selected_columns
        self.html_dir = html_dir
        self.chart_type = chart_type
        self.style_config = style_config
        
    def run(self):
        try:
            # Read data based on file extension
            file_ext = os.path.splitext(self.file_path)[1].lower()
            if file_ext == '.csv':
                data = pd.read_csv(self.file_path, sep=',', header=0)
            elif file_ext in ['.xlsx', '.xls']:
                data = pd.read_excel(self.file_path)
            else:
                self.error_signal.emit(f"Unsupported file format: {file_ext}")
                return
                
            # Check if data is empty
            if data.empty:
                self.error_signal.emit("Data is empty")
                return
                
            # Ensure HTML directory exists
            os.makedirs(self.html_dir, exist_ok=True)
            
            # List of generated HTML file paths
            html_files = []
            
            # Process each selected column
            total_columns = len(self.selected_columns)
            
            # Initial progress
            self.progress_signal.emit(5)
            self.msleep(200)  # Delay 200ms
            
            for i, column in enumerate(self.selected_columns):
                if column not in data.columns:
                    continue
                    
                # Progress for current column (5% to 85%)
                start_progress = int(5 + (i / total_columns) * 80)
                self.progress_signal.emit(start_progress)
                self.msleep(300)  # Delay 300ms
                
                # Create chart based on chart type
                if self.chart_type == "Line Chart":
                    html_path = self.create_line_chart(data, column)
                elif self.chart_type == "Bar Chart":
                    html_path = self.create_bar_chart(data, column)
                elif self.chart_type == "Scatter Chart":
                    html_path = self.create_scatter_chart(data, column)
                elif self.chart_type == "Box Chart":
                    html_path = self.create_box_chart(data, column)
                else:
                    html_path = self.create_line_chart(data, column)
                    
                if html_path:
                    html_files.append(html_path)
                
                # Update progress after chart generation
                end_progress = int(5 + ((i + 1) / total_columns) * 80)
                self.progress_signal.emit(end_progress)
                self.msleep(200)  # Delay 200ms
                
            # Final completion progress
            self.progress_signal.emit(95)
            self.msleep(300)
            self.progress_signal.emit(100)
            self.msleep(500)  # Hold for a while after completion
            self.finished_signal.emit(html_files)
            
        except Exception as e:
            self.error_signal.emit(f"Error processing data: {str(e)}")
    
    def create_line_chart(self, data, column):
        try:
            x_data = list(range(len(data)))
            y_data = data[column].tolist()
            
            # Get theme
            theme_map = {
                'MACARONS': ThemeType.MACARONS,
                'INFOGRAPHIC': ThemeType.INFOGRAPHIC,
                'LIGHT': ThemeType.LIGHT,
                'DARK': ThemeType.DARK,
                'ROMANTIC': ThemeType.ROMANTIC,
                'SHINE': ThemeType.SHINE,
                'VINTAGE': ThemeType.VINTAGE
            }
            theme = theme_map.get(self.style_config['theme'], ThemeType.MACARONS)
            
            c = (
                Line(init_opts=opts.InitOpts(
                    width=f"{self.style_config['width']}px", 
                    height=f"{self.style_config['height']}px", 
                    theme=theme,
                    animation_opts=opts.AnimationOpts(animation=self.style_config['animation'])
                ))
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(
                    series_name=column,
                    y_axis=y_data,
                    is_smooth=self.style_config['line_smooth'],
                    areastyle_opts=opts.AreaStyleOpts(opacity=self.style_config['area_opacity']),
                    label_opts=opts.LabelOpts(is_show=self.style_config['show_labels']),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}" if self.style_config['show_title'] else ""),
                    xaxis_opts=opts.AxisOpts(name="Index"),
                    yaxis_opts=opts.AxisOpts(name=column),
                    datazoom_opts=[opts.DataZoomOpts()] if self.style_config['show_datazoom'] else None,
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    toolbox_opts=opts.ToolboxOpts(
                        is_show=self.style_config['show_toolbox'], 
                        feature=opts.ToolBoxFeatureOpts(
                            save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(
                                background_color=self.style_config['background_color'],
                                pixel_ratio=3
                            )
                        )
                    ) if self.style_config['show_toolbox'] else None,
                    visualmap_opts=opts.VisualMapOpts(is_show=self.style_config['show_visualmap']) if self.style_config['show_visualmap'] else None,
                    legend_opts=opts.LegendOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_line.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"Error creating line chart {column}: {str(e)}")
            return None
    
    def create_bar_chart(self, data, column):
        try:
            x_data = list(range(len(data)))
            y_data = data[column].tolist()
            
            # Get theme
            theme_map = {
                'MACARONS': ThemeType.MACARONS,
                'INFOGRAPHIC': ThemeType.INFOGRAPHIC,
                'LIGHT': ThemeType.LIGHT,
                'DARK': ThemeType.DARK,
                'ROMANTIC': ThemeType.ROMANTIC,
                'SHINE': ThemeType.SHINE,
                'VINTAGE': ThemeType.VINTAGE
            }
            theme = theme_map.get(self.style_config['theme'], ThemeType.MACARONS)
            
            c = (
                Bar(init_opts=opts.InitOpts(
                    width=f"{self.style_config['width']}px", 
                    height=f"{self.style_config['height']}px", 
                    theme=theme,
                    animation_opts=opts.AnimationOpts(animation=self.style_config['animation'])
                ))
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(
                    series_name=column, 
                    y_axis=y_data, 
                    label_opts=opts.LabelOpts(is_show=self.style_config['show_labels'])
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}" if self.style_config['show_title'] else ""),
                    xaxis_opts=opts.AxisOpts(name="Index"),
                    yaxis_opts=opts.AxisOpts(name=column),
                    datazoom_opts=[opts.DataZoomOpts()] if self.style_config['show_datazoom'] else None,
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    toolbox_opts=opts.ToolboxOpts(
                        is_show=self.style_config['show_toolbox'], 
                        feature=opts.ToolBoxFeatureOpts(
                            save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(
                                background_color=self.style_config['background_color'],
                                pixel_ratio=3
                            )
                        )
                    ) if self.style_config['show_toolbox'] else None,
                    visualmap_opts=opts.VisualMapOpts(is_show=self.style_config['show_visualmap']) if self.style_config['show_visualmap'] else None,
                    legend_opts=opts.LegendOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_bar.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"Error creating bar chart {column}: {str(e)}")
            return None
    
    def create_scatter_chart(self, data, column):
        try:
            x_data = list(range(len(data)))
            y_data = data[column].tolist()
            scatter_data = list(zip(x_data, y_data))
            
            # Get theme
            theme_map = {
                'MACARONS': ThemeType.MACARONS,
                'INFOGRAPHIC': ThemeType.INFOGRAPHIC,
                'LIGHT': ThemeType.LIGHT,
                'DARK': ThemeType.DARK,
                'ROMANTIC': ThemeType.ROMANTIC,
                'SHINE': ThemeType.SHINE,
                'VINTAGE': ThemeType.VINTAGE
            }
            theme = theme_map.get(self.style_config['theme'], ThemeType.MACARONS)
            
            c = (
                Scatter(init_opts=opts.InitOpts(
                    width=f"{self.style_config['width']}px", 
                    height=f"{self.style_config['height']}px", 
                    theme=theme,
                    animation_opts=opts.AnimationOpts(animation=self.style_config['animation'])
                ))
                .add_xaxis(xaxis_data=x_data)
                .add_yaxis(
                    series_name=column, 
                    y_axis=y_data, 
                    label_opts=opts.LabelOpts(is_show=self.style_config['show_labels'])
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}" if self.style_config['show_title'] else ""),
                    xaxis_opts=opts.AxisOpts(name="Index"),
                    yaxis_opts=opts.AxisOpts(name=column),
                    datazoom_opts=[opts.DataZoomOpts()] if self.style_config['show_datazoom'] else None,
                    tooltip_opts=opts.TooltipOpts(trigger="item"),
                    toolbox_opts=opts.ToolboxOpts(
                        is_show=self.style_config['show_toolbox'], 
                        feature=opts.ToolBoxFeatureOpts(
                            save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(
                                background_color=self.style_config['background_color'],
                                pixel_ratio=3
                            )
                        )
                    ) if self.style_config['show_toolbox'] else None,
                    visualmap_opts=opts.VisualMapOpts(is_show=self.style_config['show_visualmap']) if self.style_config['show_visualmap'] else None,
                    legend_opts=opts.LegendOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_scatter.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"Error creating scatter chart {column}: {str(e)}")
            return None
    
    def create_box_chart(self, data, column):
        try:
            y_data = data[column].tolist()
            
            # Get theme
            theme_map = {
                'MACARONS': ThemeType.MACARONS,
                'INFOGRAPHIC': ThemeType.INFOGRAPHIC,
                'LIGHT': ThemeType.LIGHT,
                'DARK': ThemeType.DARK,
                'ROMANTIC': ThemeType.ROMANTIC,
                'SHINE': ThemeType.SHINE,
                'VINTAGE': ThemeType.VINTAGE
            }
            theme = theme_map.get(self.style_config['theme'], ThemeType.MACARONS)
            
            c = (
                Boxplot(init_opts=opts.InitOpts(
                    width=f"{self.style_config['width']}px", 
                    height=f"{self.style_config['height']}px", 
                    theme=theme,
                    animation_opts=opts.AnimationOpts(animation=self.style_config['animation'])
                ))
                .add_xaxis([column])
                .add_yaxis(
                    series_name=column, 
                    y_axis=[y_data], 
                    label_opts=opts.LabelOpts(is_show=self.style_config['show_labels'])
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{column}" if self.style_config['show_title'] else ""),
                    tooltip_opts=opts.TooltipOpts(trigger="item"),
                    toolbox_opts=opts.ToolboxOpts(
                        is_show=self.style_config['show_toolbox'], 
                        feature=opts.ToolBoxFeatureOpts(
                            save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(
                                background_color=self.style_config['background_color'],
                                pixel_ratio=3
                            )
                        )
                    ) if self.style_config['show_toolbox'] else None,
                    visualmap_opts=opts.VisualMapOpts(is_show=self.style_config['show_visualmap']) if self.style_config['show_visualmap'] else None,
                    legend_opts=opts.LegendOpts(is_show=True),
                )
            )
            
            file_name = f"{column}_box.html"
            html_path = os.path.join(self.html_dir, file_name)
            c.render(html_path)
            return html_path
        except Exception as e:
            self.error_signal.emit(f"Error creating box chart {column}: {str(e)}")
            return None

# Style configuration dialog
class StyleConfigDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config.copy() if config else {}
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Style Config")
        self.setFixedSize(400, 500)
        self.setModal(True)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Chart size settings
        size_group = QGroupBox("Chart Size")
        size_layout = QFormLayout()
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(400, 1920)
        self.width_spin.setValue(self.config.get('width', 800))
        self.width_spin.setSuffix(" px")
        self.width_spin.setSingleStep(50)
        size_layout.addRow("Width:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(300, 1080)
        self.height_spin.setValue(self.config.get('height', 500))
        self.height_spin.setSuffix(" px")
        self.height_spin.setSingleStep(50)
        size_layout.addRow("Height:", self.height_spin)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Theme settings
        theme_group = QGroupBox("Theme Style")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        themes = ['MACARONS', 'INFOGRAPHIC', 'LIGHT', 'DARK', 'ROMANTIC', 'SHINE', 'VINTAGE']
        self.theme_combo.addItems(themes)
        current_theme = self.config.get('theme', 'MACARONS')
        if current_theme in themes:
            self.theme_combo.setCurrentText(current_theme)
        theme_layout.addRow("Theme:", self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Display components settings
        display_group = QGroupBox("Display Components")
        display_layout = QFormLayout()
        
        self.show_title_check = QCheckBox()
        self.show_title_check.setChecked(self.config.get('show_title', True))
        display_layout.addRow("Show Title:", self.show_title_check)
        
        self.show_toolbox_check = QCheckBox()
        self.show_toolbox_check.setChecked(self.config.get('show_toolbox', True))
        display_layout.addRow("Show Toolbox:", self.show_toolbox_check)
        
        self.show_datazoom_check = QCheckBox()
        self.show_datazoom_check.setChecked(self.config.get('show_datazoom', True))
        display_layout.addRow("Show Zoom:", self.show_datazoom_check)
        
        self.show_visualmap_check = QCheckBox()
        self.show_visualmap_check.setChecked(self.config.get('show_visualmap', True))
        display_layout.addRow("Show Visual Map:", self.show_visualmap_check)
        
        self.show_labels_check = QCheckBox()
        self.show_labels_check.setChecked(self.config.get('show_labels', False))
        display_layout.addRow("Show Labels:", self.show_labels_check)
        
        self.animation_check = QCheckBox()
        self.animation_check.setChecked(self.config.get('animation', True))
        display_layout.addRow("Enable Animation:", self.animation_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Line chart special settings
        line_group = QGroupBox("Line Chart Settings")
        line_layout = QFormLayout()
        
        self.line_smooth_check = QCheckBox()
        self.line_smooth_check.setChecked(self.config.get('line_smooth', True))
        line_layout.addRow("Smooth Curve:", self.line_smooth_check)
        
        self.area_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.area_opacity_slider.setRange(0, 100)
        self.area_opacity_slider.setValue(int(self.config.get('area_opacity', 0.3) * 100))
        self.area_opacity_label = QLabel(f"{self.area_opacity_slider.value()}%")
        self.area_opacity_slider.valueChanged.connect(
            lambda v: self.area_opacity_label.setText(f"{v}%")
        )
        
        area_layout = QHBoxLayout()
        area_layout.addWidget(self.area_opacity_slider)
        area_layout.addWidget(self.area_opacity_label)
        area_widget = QWidget()
        area_widget.setLayout(area_layout)
        line_layout.addRow("Area Opacity:", area_widget)
        
        line_group.setLayout(line_layout)
        layout.addWidget(line_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_config)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def get_config(self):
        """Get current configuration"""
        return {
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'theme': self.theme_combo.currentText(),
            'show_title': self.show_title_check.isChecked(),
            'show_toolbox': self.show_toolbox_check.isChecked(),
            'show_datazoom': self.show_datazoom_check.isChecked(),
            'show_visualmap': self.show_visualmap_check.isChecked(),
            'line_smooth': self.line_smooth_check.isChecked(),
            'area_opacity': self.area_opacity_slider.value() / 100.0,
            'show_labels': self.show_labels_check.isChecked(),
            'animation': self.animation_check.isChecked(),
            'background_color': 'white'
        }
        
    def reset_config(self):
        """Reset to default configuration"""
        self.width_spin.setValue(800)
        self.height_spin.setValue(500)
        self.theme_combo.setCurrentText('MACARONS')
        self.show_title_check.setChecked(True)
        self.show_toolbox_check.setChecked(True)
        self.show_datazoom_check.setChecked(True)
        self.show_visualmap_check.setChecked(True)
        self.line_smooth_check.setChecked(True)
        self.area_opacity_slider.setValue(30)
        self.show_labels_check.setChecked(False)
        self.animation_check.setChecked(True)

# Main application class
class ParameterChartApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_file = None
        self.data = None
        self.html_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HTML")
        os.makedirs(self.html_dir, exist_ok=True)
        
        # Default style configuration values
        self.style_config = {
            'width': 800,
            'height': 500,
            'theme': 'MACARONS',
            'show_title': True,
            'show_toolbox': True,
            'show_datazoom': True,
            'show_visualmap': True,
            'line_smooth': True,
            'area_opacity': 0.3,
            'show_labels': False,
            'animation': True,
            'background_color': 'white'
        }
        
    def init_ui(self):
        # Set window properties and styles
        self.setWindowTitle("Parameter Chart Generator")
        self.setGeometry(100, 100, 630, 350)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
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
                background: #acc8e8;
                border: 2px solid #acc8e8;
                color: black;
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
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a0a0a0, stop:1 #808080);
                border: 2px solid #808080;
                color: #f0f0f0;
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
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # File selection area (minimalist compact layout)
        file_group = QGroupBox("File Selection")
        file_group.setMaximumHeight(60)  # Limit maximum height
        file_layout = QHBoxLayout(file_group)
        file_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        file_layout.setSpacing(8)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        
        self.browse_button = QPushButton("open")
        self.browse_button.setFixedSize(50, 20)  # Fixed button size
        self.browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.browse_button, 0)
        
        # Data preview area (core position, increased height)
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        
        self.info_label = QLabel("Please select a file to view data information")
        self.info_label.setStyleSheet("color: #6c757d; font-style: italic; font-size: 11px;")
        preview_layout.addWidget(self.info_label)
        
        self.table_view = QTableView()
        self.table_view.setMinimumHeight(250)  # Increase table minimum height
        self.table_view.hide()
        # Allow column selection by clicking table header
        self.table_view.horizontalHeader().setSectionsClickable(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectColumns)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        preview_layout.addWidget(self.table_view)
        
        # Control area (compact layout)
        control_group = QGroupBox("Chart Settings")
        control_group.setMaximumHeight(80)  # Limit control area height
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(8, 5, 8, 5)
        control_layout.setSpacing(5)
        
        # Column selection and chart type on the same row
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(10)
        
        # Remove QListWidget related code
        # settings_layout.addWidget(QLabel("Select columns:"))
        # self.columns_list_widget = QListWidget()
        # self.columns_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        # self.columns_list_widget.setMinimumWidth(120)
        # self.columns_list_widget.setMaximumHeight(50) # Limit height to fit original layout
        # settings_layout.addWidget(self.columns_list_widget)
        
        settings_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Line Chart", "Bar Chart", "Scatter Chart", "Box Chart"])
        self.chart_type_combo.setMinimumWidth(100)
        settings_layout.addWidget(self.chart_type_combo)
        
        # Style settings button
        self.style_button = QPushButton("🎨")
        self.style_button.clicked.connect(self.open_style_dialog)
        self.style_button.setMinimumWidth(80)
        settings_layout.addWidget(self.style_button)
        
        settings_layout.addStretch()
        control_layout.addLayout(settings_layout)
        
        # Generate button and progress bar
        action_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("Generate Charts")
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
        
        # Add to main layout, set stretch factors
        main_layout.addWidget(file_group, 0)  # File selection area no stretch
        main_layout.addWidget(preview_group, 1)  # Preview area takes main space
        main_layout.addWidget(control_group, 0)  # Control area no stretch
        
        # Create central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Set drag and drop support
        self.setAcceptDrops(True)
        
    def open_style_dialog(self):
        """Open style configuration dialog"""
        dialog = StyleConfigDialog(self, self.style_config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.style_config = dialog.get_config()
            QMessageBox.information(self, "Info", "Style configuration updated!")
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV or Excel file", "", "Data files (*.csv *.xlsx *.xls)"
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        try:
            # Read data based on file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                self.data = pd.read_csv(file_path, sep=',', header=0)
            elif file_ext in ['.xlsx', '.xls']:
                self.data = pd.read_excel(file_path)
            else:
                QMessageBox.warning(self, "Error", f"Unsupported file format: {file_ext}")
                return
            
            # Update UI
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            
            # Clear and populate column selection list - no longer needed as we select from header
            # self.columns_list_widget.clear()
            # self.columns_list_widget.addItems(self.data.columns)
            
            # Enable generate button
            self.generate_button.setEnabled(True)
            
            # Show data preview
            self.show_data_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def show_data_preview(self):
        if self.data is None:
            return
            
        # Update info label
        info_text = f"File: {os.path.basename(self.current_file)} | "
        info_text += f"Rows: {len(self.data)} | "
        info_text += f"Columns: {len(self.data.columns)}"
        self.info_label.setText(info_text)
        self.info_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        
        # Create table model and set to view
        preview_data = self.data.head(10)  # Show only first 10 rows
        model = DataTableModel(preview_data)
        self.table_view.setModel(model)
        
        # Adjust column width
        self.table_view.resizeColumnsToContents()
        
        # Show table
        self.table_view.show()
    
    def generate_charts(self):
        # Get columns selected through table header
        selected_column_indices = sorted(list(set(index.column() for index in self.table_view.selectedIndexes())))
        
        if not selected_column_indices:
            QMessageBox.warning(self, "Warning", "Please select at least one column in the data preview table for visualization")
            return
        
        selected_columns = [self.data.columns[i] for i in selected_column_indices]
        
        # Get selected chart type
        chart_type = self.chart_type_combo.currentText()
        
        # Create and start data processing thread
        self.thread = DataProcessThread(self.current_file, selected_columns, self.html_dir, chart_type, self.style_config)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.finished_signal.connect(self.show_results)
        self.thread.error_signal.connect(self.show_error)
        
        # Disable generate button
        self.generate_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start thread
        self.thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def show_results(self, html_files):
        # Re-enable generate button
        self.generate_button.setEnabled(True)
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        if not html_files:
            QMessageBox.warning(self, "Warning", "No charts were generated")
            return
        
        # Show success message and ask whether to open file
        reply = QMessageBox.question(
            self, "Success", 
            f"Generated {len(html_files)} charts, saved in {self.html_dir} directory\n\nOpen in browser to view?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Open first HTML file in system default browser
            if html_files and os.path.exists(html_files[0]):
                webbrowser.open(f'file://{html_files[0]}')
                
            # If multiple files, ask whether to open HTML directory
            if len(html_files) > 1:
                reply2 = QMessageBox.question(
                    self, "Open Directory", 
                    f"There are {len(html_files)-1} more chart files. Open HTML directory to view all files?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply2 == QMessageBox.StandardButton.Yes:
                    webbrowser.open(f'file://{self.html_dir}')
    
    def show_error(self, error_message):
        # Re-enable generate button
        self.generate_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Error", error_message)
    
    def open_html_dir(self):
        # Open HTML directory
        if os.path.exists(self.html_dir):
            webbrowser.open(f'file://{self.html_dir}')
        else:
            QMessageBox.warning(self, "Warning", "HTML directory does not exist")
    
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

# Application entry point
def main():
    app = QApplication(sys.argv)
    window = ParameterChartApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

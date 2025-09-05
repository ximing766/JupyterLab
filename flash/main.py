import sys
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QTextEdit, QMessageBox, QProgressBar, QFrame, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings, QEvent
from PyQt6.QtGui import QFont, QIcon
import serial.tools.list_ports

class FlashWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, command_args):
        super().__init__()
        self.command_args = command_args
    
    def run(self):
        try:
            # 添加-Y参数强制操作，避免确认对话框
            command_args = self.command_args + ['-Y']
            
            # 设置环境变量，确保烧录工具正常运行
            env = {
                'SYSTEMROOT': os.environ.get('SYSTEMROOT', 'C:\\Windows'),
                'PATHEXT': os.environ.get('PATHEXT', '.COM;.EXE;.BAT;.CMD'),
                'TERM': 'vt100',
                'LINES': '24',
                'COLUMNS': '80',
                'NO_COLOR': '1'
            }

            # 使用 subprocess.CREATE_NEW_CONSOLE 创建一个新控制台窗口来运行烧录工具
            # 这为 ncurses 提供了必要的环境，同时 -Y 参数可以跳过确认
            subprocess.run(
                command_args,
                check=True,
                timeout=120,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.finished.emit(True, "烧录完成")
            
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "烧录超时，请检查设备连接")
        except subprocess.CalledProcessError as e:
            error_msg = f"烧录失败(返回码 {e.returncode})。请检查设备连接和固件。"
            self.finished.emit(False, error_msg)
        except Exception as e:
            self.finished.emit(False, f"未知错误: {str(e)}")

class FlashTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DK6')
        self.settings = QSettings('DK6FlashTool', 'Settings')
        
        # 固定窗口大小和位置到居中靠右
        screen = QApplication.primaryScreen().geometry()
        width, height = 350, 220  # 优化高度，既紧凑又美观
        x = screen.width() - width - 20  # 20px margin from right edge
        y = (screen.height() - height) // 2  # 垂直居中
        self.setGeometry(x, y, width, height)
        self.setFixedSize(width, height)  # 完全固定窗口大小
        
        # 置顶窗口
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # 设置透明度
        self.setWindowOpacity(1.0)  # 默认90%透明度
        
        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(__file__), 'DK6.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 紧凑现代深色主题
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                font-size: 12px;
                color: #e0e0e0;
                margin: 2px 0;
                font-weight: 500;
            }
            QLabel#title {
                font-size: 15px;
                font-weight: bold;
                color: #ffffff;
                margin: 8px 0;
            }
            QPushButton {
                background-color: #2d7d87;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #3a9ca8;
            }
            QPushButton:pressed {
                background-color: #1a5c65;
            }
            QPushButton#flash_btn {
                background-color: #4a90e2;
                font-size: 13px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton#flash_btn:hover {
                background-color: #357abd;
            }
            QPushButton#flash_btn:pressed {
                background-color: #2968a3;
            }
            QPushButton#browse_btn {
                background-color: #5a6268;
                padding: 6px 12px;
                font-size: 11px;
            }
            QPushButton#browse_btn:hover {
                background-color: #7a8288;
            }
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #495057;
                border-radius: 3px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-size: 12px;
                min-height: 18px;
            }
            QLineEdit:focus {
                border-color: #2d7d87;
            }
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #5a6268;
                border-radius: 3px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-size: 12px;
                min-height: 18px;
            }
            QComboBox:hover {
                border-color: #2d7d87;
                background-color: #404040;
            }
            QComboBox:focus {
                border-color: #3a9ca8;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #5a6268;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #5a6268;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #e0e0e0;
                width: 0px;
                height: 0px;
                margin: 0;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #2d7d87;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #2d7d87;
                border: 1px solid #5a6268;
                font-size: 12px;
            }

            QFrame#card {
                background-color: #2d2d2d;
                border: 1px solid #5a6268;
                border-radius: 6px;
                margin: 4px;
                padding: 12px;
            }
            QProgressBar {
                border: 1px solid #5a6268;
                border-radius: 3px;
                text-align: center;
                font-weight: bold;
                background-color: #2d2d2d;
                color: #ffffff;
                font-size: 11px;
                max-height: 18px;
            }
            QProgressBar::chunk {
                background-color: #2d7d87;
                border-radius: 2px;
            }
        """)

        # 初始化变量
        self.flash_worker = None
        self.selected_file = None
        
        # 加载最近使用文件列表
        self.recent_files = []
        recent_files_str = self.settings.value('recent_files', '')
        if recent_files_str:
            self.recent_files = recent_files_str.split('|')
            self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
        
        # 设置定时器自动刷新COM口
        self.com_timer = QTimer()
        self.com_timer.timeout.connect(self.refresh_com_ports)
        self.com_timer.start(2000)  # 每2秒刷新一次
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # 第一排：串口和波特率（去掉标签）
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # 串口选择（左侧）
        self.com_combo = QComboBox()
        self.com_combo.setMinimumWidth(120)
        self.com_combo.setPlaceholderText('选择串口')
        self.refresh_com_ports()
        
        # 波特率选择（右侧）- 固定为1000000
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['3000000', '1000000', '115200', '460800'])
        self.baud_combo.setCurrentText('1000000')
        self.baud_combo.setMinimumWidth(80)
        
        top_row.addWidget(self.com_combo, 1)
        top_row.addWidget(self.baud_combo)
        main_layout.addLayout(top_row)
        
        # 第二排：文件选择
        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        self.file_combo = QComboBox()
        self.file_combo.setEditable(False)
        self.update_recent_files_combo()
        self.file_combo.currentTextChanged.connect(self.on_file_selected)

        # 使用图标按钮替换文字
        browse_btn = QPushButton('📁')
        browse_btn.setObjectName('browse_btn')
        browse_btn.setMaximumWidth(35)
        browse_btn.setMaximumHeight(28)
        browse_btn.clicked.connect(self.browse_file)

        file_row.addWidget(self.file_combo, 1)
        file_row.addWidget(browse_btn)
        main_layout.addLayout(file_row)
        
        # 烧录按钮
        flash_btn = QPushButton('Flash')
        flash_btn.setObjectName('flash_btn')
        flash_btn.clicked.connect(self.flash_firmware)
        main_layout.addWidget(flash_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 恢复上次文件
        last_file = self.settings.value("last_file", "")
        if last_file and os.path.exists(last_file):
            self.select_file(last_file)
        
        # 透明度设置
        self.setWindowOpacity(1.0)  # 默认90%透明度
        
        # 保存原始透明度设置
        self.normal_opacity = 1.0
        self.inactive_opacity = 0.6
        
        # 启用拖拽支持
        self.setAcceptDrops(True)
        


    def refresh_com_ports(self):
        current_device = self.com_combo.currentData()
        self.com_combo.clear()
        
        ports = serial.tools.list_ports.comports()
        usb_port_index = -1

        for i, port in enumerate(ports):
            self.com_combo.addItem(f"{port.device} - {port.description}", port.device)
            if "USB Serial Port" in port.description and usb_port_index == -1:
                usb_port_index = i

        # 如果找到了USB口，则自动选择
        if usb_port_index != -1:
            self.com_combo.setCurrentIndex(usb_port_index)
        # 否则，尝试恢复之前的选择
        elif current_device:
            for i in range(self.com_combo.count()):
                if self.com_combo.itemData(i) == current_device:
                    self.com_combo.setCurrentIndex(i)
                    break

    def browse_file(self):
        last_dir = self.settings.value("last_directory", r"E:\Work\UWB\Code")
        file_path, _ = QFileDialog.getOpenFileName(self, '选择固件文件', last_dir, 'BIN Files (*.bin);;HEX Files (*.hex)')
        if file_path:
            self.select_file(file_path)

    def select_file(self, file_path):
        """选择文件并更新最近使用列表"""
        if os.path.exists(file_path):
            self.selected_file = file_path
            
            # 更新最近文件列表
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            self.recent_files.insert(0, file_path)
            self.recent_files = self.recent_files[:5]  # 只保留最近5个
            
            # 保存到设置
            self.settings.setValue('recent_files', '|'.join(self.recent_files))
            self.settings.setValue("last_directory", os.path.dirname(file_path))
            self.settings.setValue("last_file", file_path)
            
            # 更新UI
            self.update_recent_files_combo()

    def on_file_selected(self, text):
        """文件选择事件处理"""
        if not text or text == '选择或拖拽固件文件':
            self.selected_file = None
            return

        # Find the full path from recent files list
        for file_path in self.recent_files:
            if os.path.basename(file_path) == text:
                self.selected_file = file_path
                self.settings.setValue("last_file", file_path)
                return # Found

    def update_recent_files_combo(self):
        """更新最近文件下拉框"""
        self.file_combo.blockSignals(True)
        
        selected_path = self.selected_file
        
        self.file_combo.clear()
        
        # 添加占位符
        if not self.recent_files or not selected_path:
            self.file_combo.addItem('选择或拖拽固件文件')
        
        for file_path in self.recent_files:
            if os.path.exists(file_path):
                self.file_combo.addItem(os.path.basename(file_path))
        
        if selected_path and os.path.exists(selected_path):
            base_name = os.path.basename(selected_path)
            index = self.file_combo.findText(base_name)
            if index != -1:
                self.file_combo.setCurrentIndex(index)
        else:
            self.file_combo.setCurrentIndex(0)  # 选择占位符
            
        self.file_combo.blockSignals(False)

    def flash_firmware(self):
        com_data = self.com_combo.currentData()
        
        if not com_data:
            QMessageBox.warning(self, '错误', '请选择串口')
            return
        
        if not self.selected_file or not os.path.exists(self.selected_file):
            QMessageBox.warning(self, '错误', '请选择有效固件文件')
            return
        
        # 检查串口占用
        try:
            import serial
            test_serial = serial.Serial(
                port=com_data,
                baudrate=int(self.baud_combo.currentText()),
                timeout=0.1
            )
            test_serial.close()
        except serial.SerialException as e:
            QMessageBox.warning(self, '串口占用', f'串口 {com_data} 被占用或不可用！\n\n错误信息：{str(e)}')
            return
        except Exception as e:
            QMessageBox.warning(self, '串口错误', f'串口 {com_data} 检查失败：{str(e)}')
            return
        
        # 准备烧录
        self.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # 确定烧录工具路径
        programmer_path = 'C:\\NXP\\DK6ProductionFlashProgrammer\\DK6Programmer.exe'
        if not os.path.exists(programmer_path):
            QMessageBox.warning(self, '错误', '未找到DK6Programmer.exe')
            self.setEnabled(True)
            self.progress_bar.setVisible(False)
            return
        
        # 启动烧录
        command_args = [programmer_path, '-s', com_data, '-P', self.baud_combo.currentText(), '-p', self.selected_file]
        self.flash_worker = FlashWorker(command_args)
        self.flash_worker.finished.connect(self.on_flash_finished)
        self.flash_worker.start()
    

    
    def on_flash_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.setEnabled(True)
        
        if success:
            print("flash OK!")
        else:
            QMessageBox.critical(self, '失败', f'烧录失败: {message}')
        
        self.flash_worker = None
    


    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self.setWindowOpacity(self.normal_opacity)
            else:
                self.setWindowOpacity(self.inactive_opacity)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith(('.bin', '.hex', '.elf')):
                self.select_file(file_path)
                break
        super().changeEvent(event)
    
    def closeEvent(self, event):
        # 停止定时器
        if hasattr(self, 'com_timer'):
            self.com_timer.stop()
        
        # 停止工作线程
        if self.flash_worker and self.flash_worker.isRunning():
            self.flash_worker.terminate()
            self.flash_worker.wait()
        
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用程序标识，这对Windows pin到桌面功能很重要
    app.setApplicationName("DK6 Flash Tool")
    app.setApplicationDisplayName("DK6 Flash Tool")
    app.setOrganizationName("DK6 Tools")
    app.setOrganizationDomain("dk6tools.com")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用程序ID (Windows 7+)
    if hasattr(app, 'setApplicationId'):
        app.setApplicationId("DK6Tools.DK6FlashTool.1.0")
    
    window = FlashTool()
    window.show()
    sys.exit(app.exec())
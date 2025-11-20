import sys
import subprocess
import os
import time
import struct
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox, QProgressBar, QFrame, QGridLayout, QDialog, QFormLayout, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings, QEvent
from PyQt6.QtGui import QIcon, QClipboard

# 常量定义 
RESET_MCU            = 0xCA  # 复位MCU命令
FIRMWARE_ERASE       = 0xCB  # 固件擦除命令
FIRMWARE_PROGRAM     = 0xCC  # 固件写入命令
FIRMWARE_READ_HEADER = 0xCD  # 读取固件头命令
SEMS_LITE_COMMAND    = 0xCE  # 获取UUID命令


# Flash参数
W25Q32JV_PAGE_SIZE      = 256       # 页大小
W25Q32JV_SECTOR_SIZE    = 4096      # 扇区大小 4KB
W25Q32JV_BLOCK_64K_SIZE = 65536     # 64KB块大小
W25Q32JV_FLASH_SIZE     = 4 * 1024 * 1024  # 总大小 4MB

# OTA传输配置
OTA_PAGES_PER_TRANSFER = 3  # 每次传输的页数，默认3页(768字节)
OTA_TRANSFER_SIZE = W25Q32JV_PAGE_SIZE * OTA_PAGES_PER_TRANSFER  # 传输大小768字节

# 固件相关常量
FIRMWARE_MAGIC = 0x12345678
EXTERNAL_FLASH_APP_START = 0x00280000
SR150_FLASH_START_ADDR = 0x00300100  # SR150固件写入地址
MAX_FIRMWARE_SIZE = 1024 * 1024  # 1MB

class UUIDDisplayDialog(QDialog):
    def __init__(self, uuid_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle('SE051W UUID')
        self.setModal(True)
        self.resize(300, 100)
        
        layout = QVBoxLayout(self)
        
        label = QLabel('设备UUID:')
        layout.addWidget(label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(uuid_text)
        self.text_edit.setReadOnly(True)
        self.text_edit.selectAll()  # 默认选中所有文本
        layout.addWidget(self.text_edit)
        
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        QMessageBox.information(self, '成功', 'UUID已复制到剪贴板')

class FlashWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, command_args):
        super().__init__()
        self.command_args = command_args
    
    def run(self):
        try:
            command_args = self.command_args + ['-Y']
            env = {
                'SYSTEMROOT': os.environ.get('SYSTEMROOT', 'C:\\Windows'),
                'PATHEXT': os.environ.get('PATHEXT', '.COM;.EXE;.BAT;.CMD'),
                'TERM': 'vt100',
                'LINES': '24',
                'COLUMNS': '80',
                'NO_COLOR': '1'
            }
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

class OTAWorker(QThread):
    # Progress and status signals
    progress_updated = pyqtSignal(int)  # Progress value (0-100)
    status_updated = pyqtSignal(str)    # Status message
    finished = pyqtSignal(bool, str)    # Success flag and message
    
    def __init__(self, operation_type, com_data, baud_rate, firmware_path=None, parent_tool=None):
        super().__init__()
        self.operation_type = operation_type  # 'ota_flash' or 'sr150_flash'
        self.com_data = com_data
        self.baud_rate = baud_rate
        self.firmware_path = firmware_path
        self.parent_tool = parent_tool  # Reference to FlashTool instance
        self.serial_conn = None
        
    def run(self):
        try:
            if self.operation_type == 'ota_flash':
                self._execute_ota_flash()
            elif self.operation_type == 'sr150_flash':
                self._execute_sr150_flash()
            else:
                self.finished.emit(False, f"未知操作类型: {self.operation_type}")
        except Exception as e:
            self.finished.emit(False, f"操作失败: {str(e)}")
        finally:
            # Clean up serial connection
            if hasattr(self, 'parent_tool') and self.parent_tool and hasattr(self.parent_tool, 'serial_conn'):
                if self.parent_tool.serial_conn and self.parent_tool.serial_conn.is_open:
                    self.parent_tool.serial_conn.close()
                    self.parent_tool.serial_conn = None
    
    def _execute_ota_flash(self):
        """Execute OTA flash operation in thread"""
        self.status_updated.emit("准备OTA固件数据...")
        
        # Prepare firmware data
        firmware_result = self.parent_tool.prepare_firmware_data()
        if not firmware_result:
            self.finished.emit(False, "固件数据准备失败")
            return
            
        firmware_data, firmware_header, complete_firmware = firmware_result
        firmware_size = len(firmware_data)
        total_size = len(complete_firmware)
        start_addr = EXTERNAL_FLASH_APP_START
        
        # Record OTA start time
        ota_start_time = time.time()
        
        # Calculate operations
        blocks_to_erase = (total_size + W25Q32JV_BLOCK_64K_SIZE - 1) // W25Q32JV_BLOCK_64K_SIZE
        pages_to_program = (total_size + W25Q32JV_PAGE_SIZE - 1) // W25Q32JV_PAGE_SIZE
        total_operations = blocks_to_erase + pages_to_program
        
        # Setup serial connection
        current_progress = self._setup_serial_connection(total_operations)
        
        self.status_updated.emit(f"开始OTA烧录: {total_size} 字节")
        
        # Phase 1: Erase blocks
        current_progress = self._execute_erase_phase(start_addr, blocks_to_erase, current_progress)
        
        # Phase 2: Program pages
        current_progress = self._execute_program_phase(start_addr, complete_firmware, total_size, pages_to_program, current_progress)
        
        # Calculate duration
        ota_end_time = time.time()
        ota_duration = ota_end_time - ota_start_time
        
        # Format duration
        if ota_duration >= 60:
            minutes = int(ota_duration // 60)
            seconds = ota_duration % 60
            duration_str = f"{minutes}分{seconds:.1f}秒"
        else:
            duration_str = f"{ota_duration:.2f}秒"
        
        # Phase 3: Verification
        verification_msg = self._execute_verification_phase(start_addr, firmware_data, firmware_size, duration_str)
        
        success_msg = (f'固件烧录完成！{verification_msg}\n\n'
                      f'文件: {os.path.basename(self.firmware_path)}\n'
                      f'大小: {firmware_size} 字节\n'
                      f'地址范围: 0x{start_addr:08X} - 0x{start_addr + firmware_size - 1:08X}\n'
                      f'耗时: {duration_str}\n\n')
        
        self.finished.emit(True, success_msg)
    
    def _setup_serial_connection(self, total_operations):
        """Setup serial connection and initialize progress"""
        self.parent_tool.serial_conn = serial.Serial(
            port=self.com_data,
            baudrate=self.baud_rate,
            timeout=2.0
        )
        return 0
    
    def _execute_erase_phase(self, start_addr, blocks_to_erase, current_progress):
        """Execute erase phase in thread"""
        self.status_updated.emit("正在擦除Flash块...")
        
        packet = self.parent_tool.build_protocol_packet(FIRMWARE_ERASE, start_addr, blocks_to_erase)
        success, msg = self.parent_tool.send_packet_and_wait_response(packet, timeout=5.0)
        if not success:
            raise Exception(f"块擦除失败: {msg}")
        
        # 擦除阶段完成后设置进度为10%
        self.progress_updated.emit(10)
        
        return current_progress
    
    def _execute_program_phase(self, start_addr, complete_firmware, total_size, pages_to_program, current_progress):
        """Execute program phase in thread"""
        self.status_updated.emit("正在写入固件数据...")
        
        # Calculate transfer count: each transfer sends OTA_PAGES_PER_TRANSFER pages (768 bytes)
        transfers_needed = (pages_to_program + OTA_PAGES_PER_TRANSFER - 1) // OTA_PAGES_PER_TRANSFER
        
        for transfer in range(transfers_needed):
            # Calculate current transfer start page and page count
            start_page = transfer * OTA_PAGES_PER_TRANSFER
            remaining_pages = pages_to_program - start_page
            current_pages = min(remaining_pages, OTA_PAGES_PER_TRANSFER)
            
            # Calculate address and data offset
            transfer_addr = start_addr + start_page * W25Q32JV_PAGE_SIZE
            data_offset = start_page * W25Q32JV_PAGE_SIZE
            transfer_size = current_pages * W25Q32JV_PAGE_SIZE
            
            # Get current transfer data
            if data_offset + transfer_size <= total_size:
                transfer_data = complete_firmware[data_offset:data_offset + transfer_size]
            else:
                # Last transfer, may be less than 1024 bytes, pad with 0xFF
                transfer_data = complete_firmware[data_offset:]
                padding_size = transfer_size - len(transfer_data)
                if padding_size > 0:
                    transfer_data += b'\xFF' * padding_size
            
            print(f"传输 {transfer + 1}/{transfers_needed}: 0x{transfer_addr:08X} ({current_pages}页, {len(transfer_data)} 字节)")
            
            # Use FIRMWARE_PROGRAM command to send multi-page data
            packet = self.parent_tool.build_protocol_packet(FIRMWARE_PROGRAM, transfer_addr, transfer_data)
            context_info = f"{transfer + 1}/{transfers_needed}"
            success, msg = self.parent_tool.send_packet_and_wait_response(packet, timeout=5.0, context_info=context_info)
            
            if not success:
                raise Exception(f"多页写入失败 (0x{transfer_addr:08X}): {msg}")
            
            # Update progress
            current_progress += current_pages
            progress_percent = min(int(10 + ((transfer + 1) / transfers_needed) * 80), 90)
            self.progress_updated.emit(progress_percent)
            
            time.sleep(0.1)
        
        return current_progress
    
    def _execute_verification_phase(self, start_addr, firmware_data, firmware_size, duration_str=None):
        """Execute verification phase in thread"""
        self.status_updated.emit("正在验证固件头...")
        
        packet = self.parent_tool.build_protocol_packet(FIRMWARE_READ_HEADER, start_addr)
        success, msg = self.parent_tool.send_packet_and_wait_response(packet, timeout=5.0)
        
        self.progress_updated.emit(100)
        
        if success and isinstance(msg, (bytes, bytearray)):
            if len(msg) >= 5:
                payload_len = msg[3] + (msg[4] << 8)
                payload_start = 5
                data_start = payload_start + 16
                if len(msg) >= data_start + 32:
                    header_data = msg[data_start:data_start + 32]
                else:
                    return "\n⚠️ 固件头数据不完整"
            else:
                return "\n⚠️ 响应数据格式错误"
            
            if len(header_data) >= 32:
                magic = int.from_bytes(header_data[0:4], 'little')
                version = int.from_bytes(header_data[4:8], 'little')
                size = int.from_bytes(header_data[8:12], 'little')
                crc32 = int.from_bytes(header_data[12:16], 'little')
                update_flag = header_data[16]
                
                # Display firmware header information
                print("\n读取到的固件头信息 (32字节):")
                print(f"  魔术字:      {header_data[0:4].hex()} (0x{magic:08x})")
                print(f"  版本号:      {header_data[4:8].hex()} (0x{version:08x})")
                print(f"  固件大小:    {header_data[8:12].hex()} ({size} 字节)")
                print(f"  CRC32校验:   {header_data[12:16].hex()} (0x{crc32:08x})")
                print(f"  更新标志:    {header_data[16:17].hex()} (0x{update_flag:02x})")
                print(f"  保留字段:    {header_data[17:32].hex()}")
                
                # Display timing information if available
                if duration_str is not None:
                    print(f"  烧录耗时:    {duration_str}")
                
                if magic == FIRMWARE_MAGIC and size == firmware_size and crc32 == self.parent_tool.calculate_crc32(firmware_data):
                    return "\n✅ 固件头验证成功"
                else:
                    return "\n⚠️ 固件头验证失败"
            else:
                return "\n⚠️ 固件头数据不完整"
        else:
            return "\n⚠️ 固件头读取失败"
    
    def _execute_sr150_program_phase(self, start_addr, firmware_data, firmware_size, pages_to_program, current_progress):
        """Execute SR150 firmware program phase (no header, direct data)"""
        self.status_updated.emit("正在写入SR150固件数据...")
        
        # Calculate transfer count: each transfer sends OTA_PAGES_PER_TRANSFER pages (768 bytes)
        transfers_needed = (pages_to_program + OTA_PAGES_PER_TRANSFER - 1) // OTA_PAGES_PER_TRANSFER
        
        for transfer in range(transfers_needed):
            # Calculate current transfer start page and page count
            start_page = transfer * OTA_PAGES_PER_TRANSFER
            remaining_pages = pages_to_program - start_page
            current_pages = min(remaining_pages, OTA_PAGES_PER_TRANSFER)
            
            # Calculate address and data offset
            transfer_addr = start_addr + start_page * W25Q32JV_PAGE_SIZE
            data_offset = start_page * W25Q32JV_PAGE_SIZE
            transfer_size = current_pages * W25Q32JV_PAGE_SIZE
            
            # Get current transfer data
            if data_offset + transfer_size <= firmware_size:
                transfer_data = firmware_data[data_offset:data_offset + transfer_size]
            else:
                # Last transfer, may be less than 1024 bytes, pad with 0xFF
                transfer_data = firmware_data[data_offset:]
                padding_size = transfer_size - len(transfer_data)
                if padding_size > 0:
                    transfer_data += b'\xFF' * padding_size
            
            # Use FIRMWARE_PROGRAM command to send multi-page data
            packet = self.parent_tool.build_protocol_packet(FIRMWARE_PROGRAM, transfer_addr, transfer_data)
            context_info = f"{transfer + 1}/{transfers_needed}"
            success, msg = self.parent_tool.send_packet_and_wait_response(packet, timeout=5.0, context_info=context_info)
            
            if not success:
                raise Exception(f"SR150多页写入失败 (0x{transfer_addr:08X}): {msg}")
            
            # Update progress
            current_progress += current_pages
            progress_percent = min(int(30 + ((transfer + 1) / transfers_needed) * 60), 90)
            self.progress_updated.emit(progress_percent)
            
            time.sleep(0.1)
        
        return current_progress
    
    def _write_sr150_config_info(self, firmware_data, firmware_size):
        """Write CRC and length configuration to 0x00300000 address"""
        self.status_updated.emit("正在写入SR150配置信息...")
        
        # Calculate CRC-XMODEM for firmware data
        firmware_crc = self.parent_tool.calculate_crc_xmodem(firmware_data)
        
        # Create configuration data (1 page = 256 bytes)
        config_data = bytearray(W25Q32JV_PAGE_SIZE)  # Initialize with zeros
        
        # Write CRC (2 bytes, little-endian) at offset 0
        config_data[0:2] = struct.pack('<H', firmware_crc)
        
        # Write firmware length (4 bytes, little-endian) at offset 2
        config_data[2:6] = struct.pack('<I', firmware_size)
        
        # Fill remaining bytes with 0xFF (typical flash erased state)
        for i in range(6, W25Q32JV_PAGE_SIZE):
            config_data[i] = 0xFF
        
        # Write configuration to 0x00300000
        config_addr = 0x00300000
        
        # Build and send packet
        packet = self.parent_tool.build_protocol_packet(FIRMWARE_PROGRAM, config_addr, bytes(config_data))
        success, msg = self.parent_tool.send_packet_and_wait_response(packet, timeout=5.0)
        
        if not success:
            raise Exception(f"SR150配置信息写入失败 (0x{config_addr:08X}): {msg}")
        
        self.progress_updated.emit(100)
    
    def _execute_sr150_flash(self):
        """Execute SR150 flash operation in thread"""
        # Use selected firmware path passed from UI
        firmware_path = self.firmware_path
        
        # Check if firmware file exists
        if not os.path.exists(firmware_path):
            self.finished.emit(False, f'SR150固件文件不存在:\n{firmware_path}')
            return
        
        self.status_updated.emit("读取SR150固件数据...")
        
        # Record SR150 start time
        sr150_start_time = time.time()
        
        # Read firmware data (no header generation)
        with open(firmware_path, 'rb') as f:
            firmware_data = f.read()
        
        firmware_size = len(firmware_data)
        
        # Calculate erase and program parameters
        blocks_to_erase = (firmware_size + W25Q32JV_BLOCK_64K_SIZE - 1) // W25Q32JV_BLOCK_64K_SIZE
        pages_to_program = (firmware_size + W25Q32JV_PAGE_SIZE - 1) // W25Q32JV_PAGE_SIZE
        total_operations = blocks_to_erase + pages_to_program
        
        # Setup serial connection
        current_progress = self._setup_serial_connection(total_operations)
        
        self.status_updated.emit(f"开始SR150固件烧录: {firmware_size} 字节")
        
        # Phase 1: Block erase
        current_progress = self._execute_erase_phase(SR150_FLASH_START_ADDR, blocks_to_erase, current_progress)
        
        # Phase 2: Program pages (direct firmware data, no header)
        current_progress = self._execute_sr150_program_phase(SR150_FLASH_START_ADDR, firmware_data, firmware_size, pages_to_program, current_progress)
        
        # Phase 3: Write CRC and length configuration to 0x00300000
        self._write_sr150_config_info(firmware_data, firmware_size)
        
        # Calculate duration
        sr150_end_time = time.time()
        sr150_duration = sr150_end_time - sr150_start_time
        
        # Format duration
        if sr150_duration >= 60:
            minutes = int(sr150_duration // 60)
            seconds = sr150_duration % 60
            duration_str = f"{minutes}分{seconds:.1f}秒"
        else:
            duration_str = f"{sr150_duration:.1f}秒"
        
        success_msg = (f'SR150固件烧录完成！\n\n'
                      f'固件大小: {firmware_size} 字节\n'
                      f'固件地址: 0x{SR150_FLASH_START_ADDR:08X} - 0x{SR150_FLASH_START_ADDR + firmware_size - 1:08X}\n'
                      f'配置地址: 0x00300000 (CRC + 长度信息)\n'
                      f'耗时: {duration_str}\n\n'
                      f'✅ 固件和配置信息已成功写入外部Flash')
        
        self.finished.emit(True, success_msg)

class FlashTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DK6')
        self.settings = QSettings('DK6FlashTool', 'Settings')
        
        self.setFixedWidth(280)  # 注释掉固定宽度设置，允许宽度调整
        self.setFixedHeight(180)  # 设置固定高度为250px，BUILD按钮移到Pages栏后减小高度
        
        # 置顶窗口
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # 设置窗口位置到鼠标所在屏幕的右上角
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QCursor
        
        # 获取鼠标当前位置
        cursor_pos = QCursor.pos()
        
        # 找到鼠标所在的屏幕
        current_screen = None
        for screen in QApplication.screens():
            if screen.geometry().contains(cursor_pos):
                current_screen = screen
                break
        
        # 如果没有找到，使用主屏幕
        if current_screen is None:
            current_screen = QApplication.primaryScreen()
        
        # 获取当前屏幕的可用区域
        screen_geometry = current_screen.availableGeometry()
        window_width = 320
        window_height = 225
        x = screen_geometry.x() + screen_geometry.width() - window_width - 20  # 距离右边缘20像素
        y = screen_geometry.y() + 20  # 距离顶部20像素
        self.move(x, y)
        
        icon_path = os.path.join(os.path.dirname(__file__), 'DK6.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 加载外部样式文件
        self.load_styles()

        # 初始化变量
        self.flash_worker  = None
        self.ota_worker    = None  # OTA worker thread
        self.selected_file = None
        self.serial_conn   = None
        
        # 加载UI配置OTA传输页
        global OTA_PAGES_PER_TRANSFER, OTA_TRANSFER_SIZE
        saved_pages = self.settings.value('ota_pages_per_transfer', 3, type=int)
        if 1 <= saved_pages <= 3:
            OTA_PAGES_PER_TRANSFER = saved_pages
            OTA_TRANSFER_SIZE = W25Q32JV_PAGE_SIZE * OTA_PAGES_PER_TRANSFER
        
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
        main_layout.setSpacing(4)  # 减小主布局间距
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        self.com_combo = QComboBox()
        self.com_combo.setMinimumWidth(120)
        self.com_combo.setPlaceholderText('选择串口')
        self.refresh_com_ports()
        
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['1000000', '460800'])
        self.baud_combo.setCurrentText('1000000')
        self.baud_combo.setMinimumWidth(80)
        
        top_row.addWidget(self.com_combo, 1)
        top_row.addWidget(self.baud_combo)
        main_layout.addLayout(top_row)
        
        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        self.file_combo = QComboBox()
        self.file_combo.setEditable(False)
        self.update_recent_files_combo()
        self.file_combo.currentTextChanged.connect(self.on_file_selected)

        browse_btn = QPushButton('📁')
        browse_btn.setObjectName('browse_btn')
        browse_btn.setMaximumWidth(35)
        browse_btn.setMaximumHeight(28)
        browse_btn.clicked.connect(self.browse_file)

        file_row.addWidget(self.file_combo, 1)
        file_row.addWidget(browse_btn)
        main_layout.addLayout(file_row)
        
        config_row = QHBoxLayout()
        config_row.setSpacing(8)
        
        pages_label = QLabel('Pages:')
        pages_label.setMinimumWidth(20)
        
        self.pages_combo = QComboBox()
        self.pages_combo.addItems(['1', '2', '3'])
        self.pages_combo.setCurrentIndex(OTA_PAGES_PER_TRANSFER - 1)  # 设置为保存的配置
        self.pages_combo.setMinimumWidth(100)
        self.pages_combo.currentIndexChanged.connect(self.on_pages_changed)

        # config_row.addWidget(pages_label)
        # config_row.addWidget(self.pages_combo)
        config_row.addStretch()  # 添加弹性空间
        main_layout.addLayout(config_row)
        
        button_frame = QFrame()
        button_grid = QGridLayout(button_frame)
        button_grid.setContentsMargins(0, 0, 0, 0)
        
        flash_btn = QPushButton('FLASH')
        flash_btn.setObjectName('flash_btn')
        flash_btn.clicked.connect(self.flash_firmware)
        button_grid.addWidget(flash_btn, 0, 0)
        
        reset_btn = QPushButton('RESET')
        reset_btn.setObjectName('reset_btn')
        reset_btn.clicked.connect(self.reset_device)
        button_grid.addWidget(reset_btn, 0, 1)

        app_flash_btn = QPushButton('APP FLASH')
        app_flash_btn.setObjectName('app_flash_btn')  # 使用专用的App Flash按钮样式
        app_flash_btn.setEnabled(True)  # 启用App Flash按钮
        app_flash_btn.clicked.connect(lambda: self.flash_firmware(0x19000))
        button_grid.addWidget(app_flash_btn, 0, 2)
        
        # 第二排按钮
        ota_flash_btn = QPushButton('OTA FLASH')
        ota_flash_btn.setObjectName('ota_flash_btn')
        ota_flash_btn.clicked.connect(self.ota_flash_firmware)
        button_grid.addWidget(ota_flash_btn, 1, 0)
        
        # UUID按钮
        uuid_btn = QPushButton('UUID')
        uuid_btn.setObjectName('uuid_btn')
        uuid_btn.clicked.connect(self.get_uuid)
        button_grid.addWidget(uuid_btn, 1, 1)

        sr150_btn = QPushButton('SR150')
        sr150_btn.setObjectName('sr150_btn')
        sr150_btn.clicked.connect(self.sr150_flash_firmware)
        button_grid.addWidget(sr150_btn, 1, 2)
        
        # 设置按钮间距
        button_grid.setVerticalSpacing(4)  
        button_grid.setHorizontalSpacing(2)  
        
        main_layout.addWidget(button_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 恢复上次文件
        last_file = self.settings.value("last_file", "")
        if last_file and os.path.exists(last_file):
            self.select_file(last_file)
        
        self.setWindowOpacity(1.0)
        # 启用拖拽支持
        self.setAcceptDrops(True)
        
        
    def load_styles(self):
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            style_file = os.path.join(current_dir, 'styles.qss')
            
            if os.path.exists(style_file):
                with open(style_file, 'r', encoding='utf-8') as f:
                    style_sheet = f.read()
                self.setStyleSheet(style_sheet)
            else:
                print(f"样式文件不存在: {style_file}")
        except Exception as e:
            print(f"加载样式文件失败: {e}")

    def calculate_crc32(self, data):
        crc = 0xFFFFFFFF
        polynomial = 0xEDB88320
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ polynomial
                else:
                    crc >>= 1
        return (~crc) & 0xFFFFFFFF
    
    def calculate_crc_xmodem(self, data):
        """Calculate CRC-XMODEM (CRC-16/XMODEM) checksum
        Based on uwb_fwdl_provider_rv4.c implementation
        """
        # CRC-XMODEM lookup table (same as gCrcXmodemTable in C code)
        crc_xmodem_table = [
            0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
            0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
            0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
            0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
            0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
            0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
            0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
            0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
            0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
            0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
            0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
            0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
            0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
            0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
            0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
            0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
            0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
            0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
            0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
            0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
            0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
            0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
            0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
            0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
            0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
            0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
            0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
            0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
            0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
            0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
            0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
            0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
        ]
        
        crc = 0x0000  # Initial value for CRC-XMODEM
        
        for byte in data:
            # Same algorithm as uwb_fwdl_provider_generate_crc function
            default_crc = ((crc >> 8) ^ (0xff & byte))
            crc = ((crc << 8) ^ crc_xmodem_table[default_crc]) & 0xFFFF
            
        return crc
    
    def generate_firmware_header(self, firmware_data, version=1):
        size = len(firmware_data)
        crc32 = self.calculate_crc32(firmware_data)
        update_flag = 1  # 更新标志
        
        header = struct.pack('<IIIIB3B3I', 
                           FIRMWARE_MAGIC,    # magic (4字节)
                           version,           # version (4字节)
                           size,              # size (4字节)
                           crc32,             # crc32 (4字节)
                           update_flag,       # update_flag (1字节)
                           0, 0, 0,           # 填充3字节对齐到4字节边界
                           0, 0, 0)           # reserved (12字节)
        return header
        
    def build_protocol_packet(self, command, addr=0, data=b''):
        packet = bytearray()
        packet.append(0x00)
        packet.extend([0x00, 0xFF])
        payload = bytearray()
        payload.extend([0x05, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        payload.extend([0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        payload.append(0x01)
        payload.append(command)
        payload.append(0x00)
        payload.append(0x00)
        if command == RESET_MCU:
            pass
        elif command == FIRMWARE_ERASE:
            # 固件擦除: 地址(4字节) + 块数(1字节)
            addr_bytes = struct.pack('<I', addr)  # 小端格式
            payload.extend(addr_bytes)
            # 添加块数信息
            if isinstance(data, int):
                payload.append(data)  # 直接传入块数
            else:
                payload.append(1)
                
        elif command == FIRMWARE_PROGRAM:
            # 固件写入: 地址(4字节) + 页数(1字节) + 实际数据
            addr_bytes = struct.pack('<I', addr)  # 小端格式
            payload.extend(addr_bytes)
            
            # 添加页数字段 - 计算实际传输的页数
            if isinstance(data, (bytes, bytearray)):
                pages = (len(data) + W25Q32JV_PAGE_SIZE - 1) // W25Q32JV_PAGE_SIZE  # 向上取整
                pages = min(pages, OTA_PAGES_PER_TRANSFER)  # 限制最大页数
            else:
                pages = OTA_PAGES_PER_TRANSFER  # 默认页数
            payload.append(pages)
            
            if isinstance(data, (bytes, bytearray)):
                payload.extend(data)  # 实际数据
                
        elif command == FIRMWARE_READ_HEADER:
            # 读取固件头: 地址(4字节)
            addr_bytes = struct.pack('<I', addr)  # 小端格式
            payload.extend(addr_bytes)
        elif command == SEMS_LITE_COMMAND:
            # 获取UUID命令: 不需要额外数据
            pass
        
        payload_length = len(payload)
        packet.extend(struct.pack('<H', payload_length))
        packet.extend(payload)
        dcs = 0
        for b in payload:
            dcs += b
        dcs = (0x00 - dcs) & 0xFF 
        packet.append(dcs)
        packet.append(0x00)
        return bytes(packet)
        
    def send_packet_and_wait_response(self, packet, timeout=5.0, context_info=None):
        if not self.serial_conn or not self.serial_conn.is_open:
            return False, "串口未连接"
        try:
            self.serial_conn.write(packet)
            self.serial_conn.flush()
            start_time = time.time()
            first_data_time = None
            received_data = bytearray()
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    received_data.extend(data)
                    if first_data_time is None:
                        first_data_time = time.time()
                    if len(received_data) >= 5:
                        if received_data[0] == 0x00 and received_data[1] == 0x00 and received_data[2] == 0xFF:
                            payload_len = received_data[3] + (received_data[4] << 8)
                            expected_total_len = 5 + payload_len + 2  # header(3) + length(2) + payload + DCS(1) + end(1)
                            
                            if len(received_data) >= expected_total_len:
                                # 验证结束码
                                if received_data[expected_total_len - 1] != 0x00:
                                    print(f"响应格式错误: 结束码不正确")
                                    return False, "响应格式错误"
                                
                                if context_info:
                                    print(f'接收 {context_info}')
                                payload_start = 5
                                payload_end = payload_start + payload_len
                                dcs_pos = payload_end
                                
                                calculated_sum = 0
                                for i in range(payload_start, payload_end):
                                    calculated_sum += received_data[i]
                                calculated_sum += received_data[dcs_pos]  # 加上DCS
                                calculated_sum &= 0xFF
                                
                                if calculated_sum != 0:
                                    print(f"DCS校验失败: 累加和={calculated_sum:02X}")
                                    return False, "DCS校验失败"
                                
                                # 解析payload中的字段（根据ApduPayload_t结构体定义）
                                # SADDR(0-5) + TADDR(6-11) + SNQ(12) + cmd_type(13) + result(14) + apdu_count(15)
                                if payload_len >= 16:
                                    cmd_type = received_data[payload_start + 13]  # cmd_type字段在payload的第13个字节
                                    result = received_data[payload_start + 14]    # result字段在payload的第14个字节
                                    
                                    cmd_name = "未知命令"
                                    if cmd_type == 0xCA:
                                        cmd_name = "复位MCU"
                                    elif cmd_type == 0xCB:
                                        cmd_name = "擦除"
                                    elif cmd_type == 0xCC:
                                        cmd_name = "写入"
                                    elif cmd_type == 0xCD:
                                        cmd_name = "读取固件头"
                                    elif cmd_type == 0xCE:
                                        cmd_name = "获取UUID"
                                    
                                    if result == 0:
                                        if cmd_type == 0xCD:  # 固件头读取命令返回完整数据
                                            return True, received_data
                                        elif cmd_type == 0xCE:  # UUID命令返回完整数据
                                            return True, received_data
                                        else:
                                            return True, f"{cmd_name}成功"
                                    else:
                                        print(f"{cmd_name}操作失败: result={result}")
                                        return False, f"{cmd_name}失败 (result: {result})"
                                else:
                                    print(f"响应payload长度不足: {payload_len}")
                                    return False, "响应数据格式错误"
                            else:
                                # 数据还不完整，继续等待
                                continue
                        else:
                            # 如果不是预期的协议头，等待一段时间后返回错误
                            if first_data_time and time.time() - first_data_time > 1.0:
                                print(f"收到无效协议头: {received_data[:3].hex()}")
                                return False, f"收到无效响应: {received_data.hex()}"
                                
                time.sleep(0.01)
                
            if len(received_data) == 0:
                return False, "设备无响应 - 可能DCS校验失败或协议格式错误"
            else:
                return False, f"响应超时 - 收到不完整数据: {received_data.hex()}"
            
        except Exception as e:
            return False, f"通信错误: {str(e)}"

    def refresh_com_ports(self):
        current_device = self.com_combo.currentData()
        self.com_combo.clear()
        
        ports = serial.tools.list_ports.comports()
        usb_port_index = -1

        for i, port in enumerate(ports):
            self.com_combo.addItem(f"{port.device} - {port.description}", port.device)
            if "USB Serial Port" in port.description and usb_port_index == -1:
                usb_port_index = i

        if current_device:
            for i in range(self.com_combo.count()):
                if self.com_combo.itemData(i) == current_device:
                    self.com_combo.setCurrentIndex(i)
                    return
        
        if usb_port_index != -1:
            self.com_combo.setCurrentIndex(usb_port_index)

    def browse_file(self):
        last_dir = self.settings.value("last_directory", r"E:\Work\UWB\Code")
        file_path, _ = QFileDialog.getOpenFileName(self, '选择固件文件', last_dir, 'BIN Files (*.bin);;HEX Files (*.hex)')
        if file_path:
            self.select_file(file_path)

    def select_file(self, file_path):
        if os.path.exists(file_path):
            self.selected_file = file_path
            
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            self.recent_files.insert(0, file_path)
            self.recent_files = self.recent_files[:10]  # 只保留最近10个
            
            # 保存到设置
            self.settings.setValue('recent_files', '|'.join(self.recent_files))
            self.settings.setValue("last_directory", os.path.dirname(file_path))
            self.settings.setValue("last_file", file_path)
            
            self.update_recent_files_combo()

    def on_file_selected(self, text):
        if not text or text == '选择或拖拽固件文件':
            self.selected_file = None
            return

        for file_path in self.recent_files:
            if os.path.basename(file_path) == text:
                self.selected_file = file_path
                self.settings.setValue("last_file", file_path)
                return # Found

    def on_pages_changed(self, index):
        global OTA_PAGES_PER_TRANSFER, OTA_TRANSFER_SIZE
        
        pages = index + 1  # 索引0对应1页，索引1对应2页，以此类推
        OTA_PAGES_PER_TRANSFER = pages
        OTA_TRANSFER_SIZE = W25Q32JV_PAGE_SIZE * OTA_PAGES_PER_TRANSFER
        
        print(f"OTA传输配置已更新: {pages}页 ({OTA_TRANSFER_SIZE}字节)")
        
        self.settings.setValue("ota_pages_per_transfer", pages)

    def update_recent_files_combo(self):
        self.file_combo.blockSignals(True)
        selected_path = self.selected_file
        self.file_combo.clear()
        
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

    def flash_firmware(self, address=None):
        com_data = self.com_combo.currentData()
        if not com_data:
            QMessageBox.warning(self, '错误', '请选择串口')
            return
        if not self.selected_file or not os.path.exists(self.selected_file):
            QMessageBox.warning(self, '错误', '请选择有效的固件文件')
            return
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
        
        self.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        programmer_path = 'C:\\NXP\\DK6ProductionFlashProgrammer\\DK6Programmer.exe'
        if not os.path.exists(programmer_path):
            QMessageBox.warning(self, '错误', '未找到DK6Programmer.exe')
            self.setEnabled(True)
            self.progress_bar.setVisible(False)
            return
        
        if address is None:
            # Flash button: erase entire flash and program to default address
            command_args = [programmer_path, '-s', com_data, '-P', self.baud_combo.currentText(), '-Y', '-e', 'FLASH', '-p', self.selected_file]
        else:
            # App Flash button: program to specific address without erasing
            command_args = [programmer_path, '-s', com_data, '-P', self.baud_combo.currentText(), '-Y', '-p', f'FLASH@{hex(address)}={self.selected_file}']
        self.flash_worker = FlashWorker(command_args)
        self.flash_worker.finished.connect(self.on_flash_finished)
        self.flash_worker.start()
    
    def on_flash_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.setEnabled(True)
        
        if success:
            print("flash OK!")
        else:
            # QMessageBox.critical(self, '失败', f'烧录失败: {message}')
            print("flash failed!")
        
        self.flash_worker = None
    
    def reset_device(self):
        """复位设备 - 发送复位命令后不等待响应"""
        com_data = self.com_combo.currentData()
        if not com_data:
            QMessageBox.warning(self, '错误', '请选择串口')
            return
        try:
            self.serial_conn = serial.Serial(
                port=com_data,
                baudrate=int(self.baud_combo.currentText()),
                timeout=1.0
            )
            
            packet = self.build_protocol_packet(RESET_MCU)
            print(f"发送复位指令: {packet.hex()}")
            self.serial_conn.write(packet)
            self.serial_conn.flush()
            QMessageBox.information(self, '成功', '复位命令已发送，设备将重新启动')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'复位设备时出错: {str(e)}')
        finally:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                self.serial_conn = None

    
    def get_uuid(self):
        """获取UUID - 发送获取UUID命令并等待响应"""
        com_data = self.com_combo.currentData()
        if not com_data:
            QMessageBox.warning(self, '错误', '请选择串口')
            return
        try:
            self.serial_conn = serial.Serial(
                port=com_data,
                baudrate=int(self.baud_combo.currentText()),
                timeout=1.0
            )
            
            packet = self.build_protocol_packet(SEMS_LITE_COMMAND)
            # print(f"发送获取UUID指令: {packet.hex()}")
            
            success, response_data = self.send_packet_and_wait_response(packet, timeout=5.0)
            
            if success and isinstance(response_data, bytearray):
                payload_start = 5
                payload_len = response_data[3] + (response_data[4] << 8)
                
                # UUID数据从payload的第16个字节开始（跳过SADDR+TADDR+SNQ+cmd_type+result+apdu_count）
                uuid_start = payload_start + 16
                uuid_data = response_data[uuid_start:payload_start + payload_len]  # DCS在payload之后，不需要减1
                
                uuid_hex = uuid_data.hex().upper()
                
                dialog = UUIDDisplayDialog(f"{uuid_hex}", self)
                dialog.exec()
            else:
                QMessageBox.critical(self, '错误', f'获取UUID失败: {response_data if isinstance(response_data, str) else "未知错误"}')
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'获取UUID时出错: {str(e)}')
        finally:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                self.serial_conn = None
    
    def show_firmware_flash_confirmation_dialog(self, firmware_size, firmware_header, total_size, start_addr):
        dialog = QDialog(self)
        dialog.setWindowTitle('固件烧录确认')

        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        info_frame = QFrame()
        info_frame.setObjectName('InfoFrame')
        form_layout = QFormLayout(info_frame)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def add_info_row(label_text, value_text, value_object_name="ValueField"):
            label = QLabel(label_text)
            label.setObjectName("LabelField")
            value = QLabel(value_text)
            value.setObjectName(value_object_name)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form_layout.addRow(label, value)

        add_info_row("文件名称:", os.path.basename(self.selected_file))
        add_info_row("固件大小:", f"{firmware_size:,} 字节")
        add_info_row("头部大小:", f"{len(firmware_header):,} 字节")
        add_info_row("总大小:", f"{total_size:,} 字节", "TotalSizeValue")
        add_info_row("起始地址:", f"0x{start_addr:08X}")
        add_info_row("结束地址:", f"0x{start_addr + total_size - 1:08X}")

        main_layout.addWidget(info_frame)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton('取消操作')
        cancel_btn.setObjectName('CancelButton')
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton('开始烧录')
        confirm_btn.setObjectName('ConfirmButton')
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(confirm_btn)

        main_layout.addLayout(button_layout)
        
        return dialog.exec() == QDialog.DialogCode.Accepted
    
    def prepare_firmware_data(self):
        if not self.selected_file or not os.path.exists(self.selected_file):
            QMessageBox.warning(self, '错误', '请选择有效的固件文件')
            return None
        try:
            with open(self.selected_file, 'rb') as f:
                firmware_data = f.read()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'读取固件文件失败: {str(e)}')
            return None
            
        firmware_size = len(firmware_data)
        if firmware_size == 0:
            QMessageBox.warning(self, '错误', '固件文件为空')
            return None
            
        if firmware_size > MAX_FIRMWARE_SIZE:
            QMessageBox.warning(self, '错误', f'固件文件过大 ({firmware_size} 字节)，超过Flash容量 ({MAX_FIRMWARE_SIZE} 字节)')
            return None
            
        firmware_header = self.generate_firmware_header(firmware_data)
        
        print("固件头结构 (32字节):")
        print(f"  魔术字:      {firmware_header[0:4].hex()} (0x12345678)")
        print(f"  版本号:      {firmware_header[4:8].hex()} (0x{int.from_bytes(firmware_header[4:8], 'little'):08x})")
        print(f"  固件大小:    {firmware_header[8:12].hex()} ({int.from_bytes(firmware_header[8:12], 'little')} 字节)")
        print(f"  CRC32校验:   {firmware_header[12:16].hex()} (0x{int.from_bytes(firmware_header[12:16], 'little'):08x})")
        print(f"  更新标志:    {firmware_header[16:17].hex()} (0x01=更新固件)")
        print(f"  保留字段:    {firmware_header[17:29].hex()}")
        print(f"固件头大小: {len(firmware_header)} 字节")
        
        complete_firmware = firmware_header + firmware_data
        total_size = len(complete_firmware)
        print(f"完整固件大小: {total_size} 字节 (头部: {len(firmware_header)}, 数据: {firmware_size})")
        
        return firmware_data, firmware_header, complete_firmware
    
    def setup_serial_and_progress(self, com_data, total_operations):
        self.serial_conn = serial.Serial(
            port=com_data,
            baudrate=int(self.baud_combo.currentText()),
            timeout=2.0
        )
        self.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total_operations)
        return 0  
    
    def ota_flash_firmware(self):
        # Check if OTA worker is already running
        if self.ota_worker and self.ota_worker.isRunning():
            QMessageBox.warning(self, '操作进行中', 'OTA操作正在进行中，请等待完成')
            return
            
        com_data = self.com_combo.currentData()
        if not com_data:
            QMessageBox.warning(self, '错误', '请选择串口')
            return
            
        firmware_result = self.prepare_firmware_data()
        if not firmware_result:
            return
            
        firmware_data, firmware_header, complete_firmware = firmware_result
        firmware_size = len(firmware_data)
        total_size = len(complete_firmware)
        start_addr = EXTERNAL_FLASH_APP_START
        
        if not self.show_firmware_flash_confirmation_dialog(firmware_size, firmware_header, total_size, start_addr):
            return
        
        # Disable UI and show progress bar
        self.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Create and start OTA worker thread
        self.ota_worker = OTAWorker(
            operation_type='ota_flash',
            com_data=com_data,
            baud_rate=int(self.baud_combo.currentText()),
            firmware_path=self.selected_file,
            parent_tool=self
        )
        
        # Connect signals
        self.ota_worker.progress_updated.connect(self.progress_bar.setValue)
        self.ota_worker.status_updated.connect(self.update_status_message)
        self.ota_worker.finished.connect(self.on_ota_finished)
        
        # Start the worker thread
        self.ota_worker.start()
    
    def update_status_message(self, message):
        """Update status message (can be used for status bar if needed)"""
        print(f"状态: {message}")
    
    def on_ota_finished(self, success, message):
        """Handle OTA operation completion"""
        # Re-enable UI
        self.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Show result message
        if success:
            QMessageBox.information(self, 'OTA烧录成功', message)
        else:
            QMessageBox.critical(self, 'OTA烧录失败', message)
        
        # Clean up worker
        if self.ota_worker:
            self.ota_worker.deleteLater()
            self.ota_worker = None
    


    def sr150_flash_firmware(self):
        """SR150从选中文件进行OTA烧录"""
        # Check if OTA worker is already running
        if self.ota_worker and self.ota_worker.isRunning():
            QMessageBox.warning(self, '操作进行中', 'OTA操作正在进行中，请等待完成')
            return
        
        # 使用用户选中的固件文件
        firmware_path = self.selected_file
        if not firmware_path:
            QMessageBox.warning(self, '文件错误', '请选择固件文件')
            return
        
        # Check if firmware file exists
        if not os.path.exists(firmware_path):
            QMessageBox.critical(self, '文件错误', f'SR150固件文件不存在:\n{firmware_path}')
            return
        
        # Get COM port selection
        com_data = self.com_combo.currentData()
        if not com_data:
            QMessageBox.warning(self, '端口错误', '请选择有效的串口')
            return
        
        # Show confirmation dialog
        firmware_size = os.path.getsize(firmware_path)
        reply = QMessageBox.question(self, 'SR150固件烧录确认', 
                                   f'确定要烧录SR150固件吗？\n\n'
                                   f'文件: {os.path.basename(firmware_path)}\n'
                                   f'固件大小: {firmware_size} 字节\n'
                                   f'目标地址: 0x{SR150_FLASH_START_ADDR:08X}\n\n',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable UI and show progress bar
        self.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Create and start OTA worker thread for SR150
        self.ota_worker = OTAWorker(
            operation_type='sr150_flash',
            com_data=com_data,
            baud_rate=int(self.baud_combo.currentText()),
            firmware_path=firmware_path,  # 使用选中的固件文件
            parent_tool=self
        )
        
        # Connect signals
        self.ota_worker.progress_updated.connect(self.progress_bar.setValue)
        self.ota_worker.status_updated.connect(self.update_status_message)
        self.ota_worker.finished.connect(self.on_ota_finished)
        
        # Start the worker thread
        self.ota_worker.start()

    def execute_sr150_program_phase(self, start_addr, firmware_data, firmware_size, pages_to_program, current_progress):
        """Execute SR150 firmware program phase (no header, direct data)"""
        print("\n=== SR150阶段2: 页面写入 (768字节传输, 无固件头) ===")
        
        # Calculate transfer count: each transfer sends OTA_PAGES_PER_TRANSFER pages (768 bytes)
        transfers_needed = (pages_to_program + OTA_PAGES_PER_TRANSFER - 1) // OTA_PAGES_PER_TRANSFER
        
        for transfer in range(transfers_needed):
            # Calculate current transfer start page and page count
            start_page = transfer * OTA_PAGES_PER_TRANSFER
            remaining_pages = pages_to_program - start_page
            current_pages = min(remaining_pages, OTA_PAGES_PER_TRANSFER)
            
            # Calculate address and data offset
            transfer_addr = start_addr + start_page * W25Q32JV_PAGE_SIZE
            data_offset = start_page * W25Q32JV_PAGE_SIZE
            transfer_size = current_pages * W25Q32JV_PAGE_SIZE
            
            # Get current transfer data
            if data_offset + transfer_size <= firmware_size:
                transfer_data = firmware_data[data_offset:data_offset + transfer_size]
            else:
                # Last transfer, may be less than 1024 bytes, pad with 0xFF
                transfer_data = firmware_data[data_offset:]
                padding_size = transfer_size - len(transfer_data)
                if padding_size > 0:
                    transfer_data += b'\xFF' * padding_size
                    
            print(f"传输 {transfer + 1}/{transfers_needed}: 0x{transfer_addr:08X} ({current_pages}页, {len(transfer_data)} 字节)")
            
            # Use FIRMWARE_PROGRAM command to send multi-page data
            packet = self.build_protocol_packet(FIRMWARE_PROGRAM, transfer_addr, transfer_data)
            context_info = f"{transfer + 1}/{transfers_needed}"
            success, msg = self.send_packet_and_wait_response(packet, timeout=5.0, context_info=context_info)
            
            if not success:
                raise Exception(f"SR150多页写入失败 (0x{transfer_addr:08X}): {msg}")
                
            # Update progress bar (by page count)
            current_progress += current_pages
            self.progress_bar.setValue(current_progress)
            QApplication.processEvents()
            time.sleep(0.1)
            
        print("SR150页面写入完成")
        return current_progress
    
    def write_sr150_config_info(self, firmware_data, firmware_size):
        """Write CRC and length configuration to 0x00300000 address"""
        print("\n=== SR150阶段3: 写入配置信息到0x00300000 ===")
        
        # Calculate CRC-XMODEM for firmware data
        firmware_crc = self.calculate_crc_xmodem(firmware_data)
        print(f"固件CRC-XMODEM: 0x{firmware_crc:04X}")
        print(f"固件长度: {firmware_size} 字节")
        
        # Create configuration data (1 page = 256 bytes)
        config_data = bytearray(W25Q32JV_PAGE_SIZE)  # Initialize with zeros
        
        # Write CRC (2 bytes, little-endian) at offset 0
        config_data[0:2] = struct.pack('<H', firmware_crc)
        
        # Write firmware length (4 bytes, little-endian) at offset 2  
        config_data[2:6] = struct.pack('<I', firmware_size)
        
        # Fill remaining bytes with 0xFF (typical flash erased state)
        for i in range(6, W25Q32JV_PAGE_SIZE):
            config_data[i] = 0xFF
            
        # Write configuration to 0x00300000
        config_addr = 0x00300000
        print(f"写入配置信息到地址: 0x{config_addr:08X}")
        
        # Build and send packet
        packet = self.build_protocol_packet(FIRMWARE_PROGRAM, config_addr, bytes(config_data))
        success, msg = self.send_packet_and_wait_response(packet, timeout=5.0)
        
        if not success:
            raise Exception(f"SR150配置信息写入失败 (0x{config_addr:08X}): {msg}")
            
        print("SR150配置信息写入完成")
        print(f"  CRC: 0x{firmware_crc:04X} (2字节)")
        print(f"  长度: {firmware_size} (4字节)")
    
    def show_sr150_success_message(self, firmware_size, firmware_path, sr150_duration=None):
        """Show SR150 firmware flash success message"""
        print(f"\n=== SR150固件烧录成功 ===")
        print(f"固件大小: {firmware_size} 字节")
        print(f"固件地址: 0x{SR150_FLASH_START_ADDR:08X} - 0x{SR150_FLASH_START_ADDR + firmware_size - 1:08X}")
        print(f"配置地址: 0x00300000 (CRC + 长度)")
        
        # 格式化耗时信息
        duration_str = ""
        if sr150_duration is not None:
            minutes = int(sr150_duration // 60)
            seconds = sr150_duration % 60
            if minutes > 0:
                duration_str = f"耗时: {minutes}分{seconds:.1f}秒\n"
            else:
                duration_str = f"耗时: {seconds:.1f}秒\n"
            print(f"耗时: {duration_str.strip()}")
        
        QMessageBox.information(self, 'SR150烧录成功', 
                              f'SR150固件烧录完成！\n\n'
                              f'固件大小: {firmware_size} 字节\n'
                              f'固件地址: 0x{SR150_FLASH_START_ADDR:08X} - 0x{SR150_FLASH_START_ADDR + firmware_size - 1:08X}\n'
                              f'配置地址: 0x00300000 (CRC + 长度信息)\n'
                              f'{duration_str}\n'
                              f'✅ 固件和配置信息已成功写入外部Flash')

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self.setWindowOpacity(1.0)
            else:
                self.setWindowOpacity(0.5)
        super().changeEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith(('.bin', '.hex', '.elf')):
                self.select_file(file_path)
                break
        super().dropEvent(event)
    
    def closeEvent(self, event):
        # 停止定时器
        if hasattr(self, 'com_timer'):
            self.com_timer.stop()
        
        # 停止工作线程
        if self.flash_worker and self.flash_worker.isRunning():
            self.flash_worker.terminate()
            self.flash_worker.wait()
        
        # 停止OTA工作线程
        if hasattr(self, 'ota_worker') and self.ota_worker and self.ota_worker.isRunning():
            self.ota_worker.terminate()
            self.ota_worker.wait()
        
        # 关闭串口连接
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("DK6 OTA Flash Tool")
    app.setApplicationDisplayName("DK6 OTA Flash Tool")
    app.setOrganizationName("DK6 Tools")
    app.setOrganizationDomain("dk6tools.com")
    app.setApplicationVersion("1.0.0")
    
    if hasattr(app, 'setApplicationId'):
        app.setApplicationId("DK6Tools.DK6OTAFlashTool.1.0")
    
    window = FlashTool()
    window.show()
    sys.exit(app.exec())
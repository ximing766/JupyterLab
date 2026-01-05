#!/usr/bin/env python3
import sys
import os
import time
import struct
import argparse
import serial
import serial.tools.list_ports

# ==========================================
# 常量定义
# ==========================================
RESET_MCU            = 0xCA  # 复位MCU命令
FIRMWARE_ERASE       = 0xCB  # 固件擦除命令
FIRMWARE_PROGRAM     = 0xCC  # 固件写入命令
FIRMWARE_READ_HEADER = 0xCD  # 读取固件头命令

# Flash参数
W25Q32JV_PAGE_SIZE      = 256       # 页大小
W25Q32JV_SECTOR_SIZE    = 4096      # 扇区大小 4KB
W25Q32JV_BLOCK_64K_SIZE = 65536     # 64KB块大小
W25Q32JV_FLASH_SIZE     = 4 * 1024 * 1024  # 总大小 4MB

# OTA传输配置
OTA_PAGES_PER_TRANSFER = 3  # 每次传输的页数，默认3页(768字节)
OTA_TRANSFER_SIZE = W25Q32JV_PAGE_SIZE * OTA_PAGES_PER_TRANSFER

# 固件相关常量
FIRMWARE_MAGIC = 0x12345678
INTER_APP_ADDR = 0x0A000
EXTERNAL_FLASH_APP_START = 0x00260000
SR150_FLASH_START_ADDR = 0x00300100
MAX_FIRMWARE_SIZE = 1024 * 1024  # 1MB


class OTAClient:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None

    def connect(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    timeout=2.0
                )
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"串口连接失败: {e}，正在重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(1.0)
                else:
                    print(f"串口连接失败: {e}")
                    return False

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

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
        
        crc = 0x0000
        for byte in data:
            default_crc = ((crc >> 8) ^ (0xff & byte))
            crc = ((crc << 8) ^ crc_xmodem_table[default_crc]) & 0xFFFF
        return crc

    # ==========================================
    # 协议封装
    # ==========================================
    def generate_firmware_header(self, firmware_data, version=1):
        size = len(firmware_data)
        crc32 = self.calculate_crc32(firmware_data)
        update_flag = 1
        
        header = struct.pack('<IIIIB3B3I', 
                           FIRMWARE_MAGIC, version, size, crc32, update_flag,
                           0, 0, 0, 0, 0, 0)
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
            addr_bytes = struct.pack('<I', addr)
            payload.extend(addr_bytes)
            if isinstance(data, int):
                payload.append(data)
            else:
                payload.append(1)
        elif command == FIRMWARE_PROGRAM:
            addr_bytes = struct.pack('<I', addr)
            payload.extend(addr_bytes)
            if isinstance(data, (bytes, bytearray)):
                pages = (len(data) + W25Q32JV_PAGE_SIZE - 1) // W25Q32JV_PAGE_SIZE
                pages = min(pages, OTA_PAGES_PER_TRANSFER)
            else:
                pages = OTA_PAGES_PER_TRANSFER
            payload.append(pages)
            if isinstance(data, (bytes, bytearray)):
                payload.extend(data)
        elif command == FIRMWARE_READ_HEADER:
            addr_bytes = struct.pack('<I', addr)
            payload.extend(addr_bytes)
        
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

    def send_packet_and_wait_response(self, packet, timeout=2.0, context_info=None):
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
                            expected_total_len = 5 + payload_len + 2
                            
                            if len(received_data) >= expected_total_len:
                                if received_data[expected_total_len - 1] != 0x00:
                                    return False, "响应格式错误"
                                
                                payload_start = 5
                                payload_end = payload_start + payload_len
                                dcs_pos = payload_end
                                
                                calculated_sum = 0
                                for i in range(payload_start, payload_end):
                                    calculated_sum += received_data[i]
                                calculated_sum += received_data[dcs_pos]
                                calculated_sum &= 0xFF
                                
                                if calculated_sum != 0:
                                    return False, "DCS校验失败"
                                
                                if payload_len >= 16:
                                    cmd_type = received_data[payload_start + 13]
                                    result = received_data[payload_start + 14]
                                    
                                    if result == 0:
                                        if cmd_type == 0xCD: # READ HEADER
                                            return True, received_data
                                        else:
                                            return True, "成功"
                                    else:
                                        return False, f"失败 (result: {result})"
                                else:
                                    return False, "响应数据格式错误"
                            else:
                                continue
                        else:
                            if first_data_time and time.time() - first_data_time > 1.0:
                                return False, f"收到无效响应: {received_data.hex()}"
                                
                time.sleep(0.01)
                
            if len(received_data) == 0:
                return False, "设备无响应"
            else:
                return False, f"响应超时 - 数据: {received_data.hex()}"
            
        except Exception as e:
            return False, f"通信错误: {str(e)}"

    def get_version(self):
        # User provided fixed packet:
        # 00 00 FF 15 00 06 FF FF FF FF FF 05 FF FF FF FF FF 01 C5 00 01 03 00 03 02 00 30 00
        packet = bytes([
            0x00, 0x00, 0xFF, 0x15, 0x00, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x05, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
            0x01, 0xC5, 0x00, 0x01, 0x03, 0x00, 0x03, 0x02, 0x00, 0x30, 0x00
        ])
        
        try:
            self.serial_conn.write(packet)
            self.serial_conn.flush()
            
            # Read response
            start_time = time.time()
            received_data = bytearray()
            while time.time() - start_time < 2.0:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    received_data.extend(data)
                    
                    # Basic check for response
                    if len(received_data) > 5:
                         # Assuming we just want to print whatever we get for now as user didn't specify response format
                         pass
                time.sleep(0.01)
                
            if len(received_data) > 0:
                print(f"收到响应: {received_data}")
                return True
            else:
                print("未收到响应")
                return False
                
        except Exception as e:
            print(f"获取版本失败: {e}")
            return False

    def reset_device(self):
        packet = self.build_protocol_packet(RESET_MCU)
        print(f"发送复位指令...")
        try:
            self.serial_conn.write(packet)
            self.serial_conn.flush()
            print("复位命令已发送")
            return True
        except Exception as e:
            print(f"复位失败: {e}")
            return False

    def _execute_erase_phase(self, start_addr, blocks_to_erase):
        packet = self.build_protocol_packet(FIRMWARE_ERASE, start_addr, blocks_to_erase)
        success, msg = self.send_packet_and_wait_response(packet, timeout=5.0)
        if not success:
            raise Exception(f"块擦除失败: {msg}")
        print("擦除完成")

    def _execute_program_phase(self, start_addr, complete_firmware, total_size, pages_to_program):
        transfers_needed = (pages_to_program + OTA_PAGES_PER_TRANSFER - 1) // OTA_PAGES_PER_TRANSFER
        
        for transfer in range(transfers_needed):
            start_page = transfer * OTA_PAGES_PER_TRANSFER
            remaining_pages = pages_to_program - start_page
            current_pages = min(remaining_pages, OTA_PAGES_PER_TRANSFER)
            
            transfer_addr = start_addr + start_page * W25Q32JV_PAGE_SIZE
            data_offset = start_page * W25Q32JV_PAGE_SIZE
            transfer_size = current_pages * W25Q32JV_PAGE_SIZE
            
            if data_offset + transfer_size <= total_size:
                transfer_data = complete_firmware[data_offset:data_offset + transfer_size]
            else:
                transfer_data = complete_firmware[data_offset:]
                padding_size = transfer_size - len(transfer_data)
                if padding_size > 0:
                    transfer_data += b'\xFF' * padding_size
            
            # Progress calculation
            progress = int( ((transfer + 1) / transfers_needed) * 100)
            status_msg = f"\r\x1b[K进度: {progress}% | APP {transfer + 1}/{transfers_needed}: 0x{transfer_addr:08X} "
            sys.stdout.write(status_msg)
            sys.stdout.flush()
            
            packet = self.build_protocol_packet(FIRMWARE_PROGRAM, transfer_addr, transfer_data)
            context_info = f"{transfer + 1}/{transfers_needed}"
            
            # Retry logic
            max_retries = 5
            success = False
            last_msg = ""
            
            for attempt in range(max_retries):
                if attempt > 0:
                    sys.stdout.write(f"\n写入超时，正在重试 ({attempt}/{max_retries-1})...\n")
                    time.sleep(0.5)
                
                success, msg = self.send_packet_and_wait_response(packet, timeout=2.0, context_info=context_info)
                if success:
                    break
                last_msg = msg
            
            if not success:
                raise Exception(f"多页写入失败 (0x{transfer_addr:08X}) 重试{max_retries}次后仍失败: {last_msg}")
            
            time.sleep(0.1)

        print() # Newline after loop

    def _execute_verification_phase(self, start_addr, firmware_data, firmware_size):

        packet = self.build_protocol_packet(FIRMWARE_READ_HEADER, start_addr)
        success, msg = self.send_packet_and_wait_response(packet, timeout=2.0)
        
        if success and isinstance(msg, (bytes, bytearray)):
            if len(msg) >= 5:
                payload_len = msg[3] + (msg[4] << 8)
                payload_start = 5
                data_start = payload_start + 16
                if len(msg) >= data_start + 32:
                    header_data = msg[data_start:data_start + 32]
                    
                    magic = int.from_bytes(header_data[0:4], 'little')
                    size = int.from_bytes(header_data[8:12], 'little')
                    crc32 = int.from_bytes(header_data[12:16], 'little')
                    
                    print(f"读取头: Size={size}, CRC={crc32:08X}")
                    
                    if magic == FIRMWARE_MAGIC and size == firmware_size and crc32 == self.calculate_crc32(firmware_data):
                        print("✅ 固件头验证成功")
                        return True
                    else:
                        print("⚠️ 固件头验证失败")
                        return False
            print("⚠️ 固件头数据不完整")
            return False
        else:
            print("⚠️ 固件头读取失败")
            return False

    def ota_flash(self, firmware_path):
        if not os.path.exists(firmware_path):
            print(f"文件不存在: {firmware_path}")
            return False

        with open(firmware_path, 'rb') as f:
            firmware_data = f.read()
        
        firmware_size = len(firmware_data)
        if firmware_size > MAX_FIRMWARE_SIZE:
            print(f"固件过大: {firmware_size}")
            return False
            
        firmware_header = self.generate_firmware_header(firmware_data)
        complete_firmware = firmware_header + firmware_data
        total_size = len(complete_firmware)
        start_addr = EXTERNAL_FLASH_APP_START
        
        print(f"开始OTA烧录: {total_size} 字节 -> 0x{start_addr:08X}")
        
        blocks_to_erase = (total_size + W25Q32JV_BLOCK_64K_SIZE - 1) // W25Q32JV_BLOCK_64K_SIZE
        pages_to_program = (total_size + W25Q32JV_PAGE_SIZE - 1) // W25Q32JV_PAGE_SIZE
        
        try:
            self._execute_erase_phase(start_addr, blocks_to_erase)
            self._execute_program_phase(start_addr, complete_firmware, total_size, pages_to_program)
            self._execute_verification_phase(start_addr, firmware_data, firmware_size)
            return True
        except Exception as e:
            print(f"OTA失败: {e}")
            return False

    def sr150_flash(self, firmware_path):
        if not os.path.exists(firmware_path):
            print(f"文件不存在: {firmware_path}")
            return False

        with open(firmware_path, 'rb') as f:
            firmware_data = f.read()
            
        firmware_size = len(firmware_data)
        print(f"开始SR150烧录: {firmware_size} 字节")
        
        blocks_to_erase = (firmware_size + W25Q32JV_BLOCK_64K_SIZE - 1) // W25Q32JV_BLOCK_64K_SIZE
        pages_to_program = (firmware_size + W25Q32JV_PAGE_SIZE - 1) // W25Q32JV_PAGE_SIZE
        
        try:
            self._execute_erase_phase(SR150_FLASH_START_ADDR, blocks_to_erase)
            
            # SR150 Program Phase (Similar to normal program but no header)
            transfers_needed = (pages_to_program + OTA_PAGES_PER_TRANSFER - 1) // OTA_PAGES_PER_TRANSFER
            
            for transfer in range(transfers_needed):
                start_page = transfer * OTA_PAGES_PER_TRANSFER
                remaining_pages = pages_to_program - start_page
                current_pages = min(remaining_pages, OTA_PAGES_PER_TRANSFER)
                
                transfer_addr = SR150_FLASH_START_ADDR + start_page * W25Q32JV_PAGE_SIZE
                data_offset = start_page * W25Q32JV_PAGE_SIZE
                transfer_size = current_pages * W25Q32JV_PAGE_SIZE
                
                if data_offset + transfer_size <= firmware_size:
                    transfer_data = firmware_data[data_offset:data_offset + transfer_size]
                else:
                    transfer_data = firmware_data[data_offset:]
                    padding_size = transfer_size - len(transfer_data)
                    if padding_size > 0:
                        transfer_data += b'\xFF' * padding_size
                
                status_msg = f"\r\x1b[KSR150 {transfer + 1}/{transfers_needed}: 0x{transfer_addr:08X}"
                sys.stdout.write(status_msg)
                sys.stdout.flush()
                
                packet = self.build_protocol_packet(FIRMWARE_PROGRAM, transfer_addr, transfer_data)
                context_info = f"{transfer + 1}/{transfers_needed}"
                success, msg = self.send_packet_and_wait_response(packet, timeout=2.0, context_info=context_info)
                
                if not success:
                    raise Exception(f"SR150写入失败: {msg}")
                
                time.sleep(0.1)
            
            print()
            
            # Write config
            print("写入SR150配置信息...")
            firmware_crc = self.calculate_crc_xmodem(firmware_data)
            config_data = bytearray(W25Q32JV_PAGE_SIZE)
            config_data[0:2] = struct.pack('<H', firmware_crc)
            config_data[2:6] = struct.pack('<I', firmware_size)
            for i in range(6, W25Q32JV_PAGE_SIZE):
                config_data[i] = 0xFF
            
            packet = self.build_protocol_packet(FIRMWARE_PROGRAM, 0x00300000, bytes(config_data))
            success, msg = self.send_packet_and_wait_response(packet, timeout=2.0)
            if not success:
                raise Exception(f"配置写入失败: {msg}")
                
            print("SR150烧录完成")
            return True
            
        except Exception as e:
            print(f"SR150操作失败: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='DK6 OTA Flash Tool (CLI Version)')
    parser.add_argument('--port', required=True, help='串口号 (如 /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=460800, help='波特率 (默认 460800)')
    parser.add_argument('--file', help='固件文件路径 (升级模式必需)')
    parser.add_argument('--v', action='store_true', help='获取设备版本信息')
    parser.add_argument('--mode', choices=['ota', 'sr150', 'reset'], default='ota', help='默认ota模式\n'
                                                                                            'sr150模式: 升级SR150固件\n'
                                                                                            'reset模式: 复位设备')
    parser.add_argument('--auto-reset', action='store_true', help='升级完成后自动复位设备')
    
    args = parser.parse_args()
    
    # 检查参数依赖
    if args.mode in ['ota', 'sr150'] and not args.file and not args.v:
        print("错误: 升级模式下必须指定 --file")
        sys.exit(1)
        
    client = OTAClient(args.port, args.baud)
    if not client.connect():
        sys.exit(1)
        
    try:
        if args.v:
            client.get_version()
        elif args.mode == 'reset':
            client.reset_device()
        elif args.mode == 'ota':
            if client.ota_flash(args.file):
                if args.auto_reset:
                    time.sleep(1)
                    client.reset_device()
        elif args.mode == 'sr150':
            if client.sr150_flash(args.file):
                if args.auto_reset:
                    time.sleep(1)
                    client.reset_device()
    finally:
        client.close()

if __name__ == '__main__':
    main()

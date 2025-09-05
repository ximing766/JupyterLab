#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from ppadb.client import Client as AdbClient
import time
import subprocess
import sys

def start_adb_server():
    """启动ADB服务器"""
    try:
        # 尝试启动ADB服务器
        result = subprocess.run(['adb', 'start-server'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print('ADB服务器启动成功')
            return True
        else:
            print(f'ADB服务器启动失败: {result.stderr}')
            return False
    except Exception as e:
        print(f'启动ADB服务器时出错: {e}')
        return False

def check_adb_connection():
    """检查ADB连接状态"""
    try:
        client = AdbClient(host="127.0.0.1", port=5037)
        devices = client.devices()
        return client, devices
    except Exception as e:
        print(f"ADB连接失败: {e}")
        return None, None

# 飞行模式控制函数
def toggle_airplane_mode(device, enable=True):
    """开启或关闭飞行模式"""
    if enable:
        device.shell('settings put global airplane_mode_on 1')
        device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true')
        print('正在开启飞行模式...')
    else:
        device.shell('settings put global airplane_mode_on 0')
        device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false')
        print('正在关闭飞行模式...')

def check_airplane_mode_status(device):
    """检查飞行模式状态"""
    result = device.shell('settings get global airplane_mode_on')
    return result.strip() == '1'

if __name__ == '__main__':
    try:
        # 1. 首先启动ADB服务器
        print('正在启动ADB服务器...')
        if not start_adb_server():
            sys.exit(1)
        
        # 2. 等待服务器启动
        time.sleep(2)
        
        # 3. 检查ADB连接
        print('正在连接设备...')
        client, devices = check_adb_connection()
        if not client or len(devices) == 0:
            print('没有找到连接的设备')
            print('请确保：')
            print('1. Android设备已通过USB连接到树莓派')
            print('2. 设备已开启USB调试模式')
            print('3. 已授权树莓派进行调试')
            sys.exit(1)
        
        device = devices[0]
        print(f'成功连接到设备: {device.serial}')
        
        # 4. 检查当前飞行模式状态
        print(f'当前飞行模式状态: {"开启" if check_airplane_mode_status(device) else "关闭"}')
        
        # 5. 飞行模式操作示例
        print('\n=== 飞行模式控制示例 ===')
        toggle_airplane_mode(device, True)   # 开启飞行模式
        time.sleep(3)
        toggle_airplane_mode(device, False)  # 关闭飞行模式
        
        # 6. 再次检查状态
        time.sleep(2)
        print(f'操作后飞行模式状态: {"开启" if check_airplane_mode_status(device) else "关闭"}')
        
    except KeyboardInterrupt:
        print('\n程序被用户中断')
    except Exception as e:
        print(f'程序运行出错: {e}')
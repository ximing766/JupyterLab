import sys
import os
import time
import threading
import ctypes
import serial
import serial.tools.list_ports
from datetime import datetime
from Ecb_Des import MyEcbDes



class UwbService:
    def __init__(self):
        self.version = "_v1.0"
        self.trans_flag = 0
        self.EnterSerial = None
        self.ExitSerial = None
        self.enter_running = False
        self.exit_running = False
        self.timeout_threshold = 0.1
        self.enter_id = 1
        self.exit_id = 1
        self.sequence = "06FFFFFFFFFF05FFFFFFFFFF"

        self.defaultKey = bytes.fromhex("32D464AC81F1640A687D023BF99E35DF")
        self.posId = "040900010001"
        self.EnterMoney = "00000001"
        self.ExitMoney = "00000001"
        self.EnterEP = "03"
        self.ExitEP = "04"
        self.balance = "00002190"
        self.CardNo = ""
        self.MAC = "00000000"
        self.OnlineSeqNo = ""
        self.RandomNo = ""
        self.halt_data_res = "0000FF130005FFFFFFFFFF06FFFFFFFFFF45C20001010000F600"

        self.DateTime = datetime.now().strftime("%Y%m%d%H%M%S")
        self.MyEcbDes = MyEcbDes() if MyEcbDes else None

        self.enter_port = ""
        self.exit_port = ""
        self.enter_baud = 460800
        self.exit_baud = 460800
        self.e1_check_enabled = True

        self.on_enter_log = None
        self.on_exit_log = None
        self.on_error = None
        self.on_state = None

        self.port_options = []
        self.old_port_options = []

    def set_callbacks(self, on_enter_log=None, on_exit_log=None, on_error=None, on_state=None):
        self.on_enter_log = on_enter_log
        self.on_exit_log = on_exit_log
        self.on_error = on_error
        self.on_state = on_state

    def set_enter_port(self, port, baud):
        self.enter_port = port or ""
        self.enter_baud = int(baud) if baud else 460800

    def set_exit_port(self, port, baud):
        self.exit_port = port or ""
        self.exit_baud = int(baud) if baud else 460800

    def set_e1_check(self, enabled: bool):
        self.e1_check_enabled = bool(enabled)

    def calculate_DCS(self, hex_string):
        data = bytes.fromhex(hex_string)
        s = sum(data)
        low = s % 256
        comp = (256 - low) % 256
        return f"{comp:02x}"

    def update_read_data_res(self, type_):
        industry_code_map = {
            "公交": "01",
            "地铁": "02",
            "轮渡": "03",
            "BRT": "04",
        }
        self.DateTime = datetime.now().strftime("%Y%m%d%H%M%S")
        if type_ == 0:
            Enter_IndustryCode_val = industry_code_map.get(self.IndustryCode_val, "BRT")
            Enter_Line_val = self.Line_val
            Enter_Site_val = self.Site_val
            if self.EnterMoney == "":
                self._error("please input enter money")
                return 0
            self.enter_read_data_res = (
                "05FFFFFFFFFF06FFFFFFFFFF2AC200021100805003020B01"
                + self.EnterMoney
                + self.posId
                + "0F"
                + "350080DC00F030"
                + self.EnterEP
                + "0000"
                + self.posId
                + Enter_IndustryCode_val
                + Enter_Line_val
                + Enter_Site_val
                + "000015"
                + self.EnterMoney
                + self.balance
                + self.DateTime
                + "584012215840FFFFFFFF000000000000"
            )
            dcs = self.calculate_DCS(self.enter_read_data_res)
            self.enter_read_data_res = "0000FF5A00" + self.enter_read_data_res + dcs + "00"
        elif type_ == 1:
            Exit_IndustryCode_val = industry_code_map.get(self.IndustryCode_val1, "BRT")
            Exit_Line_val = self.Line_val1
            Exit_Site_val = self.Site_val1
            if self.ExitMoney == "":
                self._error("please input exit money")
                return 0
            self.exit_read_data_res = (
                "05FFFFFFFFFF06FFFFFFFFFF2AC200021100805003020B01"
                + self.ExitMoney
                + self.posId
                + "0F"
                + "350080DC00F030"
                + self.ExitEP
                + "0000"
                + self.posId
                + Exit_IndustryCode_val
                + Exit_Line_val
                + Exit_Site_val
                + "000015"
                + self.ExitMoney
                + self.balance
                + self.DateTime
                + "584012215840FFFFFFFF000000000000"
            )
            dcs = self.calculate_DCS(self.exit_read_data_res)
            self.exit_read_data_res = "0000FF5A00" + self.exit_read_data_res + dcs + "00"
        return 1

    def update_write_data_res(self):
        self.enter_write_data_res = (
            "05FFFFFFFFFF06FFFFFFFFFF17C200011500805401000F00000001" + self.DateTime
        )
        self.exit_write_data_res = (
            "05FFFFFFFFFF06FFFFFFFFFF17C200011500805401000F00000001" + self.DateTime
        )
        self.Enter_macdata = bytes.fromhex(
            self.EnterMoney + "09" + self.posId + self.DateTime + "80" + "0000000000"
        )
        self.Exit_macdata = bytes.fromhex(
            self.ExitMoney + "09" + self.posId + self.DateTime + "80" + "0000000000"
        )

    def _error(self, msg):
        if self.on_error:
            self.on_error(str(msg))

    def get_available_ports(self):
        try:
            import winreg
            self.old_port_options = self.port_options.copy()
            self.port_options = []
            path = "HARDWARE\\DEVICEMAP\\SERIALCOMM"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            for i in range(256):
                try:
                    val = winreg.EnumValue(key, i)
                    self.port_options.append(val[1])
                except Exception:
                    break
            winreg.CloseKey(key)
            if not self.port_options:
                ports = serial.tools.list_ports.comports()
                self.port_options = [p.device for p in ports]
        except Exception:
            try:
                ports = serial.tools.list_ports.comports()
                self.port_options = [p.device for p in ports]
            except Exception:
                self.port_options = []
        return self.port_options

    def connect_enter(self):
        try:
            if self.enter_port:
                self.EnterSerial = serial.Serial(self.enter_port, self.enter_baud, timeout=0.05)
                self.enter_running = True
                t = threading.Thread(target=self.read_data_enter, daemon=True)
                self.read_thread_enter = t
                t.start()
                if self.on_state:
                    self.on_state("enter", True)
        except Exception as e:
            self._error(e)

    def connect_exit(self):
        try:
            if self.exit_port:
                self.ExitSerial = serial.Serial(self.exit_port, self.exit_baud, timeout=0.05)
                self.exit_running = True
                t = threading.Thread(target=self.read_data_exit, daemon=True)
                self.read_thread_exit = t
                t.start()
                if self.on_state:
                    self.on_state("exit", True)
        except Exception as e:
            self._error(e)

    def disconnect_enter(self):
        try:
            self.enter_running = False
            if getattr(self, "read_thread_enter", None):
                self.read_thread_enter.join(timeout=1.0)
            if self.EnterSerial:
                self.EnterSerial.close()
                self.EnterSerial = None
            if self.on_state:
                self.on_state("enter", False)
        except Exception as e:
            self._error(e)

    def disconnect_exit(self):
        try:
            self.exit_running = False
            if getattr(self, "read_thread_exit", None):
                self.read_thread_exit.join(timeout=1.0)
            if self.ExitSerial:
                self.ExitSerial.close()
                self.ExitSerial = None
            if self.on_state:
                self.on_state("exit", False)
        except Exception as e:
            self._error(e)

    def on_window_closing(self):
        if self.enter_running:
            self.disconnect_enter()
        if self.exit_running:
            self.disconnect_exit()

    def get_mac(self, write_data_res, type_):
        try:
            if not self.MyEcbDes:
                self._error("算法模块缺失")
                return False
            macdata = self.Enter_macdata if type_ == 0 else self.Exit_macdata
            if len(self.CardNo) != 20 or len(self.RandomNo) != 8 or len(self.OnlineSeqNo) != 4:
                return False
            factor = self.CardNo[-16:]
            xor_result = self.MyEcbDes.str_xor(factor, "FFFFFFFFFFFFFFFF")
            factor = bytes.fromhex(factor + xor_result)
            loadKey = self.MyEcbDes.des3_encrypt(self.defaultKey, factor)[:16]
            sessionKey = self.MyEcbDes.des3_encrypt(loadKey, bytes.fromhex(self.RandomNo + self.OnlineSeqNo + "0001"))[:8]
            self.MAC = self.MyEcbDes.process_macdata(sessionKey, macdata)[:4].hex()
            write_data_res = write_data_res + self.MAC + "08"
            dcs = self.calculate_DCS(write_data_res)
            write_data_res = "0000FF2700" + write_data_res + dcs + "00"
            if type_ == 0:
                self.enter_write_data_res = write_data_res
            else:
                self.exit_write_data_res = write_data_res
        except Exception as e:
            self._error(e)
            return False
        return True

    def ApduHandle(self, data, sequence, is_enter=True):
        data_upper = data.upper()
        sequence_upper = sequence.upper()
        index = data_upper.find(sequence_upper)
        if index == -1:
            return
        pos = {
            "COMMAND": (index + 26, index + 28),
            "STATUS": (index + 28, index + 30),
            "APDU_NUM": (index + 30, index + 32),
            "BALANCE": (index + 36, index + 44),
            "ONLINE_SEQ": (index + 44, index + 48),
            "RANDOM_NO": (index + 58, index + 66),
            "R_APDU_NUM": (index + 54, index + 56),
            "W_APDU_NUM": (index + 30, index + 32),
            "E1": (index + 710, index + 712),
            "APPLET_RES": (index + 148, index + 152),
        }
        command = data_upper[pos["COMMAND"][0]:pos["COMMAND"][1]]
        status = data_upper[pos["STATUS"][0]:pos["STATUS"][1]]
        apdu_num = int(data_upper[pos["APDU_NUM"][0]:pos["APDU_NUM"][1]], 16)
        send_data = self.send_enter_data if is_enter else self.send_exit_data
        station_type = 0 if is_enter else 1
        if command == "C2" and status == "00" and apdu_num > 5:
            e1 = data_upper[pos["E1"][0]:pos["E1"][1]]
            if self.e1_check_enabled:
                if is_enter and e1 not in ["04", "00"]:
                    self._log(is_enter, "请勿重复进站")
                    return
                if not is_enter and e1 not in ["03"]:
                    self._log(is_enter, "进出站逻辑顺序错误")
                    return
            card_pattern = "0310487"
            card_start_index = data_upper.find(card_pattern)
            if card_start_index != -1:
                self.CardNo = data_upper[card_start_index:card_start_index + 20]
            else:
                self.CardNo = ""
                self._log(is_enter, "未找到有效的SZT卡号")
                return
            if self.update_read_data_res(station_type) != 0:
                send_data(self.enter_read_data_res if is_enter else self.exit_read_data_res, 1)
        elif command == "C2" and status == "00" and apdu_num == 2:
            balance = data_upper[pos["BALANCE"][0]:pos["BALANCE"][1]]
            self.OnlineSeqNo = data_upper[pos["ONLINE_SEQ"][0]:pos["ONLINE_SEQ"][1]]
            self.RandomNo = data_upper[pos["RANDOM_NO"][0]:pos["RANDOM_NO"][1]]
            self.update_write_data_res()
            if self.get_mac(self.enter_write_data_res if is_enter else self.exit_write_data_res, station_type):
                send_data(self.enter_write_data_res if is_enter else self.exit_write_data_res, 2)
        elif command == "C2" and status == "00" and apdu_num == 1:
            send_data(self.halt_data_res, 3)
            print("HALT")

    def read_data_enter(self):
        buffer = b""
        last_receive_time = time.time()
        while self.enter_running and self.EnterSerial:
            try:
                data = self.EnterSerial.read(1024)
                if data:
                    buffer += data
                    last_receive_time = time.time()
                else:
                    if time.time() - last_receive_time > self.timeout_threshold:
                        if buffer:
                            hex_data = buffer.hex()
                            self.ApduHandle(hex_data, self.sequence, True)
                            buffer = b""
                        last_receive_time = time.time()
            except serial.SerialException as e:
                self._error(e)
                self.disconnect_enter()
            except Exception as e:
                self._error(e)

    def read_data_exit(self):
        buffer = b""
        last_receive_time = time.time()
        while self.exit_running and self.ExitSerial:
            try:
                data = self.ExitSerial.read(1024)
                if data:
                    buffer += data
                    last_receive_time = time.time()
                else:
                    if time.time() - last_receive_time > self.timeout_threshold:
                        if buffer:
                            hex_data = buffer.hex()
                            self.ApduHandle(hex_data, self.sequence, False)
                            buffer = b""
                        last_receive_time = time.time()
            except serial.SerialException as e:
                self._error(e)
                self.disconnect_exit()
            except Exception as e:
                self._error(e)

    def send_enter_data(self, hex_data, type_):
        try:
            if len(hex_data) % 2 != 0:
                self._error("data len is not even")
                return
            byte_data = bytes.fromhex(hex_data)
            if self.EnterSerial and self.EnterSerial.is_open:
                self.EnterSerial.write(byte_data)
                if type_ == 2:
                    self.enter_write_data_res = "05FFFFFFFFFF06FFFFFFFFFF17C20115805401000F00000001" + self.DateTime
                elif type_ == 3:
                    spendmsg = (
                        str(self.enter_id)
                        + " | "
                        + datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
                        + " | "
                        + "消费: $"
                        + str(int(self.EnterMoney, 16) / 100)
                        + " | OK"
                    )
                    self._log(True, spendmsg)
                    self.enter_id += 1
        except ValueError as e:
            self._error(e)

    def send_exit_data(self, hex_data, type_):
        try:
            if len(hex_data) % 2 != 0:
                self._error("data len is not even")
                return
            byte_data = bytes.fromhex(hex_data)
            if self.ExitSerial and self.ExitSerial.is_open:
                self.ExitSerial.write(byte_data)
                if type_ == 2:
                    self.exit_write_data_res = "05FFFFFFFFFF06FFFFFFFFFF17C20115805401000F00000001" + self.DateTime
                elif type_ == 3:
                    spendmsg = (
                        str(self.exit_id)
                        + " | "
                        + datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
                        + " | 消费: ￥"
                        + str(int(self.ExitMoney, 16) / 100)
                        + " | OK"
                    )
                    self._log(False, spendmsg)
                    self.exit_id += 1
        except ValueError as e:
            self._error(e)

    def _log(self, is_enter, msg):
        if is_enter:
            if self.on_enter_log:
                self.on_enter_log(str(msg))
        else:
            if self.on_exit_log:
                self.on_exit_log(str(msg))

    def set_enter_parameters(self, industry, line, site, money_hex):
        self.IndustryCode_val = industry
        self.Line_val = line
        self.Site_val = site
        self.EnterMoney = money_hex

    def set_exit_parameters(self, industry, line, site, money_hex):
        self.IndustryCode_val1 = industry
        self.Line_val1 = line
        self.Site_val1 = site
        self.ExitMoney = money_hex
import tkinter as tk
import serial
import serial.tools.list_ports
import threading
import ttkbootstrap as ttk
import customtkinter
import ctypes
import time
from PIL import Image,ImageTk
import os
import sys
from tkinter import messagebox
from datetime import datetime
sys.path.append("E:/Work/UWB/Code/UwbCOMCode")
from Crypto.Cipher import DES, DES3
from Crypto.Util.Padding import pad, unpad
from Algorithm.Ecb_Des import MyEcbDes

class UwbReaderAssistant:
    def __init__(self, master):
        self.master = master
        self.version = "_v1.0"
        self.master.title("UWBReader"+self.version)
        print("UWBReader"+self.version)
        self.master.minsize(400, 200)
        self.master.geometry("900x450")
        icon_path = os.path.join(os.path.dirname(__file__), 'UWBReader.ico')
        self.master.wm_iconbitmap(icon_path)
        self.Init_image()
        self.MyEcbDes = MyEcbDes()

        self.trans_flag = 0

        self.EnterSerial = None
        self.ExitSerial = None
        self.enter_running = False
        self.exit_running = False
        self.timeout_threshold = 0.1     #XXX 现在的写卡时间为6-700ms
        self.enter_id = 1
        self.exit_id = 1
        self.sequence = "06FFFFFFFFFF05FFFFFFFFFF"

        self.defaultKey = bytes.fromhex("32D464AC81F1640A687D023BF99E35DF")
        self.posId      = "040900010001"
        self.EnterMoney = "00000001"     
        self.ExitMoney = "00000001"
        self.EnterEP = "03"
        self.ExitEP = "04"
        self.balance = "00002190"
        self.CardNo = ""
        self.MAC = "00000000"
        self.OnlineSeqNo = ""
        self.RandomNo = ""
        self.halt_data_res =  "0000FF130005FFFFFFFFFF06FFFFFFFFFF45C20001010000F600"

        self.create_widgets()

        self.update_ports_periodically()
    
    def update_read_data_res(self, type):
        industry_code_map = {
            "公交": "01",
            "地铁": "02",
            "轮渡": "03",
            "BRT": "04"
        }
        current_time = datetime.now()
        self.DateTime = current_time.strftime("%Y%m%d%H%M%S")     # 出现长度错误后返回这儿将时间更新了，后续手机端读写时间不一致
        if type == 0:
            Enter_IndustryCode_val = industry_code_map.get(self.IndustryCode_val.get(), "BRT")
            Enter_Line_val = self.Line_val.get()
            Enter_Site_val = self.Site_val.get()
            if self.money_entry.get() == "":
                self.EnterMoney = self.money_entry.get()
                messagebox.showerror("please input enter money:h")
                return 0
            # print(f"Enter_IndustryCode: {Enter_IndustryCode_val}  Enter_Line: {Enter_Line_val}  Enter_Site: {Enter_Site_val}")
            self.enter_read_data_res = "05FFFFFFFFFF06FFFFFFFFFF2AC200021100805003020B01" + self.EnterMoney + self.posId + "0F"+ "350080DC00F030" + self.EnterEP + "0000" + self.posId \
                                        + Enter_IndustryCode_val + Enter_Line_val + Enter_Site_val + "000015" + self.EnterMoney + self.balance + self.DateTime + "584012215840FFFFFFFF000000000000"
            self.dcs = self.calculate_DCS(self.enter_read_data_res)
            self.enter_read_data_res = "0000FF5A00" + self.enter_read_data_res + self.dcs + "00"                #XXX 长度57为self.enter_read_data_res的长度
        elif type == 1:
            Exit_IndustryCode_val = industry_code_map.get(self.IndustryCode_val1.get(), "BRT")
            Exit_Line_val = self.Line_val1.get()
            Exit_Site_val = self.Site_val1.get()
            self.ExitMoney = self. money_exit.get()
            if self.ExitMoney == "":
                messagebox.showerror("please input exit money:")
                return 0
            # print(f"Exit_IndustryCode: {Exit_IndustryCode_val}  Exit_Line: {Exit_Line_val}  Exit_Site: {Exit_Site_val}")
            self.exit_read_data_res = "05FFFFFFFFFF06FFFFFFFFFF2AC200021100805003020B01" + self.ExitMoney + self.posId + "0F"+ "350080DC00F030" + \
                                    self.ExitEP + "0000" + self.posId + Exit_IndustryCode_val + Exit_Line_val + Exit_Site_val + "000015" + \
                                    self.ExitMoney + self.balance + self.DateTime + "584012215840FFFFFFFF000000000000"
            self.dcs = self.calculate_DCS(self.exit_read_data_res)
            self.exit_read_data_res = "0000FF5A00" + self.exit_read_data_res + self.dcs + "00"
        return 1
    # BM: 初始读写卡数据
    def update_write_data_res(self):
        self.enter_write_data_res = "05FFFFFFFFFF06FFFFFFFFFF17C200011500805401000F00000001"+self.DateTime      #+self.MAC+"08"+"F500"
        self.exit_write_data_res = "05FFFFFFFFFF06FFFFFFFFFF17C200011500805401000F00000001"+self.DateTime
        self.Enter_macdata = self.EnterMoney + "09" + self.posId + self.DateTime + "80" + "0000000000"     # 这里的时间需要和APDU的时间一致
        self.Enter_macdata = bytes.fromhex(self.Enter_macdata)
        self.Exit_macdata = self.ExitMoney + "09" + self.posId + self.DateTime + "80" + "0000000000"
        self.Exit_macdata = bytes.fromhex(self.Exit_macdata)

    def create_widgets(self):
        for col in range(7):
            self.master.grid_columnconfigure(col, weight=1)
        self.master.grid_rowconfigure(0, weight=0)
        self.master.grid_rowconfigure(2, weight=1)

        self.port_options = []
        self.port_var = tk.StringVar(self.master)
        self.port_var1 = tk.StringVar(self.master)
        
        self.baudrate_var = tk.IntVar(self.master, 460800)  
        self.baudrate_var1 = tk.IntVar(self.master, 460800)  
        self.font = ["Roboto", "Times New Roman", "Segoe UI"]
        def create_label(master, text, column, row, columnspan, padx, pady):
            label_style = {
                "corner_radius": 15,
                "fg_color": ("#E0E0E0", "#87CEEB"),
                "font": ("Times New Roman", 20, "bold"),    
                "text_color": "#6A1B9A",
                "anchor": "center"
            }
            label = customtkinter.CTkLabel(master, text=text, **label_style)
            label.grid(column=column, row=row, columnspan=columnspan, padx=padx, pady=pady, sticky='ew')
            return label

        # 创建标题
        self.port_label = create_label(self.master, "ENTER", 0, 0, 3, 75, (10,0))
        self.port_label1 = create_label(self.master, "EXIT", 4, 0, 3, 75, (10,0))

        ## Tab ##
        TabColor = ("#E0F2F8","#AED6F1")
        TextColor = ("#663300", "#663300")
        self.EnterTab = customtkinter.CTkTabview(self.master, fg_color=TabColor)
        self.EnterTab.grid(row=2, column=0, columnspan=3, rowspan=5, padx=10, pady=(10),sticky='nsew')
        self.EnterTab.add("COM")
        self.EnterTab.add("Setting")
        self.EnterTab.add("Log")
        self.EnterTab.set("COM")

        self.ExitTab = customtkinter.CTkTabview(master=self.master, fg_color=TabColor)
        self.ExitTab.grid(row=2, column=4, columnspan=3, rowspan = 5, padx=10, pady=10,sticky='nsew')
        self.ExitTab.add("COM")
        self.ExitTab.add("Setting")
        self.ExitTab.add("Log")
        self.ExitTab.set("COM")

        EnterTabFrame = customtkinter.CTkFrame(self.EnterTab.tab("Log"))
        EnterTabFrame.pack(padx=20, pady=20, fill="both", expand=True)
        EnterTabFrame.grid_columnconfigure(0, weight=1)
        EnterTabFrame.grid_rowconfigure(0, weight=1)
        ExitTabFrame = customtkinter.CTkFrame(self.ExitTab.tab("Log"))
        ExitTabFrame.pack(padx=20, pady=20, fill="both", expand=True)
        ExitTabFrame.grid_columnconfigure(0, weight=1)
        ExitTabFrame.grid_rowconfigure(0, weight=1)

        ## Textbox ##
        self.text_area = customtkinter.CTkTextbox(EnterTabFrame, width=200, height=400,  fg_color=("#E6E6FF", "#A0C8CF"), text_color="black")
        self.text_area.grid(row=0, column=0,padx=1, pady=1, sticky='nsew')
        self.clear_button = customtkinter.CTkButton(EnterTabFrame, text="", command=self.clear_text_area, font=("Roboto", 15), image=self.delete_img)
        self.clear_button.grid(row=1, column=0, padx=1, pady=1, sticky="ew")

        self.text_area1 = customtkinter.CTkTextbox(ExitTabFrame, width=200, height=400,  fg_color=("#E6E6FF", "#A0C8CF"), text_color="black")  
        self.text_area1.grid(row=0, column=0,padx=1, pady=1, sticky='nsew')
        self.clear_button1 = customtkinter.CTkButton(ExitTabFrame, text="", command=self.clear_text_area1, font=("Roboto", 15), image=self.delete_img)
        self.clear_button1.grid(row=1, column=0, padx=1,pady=1, sticky="ew")
        
        ## Setting ##
        industry_frame = customtkinter.CTkFrame(self.EnterTab.tab("Setting"),fg_color= TabColor)
        industry_frame.pack(padx=20, pady=10, fill="x")
        industry_code_label = customtkinter.CTkLabel(industry_frame, text="行业代码:", font=("Roboto", 15), text_color=TextColor)
        industry_code_label.pack(side="left", padx=(0, 10))  
        self.IndustryCode_val = tk.StringVar(self.master, "BRT")
        self.IndustryCode_menu = customtkinter.CTkOptionMenu(industry_frame, variable=self.IndustryCode_val, values=["公交", "地铁", "轮渡", "BRT"], font=("Roboto", 15))
        self.IndustryCode_menu.pack(side="left")

        line_frame = customtkinter.CTkFrame(self.EnterTab.tab("Setting"),fg_color= TabColor)
        line_frame.pack(padx=20, pady=10, fill="x")
        line_label = customtkinter.CTkLabel(line_frame, text="线路代码:", font=("Roboto", 15), text_color=TextColor)
        line_label.pack(side="left", padx=(0, 10)) 
        self.Line_val = tk.StringVar(self.master, "0000")
        self.Line_menu = customtkinter.CTkOptionMenu(line_frame, variable=self.Line_val, values=["0000", "0001", "0002", "0003"], font=("Roboto", 15))
        self.Line_menu.pack(side="left")
        
        site_frame = customtkinter.CTkFrame(self.EnterTab.tab("Setting"),fg_color= TabColor)
        site_frame.pack(padx=20, pady=10, fill="x")
        site_label = customtkinter.CTkLabel(site_frame, text="站点代码:", font=("Roboto", 15), text_color=TextColor)
        site_label.pack(side="left", padx=(0, 10))  
        self.Site_val = tk.StringVar(self.master, "0000")
        self.Site_menu = customtkinter.CTkOptionMenu(site_frame, variable=self.Site_val, values=["0000", "0001", "0002", "0003"], font=("Roboto", 15))
        self.Site_menu.pack(side="left")

        money_frame = customtkinter.CTkFrame(self.EnterTab.tab("Setting"),fg_color= TabColor)
        money_frame.pack(padx=20, pady=10, fill="x")
        money_label = customtkinter.CTkLabel(money_frame, text="入站金额:", font=("Roboto", 15), text_color=TextColor)
        money_label.pack(side="left", padx=(0, 10))  
        self.money_entry = customtkinter.CTkEntry(money_frame, font=("Roboto", 15), placeholder_text="请输入金额")
        self.money_entry.insert(0, "00000000")
        self.money_entry.pack(side="left")

        ## Setting ##
        industry_code_frame = customtkinter.CTkFrame(self.ExitTab.tab("Setting"),fg_color= TabColor)
        industry_code_frame.pack(padx=20, pady=10, fill="x")
        industry_code_label = customtkinter.CTkLabel(industry_code_frame, text="行业代码:", font=("Roboto", 15), text_color=TextColor)
        industry_code_label.pack(side="left", padx=(0, 10))  
        self.IndustryCode_val1 = tk.StringVar(self.master, "BRT")
        self.IndustryCode_menu1 = customtkinter.CTkOptionMenu(industry_code_frame, variable=self.IndustryCode_val1, values=["公交", "地铁", "轮渡", "BRT"], font=("Roboto", 15))
        self.IndustryCode_menu1.pack(side="left")

        line_frame1 = customtkinter.CTkFrame(self.ExitTab.tab("Setting"),fg_color= TabColor)
        line_frame1.pack(padx=20, pady=10, fill="x")
        line_label = customtkinter.CTkLabel(line_frame1, text="线路代码:", font=("Roboto", 15), text_color=TextColor)
        line_label.pack(side="left", padx=(0, 10))  
        self.Line_val1 = tk.StringVar(self.master, "0000")
        self.Line_menu1 = customtkinter.CTkOptionMenu(line_frame1, variable=self.Line_val1, values=["0000", "0001", "0002", "0003"], font=("Roboto", 15))
        self.Line_menu1.pack(side="left")

        site_frame1 = customtkinter.CTkFrame(self.ExitTab.tab("Setting"),fg_color= TabColor)
        site_frame1.pack(padx=20, pady=10, fill="x")
        site_label = customtkinter.CTkLabel(site_frame1, text="站点代码:", font=("Roboto", 15), text_color=TextColor)
        site_label.pack(side="left", padx=(0, 10))  
        self.Site_val1 = tk.StringVar(self.master, "0000")
        self.Site_menu1 = customtkinter.CTkOptionMenu(site_frame1, variable=self.Site_val1, values=["0000", "0001", "0002", "0003"], font=("Roboto", 15))
        self.Site_menu1.pack(side="left")

        money_frame1 = customtkinter.CTkFrame(self.ExitTab.tab("Setting"),fg_color= TabColor)
        money_frame1.pack(padx=20, pady=10, fill="x")
        money_label1 = customtkinter.CTkLabel(money_frame1, text="出站金额:", font=("Roboto", 15), text_color=TextColor)
        money_label1.pack(side="left", padx=(0, 10)) 
        self.money_exit = customtkinter.CTkEntry(money_frame1, font=("Roboto", 15), placeholder_text="请输入金额")
        self.money_exit.insert(0, "00000001")
        self.money_exit.pack(side="left")

        ## COM Enter ##
        port_frame = customtkinter.CTkFrame(self.EnterTab.tab("COM"),fg_color= TabColor)
        port_frame.pack(padx=20, pady=10, fill="x")
        port_label = customtkinter.CTkLabel(port_frame, text="COM选择 :", font=("Roboto", 15), text_color=TextColor)
        port_label.pack(side="left", padx=(0, 22))  

        self.port_menu = customtkinter.CTkOptionMenu(port_frame, variable=self.port_var, values=[*self.port_options], font=("Roboto", 15))
        self.port_menu.pack(side="left")
        baudrate_frame = customtkinter.CTkFrame(self.EnterTab.tab("COM"),fg_color= TabColor)
        baudrate_frame.pack(padx=20, pady=10, fill="x")
        baudrate_label = customtkinter.CTkLabel(baudrate_frame, text="波特率选择 :", font=("Roboto", 15), text_color=TextColor)
        baudrate_label.pack(side="left", padx=(0, 10))  
        self.baudrate_menu = customtkinter.CTkOptionMenu(baudrate_frame, variable=self.baudrate_var, values=["230400","460800", "115200", "3000000", "9600"], font=("Roboto", 15))
        self.baudrate_menu.pack(side="left")

        self.segemented_button = customtkinter.CTkSegmentedButton(self.EnterTab.tab("COM"), values=["Connect", "Disconnect"], command=self.segmented_button_callback, font=("Roboto", 15), width=200)
        self.segemented_button.pack(padx=20, pady=10, fill="x")
        self.segemented_button.set("Disconnect")

        other_frame = customtkinter.CTkFrame(self.EnterTab.tab("COM"),fg_color= TabColor)
        other_frame.pack(padx=20, pady=10, fill="x")

        self.switch_var = customtkinter.StringVar(value="off")
        switch = customtkinter.CTkCheckBox(other_frame, text="Pin to Screen", command=self.toggle_topmost, variable=self.switch_var, onvalue="on", offvalue="off", text_color=TextColor)
        switch.pack(side="left", padx=(0, 10), pady=(0,10))
        
        # 添加E1检查开关
        self.e1_check_var = customtkinter.StringVar(value="on")
        e1_check_switch = customtkinter.CTkCheckBox(other_frame, text="1E检查", variable=self.e1_check_var, onvalue="on", offvalue="off", text_color=TextColor)
        e1_check_switch.pack(side="left", padx=(0, 0), pady=(0,10))
        
        # 创建新的一行框架
        

        ## COM Exit ##
        port_frame1 = customtkinter.CTkFrame(self.ExitTab.tab("COM"),fg_color= TabColor)
        port_frame1.pack(padx=20, pady=10, fill="x")
        port_label1 = customtkinter.CTkLabel(port_frame1, text="COM选择 :", font=("Roboto", 15), text_color=TextColor)
        port_label1.pack(side="left", padx=(0, 22))  
        self.port_menu1 = customtkinter.CTkOptionMenu(port_frame1, variable=self.port_var1, values=[*self.port_options], font=("Roboto", 15))
        self.port_menu1.pack(side="left")

        baudrate_frame1 = customtkinter.CTkFrame(self.ExitTab.tab("COM"),fg_color= TabColor)
        baudrate_frame1.pack(padx=20, pady=10, fill="x")
        baudrate_label1 = customtkinter.CTkLabel(baudrate_frame1, text="波特率选择 :", font=("Roboto", 15), text_color=TextColor)
        baudrate_label1.pack(side="left", padx=(0, 10))  
        self.baudrate_menu1 = customtkinter.CTkOptionMenu(baudrate_frame1, variable=self.baudrate_var1, values=["230400","460800", "115200", "3000000", "9600"], font=("Roboto", 15))
        self.baudrate_menu1.pack(side="left")

        self.segemented_button1 = customtkinter.CTkSegmentedButton(self.ExitTab.tab("COM"), values=["Connect", "Disconnect"], command=self.segmented_button_callback1, font=("Roboto", 15), width=200)
        self.segemented_button1.pack(padx=20, pady=10, fill="x")
        self.segemented_button1.set("Disconnect")

    def calculate_DCS(self,hex_string):
        data = bytes.fromhex(hex_string)
        sum_bytes = sum(data)
        low_byte_sum = sum_bytes % 256
        complement = (256 - low_byte_sum) % 256
        complement_hex_str = f"{complement:02x}"
        return complement_hex_str
    
    def RS_Encode(self, data):
        codeword = (ctypes.c_ubyte * (len(data) + 10))()
        self.my_lib.encode_data((ctypes.c_ubyte * len(data)).from_buffer_copy(data), len(data), codeword)
        # result = bytes(codeword)
        hex_string = ''.join(f'{byte:02x}' for byte in bytes(codeword))
        print("Encoded data:", hex_string)
        return hex_string
    
    def clear_text_area(self):
        self.enter_id = 1
        self.text_area.delete(1.0, tk.END)  

    def clear_text_area1(self):
        self.exit_id = 1
        self.text_area1.delete(1.0, tk.END)  
    
    def segmented_button_callback(self, value):
        # print(f"enter callback of segmented button: {value}")
        if value == "Connect":
            self.connect_enter()
        elif value == "Disconnect":
            self.disconnect_enter()

    def segmented_button_callback1(self, value):
        # print(f"exit callback of segmented button: {value}")
        if value == "Connect":
            self.connect_exit()
        elif value == "Disconnect":
            self.disconnect_exit()
            
    def get_serial_ports(self):
        ports = []
        try:
            ports = serial.tools.list_ports.comports()
            ports = [port.device for port in ports]
        except Exception as e:
            messagebox.showerror("Request Uart List error:", e)
        return ports

    def connect_enter(self): 
        try:
            if self.port_var.get():
                self.EnterSerial = serial.Serial(self.port_var.get(), self.baudrate_var.get(), timeout=0.05)
                self.enter_running = True
                self.read_thread_enter = threading.Thread(target=self.read_data_enter)
                self.read_thread_enter.start()
        except Exception as e:
            messagebox.showerror("Connect Uart error:", e)
            self.segemented_button.set("Disconnect")
    
    def connect_exit(self):
        try:
            if self.port_var1.get():
                self.ExitSerial = serial.Serial(self.port_var1.get(), self.baudrate_var1.get(), timeout=0.05)
                self.exit_running = True
                self.read_thread_exit = threading.Thread(target=self.read_data_exit)
                self.read_thread_exit.start()
        except Exception as e:
            messagebox.showerror("Connect Uart error:", e)
            self.segemented_button1.set("Disconnect")

    def disconnect_enter(self):
        try:
            self.enter_running = False
            if self.read_thread_enter:
                self.read_thread_enter.join()
            if self.EnterSerial:
                self.EnterSerial.close()
        except Exception as e:
            messagebox.showerror("Disconnect Uart error:", e)

    def disconnect_exit(self):
        self.exit_running = False
        if self.read_thread_exit:
            self.read_thread_exit.join()
        if self.ExitSerial:
            self.ExitSerial.close()
    
    def on_window_closing(self):
        if self.enter_running == True:
            self.disconnect_enter()
        if self.exit_running == True:
            self.disconnect_exit()
        self.master.destroy()
    
    def get_mac(self, write_data_res, type):  # BM: 计算MAC
        try:
            macdata = self.Enter_macdata if type == 0 else self.Exit_macdata   #修改macdata

            if len(self.CardNo) != 20 or len(self.RandomNo) != 8 or len(self.OnlineSeqNo) != 4:
                print(f"Len ERROR: \nlen(self.CardNo) = {len(self.CardNo)} len(self.RandomNo) = {len(self.RandomNo)} len(self.OnlineSeqNo) = {len(self.OnlineSeqNo)}")
                print(f"CardNo: {self.CardNo}  RandomNo: {self.RandomNo}  OnlineSeqNo: {self.OnlineSeqNo}")
                return False
            print(f"RandomNo: {self.RandomNo}  OnlineSeqNo: {self.OnlineSeqNo}  CardNo: {self.CardNo}  DateTime: {self.DateTime}")
            factor = self.CardNo[-16:]
            xor_result = self.MyEcbDes.str_xor(factor, "FFFFFFFFFFFFFFFF")
            factor = factor + xor_result
            factor = bytes.fromhex(factor)
            loadKey = self.MyEcbDes.des3_encrypt(self.defaultKey, factor)[:16]
            # print("loadKey: ", loadKey.hex())
            sessionKey = self.MyEcbDes.des3_encrypt(loadKey, bytes.fromhex(self.RandomNo + self.OnlineSeqNo + "0001"))[:8]
            # print("sessionKey", sessionKey.hex())
            self.MAC = self.MyEcbDes.process_macdata(sessionKey, macdata)[:4].hex()
            print(f"MAC: {self.MAC}")

            write_data_res =write_data_res + self.MAC + "08"
            self.dcs = self.calculate_DCS(write_data_res)
            write_data_res ="0000FF2700" + write_data_res + self.dcs + "00"
            # print(f"write_data_res: {write_data_res}")
            if type == 0:
                self.enter_write_data_res = write_data_res
            else:
                self.exit_write_data_res = write_data_res
        except Exception as e:
            messagebox.showerror("MAC cacl error:", e)
            return False
        return True

    def ApduHandle(self, data, sequence, is_enter=True): # BM: 处理APDU数据
        data_upper = data.upper()
        sequence_upper = sequence.upper()
        index = data_upper.find(sequence_upper)
        r_index = index 
        if index == -1:
            return
        DATA_POSITIONS = {
            'COMMAND'   : (index + 26, index + 28),
            'STATUS'    : (index + 28, index + 30),
            'APDU_NUM'  : (index + 30, index + 32),
            'BALANCE'   : (index + 36, index + 44),
            'ONLINE_SEQ': (index + 44, index + 48),
            'RANDOM_NO' : (index + 58, index + 66),
            'R_APDU_NUM': (index + 54, index + 56),   #TODO 用于后续判断每个apdu是否都是9000
            'W_APDU_NUM': (index + 30, index + 32),
            'E1'        : (index + 710, index + 712),
            'APPLET_RES': (index + 148, index + 152),
        }
        
        command = data_upper[DATA_POSITIONS['COMMAND'][0]:DATA_POSITIONS['COMMAND'][1]]
        status = data_upper[DATA_POSITIONS['STATUS'][0]:DATA_POSITIONS['STATUS'][1]]
        apdu_num = int(data_upper[DATA_POSITIONS['APDU_NUM'][0]:DATA_POSITIONS['APDU_NUM'][1]],16)
        print(f"Response data = {data}")
        # print(f'status = {status}')
        
        send_data = self.send_enter_data if is_enter else self.send_exit_data
        station_type = 0 if is_enter else 1
        if command == 'C2' and status == '00' and apdu_num > 5:    # send 8050,80dc
            r_apdu_num = int(data_upper[DATA_POSITIONS['R_APDU_NUM'][0]:DATA_POSITIONS['R_APDU_NUM'][1]],16)
            
            # Applet response checking
            applet_res = data_upper[DATA_POSITIONS['APPLET_RES'][0]:DATA_POSITIONS['APPLET_RES'][1]]
            # if applet_res != '9000':
            #     print(f'applet res = {applet_res}')
            #     self.show_in_text_area("Card info is in error.") if is_enter else self.show_in_text_area1("Card info is in error.")
            #     return 

            # E1 file checking
            e1 = data_upper[DATA_POSITIONS['E1'][0]:DATA_POSITIONS['E1'][1]]
            # print(f"E1 = {e1}")
            # 根据E1检查开关状态决定是否执行E1检查
            if self.e1_check_var.get() == "on":
                if is_enter and e1 not in ['04', '00']:
                    self.show_in_text_area("请勿重复进站")
                    return
                elif not is_enter and e1 not in ['03']:
                    self.show_in_text_area1("进出站逻辑顺序错误")
                    return

            # SZT card checking - search for card number starting with "0310487"
            card_pattern = "0310487"
            card_start_index = data_upper.find(card_pattern)
            if card_start_index != -1:
                # Extract card number with original length (20 characters)
                self.CardNo = data_upper[card_start_index:card_start_index + 20]
            else:
                self.CardNo = ""
                message = "未找到有效的SZT卡号"
                self.show_in_text_area(message) if is_enter else self.show_in_text_area1(message)
                return

            if self.update_read_data_res(station_type) != 0:
                print(f"send {'enter' if is_enter else 'exit'} read data")
                send_data(self.enter_read_data_res if is_enter else self.exit_read_data_res, 1)
                 
        elif command == 'C2' and status == '00' and apdu_num == 2:   #send 8054
            w_apdu_num = int(data_upper[DATA_POSITIONS['W_APDU_NUM'][0]:DATA_POSITIONS['W_APDU_NUM'][1]],16)
            balance = data_upper[DATA_POSITIONS['BALANCE'][0]:DATA_POSITIONS['BALANCE'][1]]
            print(f'BALANCE = {int(balance,16)/100}￥')
            self.OnlineSeqNo = data_upper[DATA_POSITIONS['ONLINE_SEQ'][0]:DATA_POSITIONS['ONLINE_SEQ'][1]]
            self.RandomNo = data_upper[DATA_POSITIONS['RANDOM_NO'][0]:DATA_POSITIONS['RANDOM_NO'][1]]
            self.update_write_data_res()
            if self.get_mac(self.enter_write_data_res if is_enter else self.exit_write_data_res, station_type):
                send_data(self.enter_write_data_res if is_enter else self.exit_write_data_res, 2)
                # print(f"send {'enter' if is_enter else 'exit'} write data")

        elif command == 'C2' and status == '00' and apdu_num == 1:   #send halt
            w_apdu_num = int(data_upper[DATA_POSITIONS['W_APDU_NUM'][0]:DATA_POSITIONS['W_APDU_NUM'][1]],16)
            # print(f"w_apdu_num: {w_apdu_num}")
            # print(f"send {'enter' if is_enter else 'exit'} halt data")
            send_data(self.halt_data_res, 3)

    def read_data_enter(self):
        buffer = b''
        last_receive_time = time.time()
        while self.enter_running and self.EnterSerial:
            try:
                data = self.EnterSerial.read(1024)
                if data:
                    buffer += data
                    last_receive_time = time.time()
                else:
                    if time.time() - last_receive_time > self.timeout_threshold:  #确保没有数据了再结束,但该方案会导致串口的处理速度下降很多
                        if buffer:
                            hex_data = buffer.hex()
                            # print(hex_data)
                            self.ApduHandle(hex_data, self.sequence, True)
                            buffer = b''
                        last_receive_time = time.time()
            except serial.SerialException as e:
                messagebox.showerror("Read data error:", e)
                self.segemented_button.set("Disconnect")
                self.segmented_button_callback("Disconnect")

            except Exception as e:
                messagebox.showerror("Unexpected error:", e)

    def read_data_exit(self):
        buffer = b''
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
                            # print(hex_data)
                            self.ApduHandle(hex_data, self.sequence, False)
                            buffer = b''
                        last_receive_time = time.time()
            except serial.SerialException as e:
                messagebox.showerror("Read data error:", e)
                self.segemented_button1.set("Disconnect")
                self.segmented_button_callback1("Disconnect")

            except Exception as e:
                messagebox.showerror("Unexpected error:", e)
    
    def cacl_money(self, money):
        self.money = money

    def send_enter_data(self, hex_data, type):
        try:
            if len(hex_data) % 2 != 0:
                messagebox.showerror("data len is not even:", e)
                return
            byte_data = bytes.fromhex(hex_data)
            if self.EnterSerial and self.EnterSerial.is_open:
                print(f"Enter Send: {hex_data}")
                self.EnterSerial.write(byte_data)
                if type == 2:
                    self.enter_write_data_res = "05FFFFFFFFFF06FFFFFFFFFF17C20115805401000F00000001"+self.DateTime
                elif type == 3:
                    spendmsg = str(self.enter_id) + " | " + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + " | " + "消费: $" + str(int(self.money_entry.get(),16)/100) + " | " + "OK"
                    if self.switch_var.get() == "on":
                        spendmsg = str(self.enter_id) + " | " + datetime.now().strftime("%H:%M:%S") + " | " + "$" + str(int(self.money_entry.get(),16)/100) + " | " + "OK"
                    self.show_in_text_area(spendmsg)
                    self.enter_id += 1
                    print("--------------------------------------ENTER OK --------------------------------------\n")
        except ValueError as e:
            messagebox.showerror("Send data error:", e)     
    
    def send_exit_data(self, hex_data,type):
        try:
            if len(hex_data) % 2 != 0:
                messagebox.showerror("data len is not even:", e)
                return

            byte_data = bytes.fromhex(hex_data)
            if self.ExitSerial and self.ExitSerial.is_open:
                self.ExitSerial.write(byte_data)
                if type == 2:
                    self.exit_write_data_res = "05FFFFFFFFFF06FFFFFFFFFF17C20115805401000F00000001"+self.DateTime
                elif type == 3:
                    spendmsg = str(self.exit_id) + " | " + datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + " | " + "消费: ￥" + str(int(self.money_exit.get(),16)/100) + " | " + "OK"
                    if self.switch_var.get() == "on":
                        spendmsg = str(self.exit_id) + " | " + datetime.now().strftime("%H:%M:%S") + " | " + "￥" + str(int(self.money_exit.get(),16)/100) + " | " + "OK"
                    self.show_in_text_area1(spendmsg)
                    self.exit_id += 1
                    print("--------------------------------------EXIT OK --------------------------------------\n")
        except ValueError as e:
            messagebox.showerror("Send data error:", e)

    def show_in_text_area(self, message):
        self.text_area.insert(tk.END, message + "\n" + "\n")
        self.text_area.see(tk.END)
    
    def show_in_text_area1(self, message):
        self.text_area1.insert(tk.END, message + "\n" + "\n")
        self.text_area1.see(tk.END)
    
    def get_available_ports(self):
        """使用注册表方式获取所有串口，包括虚拟串口"""
        try:
            import winreg
            self.old_port_options = self.port_options.copy() if hasattr(self, 'port_options') else []
            self.port_options = []
            
            # 从注册表获取串口信息
            path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            
            for i in range(256):
                try:
                    val = winreg.EnumValue(key, i)
                    # val[1]是串口名称，如COM1
                    self.port_options.append(val[1])
                except:
                    break
            
            winreg.CloseKey(key)
            
            # 如果注册表方式没有找到串口，尝试使用pyserial方式
            if not self.port_options:
                ports = serial.tools.list_ports.comports()
                self.port_options = [port.device for port in ports]
                
        except Exception as e:
            # messagebox.showerror("获取串口列表错误:", str(e))
            # 出错时尝试使用pyserial方式
            try:
                ports = serial.tools.list_ports.comports()
                self.port_options = [port.device for port in ports]
            except:
                self.port_options = []
    
    def update_ports_periodically(self):
        current_enter_selection = self.port_var.get()
        current_exit_selection = self.port_var1.get()
        
        self.get_available_ports()
        
        if set(self.old_port_options) != set(self.port_options):
            # 更新下拉菜单选项
            self.port_menu.configure(values=self.port_options)
            self.port_menu1.configure(values=self.port_options)
            
            # 处理当前选择的串口
            if current_enter_selection and current_enter_selection in self.port_options:
                self.port_var.set(current_enter_selection)
            elif self.port_options:
                self.port_var.set(self.port_options[0])
            
            if current_exit_selection and current_exit_selection in self.port_options:
                self.port_var1.set(current_exit_selection)
            elif self.port_options:
                self.port_var1.set(self.port_options[0])
        self.master.after(2000, self.update_ports_periodically)  # 每2秒更新一次

    def toggle_topmost(self):
        if self.switch_var.get() == "on":
            self.master.wm_attributes("-topmost", 1)
            self.master.geometry("550x315")
        else:
            self.master.wm_attributes("-topmost", 0)
            self.master.geometry("900x450")
    
    def change_appearance_mode_event(self, new_appearance_mode):
        if new_appearance_mode == "About":
            self.show_about()
        else:
            customtkinter.set_appearance_mode(new_appearance_mode)

    def Init_image(self):
        image_path = os.path.dirname(__file__) + "\\PIC"
        self.delete_img = customtkinter.CTkImage(Image.open(os.path.join(image_path, "Delete.png")), size=(20, 20))
        self.info_img = customtkinter.CTkImage(Image.open(os.path.join(image_path, "info.png")), size=(20, 20))
        self.update_img = customtkinter.CTkImage(Image.open(os.path.join(image_path, "info.png")), size=(20, 20))
        # self.car_img = customtkinter.CTkImage(Image.open(os.path.join(image_path, "car.mp4")), size=(20, 20))

    def show_about(self):
        about_message = f"""
        UWBReader {self.version}

        版权所有 © 2025 可为信息技术有限公司
        Author: @QLL
        Email: Tommy.yang@cardshare.cn
        """
        messagebox.showinfo("关于", about_message)
    
    def open_update_html(self):
        """打开更新日志HTML文件"""
        html_path = os.path.join(os.path.dirname(__file__), "update.html")
        if os.path.exists(html_path):
            import webbrowser
            webbrowser.open(html_path)
        else:
            messagebox.showerror("错误", "找不到更新日志文件")

    def change_theme(self, theme ):
        if theme in ("light", "dark", "System"):
            customtkinter.set_appearance_mode(theme)
        else:
            file = os.path.join(os.path.dirname(__file__), "themes", theme + ".json")
            if os.path.exists(file):
                customtkinter.set_default_color_theme("E:/Work/UWB/Code/UwbCOMCode/tools/themes/MoonlitSky.json")

if __name__ == "__main__":
    customtkinter.set_appearance_mode("light")  # Modes: System (default), light, dark
    file = os.path.join(os.path.dirname(__file__), "themes", "MyMoo" + ".json")   # MoonlitSkynew  TestCardNew
    customtkinter.set_default_color_theme(file)
    # customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    root = customtkinter.CTk()
    app = UwbReaderAssistant(root)

    menubar = tk.Menu(root, font=("Time New Roman", 15), background="black")  
    root.config(menu=menubar)
    
    # theme_menu = tk.Menu(menubar, tearoff=0)
    # menubar.add_cascade(label="主题", menu=theme_menu)
    # theme_menu.add_command(label="浅色模式", command=lambda: app.change_theme("light"))
    # theme_menu.add_command(label="深色模式", command=lambda: app.change_theme("dark"))
    # theme_menu.add_command(label="跟随系统", command=lambda: app.change_theme("System"))

    # about_menu = tk.Menu(menubar, tearoff=0)
    # menubar.add_cascade(label="关于", menu=about_menu)
    # about_menu.add_command(label = "关于", command=app.show_about, font=(app.font[0], 15))
    
    root.protocol("WM_DELETE_WINDOW", app.on_window_closing)

    root.mainloop()
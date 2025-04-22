import customtkinter as ctk
import customtkinter
import tkinter as tk
import os
from PIL import Image
from tkinter import filedialog
import pandas as pd
import numpy as np
import ttkbootstrap as ttk
import sys
sys.path.append("E:\Work\JupyterLab\AI")
from Kimi_api import KimiChatAssistant

class AiAssistant(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.width = 700
        self.height = 450
        self.version = "_v1.0"
        self.title("example" + self.version)
        self.geometry("{}x{}".format(self.width, self.height))
        self.ai_assistant = None

        self.RootFrame = customtkinter.CTkFrame(self, corner_radius=0)
        self.RootFrame.pack(fill="both", expand=True)
        # self.attributes("-transparentcolor", "white")
        # set grid layout 1x2
        self.RootFrame.grid_rowconfigure(0, weight=1)
        self.RootFrame.grid_columnconfigure(1, weight=1)   #界面变化时导航列0不会变宽
        self.Init_image()
        self.AI_init()
        
        self.create_navigation_page()
        self.create_home_page()
        self.create_second_page()
        self.create_third_page()

        # AI消息气泡（左侧浅灰色）
        self.chat_response_text.tag_config(
            "ai_bubble",
            # background="#E8E8E8",    # 背景色
            lmargin1=10,             # 左侧边距
            rmargin=100,             # 右侧边距（控制文本靠左）
            wrap=ctk.WORD,
            spacing2=5,
            foreground="#111111",        # 设置文字颜色为绿色
        )
        
        self.select_page_by_name("page_3")
    
    def create_navigation_page(self):
        self.navigation_frame = customtkinter.CTkFrame(self.RootFrame, corner_radius=0, fg_color=("#cfeffa","#1A1C2C"))
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="", font=customtkinter.CTkFont(size=15, weight="bold"),text_color="#17A2B8",
                                                             image=self.log_img, compound="left")
        self.navigation_frame_label.grid(row=0, column=0, padx=10, pady=0, sticky="ew")

        self.page_home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, width=20, height=40, border_spacing=1, text="",fg_color="transparent", 
                                                   anchor="center", command=self.page_home_button_event, font=customtkinter.CTkFont(size=12, weight="bold"), image=self.home_img)
        self.page_home_button.grid(row=1, column=0, sticky="ew")

        self.page_2_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, width=20, height=40, border_spacing=1, text="",fg_color="transparent", 
                                                    anchor="center", command=self.page_2_button_event, font=customtkinter.CTkFont(size=12, weight="bold"), image=self.page_img)
        self.page_2_button.grid(row=2, column=0, sticky="ew")
 
        self.page_3_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, width=20, height=40, border_spacing=1, text="",fg_color="transparent", 
                                                    anchor="center", command=self.page_3_button_event, font=customtkinter.CTkFont(size=12, weight="bold"), image=self.page_img)
        self.page_3_button.grid(row=3, column=0, sticky="ew")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self.navigation_frame, width=50,corner_radius=0, values=["Light", "Dark", "Sys"], command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=6, column=0, sticky="ew")
    
    def create_home_page(self):
        self.home_frame = ctk.CTkFrame(self.RootFrame, corner_radius=0, fg_color=("#e8f5f9","#241F2C"))
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.home_title_frame = ctk.CTkFrame(self.home_frame, corner_radius=0, fg_color=("#dfdffa","#2C2C2C"))
        self.home_title_frame.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        self.home_title_label = ctk.CTkLabel(self.home_title_frame, text="Home page", anchor="center", font=ctk.CTkFont("Times New Roman", size=20, weight="bold"), text_color="#17A2B8")
        self.home_title_label.pack()

        ctk.CTkFrame(self.home_frame, height=2, bg_color="#C0C0C0").grid(row=1, column=0, padx=0, pady=0, sticky="ew")

        self.file_frame = ctk.CTkFrame(self.home_frame, corner_radius=0, fg_color="transparent")
        self.file_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.file_frame.grid_rowconfigure(0, weight=1)
        self.file_frame.grid_columnconfigure(0, weight=1)
        self.file_path_entry = ctk.CTkEntry(self.file_frame, placeholder_text="File path")
        self.file_path_entry.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.select_file_button = ctk.CTkButton(self.file_frame, text="Select", command=self.select_file)
        self.select_file_button.grid(row=0, column=1, padx=10, pady=5)
    
    def create_second_page(self):
        self.second_frame = customtkinter.CTkFrame(self.RootFrame, corner_radius=0, fg_color=("#e8f5f9","#241F2C"))
        self.second_frame.grid_columnconfigure(0, weight=1)

        self.second_title_frame = ctk.CTkFrame(self.second_frame, corner_radius=0, fg_color=("#dfdffa","#2C2C2C"))
        self.second_title_frame.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        self.second_title_label = customtkinter.CTkLabel(self.second_title_frame, text="Second page", font=ctk.CTkFont("Times New Roman", size=20, weight="bold"), text_color="#17A2B8")
        self.second_title_label.pack()
    
        ctk.CTkFrame(self.second_frame, height=2, bg_color="#C0C0C0").grid(row=1, column=0, padx=0, pady=0, sticky="ew")

        # 添加 CTkScrollableFrame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.second_frame, fg_color=("#E0F7FA","#3C3048"))
        self.scrollable_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        self.button_1 = ctk.CTkButton(self.scrollable_frame, text="Button 1")
        self.button_1.grid(row=0, column=0, padx=10, pady=5)
        self.button_2 = ctk.CTkButton(self.scrollable_frame, text="Button 2")
        self.button_2.grid(row=1, column=0, padx=10, pady=5)

        self.entry_1 = ctk.CTkEntry(self.scrollable_frame, placeholder_text="Entry 1")
        self.entry_1.grid(row=2, column=0, padx=10, pady=5)
        self.entry_2 = ctk.CTkEntry(self.scrollable_frame, placeholder_text="Entry 2")
        self.entry_2.grid(row=3, column=0, padx=10, pady=5)

        self.checkbox_1 = ctk.CTkCheckBox(self.scrollable_frame, text="Checkbox 1")
        self.checkbox_1.grid(row=4, column=0, padx=10, pady=5)
        self.checkbox_2 = ctk.CTkCheckBox(self.scrollable_frame, text="Checkbox 2")
        self.checkbox_2.grid(row=5, column=0, padx=10, pady=5)

        self.label_1 = ctk.CTkLabel(self.scrollable_frame, text="Label 1")
        self.label_1.grid(row=6, column=0, padx=10, pady=5)
        self.label_2 = ctk.CTkLabel(self.scrollable_frame, text="Label 2")
        self.label_2.grid(row=7, column=0, padx=10, pady=5)

    def create_third_page(self):
        self.third_frame = customtkinter.CTkFrame(self.RootFrame, corner_radius=0, fg_color=("#e8f5f9","#241F2C"))
        self.third_frame.grid_columnconfigure(0, weight=1)
        self.third_frame.grid_rowconfigure(0, weight=1)

        self.chat_frame = customtkinter.CTkFrame(self.third_frame, corner_radius=0, fg_color="transparent")
        self.chat_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_response_text = customtkinter.CTkTextbox(self.chat_frame, state="disabled", width=250)
        self.chat_response_text.grid(row=0, column=0, columnspan = 2,  padx=10, pady=5, sticky="nsew")

        self.chat_entry = customtkinter.CTkEntry(self.chat_frame, placeholder_text="Type your message here...")
        self.chat_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.chat_button = customtkinter.CTkButton(self.chat_frame, text="", command=self.send_message_2_ai, image=self.confirm_hover)
        self.chat_button.grid(row=1, column=1, padx=10, pady=5)
        self.bind("<Return>", lambda event: self.send_message_2_ai())
        
    def select_page_by_name(self, name):
        self.pages = {
            "home": self.home_frame,
            "page_2": self.second_frame,
            "page_3": self.third_frame
        }
        # set button color for selected button
        self.page_home_button.configure(fg_color=("#17A2B8", "#0c5460") if name == "home" else "transparent")
        self.page_2_button.configure(fg_color=("#17A2B8", "#0c5460") if name == "page_2" else "transparent")
        self.page_3_button.configure(fg_color=("#17A2B8", "#0c5460") if name == "page_3" else "transparent")

        for page_name,frame in self.pages.items():
            if name == page_name:
                frame.grid(row=0, column=1, sticky="nsew")
            else:
                frame.grid_forget()

    def page_home_button_event(self):
        self.select_page_by_name("home")

    def page_2_button_event(self):
        self.select_page_by_name("page_2")

    def page_3_button_event(self):
        self.select_page_by_name("page_3")

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def AI_init(self):
        self.ai_assistant = KimiChatAssistant(
        api_key="sk-b09XXwR8nOmrdoXTrylErTOJ0mWQYxKsRZBLMmfCiV2K0grF",
        # base_url="http://127.0.0.1:8888/v1",
        base_url = "https://api.moonshot.cn/v1",
        system_content="你是哪吒，你只会使用中文进行对话，后续的所有对话你都需要按照哪吒的语气和性格来进行。",
        model="moonshot-v1-auto",
        max_context_length= 20,
        use_stream = False,
        Candidates = 1,
    )
        
    def send_message_2_ai(self):
        user_input = self.chat_entry.get()
        if user_input:
            self.chat_entry.delete(0, ctk.END) 
            self.chat_response_text.configure(state="normal")  # 启用文本框编辑
            # self.chat_response_text.insert(ctk.END, f"{user_input}\n\n", "user_bubble")  

            response = self.ai_assistant.chat(user_input)
      
            self.chat_response_text.insert(ctk.END, f"{response}\n\n", "ai_bubble")  
            self.chat_response_text.configure(state="disabled")  # 禁用文本框编辑
            self.chat_response_text.see(ctk.END) 
    
    def select_file(self):
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.file_path_entry.delete(0, ctk.END)  # 清空文本框           
            self.file_path_entry.insert(0, file_path)  # 显示文件路径
            self.read_file(file_path)
    
    def read_file(self, file_path):
        try:
            print(f"reading file: {file_path}")
            # bug修复：删除了这行代码，因为它会覆盖用户选择的文件路径
            # file_path = "E:/Work/UWB/Code/UwbCOMCode/output/UwbCOMLog/UwbCOM_Log_2025-01-03-12-14-55.csv"
            df = pd.read_csv(file_path,header=0)
            df.columns = df.columns.str.strip()
            data_x = df['x']
            data_y = df['y']
            data_z = df['z']
            print(f"data_x: {data_x}")
            pass
        except Exception as e:
            pass
    
    def Init_image(self):
        image_path = os.path.dirname(__file__) + "\\PIC"
        self.log_img = customtkinter.CTkImage(Image.open(os.path.join(os.path.dirname(__file__), "logo1.png")), size=(48, 24))
        self.page_img = customtkinter.CTkImage(Image.open(os.path.join(image_path, "Page.png")), size=(24, 24))
        self.home_img = customtkinter.CTkImage(Image.open(os.path.join(image_path, "app.png")), size=(24, 24))
        self.confirm = customtkinter.CTkImage(Image.open(os.path.join(image_path, "confirm.png")), size=(24, 24))
        self.confirm_hover = customtkinter.CTkImage(Image.open(os.path.join(image_path, "confirm-blue.png")), size=(24, 24))


if __name__ == "__main__":
    customtkinter.set_appearance_mode("light")                            # Modes: System (default), light, dark
    file = os.path.join(os.path.dirname(__file__), "themes" , "MyMoo.json")     # MyMoo  TestCardNew
    customtkinter.set_default_color_theme(file)
    app = AiAssistant()

    app.mainloop()

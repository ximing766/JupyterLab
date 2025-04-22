import customtkinter as ctk
import os
from PIL import Image


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.width = 700
        self.height = 450

        self.title("example.py")
        self.geometry("{}x{}".format(self.width, self.height))

        current_path = os.path.join(os.path.dirname(__file__), 'test_images/bg2.png')  # "./test_images/bg2.png"

        self.bg_image = ctk.CTkImage(Image.open(current_path), size=(self.width, self.height))
        self.bg_image_label = ctk.CTkLabel(self, image=self.bg_image, text="")
        self.bg_image_label.place(x=0, y=0)

        self.RootFrame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1E2127")  # 导航栏背景颜色
        self.RootFrame.pack(fill="both", expand=True)
        self.attributes("-transparentcolor", "white")
        # set grid layout 1x2
        self.RootFrame.grid_rowconfigure(0, weight=1)
        self.RootFrame.grid_columnconfigure(1, weight=1)  # 界面变化时导航列0不会变宽

        self.create_navigation_page()
        self.create_home_page()
        self.create_second_page()
        self.create_third_page()

        self.select_page_by_name("home")

    def create_navigation_page(self):
        self.navigation_frame = ctk.CTkFrame(self.RootFrame, corner_radius=0, fg_color="#1E2127")  # 导航栏背景颜色
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = ctk.CTkLabel(self.navigation_frame, text="Example",
                                                   font=ctk.CTkFont(size=15, weight="bold"),
                                                   text_color="#61AFEF")  # 标题文字颜色
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.page_home_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                              text="Home", fg_color="transparent",
                                              text_color="#ABB2BF",  # 按钮文字颜色
                                              hover_color="#282C34",  # 鼠标悬停颜色
                                              anchor="w", command=self.page_home_button_event)
        self.page_home_button.grid(row=1, column=0, sticky="ew")

        self.page_2_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                           text="Frame 2", fg_color="transparent",
                                           text_color="#ABB2BF",  # 按钮文字颜色
                                           hover_color="#282C34",  # 鼠标悬停颜色
                                           anchor="w", command=self.page_2_button_event)
        self.page_2_button.grid(row=2, column=0, sticky="ew")

        self.page_3_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                           text="Frame 3", fg_color="transparent",
                                           text_color="#ABB2BF",  # 按钮文字颜色
                                           hover_color="#282C34",  # 鼠标悬停颜色
                                           anchor="w", command=self.page_3_button_event)
        self.page_3_button.grid(row=3, column=0, sticky="ew")

        self.appearance_mode_menu = ctk.CTkOptionMenu(self.navigation_frame, values=["Light", "Dark", "System"],
                                                      command=self.change_appearance_mode_event,
                                                      fg_color="#282C34",  # 选项菜单背景颜色
                                                      text_color="#ABB2BF",  # 选项菜单文字颜色
                                                      button_color="#61AFEF",  # 选项菜单按钮颜色
                                                      button_hover_color="#56B6C2")  # 选项菜单按钮悬停颜色
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")

    def create_home_page(self):
        self.home_frame = ctk.CTkFrame(self.RootFrame, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.home_frame_large_image_label = ctk.CTkLabel(self.home_frame, text="Home Page",
                                                         font=ctk.CTkFont(size=20, weight="bold"),
                                                         text_color="#61AFEF")  # 标题文字颜色
        self.home_frame_large_image_label.grid(row=0, column=0, padx=20, pady=10)

        self.home_frame_button_1 = ctk.CTkButton(self.home_frame, text="bt1",
                                                 fg_color="#61AFEF",  # 按钮背景颜色
                                                 hover_color="#56B6C2",  # 按钮悬停颜色
                                                 text_color="#FFFFFF")  # 按钮文字颜色
        self.home_frame_button_1.grid(row=1, column=0, padx=20, pady=10)

    def create_second_page(self):
        self.second_frame = ctk.CTkFrame(self.RootFrame, corner_radius=0, fg_color="transparent")
        self.second_frame.grid_columnconfigure(0, weight=1)
        self.second_frame_large_image_label = ctk.CTkLabel(self.second_frame, text="Second page",
                                                           font=ctk.CTkFont(size=20, weight="bold"),
                                                           text_color="#61AFEF")  # 标题文字颜色
        self.second_frame_large_image_label.grid(row=0, column=0, padx=20, pady=10)

    def create_third_page(self):
        self.third_frame = ctk.CTkFrame(self.RootFrame, corner_radius=0, fg_color="transparent")
        self.third_frame.grid_columnconfigure(0, weight=1)
        self.third_frame_large_image_label = ctk.CTkLabel(self.third_frame, text="Thrid page",
                                                          font=ctk.CTkFont(size=20, weight="bold"),
                                                          text_color="#61AFEF")  # 标题文字颜色
        self.third_frame_large_image_label.grid(row=0, column=0, padx=20, pady=10)

    def select_page_by_name(self, name):
        self.pages = {
            "home": self.home_frame,
            "page_2": self.second_frame,
            "page_3": self.third_frame
        }
        # set button color for selected button
        self.page_home_button.configure(fg_color="#61AFEF" if name == "home" else "transparent",
                                        text_color="#FFFFFF" if name == "home" else "#ABB2BF")
        self.page_2_button.configure(fg_color="#61AFEF" if name == "page_2" else "transparent",
                                     text_color="#FFFFFF" if name == "page_2" else "#ABB2BF")
        self.page_3_button.configure(fg_color="#61AFEF" if name == "page_3" else "transparent",
                                     text_color="#FFFFFF" if name == "page_3" else "#ABB2BF")

        for page_name, frame in self.pages.items():
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
        ctk.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    app = App()
    app.mainloop()
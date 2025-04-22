import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl


class VideoPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Video Player")
        self.setGeometry(100, 100, 800, 600)
        self.root_path = os.path.dirname(__file__) + "/PIC"

        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.root_layout = QVBoxLayout(self.container)
        self.init_vodeo()

        # 连接信号和槽
        # self.mediaPlayer.mediaStatusChanged.connect(self.handle_media_status)

        self.play_video("car.mp4")  # 替换为你的 MP4 文件名
    
    def init_vodeo(self):
        self.mediaPlayer = QMediaPlayer()
        self.videoWidget = QVideoWidget()
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.root_layout.addWidget(self.videoWidget)

    def play_video(self, video_file_name):
        """
        播放指定的视频文件
        :param video_file_name: 视频文件名（位于 self.root_path 目录下）
        """
        video_path = os.path.join(self.root_path, video_file_name)
        if os.path.exists(video_path):
            self.mediaPlayer.setSource(QUrl.fromLocalFile(video_path))
            self.mediaPlayer.play()
        else:
            print(f"视频文件不存在: {video_path}")

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("视频播放结束")
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print("无法加载视频文件")
        else:
            print(f"状态: {status}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayerWindow()
    window.show()
    sys.exit(app.exec())
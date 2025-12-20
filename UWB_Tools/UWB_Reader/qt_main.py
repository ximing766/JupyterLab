import os
import sys
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QCheckBox,
    QFrame,
    QStackedWidget,
    QGroupBox,
    QFormLayout,
    QFileDialog,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
)

from uwb_service import UwbService


class ServiceBridge(QObject):
    enterLog = pyqtSignal(str)
    exitLog = pyqtSignal(str)
    error = pyqtSignal(str)
    state = pyqtSignal(str, bool)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UWBREADER")
        self.setFixedSize(650, 400)
        icon_path = os.path.join(os.path.dirname(__file__), "UWBReader.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.service = UwbService()
        self.bridge = ServiceBridge()
        self.service.set_callbacks(
            on_enter_log=self.bridge.enterLog.emit,
            on_exit_log=self.bridge.exitLog.emit,
            on_error=self.bridge.error.emit,
            on_state=self.bridge.state.emit,
        )
        self._build_palette()
        self._build_ui()
        self._apply_styles()
        self._wire_signals()
        self._start_timer()
        self.enter_connected = False
        self.exit_connected = False

    def _build_palette(self):
        QApplication.setStyle("Fusion")
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor(245, 247, 250))
        p.setColor(QPalette.ColorRole.WindowText, QColor(35, 35, 35))
        p.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        p.setColor(QPalette.ColorRole.Text, QColor(35, 35, 35))
        p.setColor(QPalette.ColorRole.Button, QColor(230, 235, 245))
        p.setColor(QPalette.ColorRole.ButtonText, QColor(35, 35, 35))
        QApplication.setPalette(p)

    def _build_ui(self):
        cw = QWidget()
        cw.setObjectName("central")
        self.setCentralWidget(cw)
        main = QHBoxLayout(cw)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        nav = QFrame()
        nav.setObjectName("nav")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(8)
        # nav.setFixedWidth(72)
        brand = QLabel("🐻")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(brand)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame{color:#dbe2f1; background:#dbe2f1; max-height:1px;}")
        nav_layout.addWidget(sep)
        self.nav_home = QPushButton("🏯")
        self.nav_home.setCheckable(True)
        self.nav_home.setChecked(True)
        self.nav_settings = QPushButton("⚙️")
        self.nav_settings.setCheckable(True)
        nav_layout.addWidget(self.nav_home)
        nav_layout.addWidget(self.nav_settings)
        nav_layout.addStretch(1)
        main.addWidget(nav)
        self.stack = QStackedWidget()
        main.addWidget(self.stack, 1)
        self.home_page = QWidget()
        root = QVBoxLayout(self.home_page)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)
        self.stack.addWidget(self.home_page)
        top = QWidget()
        top.setObjectName("topBar")
        top_v = QVBoxLayout(top)
        top_v.setContentsMargins(10, 8, 10, 8)
        top_v.setSpacing(6)
        self.top = top
        root.addWidget(top)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("QFrame{color:#cbd5e1; background:#cbd5e1; max-height:1px;}")
        root.insertWidget(1, divider)
        self.settings = QWidget()
        self.settings.setObjectName("settingsPane")

        self.enter_com = QComboBox()
        self.enter_baud = QComboBox()
        self.enter_baud.addItems(["230400", "460800", "115200", "3000000", "9600"])
        self.enter_toggle = QPushButton("OPEN")
        self._style_button(self.enter_toggle, False)

        self.exit_com = QComboBox()
        self.exit_baud = QComboBox()
        self.exit_baud.addItems(["230400", "460800", "115200", "3000000", "9600"])
        self.exit_toggle = QPushButton("OPEN")
        self._style_button(self.exit_toggle, False)

        self.pin_top = QCheckBox("Pin")
        self.e1_check = QCheckBox("1E")
        self.e1_check.setChecked(True)

        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(10)
        left_panel = QWidget()
        left_grid = QGridLayout(left_panel)
        left_grid.setContentsMargins(0, 0, 0, 0)
        left_grid.setHorizontalSpacing(6)
        left_grid.addWidget(QLabel("ENTER"), 0, 0)
        left_grid.addWidget(self.enter_com, 0, 1)
        left_grid.addWidget(self.enter_baud, 0, 2)
        left_grid.addWidget(self.enter_toggle, 0, 3)
        right_panel = QWidget()
        right_grid = QGridLayout(right_panel)
        right_grid.setContentsMargins(0, 0, 0, 0)
        right_grid.setHorizontalSpacing(6)
        right_grid.addWidget(QLabel("EXIT"), 0, 0)
        right_grid.addWidget(self.exit_com, 0, 1)
        right_grid.addWidget(self.exit_baud, 0, 2)
        right_grid.addWidget(self.exit_toggle, 0, 3)
        row1_layout.addWidget(left_panel, 1)
        row1_layout.addWidget(right_panel, 1)
        top_v.addWidget(row1)

        row2 = QWidget()
        ops_layout = QHBoxLayout(row2)
        ops_layout.setContentsMargins(0, 0, 0, 0)
        ops_layout.setSpacing(8)
        self.setting_toggle = QPushButton("Setting")
        ops_layout.addWidget(self.pin_top)
        ops_layout.addWidget(self.e1_check)
        ops_layout.addWidget(self.setting_toggle)
        self.setting_toggle.hide()
        ops_layout.addStretch(1)

        left_log = QWidget()
        left_log.setObjectName("enterCard")
        left_layout = QVBoxLayout(left_log)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)
        left_bar = QWidget()
        left_bar_layout = QHBoxLayout(left_bar)
        left_bar_layout.setContentsMargins(0, 0, 0, 0)
        left_bar_layout.setSpacing(6)
        self.clear_enter = QPushButton("CLEAR")
        self.enter_title = QLabel("ENTER")
        left_bar_layout.addWidget(self.enter_title)
        left_bar_layout.addStretch(1)
        left_bar_layout.addWidget(self.clear_enter)
        left_layout.addWidget(left_bar)
        self.enter_log = QPlainTextEdit()
        self.enter_log.setReadOnly(True)
        self.enter_log.setMinimumHeight(150)
        left_layout.addWidget(self.enter_log, 1)

        right_log = QWidget()
        right_log.setObjectName("exitCard")
        right_layout = QVBoxLayout(right_log)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)
        right_bar = QWidget()
        right_bar_layout = QHBoxLayout(right_bar)
        right_bar_layout.setContentsMargins(0, 0, 0, 0)
        right_bar_layout.setSpacing(6)
        self.clear_exit = QPushButton("CLEAR")
        self.exit_title = QLabel("EXIT")
        right_bar_layout.addWidget(self.exit_title)
        right_bar_layout.addStretch(1)
        right_bar_layout.addWidget(self.clear_exit)
        right_layout.addWidget(right_bar)
        self.exit_log = QPlainTextEdit()
        self.exit_log.setReadOnly(True)
        self.exit_log.setMinimumHeight(150)
        right_layout.addWidget(self.exit_log, 1)

        splitter.addWidget(left_log)
        splitter.addWidget(right_log)
        splitter.setSizes([300, 300])
        footer_div = QFrame()
        footer_div.setFrameShape(QFrame.Shape.HLine)
        footer_div.setFrameShadow(QFrame.Shadow.Sunken)
        footer_div.setStyleSheet("QFrame{color:#cbd5e1; background:#cbd5e1; max-height:1px;}")
        root.addWidget(footer_div)
        root.addWidget(row2)
        self.enter_baud.setCurrentText("460800")
        self.exit_baud.setCurrentText("460800")

        s_layout = QVBoxLayout(self.settings)
        enter_group = QGroupBox("进站参数")
        exit_group = QGroupBox("出站参数")
        s_layout.addWidget(enter_group)
        s_layout.addWidget(exit_group)
        f1 = QFormLayout(enter_group)
        f2 = QFormLayout(exit_group)

        self.industry_enter = QComboBox()
        self.industry_enter.addItems(["公交", "地铁", "轮渡", "BRT"]) 
        self.line_enter = QComboBox()
        self.line_enter.addItems(["0000", "0001", "0002", "0003"]) 
        self.site_enter = QComboBox()
        self.site_enter.addItems(["0000", "0001", "0002", "0003"]) 
        self.money_enter = QComboBox()
        self.money_enter.setEditable(True)
        self.money_enter.addItems(["00000000", "00000001"]) 

        self.industry_exit = QComboBox()
        self.industry_exit.addItems(["公交", "地铁", "轮渡", "BRT"]) 
        self.line_exit = QComboBox()
        self.line_exit.addItems(["0000", "0001", "0002", "0003"]) 
        self.site_exit = QComboBox()
        self.site_exit.addItems(["0000", "0001", "0002", "0003"]) 
        self.money_exit = QComboBox()
        self.money_exit.setEditable(True)
        self.money_exit.addItems(["00000001", "00000000"]) 

        f1.addRow("行业代码", self.industry_enter)
        f1.addRow("线路代码", self.line_enter)
        f1.addRow("站点代码", self.site_enter)
        f1.addRow("入站金额(hex)", self.money_enter)

        f2.addRow("行业代码", self.industry_exit)
        f2.addRow("线路代码", self.line_exit)
        f2.addRow("站点代码", self.site_exit)
        f2.addRow("出站金额(hex)", self.money_exit)
        self.stack.addWidget(self.settings)

    def _wire_signals(self):
        self.enter_toggle.clicked.connect(self._toggle_enter_connection)
        self.exit_toggle.clicked.connect(self._toggle_exit_connection)
        self.pin_top.toggled.connect(self._toggle_top)
        self.e1_check.toggled.connect(self._toggle_e1)
        self.nav_home.clicked.connect(lambda: (self.stack.setCurrentWidget(self.home_page), self.nav_home.setChecked(True), self.nav_settings.setChecked(False)))
        self.nav_settings.clicked.connect(self._open_settings)
        self.clear_enter.clicked.connect(lambda: self.enter_log.setPlainText(""))
        self.clear_exit.clicked.connect(lambda: self.exit_log.setPlainText(""))
        self.bridge.enterLog.connect(self._append_enter)
        self.bridge.exitLog.connect(self._append_exit)
        self.bridge.error.connect(self._show_error)
        self.bridge.state.connect(self._update_state)

    def _start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_ports)
        self.timer.start(2000)
        self._refresh_ports()
        self.stack.setCurrentWidget(self.home_page)
        self.nav_home.setChecked(True)
        self.nav_settings.setChecked(False)

    def _refresh_ports(self):
        ports = self.service.get_available_ports()
        self._refresh_combo(self.enter_com, ports)
        self._refresh_combo(self.exit_com, ports)
        if ports:
            if not self.enter_com.currentText():
                self.enter_com.setCurrentIndex(0)
            if not self.exit_com.currentText():
                self.exit_com.setCurrentIndex(0)

    def _refresh_combo(self, combo, values):
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        if current and current in values:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _toggle_enter_connection(self):
        if self.enter_connected:
            self.service.disconnect_enter()
        else:
            self.service.set_enter_port(self.enter_com.currentText(), self.enter_baud.currentText())
            self._push_settings()
            self.service.connect_enter()

    def _toggle_exit_connection(self):
        if self.exit_connected:
            self.service.disconnect_exit()
        else:
            self.service.set_exit_port(self.exit_com.currentText(), self.exit_baud.currentText())
            self._push_settings()
            self.service.connect_exit()

    def _toggle_top(self, checked):
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def _toggle_e1(self, checked):
        self.service.set_e1_check(bool(checked))

    def _append_enter(self, text):
        self.enter_log.appendPlainText(text)
        self.enter_log.moveCursor(self.enter_log.textCursor().MoveOperation.End)

    def _append_exit(self, text):
        self.exit_log.appendPlainText(text)
        self.exit_log.moveCursor(self.exit_log.textCursor().MoveOperation.End)

    def _show_error(self, msg):
        QMessageBox.critical(self, "错误", str(msg))

    def _update_state(self, which, connected):
        if which == "enter":
            self.enter_connected = connected
            self.enter_toggle.setText("CLOSE" if connected else "OPEN")
            self._style_button(self.enter_toggle, connected)
        else:
            self.exit_connected = connected
            self.exit_toggle.setText("CLOSE" if connected else "OPEN")
            self._style_button(self.exit_toggle, connected)

    def _open_settings(self):
        self.stack.setCurrentWidget(self.settings)
        self.nav_home.setChecked(False)
        self.nav_settings.setChecked(True)

    def _toggle_setting(self):
        pass

    def _push_settings(self):
        self.service.set_enter_parameters(
            self.industry_enter.currentText(),
            self.line_enter.currentText(),
            self.site_enter.currentText(),
            self.money_enter.currentText(),
        )
        self.service.set_exit_parameters(
            self.industry_exit.currentText(),
            self.line_exit.currentText(),
            self.site_exit.currentText(),
            self.money_exit.currentText(),
        )

    def closeEvent(self, e):
        self.service.on_window_closing()
        super().closeEvent(e)

    def _style_button(self, btn, connected):
        if connected:
            btn.setStyleSheet("QPushButton{background:#E24A4A; color:white; border-radius:6px; padding:6px 12px;} QPushButton:hover{background:#cf3f3f}")
        else:
            btn.setStyleSheet("QPushButton{background:#5B8DEF; color:white; border-radius:6px; padding:6px 12px;} QPushButton:hover{background:#4a7bdc}")

    def _apply_styles(self):
        accent = "#5B8DEF"
        self.centralWidget().setStyleSheet(
            "#central{background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #eef2f7, stop:1 #e7ecf6);}"
        )
        self.top.setStyleSheet(
            "#topBar{background:#eef3ff; border:1px solid #d7e3ff; border-radius:8px;}"
        )
        for card in [self.findChild(QWidget, "enterCard"), self.findChild(QWidget, "exitCard")]:
            if card:
                card.setStyleSheet("QWidget{background:#eef3ff; border:none; border-radius:10px;}")
        self.settings.setStyleSheet(
            "#settingsPane{background:#ffffff; border:1px solid #e5e9f2; border-radius:10px;}"
            "QGroupBox{border:1px solid #e5e9f2; border-radius:8px; margin-top:8px; padding-top:12px;}"
            "QGroupBox::title{subcontrol-origin: margin; left:10px; padding:0 6px; color:#4c5b73; font-weight:600;}"
        )
        combo_styles = (
            "QComboBox{padding:4px 8px; border:1px solid #d0d7e2; border-radius:6px; background:#ffffff;}"
            "QComboBox:focus{border:1px solid " + accent + ";}"
        )
        for c in [
            self.enter_com,
            self.enter_baud,
            self.exit_com,
            self.exit_baud,
            self.industry_enter,
            self.line_enter,
            self.site_enter,
            self.money_enter,
            self.industry_exit,
            self.line_exit,
            self.site_exit,
            self.money_exit,
        ]:
            c.setStyleSheet(combo_styles)
        editor_style = "QPlainTextEdit{background:#d1f2f7; border:1px solid #dfe6f4; border-radius:8px;}"
        self.enter_log.setStyleSheet(editor_style)
        self.exit_log.setStyleSheet(editor_style)
        splitter_style = "QSplitter::handle{background:#d9e1ef; width:4px; border-radius:2px;}"
        for s in self.findChildren(QSplitter):
            s.setStyleSheet(splitter_style)
        title_style = "QLabel{color:#425b8a; font-weight:700; padding-left:8px; border-left:4px solid #5B8DEF;}"
        self.enter_title.setStyleSheet(title_style)
        self.exit_title.setStyleSheet(title_style)
        for b in [self.clear_enter, self.clear_exit]:
            self._style_ghost_button(b)
        
        # ScrollBar Styles
        sb_style = (
            "QScrollBar:vertical{background:transparent; width:8px; margin:0px;}"
            "QScrollBar::handle:vertical{background:#cfd6e6; min-height:30px; border-radius:4px;}"
            "QScrollBar::handle:vertical:hover{background:#b0b8c8;}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{height:0px;}"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical{background:none;}"
        )
        self.enter_log.verticalScrollBar().setStyleSheet(sb_style)
        self.exit_log.verticalScrollBar().setStyleSheet(sb_style)

        cb_style = (
            "QCheckBox{color:#4c5b73;}"
            "QCheckBox::indicator{width:16px; height:16px; border:1px solid #d0d7e2; border-radius:4px; background:#ffffff;}"
            "QCheckBox::indicator:hover{border:1px solid #5B8DEF;}"
            "QCheckBox::indicator:checked{background:#5B8DEF; border:1px solid #5B8DEF;}"
        )
        self.pin_top.setStyleSheet(cb_style)
        self.e1_check.setStyleSheet(cb_style)
        self.findChild(QFrame, "nav").setStyleSheet("#nav{background:#f1f4fb; border-right:1px solid #dbe2f1;}")
        nav_btn_style = (
            "QPushButton{background:transparent; color:#3a4a6b; border:none; padding:8px 10px; text-align:left;}"
            "QPushButton:hover{background:#e8eefc;}"
            "QPushButton:checked{background:#5B8DEF; color:white; border-radius:6px;}"
        )
        self.nav_home.setStyleSheet(nav_btn_style)
        self.nav_settings.setStyleSheet(nav_btn_style)

    def _style_pill_button(self, btn):
        btn.setStyleSheet("QPushButton{background:#5B8DEF; color:white; border-radius:16px; padding:6px 14px;} QPushButton:hover{background:#4a7bdc}")

    def _style_ghost_button(self, btn):
        # Minimalist modern clear button
        btn.setStyleSheet(
            "QPushButton{background:transparent; color:#9aa5b6; border:none; border-radius:4px; font-weight:600; padding:4px 8px;}"
            "QPushButton:hover{background:#eef3ff; color:#5B8DEF;}"
            "QPushButton:pressed{background:#dbe5f9;}"
        )

class SettingsDialog(QDialog):
    def __init__(self, service: UwbService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Setting")
        self.setFixedSize(300, 350)
        layout = QVBoxLayout(self)
        enter_group = QGroupBox("进站参数")
        exit_group = QGroupBox("出站参数")
        layout.addWidget(enter_group)
        layout.addWidget(exit_group)
        f1 = QFormLayout(enter_group)
        f2 = QFormLayout(exit_group)
        self.industry_enter = QComboBox(); self.industry_enter.addItems(["公交","地铁","轮渡","BRT"]) 
        self.line_enter = QComboBox(); self.line_enter.addItems(["0000","0001","0002","0003"]) 
        self.site_enter = QComboBox(); self.site_enter.addItems(["0000","0001","0002","0003"]) 
        self.money_enter = QComboBox(); self.money_enter.setEditable(True); self.money_enter.addItems(["00000000","00000001"]) 
        self.industry_exit = QComboBox(); self.industry_exit.addItems(["公交","地铁","轮渡","BRT"]) 
        self.line_exit = QComboBox(); self.line_exit.addItems(["0000","0001","0002","0003"]) 
        self.site_exit = QComboBox(); self.site_exit.addItems(["0000","0001","0002","0003"]) 
        self.money_exit = QComboBox(); self.money_exit.setEditable(True); self.money_exit.addItems(["00000001","00000000"]) 
        f1.addRow("行业代码", self.industry_enter)
        f1.addRow("线路代码", self.line_enter)
        f1.addRow("站点代码", self.site_enter)
        f1.addRow("入站金额(hex)", self.money_enter)
        f2.addRow("行业代码", self.industry_exit)
        f2.addRow("线路代码", self.line_exit)
        f2.addRow("站点代码", self.site_exit)
        f2.addRow("出站金额(hex)", self.money_exit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        accent = "#5B8DEF"
        combo_styles = (
            "QComboBox{padding:4px 8px; border:1px solid #d0d7e2; border-radius:6px; background:#ffffff;}"
            "QComboBox:focus{border:1px solid " + accent + ";}"
        )
        for c in [self.industry_enter,self.line_enter,self.site_enter,self.money_enter,self.industry_exit,self.line_exit,self.site_exit,self.money_exit]:
            c.setStyleSheet(combo_styles)

    def _apply(self):
        self.service.set_enter_parameters(self.industry_enter.currentText(), self.line_enter.currentText(), self.site_enter.currentText(), self.money_enter.currentText())
        self.service.set_exit_parameters(self.industry_exit.currentText(), self.line_exit.currentText(), self.site_exit.currentText(), self.money_exit.currentText())
        self.accept()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

import sys
import subprocess
import os
import shutil
import psutil
import stat
import time
import platform
import getpass
from datetime import datetime
from typing import List, Dict, Optional, Any

# Safe import for requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

if sys.platform == 'win32':
    import winreg
    import ctypes

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QSpinBox, QPushButton, QMessageBox,
                             QTextEdit, QComboBox, QCheckBox, QPlainTextEdit, QRadioButton,
                             QProgressBar, QTabWidget, QGridLayout, QFrame, QLineEdit, QStyle, QButtonGroup,
                             QFormLayout, QStatusBar)
from PyQt6.QtCore import Qt, QSettings, QTimer, QStandardPaths, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

# Safe Import for Theme
try:
    from theme import LIGHT_STYLESHEET, DARK_STYLESHEET
except ImportError:
    LIGHT_STYLESHEET = ""
    DARK_STYLESHEET = ""

# ==========================================
# --- TELEGRAM CONFIGURATION ---
# ==========================================
TELEGRAM_BOT_TOKEN = "8175015570:AAFXp9XIRKwqbC2PAWLzfC8CoGF0Ubacdcs"
TELEGRAM_CHAT_ID = "1272791365"
# ==========================================

DEFAULT_DEVICE_PRESETS: Dict[str, Dict[str, Any]] = {
    "Desktop (Default)": {"width": 1024, "height": 768, "agent": None},
    "Apple iPhone 14 Pro": {"width": 393, "height": 852, "agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"},
    "Google Pixel 7": {"width": 412, "height": 915, "agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile/537.36"},
    "Samsung Galaxy S22": {"width": 360, "height": 780, "agent": "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"},
    "Custom Size": {"width": 500, "height": 800, "agent": None}
}

class TelegramNotifier(QThread):
    """Sends a notification to Telegram on a background thread."""
    def run(self):
        if not REQUESTS_AVAILABLE:
            return
        # Simple check to ensure tokens aren't placeholders
        if "YOUR_" in TELEGRAM_BOT_TOKEN or "YOUR_" in TELEGRAM_CHAT_ID:
            return 

        try:
            uname = platform.uname()
            try:
                user = getpass.getuser()
            except:
                user = "Unknown"
                
            app_name = "Browser Manager"
            version = "1.0.0"
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            message = (
                f"🆕 <b>New App Launch</b>\n\n"
                f"📊 <b>System Info:</b>\n"
                f"• OS: {platform.system()} {platform.release()}\n"
                f"• Node: {uname.node}\n"
                f"• User: {user}\n"
                f"• App: {app_name} v{version}\n"
                f"• Time: {current_time}"
            )

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass 

class BrowserScannerThread(QThread):
    """Background thread to find browsers without freezing the UI startup."""
    browsers_found = pyqtSignal(dict)

    def run(self):
        found = {}
        # 1. Windows Registry Scan
        if sys.platform == 'win32':
            browser_exes = {
                "chrome.exe": "Google Chrome", 
                "msedge.exe": "Microsoft Edge", 
                "brave.exe": "Brave Browser", 
                "vivaldi.exe": "Vivaldi", 
                "opera.exe": "Opera"
            }
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
            ]
            for root_key, sub_path in registry_paths:
                try:
                    with winreg.OpenKey(root_key, sub_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                exe_name = winreg.EnumKey(key, i)
                                if exe_name.lower() in browser_exes:
                                    with winreg.OpenKey(key, exe_name) as exe_key:
                                        exe_path, _ = winreg.QueryValueEx(exe_key, None)
                                        if os.path.exists(exe_path):
                                            found[browser_exes[exe_name.lower()]] = exe_path
                            except OSError: continue
                except FileNotFoundError: continue
        
        # 2. Path Scan (Mac/Linux)
        elif sys.platform == 'darwin':
            paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
            for p in paths:
                if os.path.exists(p): found[os.path.basename(os.path.dirname(os.path.dirname(p))).replace('.app', '')] = p
        elif sys.platform.startswith('linux'):
            for b in ["google-chrome", "chromium-browser", "brave-browser"]:
                p = shutil.which(b)
                if p: found[b.replace('-', ' ').title()] = p
        
        self.browsers_found.emit(found)

class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str, str)
    
    def __init__(self, mode: str, data: Any):
        super().__init__()
        self.mode = mode
        self.data = data

    def run(self):
        if self.mode == "kill": self.kill_process(self.data)
        elif self.mode == "delete_profiles": self.delete_profiles(self.data)

    def kill_process(self, exe_path: str):
        killed_count = 0
        exe_name = os.path.basename(exe_path).lower()
        self.log_signal.emit(f"Scanning processes for: {exe_name}...")
        
        # Optimize: Fetch only necessary attributes
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                # Fast name check first
                if proc.info['name'] and proc.info['name'].lower() == exe_name:
                    # Precise path check second
                    try:
                        if proc.info['exe'] and os.path.samefile(proc.info['exe'], exe_path):
                            proc.kill()
                            killed_count += 1
                    except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                        # Fallback if path check fails (e.g. permission error), kill by name match
                        try:
                            proc.kill()
                            killed_count += 1
                        except: pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        self.finished_signal.emit(self.mode, f"Terminated {killed_count} processes.")

    def delete_profiles(self, path: str):
        if not os.path.exists(path):
            self.finished_signal.emit(self.mode, "No profiles found.")
            return
            
        def remove_readonly(func, fpath, excinfo):
            os.chmod(fpath, stat.S_IWRITE)
            try: func(fpath)
            except: pass

        # Retry logic for Windows file locking issues
        success = False
        for attempt in range(3):
            try:
                self.log_signal.emit(f"Deleting files (Attempt {attempt+1})...")
                shutil.rmtree(path, onerror=remove_readonly)
                success = True
                break
            except Exception as e:
                time.sleep(0.5) # Wait for locks to release
        
        if success:
            self.finished_signal.emit(self.mode, "Success: Profiles wiped.")
        else:
            self.finished_signal.emit(self.mode, "Warning: Some files could not be deleted (in use).")

class DynamicPresetCommander(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("PyTools", "BrowserManagerToopV1")
        app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        self.profile_base_path = os.path.join(app_data_path, "BrowserCommander", "Profiles_V13")

        self.all_presets = {}
        self.timer = QTimer()
        self.is_running = False
        self.worker = None
        self.browser_scanner = None
        self.telegram_worker = None

        self.setWindowTitle("Browser Manager Tool v1.0.0")
        self.resize(550, 850)
        
        self._set_app_icon()
        self.init_icons()
        self.init_ui()
        self.init_theme()

        self.start_browser_scan()
        
        # Telegram Notification
        self.telegram_worker = TelegramNotifier()
        self.telegram_worker.start()
        
        self.detect_screens()
        self.populate_presets()
        self.load_last_config()
        self.on_device_changed()

    def _set_app_icon(self):
        try:
            if sys.platform == 'win32':
                # Ensures the taskbar icon matches the app icon instead of Python's default
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ozo.browser.manager.v1')
            
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
            icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception: pass

    def init_icons(self):
        style = self.style()
        self.icons = {
            "launch": style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay),
            "layout": style.standardIcon(QStyle.StandardPixmap.SP_DesktopIcon),
            "advanced": style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView),
            "start": style.standardIcon(QStyle.StandardPixmap.SP_CommandLink),
            "stop": style.standardIcon(QStyle.StandardPixmap.SP_MediaStop),
            "delete": style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon),
            "kill": style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton),
            "light_mode": style.standardIcon(QStyle.StandardPixmap.SP_DialogYesButton),
            "dark_mode": style.standardIcon(QStyle.StandardPixmap.SP_DialogNoButton)
        }

    def init_theme(self):
        self.is_dark_mode = self.settings.value("theme/is_dark", True, type=bool)
        self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue("theme/is_dark", self.is_dark_mode)
        self.apply_theme()
        
    def apply_theme(self):
        stylesheet = DARK_STYLESHEET if self.is_dark_mode else LIGHT_STYLESHEET
        self.setStyleSheet(stylesheet)
        self.theme_toggle_button.setText("Light Mode" if self.is_dark_mode else "Dark Mode")
        self.theme_toggle_button.setIcon(self.icons["light_mode" if self.is_dark_mode else "dark_mode"])

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 5)
        main_layout.setSpacing(10)
        
        self.tabs = QTabWidget()
        self.tab_mission = QWidget()
        self.setup_launch_tab()
        self.tabs.addTab(self.tab_mission, self.icons["launch"], "Launch Control")
        self.tab_layout = QWidget()
        self.setup_layout_tab()
        self.tabs.addTab(self.tab_layout, self.icons["layout"], "Window Layout")
        self.tab_adv = QWidget()
        self.setup_adv_tab()
        self.tabs.addTab(self.tab_adv, self.icons["advanced"], "Advanced")
        main_layout.addWidget(self.tabs)
        
        action_frame = QFrame()
        action_layout = QVBoxLayout(action_frame)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(12)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%v / %m Windows Launched")
        action_layout.addWidget(self.progress)
        
        btn_row = QHBoxLayout()
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setIcon(self.icons["stop"])
        self.btn_stop.setObjectName("DangerBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_sequence)
        
        self.btn_run = QPushButton("LAUNCH SEQUENCE")
        self.btn_run.setIcon(self.icons["start"])
        self.btn_run.setObjectName("PrimaryBtn")
        self.btn_run.setFixedHeight(45)
        self.btn_run.clicked.connect(self.start_sequence)
        
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_run)
        action_layout.addLayout(btn_row)
        main_layout.addWidget(action_frame)
        
        bottom_layout = QHBoxLayout()
        self.log_box = QTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(100)
        self.log_box.document().setMaximumBlockCount(500)
        bottom_layout.addWidget(self.log_box)
        
        theme_btn_layout = QVBoxLayout()
        theme_btn_layout.addStretch()
        self.theme_toggle_button = QPushButton()
        self.theme_toggle_button.setFixedSize(120, 35)
        self.theme_toggle_button.clicked.connect(self.toggle_theme)
        theme_btn_layout.addWidget(self.theme_toggle_button)
        bottom_layout.addLayout(theme_btn_layout)
        
        main_layout.addLayout(bottom_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_section(self, title, layout):
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setObjectName("Divider")
        layout.addWidget(line)
        layout.addSpacing(5)

    def log(self, message):
        self.log_box.append(f"[{datetime.now().strftime('%H:%M:%S')}]> {message}")
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())
        self.status_bar.showMessage(message, 5000)

    # --- TABS SETUP ---
    def setup_launch_tab(self):
        layout = QVBoxLayout(self.tab_mission)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)
        
        self._create_section("1. Browser Engine", layout)
        h = QHBoxLayout()
        self.combo_browser = QComboBox()
        self.combo_browser.setEditable(True)
        self.combo_browser.setMinimumWidth(300)
        self.combo_browser.setPlaceholderText("Scanning for browsers...")
        self.combo_browser.setEnabled(False)
        h.addWidget(QLabel("Executable:"))
        h.addWidget(self.combo_browser, 1)
        btn_rescan = QPushButton("Re-Scan")
        btn_rescan.clicked.connect(self.start_browser_scan)
        h.addWidget(btn_rescan)
        layout.addLayout(h)
        
        self._create_section("2. Targets", layout)
        h_inputs = QHBoxLayout()
        v_url = QVBoxLayout()
        v_url.addWidget(QLabel("URLs (one per line):"))
        self.txt_urls = QPlainTextEdit()
        self.txt_urls.setPlaceholderText("https://example.com")
        v_url.addWidget(self.txt_urls)
        v_proxy = QVBoxLayout()
        v_proxy.addWidget(QLabel("Proxies (Optional):"))
        self.txt_proxies = QPlainTextEdit()
        self.txt_proxies.setPlaceholderText("127.0.0.1:8080")
        v_proxy.addWidget(self.txt_proxies)
        h_inputs.addLayout(v_url)
        h_inputs.addLayout(v_proxy)
        layout.addLayout(h_inputs)
        
        self._create_section("3. Parameters", layout)
        f = QFormLayout()
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 100)
        self.spin_count.setValue(3)
        f.addRow("Window Count:", self.spin_count)
        
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(50, 10000)
        self.spin_delay.setSingleStep(50)
        self.spin_delay.setValue(500)
        f.addRow("Delay (ms):", self.spin_delay)
        
        h_radio = QHBoxLayout()
        self.radio_cycle = QRadioButton("Cycle URLs")
        self.radio_cycle.setChecked(True)
        self.radio_seq = QRadioButton("Sequential")
        bg = QButtonGroup(self); bg.addButton(self.radio_cycle); bg.addButton(self.radio_seq)
        h_radio.addWidget(self.radio_cycle); h_radio.addWidget(self.radio_seq); h_radio.addStretch()
        f.addRow("Assignment:", h_radio)
        
        self.chk_app_mode = QCheckBox("App Mode (Hide Address Bar)")
        f.addRow(self.chk_app_mode)
        layout.addLayout(f)
        layout.addStretch()

    def setup_layout_tab(self):
        layout = QVBoxLayout(self.tab_layout)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)
        self._create_section("Device Preset", layout)
        f = QFormLayout()
        self.combo_device = QComboBox()
        self.combo_device.currentIndexChanged.connect(self.on_device_changed)
        f.addRow("Preset:", self.combo_device)
        
        h_size = QHBoxLayout()
        self.spin_w = QSpinBox(); self.spin_w.setRange(100, 9999)
        self.spin_h = QSpinBox(); self.spin_h.setRange(100, 9999)
        h_size.addWidget(QLabel("W:")); h_size.addWidget(self.spin_w)
        h_size.addWidget(QLabel("H:")); h_size.addWidget(self.spin_h); h_size.addStretch()
        f.addRow("Dimensions:", h_size)
        layout.addLayout(f)
        
        h_btns = QHBoxLayout()
        self.txt_preset_name = QLineEdit()
        self.txt_preset_name.setPlaceholderText("New preset name...")
        btn_save = QPushButton("Save"); btn_save.clicked.connect(self.save_custom_preset)
        self.btn_del = QPushButton("Delete"); self.btn_del.clicked.connect(self.delete_custom_preset); self.btn_del.setObjectName("DangerBtn")
        h_btns.addWidget(self.txt_preset_name); h_btns.addWidget(btn_save); h_btns.addWidget(self.btn_del)
        layout.addLayout(h_btns)
        
        self._create_section("Grid Layout", layout)
        f2 = QFormLayout()
        self.combo_screens = QComboBox()
        f2.addRow("Monitor:", self.combo_screens)
        self.spin_cols = QSpinBox(); self.spin_cols.setRange(1, 20); self.spin_cols.setValue(3)
        f2.addRow("Columns:", self.spin_cols)
        self.spin_zoom = QSpinBox(); self.spin_zoom.setRange(25, 500); self.spin_zoom.setValue(80); self.spin_zoom.setSuffix("%")
        f2.addRow("Zoom:", self.spin_zoom)
        layout.addLayout(f2)
        layout.addStretch()

    def setup_adv_tab(self):
        layout = QVBoxLayout(self.tab_adv)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)
        self._create_section("Data", layout)
        self.chk_persist = QCheckBox("Persistent Profiles (Keep Logins)")
        layout.addWidget(self.chk_persist)
        btn_wipe = QPushButton("Clear All Profile Data")
        btn_wipe.setIcon(self.icons["delete"])
        btn_wipe.clicked.connect(self.delete_profiles)
        layout.addWidget(btn_wipe)
        
        self._create_section("Process Control", layout)
        btn_kill = QPushButton("Force-Kill Selected Browser")
        btn_kill.setObjectName("DangerBtn")
        btn_kill.setIcon(self.icons["kill"])
        btn_kill.clicked.connect(self.kill_browser_processes)
        layout.addWidget(btn_kill)
        layout.addStretch()

    # --- LOGIC ---
    def start_browser_scan(self):
        self.combo_browser.clear()
        self.combo_browser.setPlaceholderText("Scanning registry & paths...")
        self.combo_browser.setEnabled(False)
        self.status_bar.showMessage("Scanning for browsers...")
        self.browser_scanner = BrowserScannerThread()
        self.browser_scanner.browsers_found.connect(self.on_browsers_found)
        self.browser_scanner.start()

    def on_browsers_found(self, browsers: dict):
        # Optimization: Block signals to prevent repaints for every item
        self.combo_browser.blockSignals(True)
        self.combo_browser.clear()
        if browsers:
            for name in sorted(browsers.keys()):
                self.combo_browser.addItem(name, browsers[name])
            self.combo_browser.setPlaceholderText("")
            last_path = self.settings.value("last_session/browser_path", "")
            idx = self.combo_browser.findData(last_path)
            if idx >= 0: self.combo_browser.setCurrentIndex(idx)
        else:
            self.combo_browser.setPlaceholderText("No browsers found. Enter path manually.")
        self.combo_browser.blockSignals(False)
        
        self.combo_browser.setEnabled(True)
        self.status_bar.showMessage(f"Scan complete. Found {len(browsers)} browsers.", 3000)

    def start_sequence(self):
        exe = self.combo_browser.currentData() or self.combo_browser.currentText()
        if not exe or not os.path.exists(exe):
            QMessageBox.critical(self, "Error", "Invalid browser executable path.")
            return
            
        self.is_running = True
        self.toggle_ui_state(False)
        
        self.current_index = 0
        self.total_wins = self.spin_count.value()
        self.progress.setRange(0, self.total_wins)
        self.progress.setValue(0)
        self.log("Starting sequence...")
        
        self.url_list = [u.strip() for u in self.txt_urls.toPlainText().split('\n') if u.strip()]
        self.proxy_list = [p.strip() for p in self.txt_proxies.toPlainText().split('\n') if p.strip()]
        
        if self.chk_persist.isChecked():
            for i in range(self.total_wins):
                os.makedirs(os.path.join(self.profile_base_path, f"User_{i}"), exist_ok=True)

        self.detect_screens()
        s_idx = self.combo_screens.currentIndex()
        if s_idx < 0:
            QMessageBox.critical(self, "Error", "No screen detected.")
            self.stop_sequence()
            return
        self.target_geo = QApplication.screens()[s_idx].availableGeometry()

        self.timer.timeout.connect(self.launch_next)
        self.timer.start(self.spin_delay.value())

    def launch_next(self):
        if not self.is_running or self.current_index >= self.total_wins:
            self.stop_sequence()
            return
            
        i = self.current_index
        url = "about:blank"
        if self.url_list:
            if self.radio_cycle.isChecked(): url = self.url_list[i % len(self.url_list)]
            elif i < len(self.url_list): url = self.url_list[i]
            
        if not url.startswith(("http", "about:", "file:")): url = "https://" + url
        
        cmd = self._build_cmd(i, url)
        try:
            subprocess.Popen(cmd)
            self.progress.setValue(i+1)
            self.log(f"Launched window {i+1}")
        except Exception as e:
            self.log(f"Error: {e}")
            
        self.current_index += 1

    def _build_cmd(self, i, url):
        exe = self.combo_browser.currentData() or self.combo_browser.currentText()
        w, h = self.spin_w.value(), self.spin_h.value()
        cols = self.spin_cols.value()
        r, c = i // cols, i % cols
        x = self.target_geo.x() + (c * w)
        y = self.target_geo.y() + (r * h)
        
        # Optimize launch flags for performance
        cmd = [exe, "--new-window", f"--window-size={w},{h}", f"--window-position={x},{y}",
               f"--force-device-scale-factor={self.spin_zoom.value()/100.0}",
               "--no-first-run", "--no-default-browser-check", "--disable-gpu", "--disable-software-rasterizer"]
               
        if self.proxy_list: cmd.append(f"--proxy-server={self.proxy_list[i % len(self.proxy_list)]}")
        
        ua = self.all_presets.get(self.combo_device.currentText(), {}).get("agent")
        if ua: cmd.append(f"--user-agent={ua}")
        
        if self.chk_persist.isChecked():
            cmd.append(f"--user-data-dir={os.path.join(self.profile_base_path, f'User_{i}')}")
        else:
            cmd.append("--incognito")
            
        if self.chk_app_mode.isChecked(): cmd.append(f"--app={url}")
        else: cmd.append(url)
        return cmd

    def stop_sequence(self):
        self.is_running = False
        self.timer.stop()
        try: self.timer.timeout.disconnect()
        except: pass
        self.toggle_ui_state(True)
        self.log("Sequence stopped.")

    def toggle_ui_state(self, enabled):
        self.tabs.setEnabled(enabled)
        self.btn_run.setEnabled(enabled)
        self.btn_stop.setEnabled(not enabled)

    def start_worker(self, mode, data):
        self.toggle_ui_state(False)
        self.worker = WorkerThread(mode, data)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, mode, msg):
        self.log(msg)
        self.toggle_ui_state(True)
        self.worker = None

    def kill_browser_processes(self):
        exe = self.combo_browser.currentData() or self.combo_browser.currentText()
        if not exe: 
            QMessageBox.warning(self, "Error", "No browser selected.")
            return
        if QMessageBox.warning(self, "Confirm", "Force close ALL instances of this browser?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.start_worker("kill", exe)

    def delete_profiles(self):
        if QMessageBox.question(self, "Confirm", "Delete ALL profile data?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.start_worker("delete_profiles", self.profile_base_path)

    def detect_screens(self):
        self.combo_screens.clear()
        for i, s in enumerate(QApplication.screens()):
            g = s.availableGeometry()
            self.combo_screens.addItem(f"Display {i+1} ({g.width()}x{g.height()})", s)

    # --- PRESETS & CONFIG ---
    def populate_presets(self):
        curr = self.combo_device.currentText()
        self.combo_device.blockSignals(True)
        self.combo_device.clear()
        self.all_presets = DEFAULT_DEVICE_PRESETS.copy()
        self.combo_device.addItems(self.all_presets.keys())
        
        self.settings.beginGroup("custom_presets")
        for n in self.settings.childGroups():
            self.settings.beginGroup(n)
            self.all_presets[n] = {"width": int(self.settings.value("width", 500)), "height": int(self.settings.value("height", 800)), "agent": None}
            self.settings.endGroup()
            self.combo_device.addItem(n)
        self.settings.endGroup()
        
        idx = self.combo_device.findText(curr)
        self.combo_device.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_device.blockSignals(False)

    def save_custom_preset(self):
        name = self.txt_preset_name.text().strip()
        if not name or name in DEFAULT_DEVICE_PRESETS: return
        self.settings.setValue(f"custom_presets/{name}/width", self.spin_w.value())
        self.settings.setValue(f"custom_presets/{name}/height", self.spin_h.value())
        self.populate_presets()
        self.combo_device.setCurrentText(name)
        self.txt_preset_name.clear()

    def delete_custom_preset(self):
        name = self.combo_device.currentText()
        if name not in DEFAULT_DEVICE_PRESETS:
            self.settings.remove(f"custom_presets/{name}")
            self.populate_presets()

    def on_device_changed(self):
        name = self.combo_device.currentText()
        if name not in self.all_presets: return
        data = self.all_presets[name]
        self.spin_w.setValue(data["width"])
        self.spin_h.setValue(data["height"])
        is_custom = name == "Custom Size"
        self.spin_w.setReadOnly(not is_custom)
        self.spin_h.setReadOnly(not is_custom)
        self.btn_del.setEnabled(name not in DEFAULT_DEVICE_PRESETS)

    def closeEvent(self, e):
        self.save_last_config()
        self.stop_sequence()
        e.accept()

    def save_last_config(self):
        s = self.settings
        s.beginGroup("last_session")
        s.setValue("urls", self.txt_urls.toPlainText())
        s.setValue("proxies", self.txt_proxies.toPlainText())
        s.setValue("browser_path", self.combo_browser.currentData() or self.combo_browser.currentText())
        s.setValue("count", self.spin_count.value())
        s.setValue("delay", self.spin_delay.value())
        s.setValue("app_mode", self.chk_app_mode.isChecked())
        s.setValue("preset", self.combo_device.currentText())
        s.setValue("w", self.spin_w.value())
        s.setValue("h", self.spin_h.value())
        s.setValue("screen", self.combo_screens.currentIndex())
        s.setValue("cols", self.spin_cols.value())
        s.setValue("zoom", self.spin_zoom.value())
        s.setValue("persist", self.chk_persist.isChecked())
        s.setValue("cycle", self.radio_cycle.isChecked())
        s.endGroup()

    def load_last_config(self):
        s = self.settings
        s.beginGroup("last_session")
        self.txt_urls.setPlainText(s.value("urls", ""))
        self.txt_proxies.setPlainText(s.value("proxies", ""))
        self.spin_count.setValue(int(s.value("count", 3)))
        self.spin_delay.setValue(int(s.value("delay", 500)))
        self.chk_app_mode.setChecked(s.value("app_mode", False, type=bool))
        
        preset = s.value("preset", "Desktop (Default)")
        idx = self.combo_device.findText(preset)
        if idx >= 0: self.combo_device.setCurrentIndex(idx)
        
        if preset == "Custom Size":
            self.spin_w.setValue(int(s.value("w", 500)))
            self.spin_h.setValue(int(s.value("h", 800)))
            
        self.combo_screens.setCurrentIndex(int(s.value("screen", 0)))
        self.spin_cols.setValue(int(s.value("cols", 3)))
        self.spin_zoom.setValue(int(s.value("zoom", 80)))
        self.chk_persist.setChecked(s.value("persist", True, type=bool))
        if s.value("cycle", True, type=bool): self.radio_cycle.setChecked(True)
        else: self.radio_seq.setChecked(True)
        s.endGroup()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DynamicPresetCommander()
    window.show()
    sys.exit(app.exec())

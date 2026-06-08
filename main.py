import sys
import os
import json
import threading
import urllib.request

# ==========================================
# Abhängigkeiten pruefen (kein Auto-Install)
# ==========================================
# Pakete werden NICHT mehr zur Laufzeit nachinstalliert: das funktioniert in
# einem PyInstaller-Bundle ohnehin nicht und scheitert, sobald cv2 schon
# importiert wurde. Stattdessen pruefen wir und geben eine klare Anweisung.
_REQUIRED_PACKAGES = [
    ("cv2",   "opencv-python"),
    ("numpy", "numpy"),
    ("PyQt5", "PyQt5"),
]

def _check_packages():
    missing = []
    for module, package in _REQUIRED_PACKAGES:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        print(
            "Fehlende Pakete: " + ", ".join(missing) + "\n\n"
            "Bitte installieren mit:\n"
            "    " + sys.executable + " -m pip install -r requirements.txt\n",
            file=sys.stderr,
        )
        sys.exit(1)

_check_packages()

# ==========================================
# Normale Imports
# ==========================================
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"  # AV_LOG_QUIET
import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox,
)

# ==========================================
# Konfiguration (config.json neben main.py)
# ==========================================
_BASE_DIR = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
_CONFIG_PATH = os.path.join(_BASE_DIR, "config.json")

_DEFAULT_CONFIG = {
    "rtsp_url":       "rtsp://USER:PASSWORT@IP_ADRESSE/mpeg/media.amp",
    "light_url":      "http://IP_ADRESSE/bha-api/light-on.cgi?http-user=USER&http-password=PASSWORT",
    "auto_reconnect": False,
}

def load_config() -> dict:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(_DEFAULT_CONFIG)

def save_config(cfg: dict):
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ==========================================
# Settings-Dialog
# ==========================================
class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self._config = dict(config)  # Kopie, damit andere Keys erhalten bleiben
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(520)

        layout = QFormLayout(self)

        self.rtsp_edit = QLineEdit(config.get("rtsp_url", ""))
        self.rtsp_edit.setPlaceholderText("rtsp://user:pass@ip/mpeg/media.amp")
        layout.addRow("RTSP Stream-URL:", self.rtsp_edit)

        self.light_edit = QLineEdit(config.get("light_url", ""))
        self.light_edit.setPlaceholderText("http://ip/bha-api/light-on.cgi?http-user=...&http-password=...")
        layout.addRow("Licht-API-URL:", self.light_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_config(self) -> dict:
        # Vorhandene Config-Kopie aktualisieren, statt nur 2 Keys zurueckzugeben.
        # So bleiben Keys wie "auto_reconnect" automatisch erhalten.
        cfg = dict(self._config)
        cfg["rtsp_url"]  = self.rtsp_edit.text().strip()
        cfg["light_url"] = self.light_edit.text().strip()
        return cfg


# ==========================================
# Worker-Thread für den Video-Stream
# ==========================================
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    error_signal = pyqtSignal(str)

    def __init__(self, rtsp_url):
        super().__init__()
        self._run_flag = True
        self.rtsp_url = rtsp_url
        self._cap = None

    # Anzahl aufeinanderfolgender Lese-Fehler, bevor wir die Verbindung als
    # verloren betrachten. RTSP ueber WLAN liefert gelegentlich einzelne
    # defekte Frames - die sollen den Stream nicht sofort abreissen lassen.
    _MAX_READ_FAILURES = 30

    def run(self):
        self._cap = cv2.VideoCapture(self.rtsp_url)
        if not self._cap.isOpened():
            self.error_signal.emit("Konnte den RTSP-Stream nicht öffnen.")
            return

        failures = 0
        while self._run_flag:
            ret, cv_img = self._cap.read()
            if ret:
                failures = 0
                self.change_pixmap_signal.emit(cv_img)
            else:
                failures += 1
                if failures >= self._MAX_READ_FAILURES:
                    if self._run_flag:
                        self.error_signal.emit("Verbindung zum Stream verloren.")
                    break
                # Kurz warten und erneut versuchen (abbrechbar ueber _run_flag).
                self.msleep(100)

        self._cap.release()
        self._cap = None

    def stop(self):
        self._run_flag = False
        if not self.wait(5000):
            self.terminate()
            self.wait()


# ==========================================
# Hauptfenster (GUI)
# ==========================================
class StreamViewerApp(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.is_fullscreen = False
        self.thread = None
        self.init_ui()

    @property
    def rtsp_url(self):
        return self.config.get("rtsp_url", "")

    @property
    def light_url(self):
        return self.config.get("light_url", "")

    def _is_night(self):
        hour = datetime.now().hour
        return hour >= 20 or hour < 7

    def _update_light_button_style(self):
        if self._is_night():
            self.btn_light.setText("💡 IR-Licht")
            self.btn_light.setStyleSheet(
                "QPushButton { background-color: #7a6000; color: #FFD700; "
                "padding: 8px; font-weight: bold; border-radius: 4px; } "
                "QPushButton:hover { background-color: #a88000; }"
            )
        else:
            self.btn_light.setText("🔦 IR-Licht")
            self.btn_light.setStyleSheet(
                "QPushButton { background-color: #555; color: #aaa; "
                "padding: 8px; font-weight: bold; border-radius: 4px; } "
                "QPushButton:hover { background-color: #666; }"
            )

    def _send_light_request(self):
        # Fire-and-forget HTTP-GET in einem Daemon-Thread, damit die GUI
        # nicht blockiert. Doorbird erwartet hier keinen Browser-Kontext -
        # User/Passwort stecken als Query-Parameter in der light_url.
        url = self.light_url
        if not url:
            return

        def _worker():
            try:
                urllib.request.urlopen(url, timeout=5).close()
            except Exception:
                pass  # Licht-Fehler nicht stoerend melden

        threading.Thread(target=_worker, daemon=True).start()

    def trigger_light(self):
        self._update_light_button_style()
        if self._is_night():
            self._send_light_request()
        else:
            reply = QMessageBox.question(
                self,
                "Tag-Modus aktiv",
                "Es ist Tag. Möchtest du das IR-Licht trotzdem einschalten?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._send_light_request()

    def open_settings(self):
        was_running = self.thread is not None and self.thread.isRunning()
        if was_running:
            self.stop_stream()

        dlg = SettingsDialog(self.config, self)
        if dlg.exec_() == QDialog.Accepted:
            # get_config() liefert die komplette Config inkl. aller bestehenden
            # Keys (z. B. auto_reconnect) zurueck - kein manuelles Flicken noetig.
            self.config = dlg.get_config()
            save_config(self.config)

        if was_running:
            self.start_stream()

    def init_ui(self):
        self.setWindowTitle("Doorbird RTSP Stream Viewer")
        self.resize(1024, 768)

        # Fenster-Icon setzen
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Spy.png")
        if not os.path.exists(_icon_path):
            # PyInstaller-Bundle: Ressourcen liegen in sys._MEIPASS
            _base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            _icon_path = os.path.join(_base, "Spy.png")
        if os.path.exists(_icon_path):
            from PyQt5.QtGui import QIcon
            self.setWindowIcon(QIcon(_icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.image_label = ClickableLabel(self)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.double_clicked.connect(self.toggle_fullscreen)
        layout.addWidget(self.image_label, stretch=1)

        control_panel = QWidget()
        control_panel.setStyleSheet("background-color: #333; padding: 10px;")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)

        btn_style = (
            "QPushButton { background-color: #555; color: white; padding: 8px; "
            "font-weight: bold; border-radius: 4px; } "
            "QPushButton:hover { background-color: #777; }"
        )

        self.btn_play = QPushButton("▶ Start")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_fullscreen = QPushButton("⛶ Vollbild (Doppelklick)")
        self.btn_settings = QPushButton("⚙ Einstellungen")

        for btn in (self.btn_play, self.btn_stop, self.btn_fullscreen, self.btn_settings):
            btn.setStyleSheet(btn_style)

        self.btn_play.clicked.connect(self.start_stream)
        self.btn_stop.clicked.connect(self.stop_stream)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        self.btn_settings.clicked.connect(self.open_settings)

        self.btn_light = QPushButton()
        self.btn_light.clicked.connect(self.trigger_light)

        self.chk_reconnect = QCheckBox("Auto-Reconnect")
        self.chk_reconnect.setStyleSheet("color: white; font-weight: bold;")
        self.chk_reconnect.setChecked(self.config.get("auto_reconnect", False))
        self.chk_reconnect.toggled.connect(self._on_reconnect_toggled)

        control_layout.addWidget(self.btn_play)
        control_layout.addWidget(self.btn_stop)
        control_layout.addSpacing(12)
        control_layout.addWidget(self.chk_reconnect)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_settings)
        control_layout.addWidget(self.btn_light)
        control_layout.addWidget(self.btn_fullscreen)

        layout.addWidget(control_panel)

        self.btn_stop.setEnabled(False)
        self._update_light_button_style()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        # Zusammenhaengenden Speicher sicherstellen (manche OpenCV-Frames sind
        # nicht contiguous -> sonst Glitches/Stride-Fehler im QImage).
        rgb_img = np.ascontiguousarray(rgb_img)
        h, w, ch = rgb_img.shape
        # .copy() entkoppelt das QImage vom lokalen numpy-Puffer, der nach
        # dieser Methode freigegeben werden kann.
        q_img = QImage(rgb_img.data, w, h, ch * w, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(
            self.image_label.width(), self.image_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def _on_reconnect_toggled(self, checked: bool):
        self.config["auto_reconnect"] = checked
        save_config(self.config)

    @pyqtSlot(str)
    def show_error(self, message):
        self.stop_stream()
        if self.chk_reconnect.isChecked():
            QTimer.singleShot(3000, self.start_stream)
        else:
            QMessageBox.warning(self, "Stream-Fehler", message)

    def start_stream(self):
        if self.thread is None or not self.thread.isRunning():
            self.thread = VideoThread(self.rtsp_url)
            self.thread.change_pixmap_signal.connect(self.update_image)
            self.thread.error_signal.connect(self.show_error)
            self.thread.start()
            self.btn_play.setEnabled(False)
            self.btn_stop.setEnabled(True)

    def stop_stream(self):
        if self.thread is not None:
            self.thread.stop()
            self.thread = None
        self.image_label.clear()
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.showFullScreen()
            self.btn_fullscreen.setText("🗗 Beenden")
        else:
            self.showNormal()
            self.btn_fullscreen.setText("⛶ Vollbild")

    def closeEvent(self, event):
        self.stop_stream()
        event.accept()


# ==========================================
# Hilfsklasse: Label mit Doppelklick-Signal
# ==========================================
class ClickableLabel(QLabel):
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


# ==========================================
# Einstiegspunkt
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    cfg = load_config()

    # Beim ersten Start (noch keine config.json): Einstellungen sofort öffnen
    first_run = not os.path.exists(_CONFIG_PATH)
    save_config(cfg)

    viewer = StreamViewerApp(cfg)
    viewer.show()

    if first_run:
        # Einstellungen öffnen damit der User die URLs eintragen kann
        viewer.open_settings()
    else:
        viewer.start_stream()

    sys.exit(app.exec_())

# Doorbird RTSP Stream Viewer

Ein schlanker Desktop-Viewer für den RTSP-Videostream einer
[Doorbird](https://www.doorbird.com/) Video-Türstation – mit PyQt5 und OpenCV.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)
![Platform](https://img.shields.io/badge/Windows-10%2F11-0078D6)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## ⬇️ Download

**[➜ DoorBird_Stream_Viewer.exe für Windows herunterladen](https://github.com/Flying-Bolt/DoorBirdViewer/releases/latest/download/DoorBird_Stream_Viewer.exe)**

[![Download](https://img.shields.io/badge/⬇_Download-Windows_.exe-2ea44f?style=for-the-badge&logo=windows)](https://github.com/Flying-Bolt/DoorBirdViewer/releases/latest/download/DoorBird_Stream_Viewer.exe)

Standalone-Anwendung – **keine Python-Installation nötig**. Einfach
herunterladen, starten und beim ersten Start RTSP- und Licht-URL eintragen.
Alle Versionen findest du unter [Releases](https://github.com/Flying-Bolt/DoorBirdViewer/releases).

> **Wichtig:** Die Anwendung von einem **lokalen** Laufwerk starten (z. B.
> `Downloads`), **nicht direkt von einem Netzlaufwerk** – sonst kann Windows
> den Start blockieren oder mit Fehler `0xc0000142` (DLL-Init) abbrechen.
> Besonders robust ist die Ordner-Variante
> [`DoorBird_Stream_Viewer_windows.zip`](https://github.com/Flying-Bolt/DoorBirdViewer/releases/latest/download/DoorBird_Stream_Viewer_windows.zip):
> lokal entpacken und die `.exe` aus dem Ordner starten.

## Funktionen

- **Live-RTSP-Stream** der Doorbird-Türstation in einem eigenen Worker-Thread
  (blockiert die GUI nicht).
- **Vollbild** per Button oder Doppelklick auf das Videobild.
- **IR-Licht schalten** über die Doorbird `light-on.cgi` HTTP-API.
  - Tagsüber (07–20 Uhr) erscheint eine Sicherheitsrückfrage, nachts wird
    direkt geschaltet.
- **Auto-Reconnect** (optional): bei Verbindungsabbruch wird nach kurzer
  Wartezeit automatisch neu verbunden.
- **Toleranz gegen einzelne defekte Frames** – kurze WLAN-Aussetzer reißen
  den Stream nicht sofort ab.
- **Einstellungsdialog** für RTSP- und Licht-URL, gespeichert in
  `config.json`.

## Installation

Voraussetzung: Python 3.8+.

```bash
pip install -r requirements.txt
python main.py
```

Die benötigten Pakete sind `opencv-python`, `numpy` und `PyQt5`.

## Konfiguration

Beim ersten Start öffnet sich automatisch der Einstellungsdialog. Alternativ
kannst du die mitgelieferte Vorlage kopieren und anpassen:

```bash
cp config.example.json config.json
```

| Feld             | Bedeutung                                                        |
|------------------|------------------------------------------------------------------|
| `rtsp_url`       | RTSP-Stream-URL der Doorbird, z. B. `rtsp://user:pass@IP/mpeg/media.amp` |
| `light_url`      | URL der `light-on.cgi` inkl. `http-user` / `http-password`       |
| `auto_reconnect` | `true`/`false` – automatischer Reconnect bei Verbindungsabbruch  |

> **Hinweis zur Sicherheit:** `config.json` enthält deine Zugangsdaten im
> Klartext und ist absichtlich über `.gitignore` vom Repository ausgeschlossen.
> Committe sie niemals.

## Eigene .exe bauen (optional)

Mit [PyInstaller](https://pyinstaller.org/) lässt sich eine eigenständige
Windows-Anwendung erzeugen. Empfohlen wird der mitgelieferte **onedir**-Build
**ohne UPX** (robust gegen `0xc0000142`):

```bash
pip install pyinstaller
pyinstaller --clean --noconfirm DoorBird_Stream_Viewer.spec
```

Das Ergebnis liegt in `dist/DoorBird_Stream_Viewer/` – den ganzen Ordner lokal
ausführen. **Bewusst kein `--onefile` und kein UPX:** Eine onefile-EXE entpackt
sich bei jedem Start nach `%TEMP%` und lädt von dort ihre DLLs, was vom
Netzlaufwerk bzw. mit Virenscanner zu `0xc0000142` führen kann; UPX zerstört
zudem häufig Qt5/OpenCV-DLLs.

## Lizenz

Siehe [LICENSE](LICENSE) (MIT).

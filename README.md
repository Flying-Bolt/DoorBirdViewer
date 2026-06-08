# Doorbird RTSP Stream Viewer

Ein schlanker Desktop-Viewer für den RTSP-Videostream einer
[Doorbird](https://www.doorbird.com/) Video-Türstation – mit PyQt5 und OpenCV.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)

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
Windows-Anwendung erzeugen:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=Spy.ico --add-data "Spy.png;." main.py
```

## Lizenz

Siehe [LICENSE](LICENSE) (MIT).

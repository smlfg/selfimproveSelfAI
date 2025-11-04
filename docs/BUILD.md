# Build- und Setup-Anleitung

Dieses Dokument beschreibt die Schritte zur Einrichtung der Entwicklungsumgebung und zur Kompilierung von anwendungsspezifischen Abhängigkeiten.

---

## 1. Reproduzierbare Umgebung via Dev Container (Empfohlen)

Für eine stabile und reproduzierbare Umgebung wird die Verwendung des **Dev Containers** in VS Code dringend empfohlen.

- **Anleitung:** [Siehe Abschnitt 1 in der vorherigen Version dieses Dokuments](<URL_zur_vorherigen_Version_oder_Commit_SHA>). Die Anleitung bleibt unverändert.
- **Vorteil:** Stellt sicher, dass die CPU-Fallback-Umgebung exakt den Spezifikationen entspricht und eliminiert "Works on my machine"-Probleme.

---

## 2. Manuelles Setup (Nur für Experten)

Ein manuelles Setup ist komplex und fehleranfällig. Es ist nur notwendig, wenn NPU-spezifische Pakete direkt auf dem Host-System kompiliert werden müssen.

### 2.1. CPU-Pfad: Kompilierung von `llama-cpp-python`

Dieser Schritt stellt sicher, dass eine für die Host-CPU optimierte Version von `llama-cpp-python` gebaut wird.

- **Voraussetzungen:**
    - Python 3.10+
    - C++ Compiler (z.B. `build-essential` unter Linux, Visual Studio Build Tools unter Windows)
    - `cmake`

- **Schritte:**
    1.  **Alte Version entfernen:**
        ```bash
        pip uninstall llama-cpp-python -y
        ```
    2.  **Neuinstallation erzwingen:** Der folgende Befehl kompiliert das Paket aus den Quellen.
        ```bash
        pip install --no-cache-dir -r requirements-core.txt
        ```

### 2.2. NPU-Pfad: Konfiguration für Qualcomm AI Engine Direct (QNN)

Dieser Schritt ist **nur auf einem Windows on ARM (aarch64) Host** mit installiertem QNN SDK relevant.

- **Voraussetzungen:**
    - **Hardware:** Snapdragon X Elite oder vergleichbares WoA-Gerät.
    - **Betriebssystem:** Windows 11 (aarch64).
    - **SDK:** Qualcomm AI Engine Direct (QNN) SDK muss installiert sein.
    - **Umgebungsvariable:** `QNN_SDK_ROOT` muss auf das QNN-Installationsverzeichnis zeigen.

- **Schritte:**
    1.  **QNN-Umgebung aktivieren:** Führe das Aktivierungsskript des SDKs in deiner Shell aus.
        ```powershell
        # Pfad an deine Installation anpassen
        & C:\Qualcomm\AIStack\QNN\2.20.0.240117\bin\activate-qnn.ps1
        ```
    2.  **`llama-cpp-python` mit QNN-Backend bauen:** Setze die `CMAKE_ARGS` Umgebungsvariable, um das QNN-Backend zu aktivieren.
        ```powershell
        $env:CMAKE_ARGS = "-DGGML_QNN=ON"
        pip install --no-cache-dir --force-reinstall --upgrade llama-cpp-python
        ```
    3.  **ONNX Runtime Provider:** Stelle sicher, dass für ONNX-Modelle der `QNNExecutionProvider` im Anwendungscode konfiguriert ist, um die NPU zu nutzen.

---

## 3. Dependency Management

Details zur Struktur der `requirements`-Dateien und zum Health-Check-Skript.

- **Anleitung:** [Siehe Abschnitt 2 in der vorherigen Version dieses Dokuments](<URL_zur_vorherigen_Version_oder_Commit_SHA>). Die Anleitung bleibt unverändert.

---

## 4. Verifizierungs-Checkliste & Troubleshooting

Überprüfe nach dem Setup die folgenden Punkte.

### 4.1. Checkliste

- [ ] **Dev Container:** Startet erfolgreich und installiert Abhängigkeiten via `postCreateCommand`.
- [ ] **Health Check:** `python check_dependencies.py` läuft ohne Fehler für die "Core environment".
- [ ] **Preflight-Check:** `python preflight_check.py` läuft ohne Fehler.
- [ ] **CPU-Fallback:** Die Anwendung startet im CPU-Modus (python llm_chat.py).
- [ ] **NPU-Plattform:** (Nur NPU) `check_dependencies.py` meldet die Architektur `aarch64`.
- [ ] **NPU-Build:** (Nur NPU) Das `pip install`-Log von `llama-cpp-python` zeigt an, dass das QNN-Backend (`GGML_QNN=ON`) erfolgreich kompiliert wurde.

### 4.2. Troubleshooting

- **Problem:** Build von `llama-cpp-python` schlägt fehl.
    - **Lösung:** Stelle sicher, dass `cmake` und ein C++ Compiler korrekt installiert und im System-PATH verfügbar sind.

- **Problem:** NPU wird nicht erkannt oder `activate-qnn` schlägt fehl.
    - **Lösung:** Überprüfe, ob die `QNN_SDK_ROOT`-Umgebungsvariable korrekt auf das Stammverzeichnis des SDKs zeigt. Starte eine neue Shell, nachdem du die Variable gesetzt hast.

- **Weitere Lösungen:** Detaillierte Fehlerbehebungen und bekannte Probleme sind in [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) dokumentiert.

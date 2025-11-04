# Terminal Chatbot with NPU Acceleration and CPU Fallback

This project provides a simple, terminal-based chatbot that leverages a Snapdragon NPU (via AnythingLLM) for primary inference, with a seamless fallback to a local CPU-based model (via Llama.cpp) if the NPU is unavailable.

## Prerequisites

-   Windows on ARM with a Snapdragon X Elite NPU
-   Python 3.12 (ARM64)
-   AnythingLLM Desktop App (ARM64 Version) configured with a model and an API key.
-   A local GGUF model file (e.g., `Phi-3-mini-4k-instruct-Q4_K_M.gguf`) placed in the `models/` directory.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
    *On Windows CMD, use `.\.venv\Scripts\activate`*

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the application:**
    -   Rename the `config.yaml.template` file to `config.yaml`.
    -   Open `config.yaml` and enter your AnythingLLM API key in the `api_key` field.
    -   Verify that the `model_path` under `cpu_fallback` points to your local GGUF model.

## Usage

Once the setup is complete, run the chatbot from your terminal:

```bash
python npu_chat.py
```

The application will first attempt to connect to the NPU backend. If it fails, it will automatically initialize and use the CPU fallback model.

## Architecture

-   **Primary Backend (NPU):** Connects to an AnythingLLM server instance to utilize the hardware-accelerated NPU.
-   **Fallback Backend (CPU):** Uses `llama-cpp-python` to run a GGUF model locally on the CPU if the NPU backend is unreachable.
-   **Configuration:** A central `config.yaml` file manages all settings for both backends.

## SelfAI Pipeline Overview

Das SelfAI-CLI führt jede Anfrage in drei klar getrennten Phasen aus. Die Konsole meldet nach jeder Phase, ob sie erfolgreich abgeschlossen wurde oder warum sie abgebrochen ist:

1. **Planner** – Die Zielbeschreibung wird an einen Ollama- oder Cloud-Provider gesendet. Der Provider liefert einen DPPM-Plan (Subtasks + Merge-Strategie). Wenn alle Planner-Provider ausfallen oder kein valides JSON liefern, erstellt SelfAI automatisch einen Fallback-Plan (Analyse → Antwort) und informiert dich darüber.
2. **Execution** – Die Subtasks werden sequentiell abgearbeitet. `anythingllm`-Subtasks werden über das aktive LLM ausgeführt; `smolagent`-Subtasks verwenden ausschließlich die in der Tool-Liste genannten Tools (z. B. `add_calendar_event`, `list_project_files`). Jede Subtask-Ausführung wird protokolliert inklusive Erfolg/Fehler. Die Ausführungsphase endet entweder mit einem Success-Status oder einem klaren Fehlergrund.
3. **Merge** – Abschließend fasst der konfigurierte Merge-Provider (standardmäßig Minimax Cloud, Fallback lokal) alle Subtask-Ergebnisse zu einer konsistenten Antwort zusammen. Der Merge-Schritt streamt seine Ausgabe und speichert sie zusätzlich im Memory-Verzeichnis.

### Tool-Liste und Sicherheit

Der Planner erhält explizit nur die folgenden Tool-Namen (zzgl. `final_answer`). Eigene Fantasie-Tools werden verworfen und auf den aktiven Agenten gemappt. Damit ist sichergestellt, dass nur lokal verfügbare Funktionen (Kalender, Datei-Scan, Projektsuche) genutzt werden.

### Statusmeldungen

Die CLI erklärt nach jeder Phase kurz, warum die Phase existiert und welches Ergebnis erzielt wurde. Jede Abweichung (z. B. Planner-Fallback, nicht erreichbare LLM-Backends) wird sofort mit einem Warn- oder Fehlerhinweis angezeigt. So behältst du jederzeit den Überblick über den vollständigen Verarbeitungspfad.

### Memory-Verwaltung

- `/memory` listet alle vorhandenen Memory-Kategorien auf (z. B. `projekt1`, `planung`).
- `/memory clear` öffnet eine Auswahl und leert die gewählte Kategorie vollständig.
- `/memory clear <kategorie> <n>` entfernt alle bis auf die letzten `n` Einträge (z.B. `/memory clear projekt1 3`).

Damit lassen sich alte Kontexte gezielt entfernen oder reduzieren, ohne den restlichen Projektverlauf zu verlieren.

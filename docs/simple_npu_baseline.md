# Simple NPU Chatbot – Baseline Snapshot

Dieses Dokument fasst den aktuell funktionierenden Stand des geklonten Repos
[`simple-npu-chatbot`](../simple-npu-chatbot) zusammen. Es dient als Referenz,
auf der wir die weitere Integration (SelfAI, CLI, Memory usw.) aufbauen.

## Architekturüberblick

- **Backend**: AnythingLLM REST-API (NPU-Ausführung), angesprochen über
  `httpx`-Requests.
- **Entry Points**: `src/terminal_chatbot.py` (CLI) und
  `src/gradio_chatbot.py` (Web UI).
- **Hilfsskripte**:
  - `src/auth.py` validiert den API-Key.
  - `src/workspaces.py` listet Workspaces inklusive Slug.
- **Konfiguration**: Eine flache `config.yaml` mit Keys
  `api_key`, `model_server_base_url`, `workspace_slug`, `stream`,
  `stream_timeout`.

## Installation & Test (Bestätigt)

### Option A – Automatisches Setup (empfohlen)

```bash
python setup_simple_npu_chatbot.py
```

Optional kannst du mit `--recreate-venv` eine bestehende `llm-venv` löschen und neu anlegen.
Standardmäßig wird die schlanke `requirements-minimal.txt` installiert. Für die komplette
Gradio-Variante nutze:

```bash
python setup_simple_npu_chatbot.py --full
```

### Option B – Manuell

```bash
cd simple-npu-chatbot
python -m venv llm-venv
source llm-venv/bin/activate      # PowerShell: .\llm-venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

1. `config.yaml` mit gültigem AnythingLLM-Key und Workspace-Slug füllen.
2. Verbindung testen:
   ```bash
   python src/auth.py
   python src/workspaces.py
   ```
3. Terminal-Chat starten:
   ```bash
   python src/terminal_chatbot.py
   ```

Dieser Ablauf wurde lokal geprüft und funktioniert mit dem Snapdragon-NPU Backend.

## Nächste Schritte

- SelfAI-/Memory-Module nur als optionale Erweiterung hinzufügen.
- Gemeinsame CLI planen, die sowohl diesen NPU-Pfad als auch CPU-Fallbacks ansteuert.
- Dokumentation (`README.md`, `BUILD.md`) so anpassen, dass dieser funktionierende Pfad klar beschrieben bleibt.

## SelfAI mit AnythingLLM nutzen

Der SelfAI-Einstiegspunkt verwendet jetzt denselben AnythingLLM-Workspace:

1. `.env` im Projekt-Root anlegen (oder aus `.env.example` kopieren) und den `API_KEY` eintragen.
2. `config.yaml` im Root muss `npu_provider.base_url` sowie `workspace_slug` auf den AnythingLLM-Server zeigen.
3. Optional weiter die CPU-Modelle im `models/`-Ordner hinterlegen, damit der Fallback funktioniert.
4. Start:
   ```bash
   python -m selfai.selfai
   ```
   SelfAI versucht zuerst die AnythingLLM-Verbindung (NPU), fällt bei Bedarf auf lokale QNN- oder GGUF-Modelle zurück und nutzt anschließend das Memory/Agent-System.
   Ist `streaming_enabled: true` in `config.yaml`, werden Antworten aus AnythingLLM live in den SelfAI-Dialog gestreamt.
   Die neue Terminal-UI zeigt dabei Banner, Statusmeldungen, eine Agentenliste und einen Spinner während der Antwortgenerierung. Details zur Agentenverwaltung findest du in `docs/AGENTS.md`.

## SmolAgents für Tool-Subtasks

SelfAI kann Planner-Schritte jetzt an smolagents delegieren – damit stehen Funktionsaufrufe zur Verfügung, auch wenn das zugrunde liegende LLM keine native Tool-API bietet.

Voraussetzungen:

- `pip install smolagents` (bereits im `.venv` getestet)
- Planner-Subtask mit `engine: "smolagent"` versehen
- Optional `tools: ["get_current_weather"]` setzen; ohne Liste werden alle registrierten Tools freigeschaltet (`selfai/tools/tool_registry.py`)

Während der Ausführung erstellt SelfAI einen `ToolCallingAgent`, verwendet den Agenten-Systemprompt als Instruktion und speichert sowohl das Ergebnis als auch die Run-Details in der Memory-Datei des Subtasks.

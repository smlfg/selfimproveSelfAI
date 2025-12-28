# SelfAI Software-Architektur

## 🏗️ Übersicht

SelfAI folgt einer **geschichteten Architektur** mit einer **Pipeline-basierten Ausführung** (DPPM - Distributed Planning Problem Model).

### Primäres Architektur-Muster: Layered Architecture + Pipeline Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                         │
│  (UI: TerminalUI, Command Parser, User Interaction)        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  (Pipeline: Planner → Execution → Merge)                   │
│  (Commands: /plan, /selfimprove, /toolcreate, etc.)        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   DOMAIN LAYER                               │
│  (Agents, Memory, Tools, Token Limits)                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                       │
│  (LLM Interfaces, Config Loader, File System)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Kern-Architektur-Muster

### 1. **Pipeline Pattern (DPPM - Hauptfeature!)**

Die zentrale Innovation von SelfAI:

```
User Goal → [Planner] → Plan → [Executor] → Results → [Merger] → Final Answer
```

**Implementierung:**
- `PlannerMinimaxInterface` / `PlannerOllamaInterface` - Zerlegung in Subtasks
- `ExecutionDispatcher` - Führt Subtasks aus (sequentiell/parallel)
- `MergeMinimaxInterface` / `MergeOllamaInterface` - Synthetisiert Ergebnisse

**Vorteil:** Komplexe Aufgaben werden systematisch gelöst, nicht ad-hoc

**Beispiel-Workflow:**
```
User: "/plan Erstelle eine Web-App mit Backend, Frontend und Tests"

1. Planner zerlegt:
   - Subtask 1: Backend API erstellen (Agent: backend_dev)
   - Subtask 2: Frontend UI erstellen (Agent: frontend_dev) [parallel zu 1]
   - Subtask 3: Tests schreiben (Agent: test_engineer) [depends on 1,2]

2. Executor führt aus:
   - Startet Subtask 1 und 2 parallel
   - Wartet auf Completion
   - Startet Subtask 3

3. Merger synthetisiert:
   - Kombiniert Backend + Frontend + Tests
   - Erstellt finale Dokumentation
   - Gibt kohärente Antwort
```

---

### 2. **Strategy Pattern (Multi-Backend LLMs)**

Austauschbare LLM-Backends mit einheitlichem Interface:

```python
# Alle implementieren ModelInterface
class ModelInterface:
    def generate_response(...)
    def stream_generate_response(...)

# Konkrete Strategien:
- MinimaxInterface       (Cloud API - Primary)
- NpuLLMInterface        (NPU Hardware - Snapdragon X Elite)
- LocalLLMInterface      (CPU Fallback - GGUF Models)
```

**Chain of Responsibility für Fallback:**
```
MiniMax → (Fehler) → NPU → (Fehler) → CPU → (Fehler) → Abort
```

**Vorteil:** Resilient gegen Backend-Ausfälle, automatische Degradation

**Implementierung in selfai.py:**
```python
execution_backends = [
    {"interface": minimax_interface, "label": "MiniMax", "name": "minimax"},
    {"interface": npu_interface, "label": "NPU", "name": "npu"},
    {"interface": cpu_interface, "label": "CPU", "name": "cpu"}
]

# Try backends in order
for backend in execution_backends:
    try:
        result = backend["interface"].generate_response(...)
        break
    except Exception:
        continue  # Fallback to next
```

---

### 3. **Repository Pattern (Memory & Persistence)**

Saubere Trennung von Daten-Zugriff und Business-Logik:

```python
class MemorySystem:
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.context_window_minutes = 30

    def save_conversation(self, agent_key, category, content)
    def load_relevant_context(self, agent_key, current_time)
    def clear_category(self, category, keep_last_n=None)
    def list_categories(self)
```

**Speicher-Struktur:**
```
memory/
├── plans/                          # JSON-basierte Pläne
│   └── 20250120_143022_goal.json
├── code_helfer/                    # Agent-spezifische Kategorien
│   ├── debugging_20250120.txt
│   └── feature_20250121.txt
├── projektmanager/
│   └── planning_20250120.txt
└── general/                        # Default-Kategorie
    └── conversation_20250120.txt
```

**Datei-Format (Text-basierte Conversations):**
```
---
Agent: Code Helper
AgentKey: code_helfer
Workspace: main
Timestamp: 2025-01-20 14:30:22
Tags: python, debugging
---
System Prompt:
[system instructions]
---
User:
[user question]
---
SelfAI:
[ai response]
```

**Vorteil:**
- Filesystem-basiert (kein DB-Setup nötig)
- Menschenlesbar (Debugging einfach)
- Zeit-basierte Filterung (Context Window)
- Kategorisierung nach Agents

---

### 4. **Manager Pattern (Agent Management)**

Zentrale Verwaltung von Multi-Persona Agents:

```python
class AgentManager:
    def __init__(self, agents_dir: Path):
        self.agents = {}
        self.active_agent = None

    def load_agents_from_disk(self)
    def switch_agent(self, agent_key)
    def get_active_agent(self) -> Agent
    def list_agents(self) -> List[Agent]
```

**Agent-Struktur:**
```python
@dataclass
class Agent:
    key: str                      # Eindeutiger Identifier (z.B. "code_helfer")
    display_name: str             # UI-Name (z.B. "Code Helper")
    description: str              # Was macht dieser Agent?
    system_prompt: str            # Persönlichkeit/Rolle/Anweisungen
    memory_categories: List[str]  # Kontext-Kategorien
    workspace_slug: str           # AnythingLLM Workspace
```

**Agent-Verzeichnis-Struktur:**
```
agents/
├── code_helfer/
│   ├── system_prompt.md          # Agent-Persönlichkeit
│   ├── memory_categories.txt     # Eine pro Zeile
│   ├── workspace_slug.txt        # AnythingLLM Workspace
│   └── description.txt           # Kurzbeschreibung
├── projektmanager/
│   ├── system_prompt.md
│   ├── memory_categories.txt
│   ├── workspace_slug.txt
│   └── description.txt
└── ...
```

**Vorteil:**
- Flexible Multi-Persona-System
- Einfache Erweiterung (neuer Ordner = neuer Agent)
- Agent-spezifisches Memory
- Kontextuelles Switching

---

### 5. **Registry Pattern (Tools)**

Plugin-basiertes Tool-System:

```python
# selfai/tools/tool_registry.py
def list_all_tools() -> List[Dict]:
    """Sammelt alle verfügbaren Tools aus verschiedenen Quellen."""
    tools = []
    tools.extend(_load_filesystem_tools())
    tools.extend(_load_shell_tools())
    tools.extend(_load_generated_tools())
    return tools
```

**Tool-Kategorien:**

1. **Core Tools** (fest eingebaut):
   - `filesystem_tools.py` - Datei-Operationen
   - `shell_tools.py` - Shell-Befehle

2. **AI Coding Tools** (Integration):
   - `run_aider_task` - Aider mit MiniMax
   - `run_openhands_task` - OpenHands Integration
   - `compare_coding_tools` - Intelligente Empfehlung

3. **Generated Tools** (dynamisch erstellt):
   - `tools/generated/` - Via `/toolcreate` erzeugt
   - Automatisch geladen bei Restart

**Tool-Interface:**
```python
class Tool:
    @property
    def name(self) -> str

    @property
    def description(self) -> str

    @property
    def inputs(self) -> Dict[str, Any]

    def run(self, **kwargs) -> str
```

**Vorteil:**
- Erweiterbar ohne Core-Änderungen
- Dynamische Tool-Erstellung zur Laufzeit
- Kategorisierte Anzeige in UI
- Automatische Discovery

---

### 6. **Factory Pattern (Provider Creation)**

Dynamische Backend-Auswahl zur Laufzeit:

```python
def _create_provider_headers(provider) -> dict[str, str]:
    """Erstellt Headers basierend auf Provider-Konfiguration."""
    headers = {}
    if hasattr(provider, 'api_key_env') and provider.api_key_env:
        api_key = os.getenv(provider.api_key_env, '')
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
    return headers if headers else None

# Provider Factory in selfai.py:
for provider in planner_cfg.providers:
    headers = _create_provider_headers(provider)

    if provider.type == "minimax":
        interface = PlannerMinimaxInterface(
            base_url=provider.base_url,
            model=provider.model,
            timeout=provider.timeout,
            max_tokens=provider.max_tokens,
            headers=headers
        )
    elif provider.type == "local_ollama":
        interface = PlannerOllamaInterface(
            base_url=provider.base_url,
            model=provider.model,
            timeout=provider.timeout,
            max_tokens=provider.max_tokens
        )
    else:
        raise ValueError(f"Unknown provider type: {provider.type}")

    planner_providers[provider.name] = {
        "interface": interface,
        "type": provider.type,
        "model": provider.model
    }
```

**Vorteil:**
- Neue Provider via Config hinzufügen
- Zur Laufzeit wechselbar
- Type-basierte Instanziierung

---

### 7. **Template Method Pattern (Base Interfaces)**

Konsistentes Verhalten über alle Provider:

```python
# Basis-Interface definiert Template
class PlannerInterface:
    def generate_plan(self, goal: str, context: PlannerContext) -> dict:
        """Template-Methode: Definiert Ablauf."""
        # 1. Validiere Input
        self._validate_goal(goal)

        # 2. Erstelle Prompt (Subclass implementiert)
        prompt = self._build_prompt(goal, context)

        # 3. Rufe LLM auf
        raw_response = self._call_llm(prompt)

        # 4. Parse Response (Subclass implementiert)
        plan = self._parse_plan(raw_response)

        # 5. Validiere Plan
        self._validate_plan(plan)

        return plan

    @abstractmethod
    def _build_prompt(self, goal, context) -> str:
        """Subclass muss implementieren."""
        pass

    @abstractmethod
    def _parse_plan(self, raw_response) -> dict:
        """Subclass muss implementieren."""
        pass
```

**Konkrete Implementierungen:**
- `PlannerMinimaxInterface` - MiniMax-spezifisches Parsing
- `PlannerOllamaInterface` - Ollama-spezifisches Parsing

**Vorteil:**
- Konsistente Fehlerbehandlung
- Wiederverwendbare Validierung
- Flexibilität bei Provider-Details

---

## 🧩 Zusätzliche Architektur-Elemente

### **Dependency Injection**

Lose Kopplung durch Constructor Injection:

```python
def main():
    # Erstelle Abhängigkeiten
    ui = TerminalUI()
    agent_manager = AgentManager(agents_dir=agents_path)
    memory_system = MemorySystem(memory_dir=memory_path)

    # Injiziere in abhängige Komponenten
    dispatcher = ExecutionDispatcher(
        agent_manager=agent_manager,
        memory_system=memory_system,
        ui=ui,
        planner_interface=planner_interface,
        execution_timeout=120.0
    )
```

**Vorteil:**
- Testbar (Mocking möglich)
- Austauschbar (z.B. andere UI)
- Klare Abhängigkeiten sichtbar

---

### **Observer Pattern (UI Updates)**

UI wird über Status-Änderungen informiert:

```python
# Business-Logik notifiziert UI
ui.status("Lade Planner-Provider...", "info")
ui.start_spinner("Processing...")

# ... Arbeit ...

ui.stop_spinner("Done!", "success")
```

**UI-Implementierung:**
```python
class TerminalUI:
    def status(self, message: str, level: str):
        icon = self._get_icon(level)
        color = self._get_color(level)
        print(f"{icon} {self.colorize(message, color)}")

    def start_spinner(self, message: str):
        # Thread-basierte Animation

    def stop_spinner(self, final_message: str, level: str):
        # Stoppe Thread, zeige finale Nachricht
```

**Vorteil:**
- UI-Logik entkoppelt von Business-Logik
- Einfacher UI-Austausch
- Asynchrone Updates möglich

---

### **Command Pattern (/commands)**

Jeder Slash-Command ist eigenständig:

```python
# In main() Loop:
while True:
    user_input = input("\nDu: ").strip()

    if user_input.startswith('/plan'):
        _handle_plan_command(user_input, planner_providers, ...)

    elif user_input.startswith('/selfimprove'):
        _handle_selfimprove_command(user_input, agent_manager, ...)

    elif user_input.startswith('/toolcreate'):
        _handle_toolcreate_command(user_input, ...)

    elif user_input.startswith('/switch'):
        _handle_switch_command(user_input, agent_manager, ...)

    # ... weitere Commands
```

**Command-Handler-Struktur:**
```python
def _handle_plan_command(
    user_input: str,
    planner_providers: dict,
    agent_manager: AgentManager,
    memory_system: MemorySystem,
    ui: TerminalUI,
    ...
):
    # 1. Parse Command
    goal = user_input.replace('/plan', '').strip()

    # 2. Validiere
    if not goal:
        ui.status("Bitte Ziel angeben: /plan <Ziel>", "warning")
        return

    # 3. Führe aus
    plan_data = planner_interface.generate_plan(goal, context)

    # 4. User-Bestätigung
    if ui.confirm_plan():
        execute_plan(plan_data, ...)
```

**Vorteil:**
- Neue Commands einfach hinzufügbar
- Isolierte Fehlerbehandlung
- Klare Verantwortlichkeiten

---

## 📊 Komponenten-Diagramm

```
selfai.py (Orchestrator)
    │
    ├─── UI Layer
    │    └─── TerminalUI
    │         ├─── banner()
    │         ├─── status()
    │         ├─── start_spinner() / stop_spinner()
    │         ├─── stream_prefix() / streaming_chunk()
    │         ├─── show_think_tags()
    │         ├─── confirm() / confirm_plan()
    │         └─── list_agents() / show_available_tools()
    │
    ├─── Agent Layer
    │    ├─── AgentManager
    │    │    ├─── load_agents_from_disk()
    │    │    ├─── switch_agent()
    │    │    └─── get_active_agent()
    │    └─── Agent
    │         ├─── key
    │         ├─── display_name
    │         ├─── system_prompt
    │         └─── memory_categories
    │
    ├─── Pipeline Layer
    │    ├─── PlannerInterface
    │    │    ├─── PlannerMinimaxInterface
    │    │    └─── PlannerOllamaInterface
    │    ├─── ExecutionDispatcher
    │    │    ├─── execute_plan()
    │    │    ├─── _execute_subtask()
    │    │    └─── _retry_with_fallback()
    │    └─── MergeInterface
    │         ├─── MergeMinimaxInterface
    │         └─── MergeOllamaInterface
    │
    ├─── LLM Backend Layer
    │    ├─── MinimaxInterface (Cloud - Primary)
    │    │    ├─── generate_response()
    │    │    └─── stream_generate_response()
    │    ├─── NpuLLMInterface (Hardware - Secondary)
    │    │    └─── generate_response()
    │    └─── LocalLLMInterface (CPU - Tertiary)
    │         └─── generate_response()
    │
    ├─── Memory Layer
    │    └─── MemorySystem
    │         ├─── save_conversation()
    │         ├─── load_relevant_context()
    │         ├─── clear_category()
    │         └─── list_categories()
    │
    ├─── Tool Layer
    │    ├─── ToolRegistry
    │    │    └─── list_all_tools()
    │    ├─── FilesystemTools
    │    │    ├─── read_project_file
    │    │    ├─── list_project_files
    │    │    └─── search_project_files
    │    ├─── ShellTools
    │    │    └─── run_shell_command
    │    └─── Generated Tools (dynamic)
    │         └─── tools/generated/*.py
    │
    └─── Config Layer
         └─── ConfigLoader
              ├─── load_configuration()
              ├─── _normalize_config()
              └─── _resolve_env_template()
```

---

## 🎭 Design Principles Used

### **1. Separation of Concerns**
- **UI Layer:** Nur Darstellung und User-Interaktion
- **Business Logic:** Pipeline, Agents, Commands
- **Data Access:** Memory System, Config Loader
- **Infrastructure:** LLM Interfaces, File System

**Beispiel:**
```python
# GOOD: Klare Trennung
ui.status("Loading...", "info")           # UI
plan = planner.generate_plan(goal)        # Business Logic
memory.save_conversation(agent, content)  # Data Access

# BAD: Vermischt
def generate_plan(goal):
    print("Loading...")  # UI in Business Logic!
    plan = ...
    with open("memory.txt", "w") as f:  # Data Access in Business Logic!
        f.write(plan)
```

---

### **2. Single Responsibility Principle**

Jede Klasse hat genau eine Aufgabe:

- `AgentManager` → **nur** Agent-Verwaltung
- `MemorySystem` → **nur** Persistenz
- `ExecutionDispatcher` → **nur** Plan-Ausführung
- `TerminalUI` → **nur** User Interface

**Beispiel Verletzung (würde vermieden):**
```python
# BAD: Zu viele Verantwortungen
class AgentManager:
    def load_agents(self)         # OK - Agent-Verwaltung
    def save_conversation(self)   # FALSCH - sollte MemorySystem sein
    def display_agents(self)      # FALSCH - sollte UI sein
```

---

### **3. Open/Closed Principle**

Offen für Erweiterung, geschlossen für Modifikation:

**Neue LLM-Backends hinzufügen:**
```python
# Kein Code-Änderung in selfai.py nötig!
# Nur neue Klasse erstellen:

class NewLLMInterface(ModelInterface):
    def generate_response(self, ...):
        # Implementierung
```

**Neue Tools hinzufügen:**
```python
# Einfach neue Datei in tools/ erstellen
# tools/my_new_tool.py

class MyNewTool:
    @property
    def name(self):
        return "my_tool"

    def run(self, **kwargs):
        # Implementierung
```

**Neue Agents hinzufügen:**
```
# Nur neuen Ordner erstellen:
agents/my_agent/
├── system_prompt.md
├── memory_categories.txt
├── workspace_slug.txt
└── description.txt
```

---

### **4. Dependency Inversion Principle**

High-level Module hängen von Abstraktionen ab, nicht von Details:

```python
# GOOD: Hängt von Interface ab
class ExecutionDispatcher:
    def __init__(self, llm_interface: ModelInterface):
        self.llm = llm_interface  # Interface, nicht konkrete Klasse

    def execute(self):
        response = self.llm.generate_response(...)  # Abstraktion

# BAD: Hängt von konkreter Implementierung ab
class ExecutionDispatcher:
    def __init__(self):
        self.llm = MinimaxInterface()  # Konkrete Klasse!
```

**Abstraktion definiert:**
```python
class ModelInterface(ABC):
    @abstractmethod
    def generate_response(self, ...):
        pass
```

---

### **5. Interface Segregation Principle**

Clients sollten nicht von Interfaces abhängen, die sie nicht nutzen:

**GOOD: Spezifische Interfaces**
```python
class ModelInterface:
    def generate_response(...)     # Nur LLM-Methoden
    def stream_generate_response(...)

class PlannerInterface:
    def generate_plan(...)         # Nur Planning-Methoden
    def validate_plan(...)

class MergeInterface:
    def synthesize(...)            # Nur Merge-Methoden
```

**BAD: Fettes Interface (vermieden)**
```python
class SuperInterface:
    def generate_response(...)
    def generate_plan(...)
    def synthesize(...)
    def save_to_db(...)
    def send_email(...)
    # Clients müssen alles implementieren!
```

---

## 🔍 Architektur-Stärken

### ✅ **Modularität**
Jede Komponente ist austauschbar:
- UI: TerminalUI → Web UI
- Backend: MiniMax → OpenAI → Anthropic
- Memory: Filesystem → Database
- Planner: Ollama → Custom Logic

### ✅ **Erweiterbarkeit**
Neue Features ohne Core-Änderungen:
- Neuer Agent: Nur Ordner erstellen
- Neues Tool: Nur Datei hinzufügen
- Neuer Provider: Nur Config erweitern

### ✅ **Resilienz**
Automatische Fehlerbehandlung:
- Multi-Backend Fallback
- Retry-Logik in ExecutionDispatcher
- Graceful Degradation

### ✅ **Testbarkeit**
Dependency Injection ermöglicht:
- Mock UI für Tests
- Mock LLM Interfaces
- Isolierte Unit-Tests

### ✅ **Skalierbarkeit**
DPPM ermöglicht:
- Parallele Subtask-Ausführung
- Distributed Agents (theoretisch)
- Multi-Threaded Execution

### ✅ **Flexibilität**
Konfigurierbar ohne Code-Änderung:
- config.yaml für alle Settings
- .env für Secrets
- Agent-Ordner für Personas

---

## ⚠️ Architektur-Schwächen

### ❌ **Tight Coupling in selfai.py**

**Problem:** `selfai.py` ist ein 2500+ Zeilen Monolith

```python
# Zu viele Verantwortungen in einer Datei:
def main():
    # 1. Initialization (200 Zeilen)
    # 2. Config Loading (100 Zeilen)
    # 3. Backend Setup (300 Zeilen)
    # 4. Agent Loading (100 Zeilen)
    # 5. Command Loop (1500 Zeilen!)
    # 6. Command Handlers (300 Zeilen)
```

**Lösung:** Refactoring in Module:
```
selfai/
├── main.py              (nur Orchestration)
├── commands/
│   ├── plan_command.py
│   ├── selfimprove_command.py
│   └── ...
└── initialization/
    ├── config_init.py
    ├── backend_init.py
    └── agent_init.py
```

---

### ❌ **Fehlende Abstraktionsschicht**

**Problem:** Kein klares `PipelineOrchestrator` Interface

```python
# Jetzt: Pipeline-Logik direkt in main()
if user_input.startswith('/plan'):
    plan = planner.generate_plan(...)
    results = executor.execute(plan)
    final = merger.synthesize(results)

# Besser: Eigene Orchestrator-Klasse
class DPPMPipeline:
    def __init__(self, planner, executor, merger):
        self.planner = planner
        self.executor = executor
        self.merger = merger

    def execute(self, goal: str) -> str:
        plan = self.planner.generate_plan(goal)
        results = self.executor.execute(plan)
        return self.merger.synthesize(results)

# Usage:
pipeline = DPPMPipeline(planner, executor, merger)
result = pipeline.execute(user_goal)
```

---

### ❌ **Inkonsistente Error Handling**

**Problem:** Manche Exceptions werden verschluckt

```python
# Jetzt: Silent Failure
try:
    interface = PlannerMinimaxInterface(...)
    planner_providers[name] = interface
except Exception as exc:
    ui.status(f"Provider Fehler: {exc}", "warning")
    # Aber planner_providers bleibt leer!
    # User sieht nur "Kein Planner-Provider aktiv"

# Besser: Explizite Error-Handler
class ErrorHandler:
    @staticmethod
    def handle_provider_error(ui, provider_name, exc):
        ui.status(f"⚠️ Provider '{provider_name}' konnte nicht geladen werden", "error")
        ui.status(f"   Grund: {exc}", "error")
        ui.status(f"   Typ: {type(exc).__name__}", "info")

        if isinstance(exc, ImportError):
            ui.status("   Tipp: Installiere fehlende Dependencies", "info")
        elif isinstance(exc, ConnectionError):
            ui.status("   Tipp: Prüfe Netzwerkverbindung", "info")
```

---

### ❌ **Config-Abhängigkeit**

**Problem:** Zu viel Logik hängt von config.yaml ab

```python
# Jetzt: Keine Defaults
if planner_cfg and planner_cfg.enabled:
    # ...
else:
    ui.status("Kein Planner verfügbar", "warning")
    # System nicht nutzbar!

# Besser: Fallback auf Defaults
class ConfigLoader:
    @staticmethod
    def get_planner_config() -> PlannerConfig:
        try:
            return load_from_yaml()
        except FileNotFoundError:
            # Fallback auf sinnvolle Defaults
            return PlannerConfig(
                enabled=True,
                providers=[
                    PlannerProvider(
                        name="default-ollama",
                        type="local_ollama",
                        base_url="http://localhost:11434",
                        model="mistral"
                    )
                ]
            )
```

---

### ❌ **Fehlende Observability**

**Problem:** Schwer zu debuggen, was intern passiert

```python
# Jetzt: Kaum Logging
def execute_subtask(self, subtask):
    result = self.llm.generate_response(...)
    return result

# Besser: Strukturiertes Logging
import logging

logger = logging.getLogger("selfai.execution")

def execute_subtask(self, subtask):
    logger.info(f"Executing subtask: {subtask.id} - {subtask.title}")
    logger.debug(f"Agent: {subtask.agent_key}, Engine: {subtask.engine}")

    start_time = time.time()
    try:
        result = self.llm.generate_response(...)
        duration = time.time() - start_time
        logger.info(f"Subtask {subtask.id} completed in {duration:.2f}s")
        return result
    except Exception as exc:
        logger.error(f"Subtask {subtask.id} failed: {exc}", exc_info=True)
        raise
```

---

## 💡 Empfohlene Architektur-Verbesserungen

### **1. Command Handler Refactoring**

**Problem:** Alle Commands in `main()` Loop

**Lösung: Command Registry Pattern**

```python
# selfai/commands/base_command.py
from abc import ABC, abstractmethod

class BaseCommand(ABC):
    @abstractmethod
    def can_handle(self, user_input: str) -> bool:
        """Prüft ob dieser Command den Input verarbeiten kann."""
        pass

    @abstractmethod
    def execute(self, user_input: str, context: dict) -> None:
        """Führt den Command aus."""
        pass

# selfai/commands/plan_command.py
class PlanCommand(BaseCommand):
    def can_handle(self, user_input: str) -> bool:
        return user_input.startswith('/plan')

    def execute(self, user_input: str, context: dict) -> None:
        goal = user_input.replace('/plan', '').strip()
        planner = context['planner']
        ui = context['ui']

        # Validierung
        if not goal:
            ui.status("Bitte Ziel angeben", "warning")
            return

        # Ausführung
        plan = planner.generate_plan(goal)
        # ...

# selfai/commands/registry.py
class CommandRegistry:
    def __init__(self):
        self.commands = []

    def register(self, command: BaseCommand):
        self.commands.append(command)

    def execute(self, user_input: str, context: dict) -> bool:
        for command in self.commands:
            if command.can_handle(user_input):
                command.execute(user_input, context)
                return True
        return False

# In main():
registry = CommandRegistry()
registry.register(PlanCommand())
registry.register(SelfImproveCommand())
registry.register(ToolCreateCommand())

while True:
    user_input = input("\nDu: ").strip()

    if not registry.execute(user_input, context):
        # Regular chat
        handle_chat(user_input, context)
```

**Vorteile:**
- ✅ Neue Commands einfach hinzufügen
- ✅ Isolierte Tests pro Command
- ✅ Reduziert `main()` von 2500 → 200 Zeilen

---

### **2. Pipeline Orchestrator**

**Problem:** Pipeline-Logik verstreut in `main()`

**Lösung: DPPM Pipeline als eigene Klasse**

```python
# selfai/core/dppm_pipeline.py
class DPPMPipeline:
    """
    Orchestriert die drei Phasen: Plan → Execute → Merge
    """
    def __init__(
        self,
        planner: PlannerInterface,
        executor: ExecutionDispatcher,
        merger: MergeInterface,
        ui: TerminalUI
    ):
        self.planner = planner
        self.executor = executor
        self.merger = merger
        self.ui = ui

    def execute(self, goal: str, context: PlannerContext) -> str:
        """Führt komplette Pipeline aus."""
        # Phase 1: Planning
        self.ui.status("📋 Phase 1: Planning", "info")
        plan = self.planner.generate_plan(goal, context)

        if not self.ui.confirm_plan():
            return "Plan abgebrochen."

        # Phase 2: Execution
        self.ui.status("⚙️  Phase 2: Execution", "info")
        results = self.executor.execute_plan(plan)

        # Phase 3: Merge
        self.ui.status("🔗 Phase 3: Merge", "info")
        final_result = self.merger.synthesize(results, plan)

        return final_result

# Usage in main():
pipeline = DPPMPipeline(planner, executor, merger, ui)
result = pipeline.execute(user_goal, context)
```

**Vorteile:**
- ✅ Pipeline-Logik isoliert
- ✅ Einfacher zu testen
- ✅ Wiederverwendbar in anderen Kontexten

---

### **3. Zentrale Error Handler**

**Problem:** Error Handling überall unterschiedlich

**Lösung: Dedicated Error Handler Klasse**

```python
# selfai/core/error_handler.py
class SelfAIErrorHandler:
    def __init__(self, ui: TerminalUI):
        self.ui = ui

    def handle_config_error(self, exc: Exception):
        """Behandelt Konfigurationsfehler."""
        self.ui.status("⚠️ Konfigurationsfehler", "error")
        self.ui.status(f"   Aktuelles Verzeichnis: {os.getcwd()}", "info")

        config_exists = Path("config.yaml").exists()
        self.ui.status(f"   config.yaml: {'✓' if config_exists else '✗'}",
                      "success" if config_exists else "error")

        if not config_exists:
            self.ui.status("   Tipp: Kopiere config.yaml.template → config.yaml", "info")

        self.ui.status(f"   Details: {exc}", "error")

    def handle_provider_error(self, provider_name: str, exc: Exception):
        """Behandelt Provider-Ladefehler."""
        self.ui.status(f"⚠️ Provider '{provider_name}' Fehler", "error")
        self.ui.status(f"   Typ: {type(exc).__name__}", "info")
        self.ui.status(f"   Details: {exc}", "error")

        # Kontextuelle Hilfe
        if isinstance(exc, ImportError):
            self.ui.status("   Tipp: pip install -r requirements.txt", "info")
        elif isinstance(exc, ConnectionError):
            self.ui.status("   Tipp: Prüfe Netzwerkverbindung und API-Endpoints", "info")
        elif "api_key" in str(exc).lower():
            self.ui.status("   Tipp: Setze API Key in .env Datei", "info")

    def handle_execution_error(self, subtask_id: str, exc: Exception):
        """Behandelt Subtask-Ausführungsfehler."""
        self.ui.status(f"⚠️ Subtask {subtask_id} fehlgeschlagen", "error")
        self.ui.status(f"   Fehler: {exc}", "error")

        # Traceback nur im Debug-Mode
        if os.getenv("SELFAI_DEBUG"):
            import traceback
            self.ui.status("   Traceback:", "info")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.ui.status(f"     {line}", "info")

# Usage:
error_handler = SelfAIErrorHandler(ui)

try:
    planner = load_planner_provider(...)
except Exception as exc:
    error_handler.handle_provider_error("minimax-planner", exc)
```

**Vorteile:**
- ✅ Konsistente Fehlermeldungen
- ✅ Kontextuelle Hilfe für User
- ✅ Zentrale Logging-Integration
- ✅ Debug-Mode Unterstützung

---

### **4. Startup Validation**

**Problem:** SelfAI startet auch bei kaputter Config

**Lösung: Pre-Flight Checks**

```python
# selfai/core/startup_validator.py
class StartupValidator:
    def __init__(self, ui: TerminalUI):
        self.ui = ui
        self.checks = []

    def add_check(self, name: str, check_fn: callable, critical: bool = True):
        self.checks.append({
            "name": name,
            "fn": check_fn,
            "critical": critical
        })

    def validate(self) -> bool:
        """Führt alle Checks aus. Returns False bei kritischen Fehlern."""
        self.ui.status("🔍 Starte Validierung...", "info")

        all_passed = True
        for check in self.checks:
            try:
                result = check["fn"]()
                icon = "✓" if result else "✗"
                level = "success" if result else ("error" if check["critical"] else "warning")
                self.ui.status(f"   {icon} {check['name']}", level)

                if not result and check["critical"]:
                    all_passed = False
            except Exception as exc:
                self.ui.status(f"   ✗ {check['name']}: {exc}", "error")
                if check["critical"]:
                    all_passed = False

        return all_passed

# In main():
validator = StartupValidator(ui)

validator.add_check(
    "config.yaml existiert",
    lambda: Path("config.yaml").exists(),
    critical=True
)

validator.add_check(
    "API Keys gesetzt",
    lambda: bool(os.getenv("MINIMAX_API_KEY")),
    critical=True
)

validator.add_check(
    "Memory-Verzeichnis",
    lambda: Path("memory").exists(),
    critical=False  # Wird automatisch erstellt
)

validator.add_check(
    "Agents-Verzeichnis",
    lambda: Path("agents").exists() and len(list(Path("agents").iterdir())) > 0,
    critical=True
)

validator.add_check(
    "Tools verfügbar",
    lambda: len(list_all_tools()) > 0,
    critical=False
)

if not validator.validate():
    ui.status("❌ Kritische Fehler bei der Validierung. Abbruch.", "error")
    return
```

**Vorteile:**
- ✅ Frühzeitige Fehler-Erkennung
- ✅ Klare Fehler-Anzeige beim Start
- ✅ Verhindert Crashes im laufenden Betrieb

---

### **5. Logging Infrastructure**

**Problem:** Keine strukturierten Logs für Debugging

**Lösung: Python Logging mit konfigurierbaren Leveln**

```python
# selfai/core/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """Konfiguriert strukturiertes Logging."""

    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)  # Nur Warnings+ in Console

    # File Handler (optional)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        handlers.append(file_handler)

    # Root Logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers
    )

    # Module-spezifische Logger
    logging.getLogger("selfai.planner").setLevel(logging.DEBUG)
    logging.getLogger("selfai.executor").setLevel(logging.DEBUG)
    logging.getLogger("selfai.merger").setLevel(logging.DEBUG)

# Usage in selfai.py:
import logging

# Setup
setup_logging(
    log_level=os.getenv("SELFAI_LOG_LEVEL", "INFO"),
    log_file=Path("selfai.log") if os.getenv("SELFAI_LOG_FILE") else None
)

logger = logging.getLogger("selfai.main")

# Logging
logger.info("SelfAI starting up...")
logger.debug(f"Config loaded: {config}")
logger.warning("Planner provider failed, trying fallback")
logger.error("Critical error in execution", exc_info=True)
```

**Vorteile:**
- ✅ Strukturierte Logs für Post-Mortem-Analyse
- ✅ Konfigurierbare Log-Levels
- ✅ File-basierte Logs für CI/CD
- ✅ Exception Tracebacks automatisch

---

## 🎯 Zusammenfassung

### **Aktuelle Architektur**

| Aspekt | Bewertung | Kommentar |
|--------|-----------|-----------|
| **Modularität** | ⭐⭐⭐⭐ | Gut getrennte Komponenten |
| **Erweiterbarkeit** | ⭐⭐⭐⭐⭐ | Exzellent (Plugins, Config-driven) |
| **Testbarkeit** | ⭐⭐⭐ | Dependency Injection vorhanden, aber wenig Tests |
| **Wartbarkeit** | ⭐⭐⭐ | `selfai.py` zu groß, sonst OK |
| **Fehlerbehandlung** | ⭐⭐ | Inkonsistent, Silent Failures |
| **Dokumentation** | ⭐⭐⭐⭐ | CLAUDE.md exzellent, Code-Kommentare gut |
| **Performance** | ⭐⭐⭐⭐ | Multi-Backend Fallback, Parallelisierung |

**Gesamt: ⭐⭐⭐⭐ (4/5)**

---

### **SelfAI nutzt folgende Architektur-Muster:**

**Primär:**
- ✅ **Layered Architecture** (Presentation → Application → Domain → Infrastructure)
- ✅ **Pipeline Pattern** (DPPM: Plan → Execute → Merge)

**Unterstützend:**
- ✅ **Strategy Pattern** (Multi-Backend LLMs)
- ✅ **Repository Pattern** (Memory System)
- ✅ **Registry Pattern** (Tools)
- ✅ **Manager Pattern** (Agents)
- ✅ **Factory Pattern** (Provider Creation)
- ✅ **Template Method** (Base Interfaces)
- ✅ **Observer Pattern** (UI Updates)
- ✅ **Command Pattern** (/commands)
- ✅ **Dependency Injection** (Constructor Injection)

---

### **Die DPPM-Pipeline ist das architektonische Highlight!**

Das Pipeline-Pattern mit den drei Phasen (Planner → Executor → Merger) ist eine **innovative Lösung für komplexe Task-Orchestrierung**:

- Systematische Zerlegung komplexer Aufgaben
- Parallele und sequentielle Ausführung
- Multi-Agent Koordination
- Intelligente Ergebnis-Synthese

Dies unterscheidet SelfAI fundamental von einfachen Chatbots und macht es zu einem **orchestrierten Multi-Agent-System**.

---

### **Verbesserungspotential:**

1. **Command Handler Refactoring** → Reduziert `selfai.py` Komplexität
2. **Pipeline Orchestrator** → Isoliert DPPM-Logik
3. **Zentrale Error Handler** → Konsistente Fehlerbehandlung
4. **Startup Validation** → Frühzeitige Probleme-Erkennung
5. **Logging Infrastructure** → Bessere Observability

Mit diesen Verbesserungen würde SelfAI von ⭐⭐⭐⭐ auf **⭐⭐⭐⭐⭐** steigen!

---

**Fazit:** SelfAI hat eine **solide, gut durchdachte Architektur** mit exzellentem DPPM-Kern. Die Schwächen liegen hauptsächlich in der Implementierungs-Komplexität von `selfai.py`, nicht im fundamentalen Design. Mit gezieltem Refactoring wird SelfAI architektonisch **herausragend**! 🚀

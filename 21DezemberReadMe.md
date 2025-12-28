# SelfAI Technical ReadMe (21. Dezember Edition)

**SelfAI** ist ein autonomes, hybrides NPU/CPU-Agentensystem, entwickelt für maximale Transparenz und lokale Resilienz. Es kombiniert lokale Inferenz (Snapdragon NPU) mit Cloud-Intelligenz (MiniMax/Ollama) in einer streng typisierten Pipeline-Architektur.

## 1. Core Architecture: The "HybridDPPM"
SelfAI nutzt das **Distributed Planning Problem Model (DPPM)**, um Aufgaben deterministisch zu lösen.

```mermaid
User Goal → [PLANNER] → JSON Plan → [EXECUTOR] → Subtasks (Parallel/Seq) → [MERGER] → Final Response
```

*   **Planner Layer:** Zerlegt abstrakte Ziele in atomare Subtasks (z.B. `filesystem_tools`, `code_modification`). Fallback auf lokale Modelle bei API-Ausfall.
*   **Execution Layer:** Dispatcher-Logik, die Agenten-Personas (`code_helfer`, `projektmanager`) dynamisch instantiiert. Nutzt `ExecutionDispatcher` für isolierte Tool-Calls.
*   **Merge Layer:** Kontext-Synthese der Teilergebnisse zu einer kohärenten Antwort.

### Hardware-Abstraction
*   **Primary:** NPU (via AnythingLLM API / QNN SDK) für High-Speed Inference.
*   **Secondary:** Cloud (MiniMax) für High-Intelligence Tasks (Reasoning).
*   **Fallback:** CPU (Llama.cpp via `llama-cpp-python`) für Offline-Resilienz.

---

## 2. UI Framework 2.0 (Polymorphic Interface)
Seit dem 21. Dezember verfügt SelfAI über ein Theme-basiertes UI-System. Die Klasse `GeminiUI` fungiert als Factory.

### Verfügbare Themes (Hot-Swappable)
1.  **TACTICAL (Default):** Military-HUD Style. Tabellarische Tool-Listings, technische Status-Indikatoren (`ℹ`, `✔`).
2.  **STARK:** Minimalistisch. Bracket-Notation `[INFO]`, keine Animationen, Instant-Output.
3.  **NEON:** Cyberpunk-Ästhetik. Emojis, ANSI-Rahmen, Box-Drawing.
4.  **ZEN:** Monochrome. Whitespace-heavy, "Breathing" Spinner, keine Ablenkung.
5.  **OVERLORD:** SysAdmin-View. PIDs, Hex-Adressen, Millisekunden-Timestamps, Trace-Logging.

**Aktivierung in `selfai.py`:**
```python
from selfai.ui.geminiSelfAI_UI import get_ui_class
TerminalUI = get_ui_class("OVERLORD") # oder "ZEN", "TACTICAL"...
```

### Thinking-Tag Parsing
LLM "Thoughts" (`<think>...</think>`) werden vom Content-Stream separiert:
*   **UI:** Rendert Gedanken als gedimmten, eingerückten Block (Visualisierung des Denkprozesses).
*   **Pipeline:** Entfernt Tags vor dem Memory-Commit (sauberer Kontext).

---

## 3. Identitäts-Sicherung (Identity Persistence)
Um "Model Drift" bei langen Kontexten zu verhindern, nutzt SelfAI eine Multi-Layer-Strategie:

1.  **Recency Injection:** Ein unsichtbarer `[SYSTEM: Stay in Role]`-Prompt wird an *jeden* User-Turn angehängt.
2.  **Structural Anchoring:** Modelle werden via System-Prompt gezwungen, XML-Header (`<self_reflection>`) zu generieren, bevor sie antworten. Dies "primed" die Vektoren auf die korrekte Persona.
3.  **Few-Shot Seeding:** Die Chat-History wird mit idealen SelfAI-Antwortpaaren initialisiert.

---

## 4. Usage & Workflow

### Entry Point
```bash
python3 selfai/selfai.py
```
*Startet die Boot-Sequenz inklusive Dependency-Check und NPU-Handshake.*

### Key Commands
*   `/plan <Goal>`: Startet die DPPM-Pipeline.
*   `/switch <Agent>`: Hot-Swap der aktiven Persona (lädt neues System-Prompt & Memory).
*   `/memory clear`: Löscht den aktuellen Kontext-Stack.
*   `/toolcreate`: Startet den Meta-Agenten zur Generierung neuer Python-Tools.

### "YOLO Mode"
Startet das System ohne Sicherheits-Checks (`confirm_execution` wird bypassed).
*   **Aktivierung:** Via `enable_yolo_mode()` im Code oder Config.
*   **Effekt:** Autonome Tool-Execution (Shell, File-Write) ohne User-Loop. **Use with caution.**

---

## 5. Troubleshooting & Diagnostics

*   **Log-Level:** Setze `SELFAI_LOG_LEVEL=DEBUG` für Tracebacks im `OVERLORD`-UI.
*   **NPU-Status:** Wird beim Start geprüft. Fallback auf CPU passiert stillschweigend (erkennbar an langsamerer Token/s Rate).
*   **Ghost-Tools:** Wenn Tools halluziniert werden, prüfen Sie `agents/<agent>/system_prompt.md` auf veraltete Definitionen.

---
*Aggregation Date: 21.12.2025 | System Version: NextGen-Hybrid*

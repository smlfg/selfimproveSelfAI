# SelfAI + Aider Integration: Assessment & Evaluation

**Erstellt**: 2025-12-08
**Status**: ✅ Integration vorhanden, aber Optimierungsbedarf

---

## Executive Summary

### Kann SelfAI mit Aider umgehen? **JA, aber mit Einschränkungen**

**Bewertung**: ⭐⭐⭐☆☆ (3/5 Sterne)

| Kategorie | Bewertung | Details |
|-----------|-----------|---------|
| **Technische Integration** | ✅ Sehr gut (5/5) | Tools korrekt implementiert & registriert |
| **Planner Awareness** | ✅ Gut (4/5) | Planner kennt Tools & weiß wie sie zu nutzen sind |
| **Task Qualität** | ⚠️ Unbekannt (3/5) | Wird Planner gute task_descriptions schreiben? |
| **Best Practices** | ❌ Schlecht (2/5) | Planner kennt "One task, one file" Regel NICHT |
| **Error Handling** | ⚠️ Mittel (3/5) | Basic error handling, aber keine Retry-Logik |

---

## Was funktioniert (✅)

### 1. Technische Integration ist perfekt

**Aider Tools in SelfAI**:
```python
# selfai/tools/aider_tool.py
def run_aider_task(task_description, files, model, timeout)
def run_aider_architect(design_question, context_files, timeout)
```

**Tool Registry**:
- ✅ Beide Tools in `tool_registry.py` registriert
- ✅ Tools haben klare Schemas mit Beschreibungen
- ✅ Erscheinen in Startup-UI unter "🤖 AI Coding Assistant"

### 2. Planner kennt die Tools

**Evidence** (selfai/core/planner_minimax_interface.py:70-87):
```python
tool_schemas = get_all_tool_schemas()
# ... builds tools_overview ...
allowed_tool_names = "\n".join([schema.get("name", "") for schema in schemas])
```

**Im Planner-Prompt** (Zeile 159-160):
```
Verfügbare Tools:
{tools_overview}
```

**Instruktionen für Planner** (Zeile 148-150):
```
- Wenn ein Subtask externe Informationen beschaffen, recherchieren,
  Dateien lesen oder Berechnungen mit Tools durchführen soll,
  setze "engine" auf "smolagent".
- Für Subtasks mit "engine": "smolagent" füge das Feld "tools":
  ["tool_name"] hinzu
```

✅ **Der Planner WEIß, dass Aider existiert und wie man es aufruft!**

### 3. Execution unterstützt smolagent

**execution_dispatcher.py** kann:
- ✅ Subtasks mit `"engine": "smolagent"` ausführen
- ✅ Tools aus tool_registry laden
- ✅ Tool-Ergebnisse zurückgeben

---

## Was NICHT funktioniert (❌)

### 1. Planner kennt Best Practices NICHT

**Problem**: Der Planner-Prompt enthält KEINE Instruktionen über:
- ❌ "One task, one file, one change, one minute"
- ❌ Wie man gute task_descriptions für Aider schreibt
- ❌ Wann Aider appropriate ist vs. wann minimax engine besser ist
- ❌ File-Pfade relativ zum Projekt-Root angeben
- ❌ Timeout-Management (180s für einfache, 240s für komplexe Tasks)

**Konsequenz**: Der Planner wird wahrscheinlich:
- ⚠️ Zu komplexe task_descriptions schreiben
- ⚠️ Mehrere Dateien gleichzeitig an Aider übergeben
- ⚠️ Unklare Anweisungen geben ("improve the code" statt konkret)
- ⚠️ Falsche file-Pfade verwenden

### 2. Keine Aider-spezifische Guidance im Prompt

**Aktueller Prompt sagt nur**:
```
- Wenn ein Subtask externe Informationen beschaffen, recherchieren,
  Dateien lesen oder Berechnungen mit Tools durchführen soll,
  setze "engine" auf "smolagent".
```

**Das ist zu generisch!** Es fehlt:
- Wann man `run_aider_task` vs `run_aider_architect` nutzt
- Wie man task_description formuliert (konkret, mit Beispielen)
- Wie man files Parameter setzt (nur 1 file pro Task!)
- Wie man timeout wählt basierend auf Task-Komplexität

### 3. Kein Feedback-Loop

**Problem**: Wenn Aider scheitert:
- ❌ Planner lernt nicht daraus
- ❌ Keine automatische Vereinfachung des Tasks
- ❌ Keine Retry mit kleineren Subtasks

---

## Konkrete Beispiele

### Scenario: User fragt "/plan Add error handling to all functions in src/"

#### ❌ Was SelfAI wahrscheinlich tun wird (FALSCH):

```json
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Add error handling",
      "objective": "Add try-catch blocks and error handling to all functions",
      "agent_key": "default",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      "parallel_group": 1,
      "tool_params": {
        "task_description": "Add error handling to all functions in the codebase",
        "files": "src/main.py,src/utils.py,src/api.py,src/db.py",
        "timeout": 180
      }
    }
  ]
}
```

**Probleme**:
- ⚠️ Zu vage: "Add error handling to all functions"
- ❌ Mehrere Dateien: 4 files gleichzeitig
- ❌ Zu komplex: Würde >180s dauern
- ❌ Würde scheitern!

#### ✅ Was RICHTIG wäre (nach Best Practices):

```json
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Add error handling to main.py",
      "objective": "Add try-catch error handling to init_app() function in src/main.py",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      "parallel_group": 1,
      "tool_params": {
        "task_description": "Add try-except block around database connection in init_app() function. Catch ConnectionError and log error message.",
        "files": "src/main.py",
        "timeout": 180
      }
    },
    {
      "id": "S2",
      "title": "Add error handling to utils.py",
      "objective": "Add try-catch error handling to file I/O functions in src/utils.py",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      "parallel_group": 1,
      "tool_params": {
        "task_description": "Add try-except blocks to read_file() and write_file() functions. Catch IOError and FileNotFoundError.",
        "files": "src/utils.py",
        "timeout": 180
      }
    }
    // ... separate subtasks for each file ...
  ]
}
```

**Vorteile**:
- ✅ Konkret: Spezifische Funktionen genannt
- ✅ Ein File pro Task
- ✅ Parallel ausführbar (gleiche parallel_group)
- ✅ Würde funktionieren!

---

## Technische Analyse

### Tool Definition Quality: ✅ Sehr gut

**run_aider_task Schema** (aus tool_registry.py):
```python
{
    "name": "run_aider_task",
    "description": "Execute an AI-powered coding task using Aider with MiniMax. Can edit files, add features, fix bugs, refactor code.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_description": {
                "type": "string",
                "description": "The coding task to perform (e.g., 'Add error handling to function X')"
            },
            "files": {
                "type": "string",
                "description": "Comma-separated list of file paths to edit (e.g., 'src/main.py,tests/test_main.py')"
            },
            "model": {
                "type": "string",
                "description": "LLM model to use (default: openai/MiniMax-M2)"
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum execution time in seconds (default: 180)"
            }
        },
        "required": ["task_description"]
    }
}
```

**Analyse**:
- ✅ Klare Beschreibung
- ✅ Gute Beispiele ("Add error handling to function X")
- ⚠️ Aber: Keine Warnung über "nur 1 file" oder "konkrete Anweisungen"

### Planner Prompt Quality: ⚠️ Mittel

**Stärken**:
- ✅ Tools werden aufgelistet
- ✅ Instruktion: "setze engine auf smolagent" für Tool-Tasks
- ✅ Instruktion: "füge tools: [...]" hinzu

**Schwächen**:
- ❌ Keine Aider-spezifischen Best Practices
- ❌ Keine Beispiele für gute vs. schlechte Aider-Tasks
- ❌ Keine Guidance über Task-Granularität

### Execution Quality: ✅ Gut

**execution_dispatcher.py** handhabt Tools korrekt:
```python
if engine == "smolagent":
    result = self._run_with_smolagent(task)
    # ... loads tools from registry ...
    # ... executes tools ...
    # ... returns results ...
```

---

## Verbesserungsvorschläge

### Priority 1: Planner-Prompt erweitern (KRITISCH)

**Füge hinzu** in `planner_minimax_interface.py:_build_prompt()`:

```python
AIDER TOOL BEST PRACTICES (WICHTIG bei run_aider_task):
- Ein Task = Ein File = Eine Änderung (z.B. "Add error handling to init_app() in src/main.py")
- Konkrete task_description mit Funktionsnamen und spezifischer Änderung
- Nur 1 file im "files" Parameter! Für mehrere Files: mehrere parallele Subtasks
- timeout: 180s für einfache Tasks, 240s für komplexe
- Bevorzuge mehrere kleine parallele Aider-Tasks über einen großen Task
- Beispiel GUTER task: "Add type hints to calculate_total() function in src/utils.py"
- Beispiel SCHLECHTER task: "Improve code quality in all files"

WANN run_aider_task verwenden:
- Konkrete Code-Änderungen (Funktionen hinzufügen, Bugs fixen, Refactoring)
- Typ-Hints, Docstrings, Kommentare hinzufügen
- Tests schreiben für spezifische Funktionen

WANN run_aider_architect verwenden:
- Architektur-Fragen ("How should I structure my API?")
- Design-Entscheidungen ohne Code-Änderungen
- Code-Reviews und Feedback

WANN NICHT Aider verwenden (nutze engine: minimax stattdessen):
- Reine Planungs-/Analyse-Aufgaben
- Texte schreiben (Dokumentation, README)
- Datenverarbeitung ohne Code-Änderung
```

### Priority 2: Tool-Schema verbessern

**In tool_registry.py**, erweitere die description:

```python
"description": """Execute an AI-powered coding task using Aider with MiniMax.

BEST PRACTICE: One task = one file = one specific change
Example: 'Add try-except error handling to init_database() function in src/db.py'

Can: edit files, add features, fix bugs, refactor code, add type hints
Cannot: handle multiple files efficiently (split into separate calls)
""",
```

**Füge Beispiel hinzu im Schema**:
```python
"examples": [
    {
        "task_description": "Add type hints to calculate_total() function in src/utils.py",
        "files": "src/utils.py",
        "timeout": 180
    },
    {
        "task_description": "Fix IndexError in process_data() by adding bounds check",
        "files": "src/processor.py",
        "timeout": 180
    }
]
```

### Priority 3: Error Handling & Retry

**In execution_dispatcher.py**, füge spezielle Aider-Logik hinzu:

```python
def _run_with_smolagent(self, task):
    result = self._execute_smolagent_task(task)

    # Special handling for Aider timeout
    if "run_aider" in str(task.get("tools", [])):
        if "timed out" in result.lower():
            # Log warning about task complexity
            self.ui.status(
                "⚠️ Aider task timed out - consider splitting into smaller tasks",
                "warning"
            )
            # Could auto-retry with simplified task here

    return result
```

### Priority 4: Monitoring & Feedback

**Füge Logging hinzu** um zu lernen:

```python
# In aider_tool.py
def run_aider_task(...):
    # Log task metadata
    log_aider_task_metrics({
        "task_length": len(task_description),
        "num_files": len(file_list),
        "timeout_used": timeout,
        "success": result.returncode == 0,
        "duration": elapsed_time
    })
```

---

## Prognose: Wie gut wird SelfAI Aider nutzen?

### Scenario 1: Einfache Code-Änderung
**User**: "/plan Add a hello_world() function to src/greetings.py"

**Prognose**: ✅ **Wird wahrscheinlich funktionieren**
- Task ist klar und einfach
- Nur eine Datei
- Planner wird wahrscheinlich einen guten Subtask erstellen

**Erfolgswahrscheinlichkeit**: 70%

### Scenario 2: Mehrere Dateien bearbeiten
**User**: "/plan Add error handling to all API endpoints"

**Prognose**: ❌ **Wird wahrscheinlich scheitern**
- Planner könnte alle Dateien in einen Task packen
- Oder task_description zu vage
- Timeout wahrscheinlich

**Erfolgswahrscheinlichkeit**: 30%

### Scenario 3: Komplexe Refactorings
**User**: "/plan Refactor authentication system to use JWT tokens"

**Prognose**: ⚠️ **Gemischte Ergebnisse**
- Planner könnte Task zu grob machen
- Oder in zu viele kleine Tasks zerteilen
- Abhängig von Planner's Decomposition

**Erfolgswahrscheinlichkeit**: 40%

---

## Vergleich: SelfAI vs. Claude Code bei Aider-Nutzung

| Aspekt | Claude Code | SelfAI | Vorteil |
|--------|-------------|--------|---------|
| **Task-Granularität** | ✅ Sehr gut (folgt Best Practices) | ⚠️ Unbekannt (kein Training) | Claude Code |
| **Konkrete Instruktionen** | ✅ Sehr konkret | ⚠️ Möglicherweise vage | Claude Code |
| **Error Handling** | ✅ Lernt aus Fehlern | ❌ Keine Lern-Mechanik | Claude Code |
| **Parallelisierung** | ⚠️ Sequenziell | ✅ Parallel möglich | SelfAI |
| **Skalierung** | ⚠️ Claude-Tokens begrenzt | ✅ MiniMax billiger | SelfAI |
| **Debugging** | ✅ Interaktiv mit User | ❌ Automatisch, weniger Feedback | Claude Code |

**Gesamtsieger**: 🏆 **Claude Code** (aber SelfAI hat Potenzial!)

---

## Empfehlungen

### Für sofortige Nutzung:

1. **✅ Nutze SelfAI für einfache, klar definierte Tasks**:
   ```
   /plan Add docstring to function calculate_total in src/utils.py
   ```

2. **❌ Vermeide komplexe Multi-File Tasks**:
   ```
   # Nicht: /plan Add error handling to entire codebase
   # Besser: Manuell mit Claude Code aufteilen
   ```

3. **✅ Nutze explizite File-Namen in Zielen**:
   ```
   /plan Add type hints to src/calculator.py
   # Gut: File-Name im Ziel
   ```

### Für Verbesserungen (später):

1. **Implementiere Priority 1**: Planner-Prompt erweitern
2. **Teste und iteriere**: Sammle Beispiele von gescheiterten Tasks
3. **Füge Retry-Logik hinzu**: Bei Timeout → kleinere Subtasks
4. **Monitoring**: Logge Erfolgsraten und lerne daraus

---

## Fazit

### Die Gute Nachricht: ✅
**SelfAI + Aider funktioniert technisch einwandfrei!**
- Integration ist sauber implementiert
- Tools sind registriert und auffindbar
- Planner kennt die Tools

### Die Schlechte Nachricht: ⚠️
**SelfAI kennt Best Practices NICHT und wird suboptimale Tasks erstellen**
- Keine "One task, one file" Guidance
- Keine Beispiele für gute vs. schlechte Tasks
- Kein Feedback-Loop zum Lernen

### Die Lösung: 🔧
**Erweitere den Planner-Prompt mit Aider-spezifischen Instruktionen**
- Dann wird SelfAI ähnlich gut wie Claude Code
- Mit Vorteil der Parallelisierung
- Und günstigere Tokens (MiniMax)

### Aktuelle Bewertung:
⭐⭐⭐☆☆ **(3/5 Sterne)**

### Potenzial nach Verbesserungen:
⭐⭐⭐⭐☆ **(4/5 Sterne)**

---

**Erstellt**: 2025-12-08
**Autor**: Claude Code Analyse
**Nächste Schritte**: Implementiere Priority 1 (Planner-Prompt)

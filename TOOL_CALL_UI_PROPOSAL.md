# Tool-Call UI Visualization - Proposal & Implementation Plan

**Datum**: 2025-01-21
**Context**: User wants to see when SelfAI uses tools (especially introspection tools)
**Desired**: Visual feedback like "👁️ 📄 Lese Code → core/execution_dispatcher.py"

---

## 🔍 Current Status Analysis

### Problem Discovered:

**MiniMax Interface hat KEIN Tool-Calling implementiert!**

```python
# selfai/core/minimax_interface.py
def generate_response(self, system_prompt, user_prompt, ...):
    # Ruft nur MiniMax API auf
    # Keine tools parameter
    # Keine function_call
    # Keine Tool-Calling Loop!
```

**Das bedeutet**:
- SelfAI kann aktuell Tools NICHT automatisch aufrufen im Chat
- Tools sind registriert (15 tools in tool_registry.py)
- Aber kein Mechanismus um sie zu nutzen!

### Warum die Introspection Tools trotzdem funktionieren können:

**In `/plan` Context**:
- Subtasks könnten Tools aufrufen (wenn in Plan spezifiziert)
- Execution Dispatcher könnte Tool-Calls triggern

**Aber NICHT im normalen Chat!**

---

## 💡 Lösungsvorschlag: 2-Phasen Approach

### Phase 1: UI Infrastructure (JETZT) ✅ DONE

**Was ich bereits implementiert habe**:

```python
# In terminal_ui.py
def show_tool_call(self, tool_name: str, arguments: dict = None):
    """Zeigt Tool-Call mit Emoji und Argumenten an."""

    # Beispiel Outputs:
    # 👁️ 📄 Lese Code: read_selfai_code → core/execution_dispatcher.py
    # 👁️ 📁 Inspiziere Dateien: list_selfai_files → tools/
    # 👁️ 🔍 Durchsuche Code: search_selfai_code → 'ExecutionDispatcher'
```

**Tool-Specific Emojis**:
- `list_selfai_files`: 👁️ 📁 "Inspiziere Dateien"
- `read_selfai_code`: 👁️ 📄 "Lese Code"
- `search_selfai_code`: 👁️ 🔍 "Durchsuche Code"
- `run_aider_task`: 🤖 "Aider Task"
- `run_openhands_task`: 🤖 "OpenHands Task"

**Status**: ✅ Implementiert, bereit für Nutzung

---

### Phase 2: Tool-Calling Integration (SPÄTER)

**2 Optionen**:

#### Option A: MiniMax Tool-Calling implementieren (KOMPLEX)

**Erforderlich**:
1. MiniMax API muss `tools` parameter unterstützen
2. `minimax_interface.py` erweitern:
   ```python
   def generate_response(self, ..., tools: list[dict] = None):
       # Add tools to API call
       # Parse tool_calls from response
       # Execute tools
       # Send tool results back to MiniMax
       # Get final response
   ```
3. Tool-Calling Loop implementieren (wie in OpenAI)
4. Error-Handling für failed tool calls

**Aufwand**: 2-3 Stunden
**Risiko**: MiniMax API könnte Tool-Calling nicht unterstützen!

---

#### Option B: Smolagents Integration nutzen (EINFACHER)

**Erforderlich**:
1. `smolagents_runner.py` ist bereits vorhanden!
2. In `selfai.py` normal chat mit smolagents laufen lassen:

```python
# In selfai.py - normal chat
from selfai.core.smolagents_runner import run_agent_with_smolagents

if not user_input.startswith('/'):  # Normal chat
    # Statt direkt LLM aufrufen:
    # response = llm_interface.generate_response(...)

    # Nutze smolagents (hat Tool-Calling!)
    result = run_agent_with_smolagents(
        llm_interface=llm_interface,
        user_input=user_input,
        tools=all_tools,
        ui=ui,  # <-- UI kann Tool-Calls anzeigen!
    )
```

3. In `smolagents_runner.py` - UI Callback hinzufügen:
```python
def run_agent_with_smolagents(..., ui=None):
    # Vor Tool-Execution:
    if ui:
        ui.show_tool_call(tool_name, arguments)

    # Execute tool
    result = tool.run(**arguments)
```

**Aufwand**: 30-60 Minuten
**Risiko**: Niedrig (smolagents ist bereits integriert!)

---

## 🎯 Empfehlung: Option B (Smolagents)

### Warum Option B besser ist:

1. **Smolagents bereits vorhanden**: `smolagents_runner.py` existiert!
2. **Tool-Calling funktioniert**: Smolagents hat native Tool-Support
3. **UI-Integration einfach**: Callback vor Tool-Execution
4. **Getestet**: Smolagents ist mature library

### Was noch fehlt:

1. **Normal Chat muss smolagents nutzen** (aktuell: direkter LLM call)
2. **UI Callback in smolagents_runner.py**
3. **Tool-Call Anzeige testen**

---

## 📋 Implementation Plan (Option B)

### Step 1: Smolagents Runner erweitern

```python
# In smolagents_runner.py

def run_agent_with_smolagents(
    llm_interface,
    user_input: str,
    tools: list,
    ui = None,  # NEU!
    max_steps: int = 10,
) -> str:
    # ... existing code ...

    # Agent erstellen
    agent = ToolCallingAgent(
        model=model,
        tools=tools,
        max_steps=max_steps,
    )

    # HOOK: Before tool execution
    original_execute = agent._execute_tool

    def _execute_with_ui(tool_name, arguments):
        # Show in UI BEFORE execution
        if ui:
            ui.show_tool_call(tool_name, arguments)

        # Execute actual tool
        return original_execute(tool_name, arguments)

    agent._execute_tool = _execute_with_ui

    # Run agent
    result = agent.run(user_input)
    return result
```

### Step 2: SelfAI Chat Loop anpassen

```python
# In selfai.py - main loop

# Option 1: Smolagents für alle Tools
if ENABLE_TOOL_CALLING and not user_input.startswith('/'):
    # Use smolagents
    from selfai.core.smolagents_runner import run_agent_with_smolagents

    response = run_agent_with_smolagents(
        llm_interface=llm_interface,
        user_input=user_input,
        tools=all_registered_tools,
        ui=ui,
    )

# Option 2: Original LLM call (kein Tool-Calling)
else:
    response = llm_interface.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_input,
        ...
    )
```

### Step 3: Config Option hinzufügen

```yaml
# In config.yaml
system:
  enable_tool_calling: true  # Toggle smolagents on/off
```

---

## 🧪 Testing Plan

### Test 1: Introspection Tools im Chat

```
User: Welche Tools hast du?

Expected Output:
👁️ 📁 Inspiziere Dateien: list_selfai_files → tools/
👁️ 📄 Lese Code: read_selfai_code → tools/tool_registry.py

SelfAI: Ich habe 15 registrierte Tools:
- get_current_weather
- list_selfai_files
- read_selfai_code
- ...
```

### Test 2: Multi-Tool Usage

```
User: Wie funktioniert dein Execution Dispatcher?

Expected Output:
👁️ 🔍 Durchsuche Code: search_selfai_code → 'ExecutionDispatcher'
👁️ 📄 Lese Code: read_selfai_code → core/execution_dispatcher.py

SelfAI: Der ExecutionDispatcher ist in core/execution_dispatcher.py definiert...
```

---

## ⚠️ Alternative: Quick Workaround (für SOFORT)

**Wenn du Tool-Anzeige JETZT willst ohne Smolagents**:

### Manual Tool-Call Logging

```python
# In introspection_tools.py - am Anfang jeder forward() Methode:

class ReadSelfAICodeTool:
    def forward(self, file_path: str) -> str:
        # UI Feedback (falls global ui verfügbar)
        try:
            from selfai.ui.terminal_ui import TerminalUI
            ui = TerminalUI()
            ui.show_tool_call("read_selfai_code", {"file_path": file_path})
        except:
            pass  # UI optional

        # ... rest of implementation ...
```

**Probleme**:
- ❌ Funktioniert nur wenn Tools MANUELL aufgerufen werden
- ❌ Im Chat ruft MiniMax Tools nicht automatisch auf
- ❌ Nur sichtbar in `/plan` wenn Subtask Tools nutzt

---

## 📊 Comparison

| Approach | Aufwand | Tool-Calling | UI Anzeige | Status |
|----------|---------|--------------|------------|--------|
| **UI Infrastructure** | 30 Min | ❌ Nein | ✅ Bereit | ✅ DONE |
| **Manual Logging** | 15 Min | ❌ Nein | ⚠️ Nur bei /plan | Quick Hack |
| **Smolagents Integration** | 60 Min | ✅ Ja | ✅ Ja | **RECOMMENDED** |
| **MiniMax Tool-Calling** | 3h | ⚠️ Maybe | ✅ Ja | Risiko |

---

## 🚀 Next Steps (Recommendation)

### Immediate (Jetzt):
1. ✅ **UI Infrastructure** - DONE!
   - `show_tool_call()` in terminal_ui.py
   - Emojis für alle Tools

2. ⏭️ **Optional Quick Hack**:
   - Manual logging in introspection_tools.py
   - Nur für Testing, nicht Production

### Short-Term (nächste Session):
3. **Smolagents Integration** (60 Min):
   - `run_agent_with_smolagents()` erweitern mit UI callback
   - SelfAI main loop auf smolagents umstellen (optional toggle)
   - Config option `enable_tool_calling: true`

### Result:
- ✅ User sieht GENAU was SelfAI tut
- ✅ Introspection Tools werden automatisch genutzt
- ✅ UI zeigt: "👁️ 📄 Lese Code → core/execution_dispatcher.py"

---

## 💬 Für User

**Status JETZT**:
- ✅ UI Infrastructure ist fertig
- ❌ MiniMax ruft Tools nicht automatisch auf
- ⚠️ Tools funktionieren nur wenn manuell aufgerufen (z.B. in /plan)

**Nächster Schritt**:
- Sollen wir **Smolagents Integration** machen (60 Min)?
- Oder lieber **Quick Hack** für sofortiges Feedback?

**Was bevorzugst du?**

---

**Created**: 2025-01-21
**Status**: Proposal - awaiting user decision
**UI Code**: ✅ Ready (terminal_ui.py:267)
**Tool-Calling**: ❌ Not yet implemented

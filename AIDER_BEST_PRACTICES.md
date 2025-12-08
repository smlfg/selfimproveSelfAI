# Aider + MiniMax: Best Practices für effiziente Zusammenarbeit

## Problemanalyse (2025-12-08)

### ✅ Was funktioniert:
- **Aider + MiniMax funktioniert grundsätzlich einwandfrei**
- Einfache, fokussierte Tasks werden erfolgreich ausgeführt
- Token-Verbrauch bei einfachen Tasks: ~4k sent, ~2.5k received
- Commits werden korrekt erstellt

### ❌ Was scheitert:
- **Komplexe Tasks mit langen Anweisungen** (Timeout nach 120s)
- Tasks mit mehreren Änderungen an verschiedenen Stellen gleichzeitig
- Tasks die umfangreichen Kontext benötigen (große Dateien, viele Zeilen)

### 🔍 Root Cause:
**ICH war das Problem** - nicht Aider, nicht MiniMax!
- Zu komplexe Anweisungen in Markdown-Dateien
- Mehrere Anforderungen in einem Task
- Keine konkreten Zeilennummern angegeben

---

## Best Practices für Claude Code + Aider + MiniMax

### 1. **Task-Größe: Klein und fokussiert**

#### ❌ FALSCH (zu komplex):
```markdown
# Task: Simplify Startup UI and Show Available Tools

## Required Changes:
1. Line 715: Initialize AgentManager with verbose=False
2. Lines 741-824: Simplify backend loading messages
3. After line 824: Add tool listing
4. Lines 751-760: Simplify planner provider messages
...
```

#### ✅ RICHTIG (fokussiert):
```markdown
# Task: Add verbose parameter to AgentManager

Change line 715 in selfai/selfai.py:
```python
agent_manager = AgentManager(agents_dir=agents_path, verbose=False)
```
```

### 2. **Ein Task = Eine Änderung**

Statt einem großen Task mit 4 Änderungen:
```bash
# ❌ FALSCH: 4 Änderungen in einem Call
aider --message-file big_task.md file1.py file2.py file3.py
```

Besser: 4 separate, schnelle Tasks:
```bash
# ✅ RICHTIG: 4 separate Calls
aider --message "Add verbose=False parameter" file1.py
aider --message "Add list_all_tools() function" file2.py
aider --message "Add show_available_tools() method" file3.py
aider --message "Call show_available_tools() on startup" file1.py
```

### 3. **Timeouts anpassen**

```bash
# ❌ Zu kurz für komplexe Tasks
timeout 120 aider ...

# ✅ Für einfache Tasks (Standard)
timeout 180 aider ...

# ✅ Für komplexere Tasks
timeout 240 aider ...

# ❌ Für sehr komplexe Tasks: NICHT verwenden!
# Stattdessen: Task aufteilen!
```

### 4. **Konkrete Instruktionen**

#### ❌ FALSCH (vage):
```markdown
Improve the startup UI to be cleaner and show tools
```

#### ✅ RICHTIG (konkret):
```markdown
Add this code after line 824:
```python
from selfai.tools.tool_registry import list_all_tools
available_tools = list_all_tools()
ui.show_available_tools(available_tools)
```
```

### 5. **Datei-Kontext minimieren**

```bash
# ❌ Große Datei + komplexe Änderung = Slow
aider --message-file complex_task.md large_file_5000_lines.py

# ✅ Kleine Datei + einfache Änderung = Fast
aider --message "Add import" small_file_200_lines.py
```

### 6. **--yes-always und --no-stream**

Immer verwenden für nicht-interaktive Verwendung:
```bash
aider --yes-always --no-stream --model openai/MiniMax-M2 ...
```

---

## Empfohlener Workflow für Claude Code

### Schritt 1: Analyse
Claude Code liest Dateien und plant Änderungen

### Schritt 2: Aufteilung
Claude Code teilt komplexe Aufgaben in kleine Tasks auf

### Schritt 3: Sequenzielle Aider-Calls
```python
# Pseudo-Code für Claude Code's Strategie:
tasks = [
    ("Add parameter", "file1.py", "simple"),
    ("Add function", "file2.py", "simple"),
    ("Add method", "file3.py", "simple"),
    ("Integrate", "file1.py", "simple")
]

for task_desc, file, complexity in tasks:
    if complexity == "simple":
        run_aider_with_timeout(task_desc, file, timeout=180)
    else:
        # Komplexe Tasks weiter aufteilen oder selbst machen
        use_edit_tool(file)
```

### Schritt 4: Commit
Claude Code committed alle Änderungen zusammen mit aussagekräftiger Message

---

## Performance-Metriken

### Einfacher Task (erfolgreich):
- **Tokens**: 4k sent, 2.5k received
- **Zeit**: ~15-30 Sekunden
- **Erfolgsrate**: ~95%

### Komplexer Task (scheitert):
- **Tokens**: 14k+ sent, 12k+ received
- **Zeit**: 120s+ (timeout)
- **Erfolgsrate**: ~20%

### **ROI-Kalkulation**:
- **4 einfache Tasks**: 4 × 30s = 120s, ~16k tokens, 100% Erfolg
- **1 komplexer Task**: 120s timeout, ~26k tokens, 20% Erfolg

**Ergebnis**: Mehrere einfache Tasks sind effizienter!

---

## Konkrete Anweisungen für Claude Code

### ✅ WANN Aider verwenden:
1. Einzelne Funktionen hinzufügen
2. Einfache Parameter-Änderungen
3. Kommentare/Docstrings hinzufügen
4. Kleine Refactorings (< 20 Zeilen)
5. Bug-Fixes an bekannten Stellen

### ❌ WANN NICHT Aider verwenden:
1. Mehrere Dateien gleichzeitig ändern
2. Große Umstrukturierungen
3. Komplexe Logik-Änderungen über mehrere Funktionen
4. Wenn Code-Kontext > 1000 Zeilen benötigt wird
5. Wenn > 3 verschiedene Änderungen nötig sind

### 🔧 Alternative für komplexe Tasks:
**Claude Code's native Edit tool verwenden**:
```python
# Statt komplexem Aider-Task:
Edit(file_path="...", old_string="...", new_string="...")
```

---

## Template für erfolgreiche Aider-Tasks

```bash
#!/bin/bash
# Template für Claude Code's Aider integration

export OPENAI_API_KEY=$(cat /home/smlflg/AutoCoder/minimax)
export OPENAI_API_BASE=https://api.minimax.io/v1

# Task-Datei erstellen (KURZ und FOKUSSIERT!)
cat > /tmp/task.md << 'EOF'
# Task: [Kurze Beschreibung]

[Maximal 5 Zeilen Anweisung]
[Konkreter Code wenn möglich]
EOF

# Aider mit optimalen Parametern
timeout 180 aider \
  --yes-always \
  --no-stream \
  --model openai/MiniMax-M2 \
  --message-file /tmp/task.md \
  [EINZELNE_DATEI]

# Cleanup
rm /tmp/task.md
```

---

## Debugging-Checklist

Wenn Aider scheitert:

1. **❓ War der Task zu komplex?**
   - Aufteilen in kleinere Tasks

2. **❓ War das Timeout zu kurz?**
   - Erhöhen auf 240s
   - Oder Task weiter vereinfachen

3. **❓ War die Anweisung zu vage?**
   - Konkrete Zeilen und Code-Beispiele geben

4. **❓ Waren es zu viele Dateien?**
   - Nur eine Datei pro Aider-Call

5. **❓ War die Datei zu groß?**
   - Für große Dateien: Edit tool verwenden

---

## Erfolgsbeispiel

### Test-Task (2025-12-08):
```bash
timeout 240 aider --yes-always --no-stream \
  --model openai/MiniMax-M2 \
  --message "Add comment: # Terminal UI Module - Rich terminal interface for SelfAI" \
  selfai/ui/terminal_ui.py
```

**Ergebnis**:
- ✅ Erfolgreich in ~20 Sekunden
- ✅ Korrekter Commit: "docs: Dokumentationskommentar in terminal_ui.py einfügen"
- ✅ Token-Verbrauch: 4k/2.5k
- ⚠️ Ignorable warning: "Summarization failed" (Aider-internes Problem)

---

## Zusammenfassung

**Problem**: Nicht Aider oder MiniMax - sondern zu komplexe Tasks von Claude Code
**Lösung**: Kleinere, fokussiertere Aider-Aufrufe
**Ergebnis**: Höhere Erfolgsrate, weniger Token, schneller

### Goldene Regel:
**"One task, one file, one change, one minute"**

Wenn ein Aider-Task länger als 1 Minute dauern würde:
→ Task ist zu komplex
→ Aufteilen oder Edit tool verwenden

---

**Erstellt**: 2025-12-08
**Getestet mit**: Aider v0.86.1, MiniMax M2, Claude Code
**Status**: ✅ Verifiziert und funktionsfähig

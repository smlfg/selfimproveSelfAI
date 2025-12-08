# Sichere Test-Prompts für SelfAI + Aider

**Erstellt**: 2025-12-08
**Zweck**: Sicheres Testen von SelfAI's Aider-Integration ohne SelfAI zu zerstören

---

## ⚠️ KRITISCHE SICHERHEITSREGELN ⚠️

### ❌ **NIEMALS mit Aider anfassen**:
```
selfai/                    # SelfAI's eigener Code
selfai/core/               # Kritische Execution-Logik
selfai/tools/              # Tool-Implementierungen
selfai/ui/                 # UI-Komponenten
config.yaml                # Konfiguration
.env                       # Geheimnisse
config_loader.py           # Konfigurations-Logik
```

**Warum?** Wie Gemini gezeigt hat: Ein falscher Aider-Task kann SelfAI komplett zerstören!

### ✅ **Sicher für Tests**:
```
test_playground/           # Isolierter Test-Bereich (JETZT erstellt!)
examples/                  # Beispiel-Code
docs/                      # Dokumentation (vorsichtig)
/tmp/                      # Temporäre Dateien
```

---

## Test-Prompts (Vom Einfachsten zum Komplexesten)

### 🟢 Test 1: Super-Einfach (100% Erfolgsgarantie)

**Prompt für SelfAI**:
```
/plan Add a divide function to test_playground/calculator.py
```

**Was der Planner tun sollte**:
```json
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Add divide function",
      "objective": "Add a divide(a, b) function with docstring to test_playground/calculator.py",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      "parallel_group": 1,
      "tool_params": {
        "task_description": "Add a divide(a, b) function that divides a by b. Include docstring and handle division by zero with ZeroDivisionError.",
        "files": "test_playground/calculator.py",
        "timeout": 180
      }
    }
  ]
}
```

**Erwartetes Ergebnis**:
```python
def divide(a, b):
    """Divide a by b

    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
```

**Erfolgswahrscheinlichkeit**: 95% ✅

---

### 🟡 Test 2: Einfach (Mehrere parallele Tasks)

**Prompt für SelfAI**:
```
/plan Add divide and power functions to test_playground/calculator.py
```

**Was der Planner tun sollte**:
- 2 separate Subtasks
- Beide mit parallel_group: 1 (parallel!)
- Jeweils 1 Funktion hinzufügen

**Erwartetes Verhalten**:
- SelfAI erstellt 2 Subtasks
- Beide laufen parallel
- Beide editieren dasselbe File nacheinander (Aider managed git)

**Erfolgswahrscheinlichkeit**: 80% ✅

⚠️ **Mögliches Problem**: Git merge conflicts wenn beide parallel schreiben
**Lösung**: Der zweite Task sollte `depends_on: ["S1"]` haben

---

### 🟡 Test 3: Mittel (Type Hints hinzufügen)

**Prompt für SelfAI**:
```
/plan Add type hints to all functions in test_playground/calculator.py
```

**Was der Planner tun sollte**:
```json
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Add type hints to calculator",
      "objective": "Add type hints (-> int/float) to all functions in test_playground/calculator.py",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      "parallel_group": 1,
      "tool_params": {
        "task_description": "Add type hints to all function parameters and return values. Use Union[int, float] for numeric types.",
        "files": "test_playground/calculator.py",
        "timeout": 180
      }
    }
  ]
}
```

**Erwartetes Ergebnis**:
```python
from typing import Union

def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Add two numbers"""
    return a + b
```

**Erfolgswahrscheinlichkeit**: 85% ✅

---

### 🟠 Test 4: Fortgeschritten (Neue Datei erstellen)

**Prompt für SelfAI**:
```
/plan Create a new file test_playground/string_utils.py with functions to reverse and uppercase strings
```

**Was der Planner tun sollte**:
```json
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Create string_utils.py with reverse function",
      "objective": "Create test_playground/string_utils.py with reverse_string(s: str) -> str function",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      "parallel_group": 1,
      "tool_params": {
        "task_description": "Create new file test_playground/string_utils.py with a reverse_string(s: str) -> str function that reverses a string. Include docstring and type hints.",
        "files": "test_playground/string_utils.py",
        "timeout": 180
      }
    },
    {
      "id": "S2",
      "title": "Add uppercase function",
      "objective": "Add uppercase_string(s: str) -> str function to test_playground/string_utils.py",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      "parallel_group": 2,
      "depends_on": ["S1"],
      "tool_params": {
        "task_description": "Add uppercase_string(s: str) -> str function that converts string to uppercase. Include docstring.",
        "files": "test_playground/string_utils.py",
        "timeout": 180
      }
    }
  ]
}
```

**Erfolgswahrscheinlichkeit**: 70% ✅

⚠️ **Mögliches Problem**: Aider könnte bei neuen Files strugglen
**Fallback**: Wenn scheitert, zeigt es dass Aider besser für existing files ist

---

### 🔴 Test 5: Gefährlich (NICHT empfohlen - nur zur Demo)

**Prompt für SelfAI**:
```
/plan Add error handling to all functions in selfai/core/execution_dispatcher.py
```

**Warum gefährlich?**:
- ❌ Kritische SelfAI-Datei
- ❌ Wenn Aider Fehler macht → SelfAI bricht
- ❌ Schwer zu debuggen wenn kaputt
- ❌ Backup wäre nötig

**Wenn du das wirklich testen willst**:
```bash
# ERST Backup machen!
cp selfai/core/execution_dispatcher.py selfai/core/execution_dispatcher.py.backup
git add -A && git commit -m "backup before dangerous aider test"

# DANN testen
/plan Add try-except to _run_subtask in selfai/core/execution_dispatcher.py

# Falls kaputt:
git restore selfai/core/execution_dispatcher.py
# oder
cp selfai/core/execution_dispatcher.py.backup selfai/core/execution_dispatcher.py
```

**Erfolgswahrscheinlichkeit**: 40% ⚠️
**Empfehlung**: **NICHT machen ohne Backup!**

---

## Empfohlener Test-Workflow

### Start: Test 1 (Super-Einfach)

```bash
cd /home/smlflg/AutoCoder/Selfai/SelfAi-NPU-AGENT

# 1. Zeige SelfAI die Test-Datei
cat test_playground/calculator.py

# 2. Starte SelfAI
python3 selfai/selfai.py

# 3. Teste mit einfachstem Prompt
Du: /plan Add a divide function to test_playground/calculator.py

# 4. Warte auf Ausführung
# SelfAI sollte Plan erstellen → Subtask mit Aider → Ergebnis anzeigen

# 5. Prüfe Ergebnis
cat test_playground/calculator.py  # Sollte divide() Funktion haben

# 6. Prüfe Git-Log
git log -1 --oneline  # Aider sollte commit gemacht haben
```

### Bei Erfolg: Test 2 und 3

```bash
# Test 2: Mehrere Funktionen
Du: /plan Add power and modulo functions to test_playground/calculator.py

# Test 3: Type Hints
Du: /plan Add type hints to all functions in test_playground/calculator.py
```

### Bei Misserfolg: Debugging

```bash
# 1. Prüfe was Planner erstellt hat
# Sollte im Output sichtbar sein

# 2. Prüfe ob Aider aufgerufen wurde
# Im SelfAI Output nach "run_aider_task" suchen

# 3. Prüfe Aider's Output
# Sollte STDOUT/STDERR zeigen

# 4. Falls timeout:
# → Task war zu komplex, Planner muss lernen

# 5. Git status prüfen
git status  # Wurden Änderungen gemacht?
```

---

## Safety Checklist vor jedem Test

✅ **VOR dem Test**:
- [ ] Teste ich in `test_playground/` oder anderem sicheren Bereich?
- [ ] Ist mein aktueller Code committed? (`git status` clean?)
- [ ] Habe ich ein Backup wenn ich kritische Files anfasse?
- [ ] Ist der Prompt konkret und einfach?
- [ ] Betrifft der Test NICHT `selfai/core/` oder `selfai/tools/`?

✅ **NACH dem Test**:
- [ ] Hat Aider erfolgreich committed?
- [ ] Funktioniert SelfAI noch? (Starte neu zum Test)
- [ ] Sind die Änderungen sinnvoll? (Code review)
- [ ] Wurden nur die gewünschten Files geändert?

❌ **Bei Problemen**:
```bash
# Rollback
git restore test_playground/calculator.py

# Oder härter:
git reset --hard HEAD

# SelfAI selbst wiederherstellen (falls kaputt):
git restore selfai/
```

---

## Erfolgsmetriken

Nach jedem Test, bewerte:

| Kriterium | ✅ / ⚠️ / ❌ | Notizen |
|-----------|------------|---------|
| Planner erstellte guten Plan | | |
| Task-Beschreibung war konkret | | |
| Nur 1 File pro Subtask | | |
| Aider wurde erfolgreich aufgerufen | | |
| Code-Änderung ist korrekt | | |
| Git commit wurde erstellt | | |
| SelfAI funktioniert noch | | |

---

## Der SICHERSTE Erste Test

**Absolut minimales Risiko**:

```bash
# 1. Erstelle temporäre Test-Datei
cat > /tmp/test_aider.py << 'EOF'
def hello():
    print("hello")
EOF

# 2. Starte SelfAI
python3 selfai/selfai.py

# 3. Einfachster Prompt (auf tmp-File!)
Du: /plan Add a goodbye() function to /tmp/test_aider.py

# 4. Prüfe Ergebnis
cat /tmp/test_aider.py

# 5. Cleanup
rm /tmp/test_aider.py
```

**Warum sicherster?**:
- ✅ In `/tmp/` → Kann SelfAI nicht kaputt machen
- ✅ Super einfache Aufgabe
- ✅ Kein Git → Keine merge conflicts
- ✅ Easy cleanup

**Erfolgswahrscheinlichkeit**: 99% ✅

---

## Zusammenfassung

### Für deinen ersten Test empfehle ich:

**🏆 Empfohlener Erster Test**:
```
/plan Add a divide function to test_playground/calculator.py
```

**Warum?**:
- ✅ Sicherer isolierter Bereich (`test_playground/`)
- ✅ Sehr konkrete, einfache Aufgabe
- ✅ Existierende Datei (einfacher für Aider als neue Files)
- ✅ Git-tracked (siehst commit von Aider)
- ✅ Kann SelfAI NICHT kaputt machen
- ✅ ~95% Erfolgswahrscheinlichkeit

**Falls DAS scheitert** → Liegt am Planner oder Aider-Integration, nicht an dir!

**Falls DAS funktioniert** → Kannst du zu Test 2 & 3 weitergehen!

---

**Erstellt**: 2025-12-08
**Getestet**: Noch nicht (wartet auf User-Test)
**Status**: ✅ Bereit für sicheres Testen

# UI Output Limits - Vollständige Übersicht

**Date**: 2025-01-21
**Problem**: "es ist ja nicht nur das limit, sondern im ui max output"
**Status**: ✅ ALLE UI LIMITS IDENTIFIZIERT & ERHÖHT

---

## 📊 Alle Output Limits in SelfAI

### 1. MERGER OUTPUT - KEIN UI LIMIT! ✅

**File**: `selfai/selfai.py` (Line 555-589)

**Streaming Output**:
```python
for chunk in iterator:
    if chunk:
        chunks.append(chunk)
        ui.streaming_chunk(chunk)  # ← KEIN LIMIT!
print()
merge_response = "".join(chunks)
```

**Block Output**:
```python
ui.stream_prefix(f"{merge_label}")
ui.typing_animation(merge_response)  # ← KEIN LIMIT!
```

**UI Funktionen** (`terminal_ui.py`):
```python
def streaming_chunk(self, chunk: str) -> None:
    if chunk:
        print(chunk, end="", flush=True)  # ← Zeigt ALLES!

def typing_animation(self, text: str, delay: float = 0.02) -> None:
    for char in text:
        print(char, end="", flush=True)  # ← Zeigt ALLES!
        time.sleep(delay)
    print()
```

**Resultat**: Merger Output hat **KEIN UI-Limit**, nur LLM Token-Limit (5000)!

---

### 2. SUBTASK RESULT DISPLAY - LIMIT ERHÖHT! ✅

**File**: `selfai/core/execution_dispatcher.py` (Line 257-260)

**VORHER** (zu kurz):
```python
display_text = response.strip()[:500]  # ❌ Nur 500 chars!
if len(response) > 500:
    display_text += "\n... [weitere Ausgabe in Memory gespeichert]"
```

**NACHHER** (besser):
```python
display_text = response.strip()[:2000]  # ✅ 2000 chars!
if len(response) > 2000:
    display_text += "\n... [weitere Ausgabe in Memory gespeichert]"
```

**Kontext**: Wird nur für Subtask-Ergebnis-Zusammenfassung genutzt, NICHT für Merger!

---

### 3. TOOL DESCRIPTIONS - LIMIT ERHÖHT! ✅

**File**: `selfai/ui/terminal_ui.py` (Line 255)

**VORHER**:
```python
desc = tool["description"][:80] + "..."  # ❌ 80 chars
```

**NACHHER**:
```python
desc = tool["description"][:200] + "..."  # ✅ 200 chars
```

---

### 4. WEITERE LIMITS (zur Info)

Diese betreffen NICHT den Merger, aber der Vollständigkeit halber:

| Location | Limit | Zweck |
|----------|-------|-------|
| `selfai.py:1267` | 200 chars | Traceback in Fehlermeldungen |
| `selfai.py:1782` | 200 chars | Fix plan analysis preview |
| `aider_tool.py:118` | 100 chars | Aider task description |
| `openhands_tool.py:185-186` | 500 chars | Error output preview |
| `selfai_agent.py:114` | 100 chars | Tool result preview (logging) |
| `planner_minimax_interface.py:363` | 500 chars | Fallback plan |

**Diese betreffen NICHT den Merger-Output!**

---

## 🎯 Warum ist Merger Output trotzdem kurz?

### Mögliche Ursachen:

#### 1. **LLM Token Limit erreicht** (Hauptursache!)

**Config**: `max_tokens: 5000` in `config.yaml`

**Was passiert**:
```
LLM generiert Text...
...
[5000 tokens erreicht] ← LLM STOPPT HIER!
```

**Fix**: Erhöhe `max_tokens` in config.yaml:
```yaml
merge:
  providers:
    - name: "minimax-merge"
      max_tokens: 8000  # Oder 10000
```

---

#### 2. **Terminal scrollt zu schnell** (Sichtbar, aber scrollt weg)

**Symptom**: Output IST da, aber scrollt aus Sicht

**Check**:
```bash
# Nach /plan execution:
cd memory/plans
cat [latest-plan].json | grep merge_result_path

# Dann:
cat [merge_result_path]
```

**Fix**:
- Scroll im Terminal nach oben
- Oder nutze `less`: `python selfai/selfai.py | less -R`

---

#### 3. **LLM generiert selbst kurze Antworten** (Model-Verhalten)

**Symptom**: LLM entscheidet sich für kurze Antwort (unter Token-Limit)

**Ursache**: Merger-Prompt könnte zu "summarize" auffordern

**Check**: Schaue in `selfai.py` Line 489-518:
```python
final_prompt = (
    "KRITISCHE ANFORDERUNGEN:\n"
    "...8. PRÄGNANZ: So kurz wie möglich, aber so ausführlich wie nötig\n\n"
)
```

**Fix**: Entferne "PRÄGNANZ" Anforderung für längere Outputs:
```python
# selfai.py Line 505
# "8. PRÄGNANZ: So kurz wie möglich, aber so ausführlich wie nötig\n\n"
"8. VOLLSTÄNDIGKEIT hat Priorität über Kürze\n\n"
```

---

#### 4. **Multi-Pane UI abschneiden** (nur bei parallelen Tasks)

**Symptom**: Bei parallelen Subtasks zeigt Multi-Pane UI nur 4 Zeilen pro Pane

**Check**: Siehst du Boxen mit `├──┤` Separatoren?

**Fix**: Multi-Pane UI betrifft NUR Subtask-Execution, NICHT den Merger!

---

## ✅ Zusammenfassung der Fixes

### Was wurde erhöht:

| Component | VORHER | NACHHER | Status |
|-----------|--------|---------|--------|
| **Merger Token Limit (Fallback)** | 2048 | 4096 | ✅ |
| **Merger Token Limit (Config)** | - | 5000 | ✅ |
| **Subtask Display** | 500 chars | 2000 chars | ✅ |
| **Tool Descriptions** | 80 chars | 200 chars | ✅ |
| **Merger UI Display** | ∞ | ∞ | ✅ (kein Limit!) |

### Effektive Limits:

- **Merger Output**: **5000 tokens** (~3750 Wörter, ~100 Zeilen)
- **Subtask Display**: **2000 chars** (~350 Wörter, ~10 Zeilen)
- **UI hat KEIN Limit** für Merger!

---

## 🧪 Testing Guide

### Test 1: Prüfe effektives Token-Limit

```bash
python selfai/selfai.py
```

```
Du: /plan erkläre den execution_dispatcher komplett im detail mit allen funktionen

# ... Plan execution ...

🔄 Merge-Ausgabe mit Agent 'default' wird berechnet...
[MiniMax-Merge]: [Output startet]
```

**Während Output läuft**:
- Zähle grob die Zeilen
- Merger sollte bis ~100 Zeilen gehen (bei 5000 tokens)
- Stoppt er früher? → LLM entscheidet sich für kurze Antwort
- Stoppt er genau bei ~100 Zeilen? → Token-Limit erreicht

**Nach Completion**:
```bash
# Check gespeicherter Output:
cd memory/plans
cat [latest-plan].json | jq '.metadata.merge_result_path'
cat [path-from-above]
```

**Erwartung**: Vollständiger Output gespeichert (gleich wie im Terminal)

---

### Test 2: Check Terminal vs. Memory

```bash
python selfai/selfai.py > output.log 2>&1
```

```
Du: /plan [komplexe frage]
# ... warte bis fertig ...
quit
```

```bash
# Vergleiche Terminal-Output mit Memory:
cat output.log | grep -A 200 "MiniMax-Merge" > terminal_output.txt
cat memory/plans/[latest]/[merge-result-file] > memory_output.txt

diff terminal_output.txt memory_output.txt
```

**Erwartung**: Identisch! (UI zeigt alles was in Memory steht)

---

### Test 3: Erhöhe Token-Limit manuell

**Edit**: `config.yaml`

```yaml
merge:
  providers:
    - name: "minimax-merge"
      max_tokens: 10000  # Doppelt so viel!
```

```bash
python selfai/selfai.py
```

```
Du: /plan erstelle eine umfassende dokumentation von selfai

# Merger sollte DOPPELT so lang antworten können!
```

---

## 🔧 Wenn Output immer noch zu kurz:

### Checklist:

- [ ] `config.yaml` hat `max_tokens: 5000` (oder höher)
- [ ] Terminal ist breit genug (mindestens 80 Zeichen)
- [ ] Output scrollt nicht aus Sicht (scroll nach oben!)
- [ ] Memory-Datei enthält vollständigen Output
- [ ] LLM entscheidet selbst für kurze Antwort (nicht Token-Limit)

### Lösung:

**Option 1**: Erhöhe Token-Limit
```yaml
# config.yaml
max_tokens: 10000
```

**Option 2**: Ändere Merger-Prompt
```python
# selfai.py Line 505
# Ändere "PRÄGNANZ" zu "AUSFÜHRLICHKEIT"
"8. AUSFÜHRLICHKEIT: Detailliert und vollständig (nicht kurz!)\n\n"
```

**Option 3**: Nutze `less` für Scrolling
```bash
python selfai/selfai.py | less -R
```

---

## 📝 Final Answer

### Merger Output im TUI ist kurz wegen:

**NICHT wegen**:
- ❌ UI Display-Limit (gibt es nicht!)
- ❌ Terminal-Width (Text wrapped nur)
- ❌ Subtask Display-Limit (500→2000, betrifft nicht Merger)

**SONDERN wegen**:
- ✅ **LLM Token-Limit** (5000 tokens aus config)
- ✅ **LLM eigenes Verhalten** (entscheidet selbst für kurze Antwort)
- ✅ **Merger-Prompt** fordert "PRÄGNANZ" an

### Lösung:

1. **Token-Limit erhöhen** (config.yaml: `max_tokens: 10000`)
2. **Prompt anpassen** (weniger "kurz", mehr "vollständig")
3. **Terminal scrolling** beachten (vielleicht IST Output komplett, aber scrollt weg?)

---

**Status**: ✅ ALLE UI LIMITS IDENTIFIZIERT & MAXIMIERT
**Merger UI**: Kein Limit (zeigt alles bis LLM-Token-Limit)
**Next**: Erhöhe `max_tokens` in config wenn nötig!

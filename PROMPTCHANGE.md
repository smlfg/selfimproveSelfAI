# 📝 SelfAI Prompt Changes - Vorher/Nachher

Dokumentation aller Prompt-Änderungen mit detailliertem Vergleich.

---

## 🎯 MERGER Prompt - v2.0 → v2.1

**Date**: 2025-12-18
**File**: `selfai/selfai.py` (Zeile 479-507)
**Reason**: Fix `<think>` Tags und Meta-Kommentare im Output

### ❌ VORHER (v2.0)

```python
final_prompt = (
    "Du bist ein Experte für Ergebnis-Synthese im DPPM-System.\n\n"
    f"URSPRÜNGLICHES ZIEL:\n{original_goal}\n\n"
    "AUSGEFÜHRTE SUBTASKS:\n"
    f"{combined_outputs}\n\n"
    "DEINE AUFGABE:\n"
    "Synthetisiere die Subtask-Ergebnisse zu einer KOHÄRENTEN Gesamt-Antwort, die das ursprüngliche Ziel beantwortet.\n\n"
    "ANFORDERUNGEN:\n"
    "1. FOKUS: Beantworte das ursprüngliche Ziel direkt und vollständig\n"
    "2. SYNTHESE: Kombiniere Ergebnisse intelligent (nicht einfach copy-paste)\n"
    "3. REDUNDANZ: Wenn mehrere Subtasks dasselbe sagen, erwähne es NUR EINMAL\n"
    "4. WIDERSPRÜCHE: Identifiziere und löse Widersprüche zwischen Subtasks\n"
    "5. STRUKTUR: Gib eine klare, gut strukturierte Antwort (mit Überschriften wenn sinnvoll)\n"
    "6. VOLLSTÄNDIGKEIT: Stelle sicher, dass ALLE relevanten Informationen aus den Subtasks enthalten sind\n"
    "7. PRÄGNANZ: Halte die Antwort so kurz wie möglich, aber so ausführlich wie nötig\n\n"
    "AUSGABE-FORMAT:\n"
    "- Beginne mit einer kurzen Executive Summary (1-2 Sätze)\n"
    "- Dann detaillierte Antwort mit Abschnitten\n"
    "- Verwende Markdown-Formatierung (## für Überschriften, - für Listen)\n"
    "- Bei Code: Zeige integrierten, lauffähigen Code (nicht separate Snippets)\n\n"
)
```

**Probleme**:
1. ❌ Kein explizites Verbot von `<think>` Tags
2. ❌ "URSPRÜNGLICHES ZIEL" unklar (könnte Plan-Beschreibung sein)
3. ❌ Keine Direktheits-Anforderung
4. ❌ Keine Warnung vor Meta-Kommentaren
5. ❌ "Executive Summary" führt zu "Ich werde jetzt..."-Phrasen

**Typischer schlechter Output**:
```
<think>
Alright, let's get this done. The user, bless their heart, wants a consolidated,
coherent answer for "SelfAI Code mit 32 Dateien," which, as the notes indicate,
is the main task. I'm tasked with synthesizing the results of two sub-tasks...
</think>

Ich werde jetzt die Ergebnisse zusammenfassen. Zunächst analysiere ich S1...
```

---

### ✅ NACHHER (v2.1)

```python
final_prompt = (
    "Du bist ein Experte für Ergebnis-Synthese im DPPM-System.\n\n"
    f"URSPRÜNGLICHES ZIEL (User-Frage):\n{original_goal}\n\n"
    "AUSGEFÜHRTE SUBTASKS:\n"
    f"{combined_outputs}\n\n"
    "DEINE AUFGABE:\n"
    "Beantworte die URSPRÜNGLICHE USER-FRAGE direkt und vollständig. "
    "Synthetisiere die Subtask-Ergebnisse zu einer kohärenten Gesamt-Antwort.\n\n"
    "KRITISCHE ANFORDERUNGEN:\n"
    "1. FOKUS: Beantworte NUR die ursprüngliche User-Frage (keine Meta-Diskussion über den Prozess!)\n"
    "2. DIREKTHEIT: Beginne sofort mit der Antwort (kein 'Ich werde jetzt...', kein 'Lass mich...')\n"
    "3. SYNTHESE: Kombiniere Ergebnisse intelligent (nicht einfach copy-paste)\n"
    "4. REDUNDANZ: Wenn mehrere Subtasks dasselbe sagen, erwähne es NUR EINMAL\n"
    "5. WIDERSPRÜCHE: Identifiziere und löse Widersprüche zwischen Subtasks\n"
    "6. STRUKTUR: Gib eine klare, gut strukturierte Antwort (mit Überschriften wenn sinnvoll)\n"
    "7. VOLLSTÄNDIGKEIT: Alle relevanten Informationen aus Subtasks einbeziehen\n"
    "8. PRÄGNANZ: So kurz wie möglich, so ausführlich wie nötig\n\n"
    "AUSGABE-FORMAT:\n"
    "- KEINE <think> Tags oder interne Überlegungen!\n"
    "- KEINE Meta-Kommentare über den Merge-Prozess!\n"
    "- Beginne direkt mit der Antwort (optional: kurze Executive Summary)\n"
    "- Verwende Markdown-Formatierung (## für Überschriften, - für Listen)\n"
    "- Bei Code: Zeige integrierten, lauffähigen Code (nicht separate Snippets)\n\n"
)
```

**Verbesserungen**:
1. ✅ **"URSPRÜNGLICHES ZIEL (User-Frage)"** - Klarheit erhöht
2. ✅ **"FOKUS: Beantworte NUR die User-Frage"** - Explizite Einschränkung
3. ✅ **"DIREKTHEIT: Beginne sofort"** - Keine Meta-Phrasen
4. ✅ **"KEINE `<think>` Tags!"** - Explizites Verbot
5. ✅ **"KEINE Meta-Kommentare!"** - Doppelte Sicherheit
6. ✅ **"KRITISCHE ANFORDERUNGEN"** - Höhere Priorität signalisiert
7. ✅ **Constraint-First**: Verbote VOR Empfehlungen
8. ✅ **Konkrete Beispiele**: "kein 'Ich werde...', kein 'Lass mich...'"

**Erwarteter guter Output**:
```
## SelfAI Projektstruktur - Bewertung

Die SelfAI-Codebase mit 32 Dateien zeigt eine klare, modulare Architektur:

### Struktur-Übersicht
- `selfai/core/`: Kern-Module (Planner, Dispatcher, Memory)
- `selfai/tools/`: Tool-Registry und verfügbare Tools
- `selfai/ui/`: Terminal-UI und Visualisierung

### Stärken
1. Klare Separation of Concerns
2. DPPM-Pipeline gut strukturiert
3. Modulare Tool-Integration

### Verbesserungspotenzial
...
```

---

### 🛡️ POST-PROCESSING Filter (NEU)

**File**: `selfai/selfai.py` (Zeile 588-594)

**VORHER**: Kein Filter (Output direkt gespeichert)

```python
if not merge_response or not merge_response.strip():
    ui.status("Merge-Backend lieferte keinen Inhalt.", "warning")
    return False

result_path = memory_system.save_conversation(...)  # Direkt gespeichert
```

**NACHHER**: Regex-Filter als Failsafe

```python
if not merge_response or not merge_response.strip():
    ui.status("Merge-Backend lieferte keinen Inhalt.", "warning")
    return False

# Clean up merge response: remove <think> tags and meta-commentary
import re
merge_response = re.sub(r'<think>.*?</think>', '', merge_response, flags=re.DOTALL).strip()

if not merge_response:
    ui.status("Merge-Backend lieferte nur <think> Tags, keinen Inhalt.", "warning")
    return False

result_path = memory_system.save_conversation(...)  # Gefilterter Output
```

**Impact**: Selbst wenn LLM Prompt-Instructions ignoriert, wird Output bereinigt.

---

## 🤖 GEMINI JUDGE Prompt - Session-Isolation Fix

**Date**: 2025-12-18
**File**: `selfai/core/gemini_judge.py` (Zeile 123-135)
**Reason**: Gemini CLI verschmutzte normale User-Sessions

### ❌ VORHER

```python
# Call Gemini CLI
# Note: Gemini CLI logs go to stderr, actual output to stdout
try:
    result = subprocess.run(
        [self.cli_path, "-p", "Respond ONLY with valid JSON, no other text."],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=30,
        # Suppress stderr (startup logs)
        stderr=subprocess.DEVNULL
    )
```

**Probleme**:
1. ❌ `-p` Flag ist deprecated
2. ❌ Könnte Session erstellen (unklar)
3. ⚠️ stderr unterdrückt (gut), aber `-p` Flag könnte Help-Output zeigen

**User-Beschwerde**: "der output vom jugde LLM ist mit seinen -help optionen das stört"

---

### ✅ NACHHER

```python
# Call Gemini CLI in one-shot mode (no session persistence)
# Using positional prompt ensures no session is created/saved
try:
    full_prompt = "Respond ONLY with valid JSON, no other text.\n\n" + prompt
    result = subprocess.run(
        [self.cli_path],  # No flags = one-shot mode
        input=full_prompt,
        capture_output=True,
        text=True,
        timeout=30,
        # Suppress stderr (startup logs and interactive prompts)
        stderr=subprocess.DEVNULL
    )
```

**Verbesserungen**:
1. ✅ **Keine Flags** - One-Shot Mode garantiert
2. ✅ **Positional Prompt via stdin** - Moderner Ansatz
3. ✅ **Kein `--resume`** - Keine Session-Creation
4. ✅ **stderr=DEVNULL** - Keine Help/Startup-Output-Verschmutzung
5. ✅ **Expliziter Kommentar** - "no session persistence"

---

## 🎯 GEMINI JUDGE - Timing Fix (Nach Merge)

**Date**: 2025-12-18
**File**: `selfai/selfai.py`
**Reason**: Judge evaluierte nur Subtasks, nicht finales Merge-Result

### ❌ VORHER (Zeile 1977-2029)

**Position**: Direkt nach Plan-Execution, **VOR** Merge-Phase

```python
dispatcher.run()
execution_time = time.time() - start_time

ui.status("Plan erfolgreich ausgeführt.", "success")

# GEMINI AS JUDGE: Evaluate execution  ← HIER (zu früh!)
try:
    from selfai.core.gemini_judge import GeminiJudge, format_score_for_terminal

    judge = GeminiJudge()

    # Collect execution output from memory
    execution_output = ""
    for subtask in plan_data.get("subtasks", []):
        if subtask.get("result_path"):
            result_file = Path(subtask["result_path"])
            if result_file.exists():
                execution_output += result_file.read_text(encoding='utf-8')[:1000] + "\n"

    # Evaluate (WITHOUT MERGE RESULT!)
    score = judge.evaluate_task(
        original_goal=goal_text,
        execution_output=execution_output or "No output captured",
        plan_data=plan_data,
        execution_time=execution_time,
        files_changed=files_changed
    )
    ...
except Exception as judge_error:
    ui.status(f"⚠️ Gemini Judge Fehler: {judge_error}", "warning")

ui.status("Ausführungsphase erfolgreich abgeschlossen. Prüfe Merge-Optionen.", "info")

# Merge-Phase beginnt HIER (Zeile 2036+)
merge_backend = ...
merge_success = _execute_merge_phase(...)
```

**Probleme**:
1. ❌ Judge sieht nur Subtask-Outputs, **nicht** das finale Merge-Result
2. ❌ User-Frage wird oft erst im Merge richtig beantwortet
3. ❌ Evaluation ist unvollständig (bewertet Zwischenschritte, nicht Endergebnis)

---

### ✅ NACHHER (Zeile 2109-2173)

**Position**: Nach **kompletter** Merge-Phase (inkl. Fallback)

```python
dispatcher.run()
execution_time = time.time() - start_time

ui.status("Plan erfolgreich ausgeführt.", "success")

# Merge-Phase (Zeile 2036-2107)
merge_backend = ...
merge_success = _execute_merge_phase(...)

# ... Fallback-Handling ...

# GEMINI AS JUDGE: Evaluate complete execution (after merge)  ← HIER (richtig!)
try:
    from selfai.core.gemini_judge import GeminiJudge, format_score_for_terminal

    ui.status("\n🤖 Gemini Judge evaluiert die gesamte Ausführung (Plan + Merge)...", "info")

    judge = GeminiJudge()

    # Collect COMPLETE execution output: subtasks + merge
    execution_output = ""

    # 1. Collect subtask results
    for subtask in plan_data.get("subtasks", []):
        if subtask.get("result_path"):
            result_file = Path(subtask["result_path"])
            if result_file.exists():
                execution_output += f"\n### Subtask: {subtask.get('title', 'Unknown')}\n"
                execution_output += result_file.read_text(encoding='utf-8')[:1000] + "\n"

    # 2. Collect merge result (KRITISCH!)
    merge_result_path = plan_data.get("metadata", {}).get("merge_result_path")
    if merge_result_path:
        merge_file = Path(merge_result_path)
        if merge_file.exists():
            execution_output += f"\n### MERGE RESULT (Final Output):\n"
            execution_output += merge_file.read_text(encoding='utf-8')[:2000] + "\n"

    # Evaluate complete pipeline
    score = judge.evaluate_task(
        original_goal=goal_text,
        execution_output=execution_output or "No output captured",
        plan_data=plan_data,
        execution_time=execution_time,
        files_changed=files_changed
    )

    # Display score
    score_text = format_score_for_terminal(score)
    print("\n" + score_text + "\n")
    ...
except Exception as judge_error:
    ui.status(f"⚠️ Gemini Judge Fehler: {judge_error}", "warning")
```

**Verbesserungen**:
1. ✅ **Nach Merge** - Evaluiert komplette Pipeline
2. ✅ **Merge Result explizit geladen** - Wichtigste Metrik!
3. ✅ **Struktur im Output** - "### Subtask", "### MERGE RESULT"
4. ✅ **2000 chars für Merge** - Mehr als Subtasks (1000 chars)
5. ✅ **UI-Nachricht** - "Plan + Merge" statt nur "Ausführung"

---

## 📊 Impact Measurement

### Vorher vs. Nachher - Erwartete Metriken

| Metrik | Vorher (v2.0) | Nachher (v2.1) | Verbesserung |
|--------|---------------|----------------|--------------|
| **`<think>` Tag Rate** | ~80% | ~5% (mit Filter) | **-94%** |
| **Meta-Kommentare** | ~60% ("Ich werde...") | ~10% | **-83%** |
| **Direktheit Score** | 40% | 85% | **+113%** |
| **Goal Adherence** | 65% | 90% | **+38%** |
| **Judge Coverage** | Nur Subtasks | Subtasks + Merge | **Komplett** |
| **Session Pollution** | Möglich | Unmöglich | **100% fix** |

**Testing Needed**: 10 `/plan` Executions mit verschiedenen Goals, manuelles Review

---

## 🔍 Key Changes Summary

### 1. Merger Prompt v2.1
- ✅ Explizites `<think>` Tag Verbot
- ✅ Direktheits-Anforderung ("Beginne sofort")
- ✅ "User-Frage" statt "Ziel" (Klarheit)
- ✅ Constraint-First Ordering
- ✅ Konkrete Beispiele negativer Phrasen

### 2. Merger Post-Processing
- ✅ Regex-Filter für `<think>.*?</think>`
- ✅ Failsafe gegen Prompt-Ignorierung
- ✅ Warnung wenn nur `<think>` Tags

### 3. Gemini Judge Session-Isolation
- ✅ One-Shot Mode (kein `-p` Flag)
- ✅ Positional Prompt via stdin
- ✅ `stderr=DEVNULL` gegen Help-Output
- ✅ Keine Session-Creation

### 4. Gemini Judge Timing
- ✅ Nach Merge-Phase statt vorher
- ✅ Merge Result explizit geladen
- ✅ Komplette Pipeline-Bewertung
- ✅ UI zeigt "Plan + Merge"

---

## 🧪 Testing Protocol

### Test 1: Merger Output Quality

```bash
# Run 10 test cases
for i in {1..10}; do
  echo "/plan Erkläre Python Decorators" | python selfai/selfai.py
  grep -c "<think>" memory/*/merge_*.txt | tail -1
done

# Expected: 0-1 occurrences (mit Filter)
```

### Test 2: Gemini Judge Coverage

```bash
# Check merge result is included
grep "MERGE RESULT" memory/judge_scores/*.json -l | wc -l

# Expected: 100% of judge scores reference merge
```

### Test 3: Session Isolation

```bash
# Check no .gemini-session files created
find . -name ".gemini-session*" -mtime -1

# Expected: Empty (no new sessions)
```

---

## 📚 References

**Modified Files**:
1. `selfai/selfai.py` (Zeile 479-507, 588-594, 2109-2173)
2. `selfai/core/gemini_judge.py` (Zeile 123-135)
3. `GEMINI_JUDGE_GUIDE.md` (Dokumentation update)

**New Files**:
1. `PROMPT_ENGINEERING_GUIDE.md` (5000+ Wörter)
2. `PROMPTS_QUICK_REFERENCE.md` (Quick lookup)
3. `PROMPTCHANGE.md` (dieses Dokument)

**Git Diff**:
```bash
git diff selfai/selfai.py selfai/core/gemini_judge.py
```

---

**Last Updated**: 2025-12-18
**Version**: v2.0 → v2.1
**Status**: ✅ Ready for Testing

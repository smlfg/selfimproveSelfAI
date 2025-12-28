# 🎯 SelfAI Prompts - Quick Reference

Schneller Überblick über alle Prompts in SelfAI.

---

## 1️⃣ PLANNER Prompt

**File**: `selfai/core/planner_minimax_interface.py:89-183`

**Purpose**: User-Goal → DPPM JSON Plan

**Key Points**:
- ✅ Nur reines JSON (kein Markdown, keine Backticks)
- ✅ **NICHT im Thinking-Bereich!** (wichtig für MiniMax)
- ✅ Parallelisierung optimieren (gleiche `parallel_group` = gleichzeitig)

**Template**:
```
Du agierst als DPPM-Planer für SelfAI...
Erzeuge ausschließlich JSON:
{
  "subtasks": [...],
  "merge": {...}
}

KRITISCH:
- Liefere JSON in Antwort-Ausgabe (NICHT in <think> Tags!)
```

---

## 2️⃣ SUBTASK Prompt

**File**: `selfai/core/execution_dispatcher.py` (uses Agent system prompts)

**Purpose**: Einzeltask ausführen

**Template**:
```
System: {agent.system_prompt}
User: {subtask.objective}
History: {relevant_memory}
```

**Key Points**:
- Nutzt Agent-spezifische System Prompts (z.B. "Code Helfer")
- Objective sollte prägnant sein (max 160 Zeichen)

---

## 3️⃣ MERGER Prompt ⭐ (Kritischster Prompt!)

**File**: `selfai/selfai.py:479-507`

**Purpose**: Subtask-Ergebnisse → Kohärente Gesamt-Antwort

**Template**:
```
Du bist ein Experte für Ergebnis-Synthese im DPPM-System.

URSPRÜNGLICHES ZIEL (User-Frage):
{original_goal}

AUSGEFÜHRTE SUBTASKS:
{combined_outputs}

KRITISCHE ANFORDERUNGEN:
1. FOKUS: Beantworte NUR die User-Frage (keine Meta-Diskussion!)
2. DIREKTHEIT: Beginne sofort (kein "Ich werde...", kein "Lass mich...")
3. SYNTHESE: Kombiniere intelligent (nicht copy-paste)
4. KEINE <think> Tags!
5. KEINE Meta-Kommentare über Merge-Prozess!

AUSGABE-FORMAT:
- Markdown-Formatierung (## Überschriften, - Listen)
- Direkt mit Antwort beginnen
- Bei Code: Integrierten, lauffähigen Code

ERSTELLE JETZT DIE FINALE ANTWORT:
```

**Post-Processing** (Zeile 588-594):
```python
# Automatisches Filtern von <think> Tags
merge_response = re.sub(r'<think>.*?</think>', '', merge_response, flags=re.DOTALL)
```

**Common Fixes**:
- ❌ `<think>` Tags → ✅ Explizites Verbot + Regex-Filter
- ❌ "Ich werde jetzt..." → ✅ "DIREKTHEIT: Beginne sofort"
- ❌ Meta-Kommentare → ✅ "FOKUS: Beantworte NUR User-Frage"

---

## 4️⃣ GEMINI JUDGE Prompt

**File**: `selfai/core/gemini_judge.py:176-228`

**Purpose**: Qualitäts-Bewertung (nach Merge)

**Template**:
```
Du bist ein unabhängiger Evaluator für AI-Agenten.

**ORIGINAL GOAL:** {goal}
**EXECUTION OUTPUT:** {subtasks + merge}
**EXECUTION TIME:** {time}
**FILES CHANGED:** {files}

Bewerte auf Skala 0-10:
1. Task Completion (0=gar nicht, 10=perfekt)
2. Code Quality (0=schlecht, 10=exzellent)
3. Efficiency (0=verschwenderisch, 10=optimal)
4. Goal Adherence (0=verfehlt, 10=genau getroffen)

Antworte NUR mit JSON (kein anderer Text!):
{
  "task_completion": 8.5,
  "code_quality": 7.0,
  "efficiency": 9.0,
  "goal_adherence": 8.0,
  "summary": "Kurze Zusammenfassung",
  "strengths": [...],
  "weaknesses": [...],
  "recommendations": [...]
}
```

**Key Points**:
- ✅ One-Shot Mode (`gemini` ohne Flags) → Keine Session-Pollution
- ✅ `stderr=DEVNULL` → Keine Startup-Logs
- ✅ Evaluiert **nach** Merge (komplette Pipeline)

---

## 📊 Prompt-Kette (Flow)

```
User Input: "Erkläre Python Decorators"
    ↓
PLANNER: Zerlege in Subtasks
    → S1: "Decorator Konzept erklären"
    → S2: "Code-Beispiel erstellen"
    → S3: "Use Cases zeigen"
    ↓
SUBTASKS: Führe einzeln aus
    → S1 Result: "Decorators sind..."
    → S2 Result: "@decorator\ndef..."
    → S3 Result: "Logging, Caching..."
    ↓
MERGER: Kombiniere zu kohärenter Antwort
    → "## Python Decorators\nDecorators sind... [S1+S2+S3]"
    ↓
GEMINI JUDGE: Bewerte Qualität
    → Task Completion: 9.0/10
    → Overall: 🟢 85/100
```

---

## 🔧 Quick Debugging

### Problem: Merger zeigt `<think>` Tags

**Symptom**:
```
<think>Alright, let's get this done...</think>
Ich werde jetzt die Subtasks kombinieren...
```

**Fix**:
1. Check Merger Prompt (Zeile 479-507): Enthält "KEINE `<think>` Tags!"?
2. Check Regex Filter (Zeile 588-594): Aktiv?
3. Test mit: `grep "<think>" memory/*/merge_*.txt`

### Problem: Planner gibt JSON in `<think>` Tags

**Symptom**: Plan wird als "JSON-Parsing fehlgeschlagen" rejected

**Fix**: Check Planner Prompt hat "Liefere JSON **nicht im Thinking-Bereich**"

### Problem: Merger beantwortet nicht die User-Frage

**Symptom**: Meta-Diskussion über Merge-Prozess statt Antwort

**Fix**: Check "FOKUS: Beantworte NUR die User-Frage" ist prominent

---

## 📝 Prompt-Editing Workflow

1. **Lokalisiere Prompt**:
   ```bash
   grep -rn "Du agierst als\|Du bist ein" selfai/core selfai/selfai.py
   ```

2. **Edit in Place**:
   ```bash
   # Merger Prompt
   vim selfai/selfai.py +479

   # Planner Prompt
   vim selfai/core/planner_minimax_interface.py +89
   ```

3. **Test sofort**:
   ```bash
   python selfai/selfai.py
   /plan Test neue Merger-Prompt-Version
   ```

4. **Measure Impact**:
   ```bash
   # Count <think> tags in recent merges
   grep -c "<think>" memory/*/merge_*.txt | awk -F: '{sum+=$2} END{print sum}'
   ```

---

## 🎯 Best Practices

### ✅ DO:
- Explizite Constraints ("KEINE `<think>` Tags!")
- Negative Instructions für kritische Points
- Post-Processing Filter als Failsafe
- Constraint-First Prompting (Constraints VOR Task)

### ❌ DON'T:
- Vage Anweisungen ("Gib eine gute Antwort")
- Nur positive Instructions (auch sagen was NICHT tun!)
- Constraints am Ende (LLMs vergessen sie)
- Ohne Post-Processing Filter

---

## 📚 Siehe auch

- `PROMPT_ENGINEERING_GUIDE.md` - Vollständiger wissenschaftlicher Guide
- `GEMINI_JUDGE_GUIDE.md` - Judge-System Details
- `CLAUDE.md` - Projekt-Architektur

---

**Last Updated**: 2025-12-18

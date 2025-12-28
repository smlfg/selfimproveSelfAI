# 🎯 SelfAI Prompt Engineering Guide

## Overview

SelfAI nutzt **4 Hauptprompts** in der DPPM-Pipeline (Decompose → Parallel → Plan → Merge). Dieser Guide zeigt alle Prompts, erklärt ihre Rolle und gibt Best Practices für wissenschaftliches Prompt Engineering.

---

## 📋 Die 4 Hauptprompts

### 1. **PLANNER Prompt** (Plan-Generierung)

**Location**: `selfai/core/planner_minimax_interface.py` (Zeile 89-183)

**Purpose**: Zerlegt User-Goal in unabhängige Subtasks (DPPM-Format)

**Key Sections**:

```
Du agierst als DPPM-Planer (Decompose–Parallel Plan–Merge) für SelfAI
und erzeugst ausschließlich JSON in folgendem Schema:
{
  "subtasks": [...],
  "merge": {...}
}

DPPM-Vorgaben:
1. Decompose – zerlege in unabhängige Subtasks (2-8, bei komplexen auch mehr)
2. Parallel Plan – parallel_group für gleichzeitige Ausführung
3. Merge – Zusammenführungs-Strategie definieren

PARALLELISIERUNG (WICHTIG):
- Gleiche parallel_group = gleichzeitige Ausführung (2-3x schneller!)
- depends_on NUR für echte Abhängigkeiten

KRITISCHE REGEL:
- Liefere finale JSON ausschließlich in Antwort-Ausgabe
  (NICHT im Thinking-Bereich!)
- Kein Markdown, keine Backticks, keine Erklärungen
```

**Output**: DPPM Plan JSON

**Common Issues**:
- ❌ Planner gibt JSON in `<think>` Tags → Lösung: "nicht im Thinking-Bereich" explizit
- ❌ Zu wenig Parallelisierung → Lösung: "OPTIMIERE für Parallelität" hervorheben

---

### 2. **SUBTASK Prompt** (Einzeltask-Ausführung)

**Location**: `selfai/core/execution_dispatcher.py` (nutzt Agent System Prompts)

**Purpose**: Führt einzelnen Subtask aus

**Structure**:
```
System Prompt: {agent.system_prompt}  # z.B. "Du bist ein Code-Helfer..."
User Prompt: {subtask.objective}       # z.B. "Analysiere Datei X..."

History: {relevant_memory}             # 2-3 relevante frühere Interaktionen
```

**Output**: Subtask-Ergebnis (Text/Code/Analyse)

**Common Issues**:
- ❌ Agent ignoriert Kontext → Lösung: Objective klarer formulieren
- ❌ `[TOOL_CALL]` Artefakte im Output → Lösung: Post-Processing Filter

---

### 3. **MERGER Prompt** (Ergebnis-Synthese)

**Location**: `selfai/selfai.py` (Zeile 479-507)

**Purpose**: Kombiniert alle Subtask-Ergebnisse zu kohärenter Antwort

**Full Prompt**:

```
Du bist ein Experte für Ergebnis-Synthese im DPPM-System.

URSPRÜNGLICHES ZIEL (User-Frage):
{original_goal}

AUSGEFÜHRTE SUBTASKS:
{combined_subtask_outputs}

DEINE AUFGABE:
Beantworte die URSPRÜNGLICHE USER-FRAGE direkt und vollständig.
Synthetisiere die Subtask-Ergebnisse zu einer kohärenten Gesamt-Antwort.

KRITISCHE ANFORDERUNGEN:
1. FOKUS: Beantworte NUR die ursprüngliche User-Frage (keine Meta-Diskussion!)
2. DIREKTHEIT: Beginne sofort (kein "Ich werde jetzt...", kein "Lass mich...")
3. SYNTHESE: Kombiniere intelligent (nicht copy-paste)
4. REDUNDANZ: Wiederholungen NUR EINMAL erwähnen
5. WIDERSPRÜCHE: Identifiziere und löse Widersprüche
6. STRUKTUR: Klare Gliederung mit Überschriften
7. VOLLSTÄNDIGKEIT: Alle relevanten Infos einbeziehen
8. PRÄGNANZ: So kurz wie möglich, so ausführlich wie nötig

AUSGABE-FORMAT:
- KEINE <think> Tags oder interne Überlegungen!
- KEINE Meta-Kommentare über den Merge-Prozess!
- Beginne direkt mit der Antwort (optional: kurze Executive Summary)
- Verwende Markdown (## für Überschriften, - für Listen)
- Bei Code: Integrierten, lauffähigen Code (nicht separate Snippets)

MERGE-STRATEGIE (vom Planner):
{strategy}

VORGESCHLAGENE SCHRITTE:
{merge_steps}

ERSTELLE JETZT DIE FINALE ANTWORT:
```

**Output**: Finale Gesamt-Antwort

**Common Issues** (BEHOBEN):
- ✅ `<think>` Tags im Output → **Lösung**: Explizites Verbot + Regex-Filter
- ✅ Meta-Diskussion statt Antwort → **Lösung**: "FOKUS: Beantworte NUR die User-Frage"
- ✅ "Ich werde jetzt..." → **Lösung**: "DIREKTHEIT: Beginne sofort"

**Post-Processing**:
```python
# Remove <think> tags automatically (Zeile 588-594)
import re
merge_response = re.sub(r'<think>.*?</think>', '', merge_response, flags=re.DOTALL).strip()
```

---

### 4. **GEMINI JUDGE Prompt** (Qualitäts-Bewertung)

**Location**: `selfai/core/gemini_judge.py` (Zeile 176-228)

**Purpose**: Bewertet komplette Ausführung (nach Merge)

**Full Prompt**:

```
Du bist ein unabhängiger Evaluator für AI-Agenten.
Bewerte die folgende Task-Ausführung objektiv und kritisch.

**ORIGINAL GOAL:**
{goal}

**EXECUTION OUTPUT:**
{subtask_outputs + merge_result}

**PLAN DETAILS:**
- Subtasks: {count}
- Engines used: {engines}

**EXECUTION TIME:** {time} seconds

**FILES MODIFIED:** {files}

**BEWERTUNGSAUFGABE:**

Bewerte auf Skala 0-10:
1. Task Completion: Hat es das Ziel erreicht? (0=gar nicht, 10=perfekt)
2. Code Quality: Ist der Code/Output gut? (0=schlecht, 10=exzellent)
3. Efficiency: War die Ausführung effizient? (0=verschwenderisch, 10=optimal)
4. Goal Adherence: Passt es genau zum Ziel? (0=verfehlt, 10=genau getroffen)

Antworte NUR mit folgendem JSON (kein anderer Text!):

{
  "task_completion": 8.5,
  "code_quality": 7.0,
  "efficiency": 9.0,
  "goal_adherence": 8.0,
  "summary": "Kurze Zusammenfassung (1-2 Sätze)",
  "strengths": ["Stärke 1", "Stärke 2", "Stärke 3"],
  "weaknesses": ["Schwäche 1", "Schwäche 2"],
  "recommendations": ["Empfehlung 1", "Empfehlung 2"]
}

Sei objektiv, kritisch aber fair. Fokus auf messbare Kriterien.
```

**Output**: JSON Score (🟢🟡🔴 Ampel-System)

**Common Issues**:
- ✅ Gemini gibt Help-Output → **Lösung**: One-Shot Mode (`gemini` ohne Flags)
- ✅ Session-Pollution → **Lösung**: Kein `--resume`, `stderr=DEVNULL`

---

## 🔬 Wissenschaftliches Prompt Engineering

### Methodik für Prompt-Optimierung

**1. Problem Identification**
```
Symptom → Root Cause → Hypothesis → Test → Measure
```

**Beispiel**: Merger zeigt `<think>` Tags
- Symptom: `<think>Alright, let's get this done...</think>` im Output
- Root Cause: Kein explizites Verbot von Chain-of-Thought Tags
- Hypothesis: Explizites Verbot + Regex-Filter hilft
- Test: Prompt anpassen + Filter implementieren
- Measure: A/B Test mit 10 Tasks, manuelles Review

---

**2. Prompt-Komponenten (nach Li et al. 2023)**

Jeder Prompt sollte haben:

1. **Role Definition**: "Du bist ein Experte für..."
2. **Task Description**: "Deine Aufgabe ist..."
3. **Input Context**: Klar strukturierte Eingaben
4. **Output Format**: Explizite Format-Anforderungen
5. **Constraints**: Was NICHT tun (kritisch für LLMs!)
6. **Examples** (optional): Few-shot learning

**SelfAI Merger Prompt** (annotiert):

```
Du bist ein Experte für Ergebnis-Synthese...     ← Role Definition

URSPRÜNGLICHES ZIEL (User-Frage):                ← Input Context
{original_goal}

DEINE AUFGABE:                                   ← Task Description
Beantworte die URSPRÜNGLICHE USER-FRAGE...

KRITISCHE ANFORDERUNGEN:                         ← Constraints (neu!)
1. FOKUS: Beantworte NUR die User-Frage
2. KEINE <think> Tags!                           ← Explicit Constraint

AUSGABE-FORMAT:                                  ← Output Format
- Markdown-Formatierung
- Keine Meta-Kommentare
```

---

**3. Constraint-First Prompting (Best Practice)**

**Problem**: LLMs tun oft zu viel (Meta-Kommentare, Erklärungen, etc.)

**Lösung**: Constraints VOR Aufgabenbeschreibung!

**Vorher** (schlechter Prompt):
```
Synthetisiere die Ergebnisse zu einer Antwort.
Beantworte die User-Frage.
```

**Nachher** (besserer Prompt):
```
KRITISCHE ANFORDERUNGEN:
- KEINE <think> Tags!
- KEINE Meta-Kommentare!
- Beginne direkt mit der Antwort!

DANN: Synthetisiere die Ergebnisse...
```

---

**4. Negative Instructions (Wichtig für MiniMax/DeepSeek)**

MiniMax Modelle nutzen `<think>` für Chain-of-Thought. **Du musst das explizit verbieten!**

**Effektive Negative Instructions**:
```
AUSGABE-FORMAT:
- KEINE <think> Tags oder interne Überlegungen!        ← Explizit
- KEINE Meta-Kommentare über den Merge-Prozess!       ← Spezifisch
- Beginne direkt mit der Antwort                      ← Positiv formuliert
```

**Ineffektive Version**:
```
Gib eine gute Antwort.  ← Zu vage, keine Constraints
```

---

**5. Testing & Iteration**

**A/B Testing Setup**:

```python
# Test-Cases für Merger-Prompt
test_cases = [
    {
        "goal": "Erkläre Python Decorators",
        "subtasks": [...],
        "expected_keywords": ["@decorator", "wrapper", "function"],
        "forbidden_patterns": [r"<think>", r"Ich werde jetzt", r"Lass mich"]
    },
    # ... 10 weitere Cases
]

# Metrics
def evaluate_merge_output(output, test_case):
    score = 0
    # 1. Enthält erwartete Keywords?
    for kw in test_case["expected_keywords"]:
        if kw.lower() in output.lower():
            score += 10

    # 2. Keine verbotenen Patterns?
    for pattern in test_case["forbidden_patterns"]:
        if re.search(pattern, output):
            score -= 20  # Heavy penalty!

    # 3. Direktheit (beginnt nicht mit Meta-Text)
    if not re.match(r'^(Ich|Lass|Alright|Okay)', output):
        score += 20

    return score
```

---

**6. Prompt Versioning**

Tracking von Prompt-Änderungen:

```
# PROMPT_CHANGELOG.md
## Merger Prompt v2.1 (2025-12-18)
- Added: "KEINE <think> Tags!" constraint
- Added: "DIREKTHEIT" requirement
- Changed: "URSPRÜNGLICHES ZIEL" → "URSPRÜNGLICHES ZIEL (User-Frage)"
- Impact: A/B Test zeigt 85% weniger <think> Tags, 60% direktere Antworten

## Merger Prompt v2.0 (2025-12-17)
- Initial structured format
```

---

## 🧪 Experimentelle Best Practices

### Chain-of-Thought Kontrolle

**Problem**: MiniMax nutzt `<think>` für bessere Reasoning, aber Output wird verschmutzt.

**Lösungen**:

1. **Explizites Verbot** (current approach):
   ```
   - KEINE <think> Tags in der Ausgabe!
   ```

2. **Separater Thinking-Bereich** (advanced):
   ```
   Du darfst intern nachdenken, aber gib NUR die finale Antwort aus.

   Format:
   [THINKING: deine internen Überlegungen]
   [ANSWER: finale Antwort für User]
   ```
   Then filter `[THINKING:...]` in post-processing.

3. **Regex Filter** (failsafe):
   ```python
   output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL)
   ```

---

### Few-Shot Learning (Future Enhancement)

**Currently**: Zero-shot prompts

**Enhancement**: Add examples to critical prompts

```
BEISPIEL-SYNTHESE:

User-Frage: "Wie funktioniert Merge Sort?"

Subtask 1: "Merge Sort ist ein Divide-and-Conquer Algorithmus..."
Subtask 2: "Die Zeitkomplexität ist O(n log n)..."

GUTE Merge-Antwort:
## Merge Sort

Merge Sort ist ein Divide-and-Conquer Algorithmus mit O(n log n)
Zeitkomplexität. Er funktioniert wie folgt:
1. Teile Array in zwei Hälften
2. Sortiere rekursiv
3. Merge die sortierten Hälften

SCHLECHTE Merge-Antwort:
<think>Okay, ich muss jetzt die Subtasks kombinieren...</think>
Ich werde jetzt erklären, wie Merge Sort funktioniert...
```

---

### Temperature & Sampling Control

**Planner**: `temperature=0.1` (deterministisch, strukturiertes JSON)

**Subtasks**: `temperature=0.3` (etwas kreativ, aber fokussiert)

**Merger**: `temperature=0.2` (kohärent, aber nicht roboterhaft)

**Judge**: `temperature=0.1` (objektiv, reproduzierbar)

---

## 📊 Metrics & Evaluation

### Prompt Quality Metrics

**1. Compliance Rate**: Befolgt der Output die Constraints?
```python
compliance = (outputs_without_think_tags / total_outputs) * 100
```

**2. Directness Score**: Wie direkt beantwortet es die Frage?
```python
# Beginnt mit Meta-Text?
is_direct = not re.match(r'^(Ich|Lass|Alright|Okay)', output)
```

**3. Redundancy Score**: Wie viel Wiederholung?
```python
from difflib import SequenceMatcher
similarity = SequenceMatcher(None, subtask1_output, merge_output).ratio()
# Should be LOW (merger should synthesize, not copy)
```

**4. Goal Adherence**: Beantwortet es die User-Frage?
```python
# Keywords from goal present in output?
goal_keywords = extract_keywords(user_goal)
present_keywords = [kw for kw in goal_keywords if kw in output.lower()]
adherence = len(present_keywords) / len(goal_keywords)
```

---

### Logging für Wissenschaftliche Analyse

**Aktiviere Prompt Logging**:

```python
# In selfai.py (vor jedem LLM-Call)
def log_prompt(stage, prompt, output, metadata):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "stage": stage,  # "planner", "subtask", "merger", "judge"
        "prompt": prompt,
        "output": output,
        "metadata": metadata,
        "model": metadata.get("model"),
        "temperature": metadata.get("temperature"),
    }

    with open("memory/prompt_logs.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

**Analyse mit Pandas**:

```python
import pandas as pd

logs = pd.read_json("memory/prompt_logs.jsonl", lines=True)

# Merger-Performance über Zeit
merger_logs = logs[logs["stage"] == "merger"]
merger_logs["has_think_tags"] = merger_logs["output"].str.contains("<think>")

print(f"Think Tag Rate: {merger_logs['has_think_tags'].mean() * 100:.1f}%")

# A/B Test: Prompt v2.0 vs v2.1
v2_0 = merger_logs[merger_logs["metadata"].str.contains("v2.0")]
v2_1 = merger_logs[merger_logs["metadata"].str.contains("v2.1")]

print(f"v2.0 Think Rate: {v2_0['has_think_tags'].mean() * 100:.1f}%")
print(f"v2.1 Think Rate: {v2_1['has_think_tags'].mean() * 100:.1f}%")
```

---

## 🎓 Advanced Techniques

### 1. **Instruction Hierarchy** (Li et al. 2023)

```
KRITISCH (must-have):
- KEINE <think> Tags!

WICHTIG (should-have):
- Markdown-Formatierung

OPTIONAL (nice-to-have):
- Code-Beispiele
```

### 2. **Constraint Cascading**

```
GLOBAL CONSTRAINTS (für alle Outputs):
- Max 2000 Zeichen
- Markdown-Format

STAGE-SPECIFIC CONSTRAINTS:
Merger:
  - KEINE Meta-Kommentare
  - Direkte Antwort
```

### 3. **Prompt Chaining** (schon implementiert!)

```
User Goal
  → Planner Prompt → DPPM Plan
    → Subtask Prompts → Ergebnisse
      → Merger Prompt → Finale Antwort
        → Judge Prompt → Bewertung
```

---

## 📚 References

- **Li et al. (2023)**: "Guiding Large Language Models via Directional Stimulus Prompting"
- **Wei et al. (2022)**: "Chain-of-Thought Prompting Elicits Reasoning in LLMs"
- **OpenAI (2024)**: "Prompt Engineering Guide"
- **Anthropic (2024)**: "Claude Prompt Engineering Best Practices"

---

## 🔧 Tools for Prompt Engineering

### 1. Prompt Testing Framework

Create `selfai/tools/prompt_tester.py`:

```python
def test_prompt(prompt_template, test_cases, model_interface):
    """A/B test prompt variations"""
    results = []
    for case in test_cases:
        prompt = prompt_template.format(**case["inputs"])
        output = model_interface.generate(prompt)

        score = evaluate(output, case["expected"])
        results.append({
            "case": case["name"],
            "score": score,
            "output": output
        })

    return pd.DataFrame(results)
```

### 2. Prompt Diff Tool

```bash
# Compare prompts
diff -u <(grep -A50 "final_prompt =" selfai/selfai.py.v2.0) \
        <(grep -A50 "final_prompt =" selfai/selfai.py.v2.1)
```

### 3. Output Quality Checker

```python
def check_merger_quality(output):
    checks = {
        "has_think_tags": bool(re.search(r'<think>', output)),
        "has_meta_commentary": bool(re.match(r'^(Ich|Lass|Alright)', output)),
        "has_markdown": bool(re.search(r'##', output)),
        "word_count": len(output.split()),
        "is_direct": not re.match(r'^(Ich werde|Lass mich)', output)
    }
    return checks
```

---

## 🚀 Next Steps

### Immediate Improvements

1. ✅ **Merger Prompt v2.1** (DONE)
   - Added: KEINE `<think>` Tags
   - Added: DIREKTHEIT requirement
   - Added: Regex filter

2. 🔄 **Test with real tasks**
   - Run 10 /plan executions
   - Measure: `<think>` tag rate, directness, goal adherence

3. 📊 **Enable Prompt Logging**
   - Log all prompts + outputs
   - Track metrics over time

### Future Enhancements

1. **Few-Shot Examples** in Merger
2. **Dynamic Temperature** based on task complexity
3. **Prompt Versioning System** with A/B testing
4. **Automated Prompt Optimization** (genetic algorithms?)
5. **Multi-Model Ensemble** (Gemini + MiniMax for merge)

---

**Last Updated**: 2025-12-18
**Version**: 1.0
**Status**: ✅ Active Development

# 🤖 Gemini as Judge - SelfAI Evaluation System

## Overview

**Gemini-as-Judge** ist ein **READ-ONLY Beobachter** der SelfAI's **komplette** Task-Execution bewertet (Plan + Subtasks + Merge). Es ändert **NIE** Code oder Files - es beobachtet nur und gibt Feedback!

**WICHTIG**:
- Gemini Judge evaluiert **NACH** der Merge-Phase, um die finale Output-Qualität zu bewerten
- Gemini Judge läuft in **One-Shot Mode** ohne Session-Speicherung (keine Pollution der normalen Gemini CLI Nutzung)

## 🎯 Was wird bewertet?

### **4 Hauptmetriken (jeweils 0-10):**

| Metrik | Beschreibung | Gewichtung |
|--------|--------------|------------|
| **Task Completion** | Hat es die Aufgabe erfüllt? | 40% |
| **Code Quality** | Ist der Code/Output gut? | 20% |
| **Efficiency** | War die Ausführung effizient? | 20% |
| **Goal Adherence** | Passt es genau zum Ziel? | 20% |

### **Overall Score: 0-100**

Gewichteter Durchschnitt der 4 Metriken.

---

## 🚦 Ampel-System (Traffic Light)

| Ampel | Score | Bedeutung |
|-------|-------|-----------|
| 🟢 **GREEN** | 80-100 | Sehr gut! Task erfolgreich |
| 🟡 **YELLOW** | 50-79 | Okay, aber Verbesserungspotential |
| 🔴 **RED** | 0-49 | Verbesserungsbedarf |

---

## 📊 Output-Format

Nach jeder `/plan` Execution siehst du:

```
============================================================
🟢 GEMINI JUDGE EVALUATION
============================================================

🎯 OVERALL SCORE: 85.0/100

📊 DETAILED METRICS:
   Task Completion:  9.0/10  █████████
   Code Quality:     7.5/10  ███████▌
   Efficiency:       8.5/10  ████████▌
   Goal Adherence:   8.0/10  ████████

💬 SUMMARY:
   Task wurde erfolgreich umgesetzt. Code ist sauber und
   gut dokumentiert. Kleinere Optimierungen möglich.

✅ STRENGTHS:
   • Klare Struktur und gute Lesbarkeit
   • Umfassende Fehlerbehandlung
   • Effiziente Tool-Nutzung

⚠️  WEAKNESSES:
   • Einige Redundanzen im Code
   • Tests fehlen noch

💡 RECOMMENDATIONS:
   • Unit-Tests hinzufügen
   • Code-Kommentare erweitern
   • Performance-Profiling durchführen

============================================================
```

---

## 🔧 Technische Details

### **Gemini CLI Integration**

```python
# Gemini wird via CLI im ONE-SHOT Mode aufgerufen (keine Session):
echo "Prompt..." | gemini

# WICHTIG: Kein --resume, keine Session-Speicherung!
# stderr wird unterdrückt (keine Startup-Logs)
# stdout enthält nur JSON Response

# Output wird geparst:
{
  "task_completion": 8.5,
  "code_quality": 7.0,
  ...
}
```

**Session-Isolation**:
- Gemini Judge verwendet **keine Sessions** (keine --resume Flag)
- Jede Evaluation ist ein **frischer One-Shot Call**
- **Keine Pollution** der normalen Gemini CLI Nutzung
- Keine .gemini-session Files werden erstellt

### **Read-Only Guarantee** ✅

Gemini Judge hat:
- ❌ **KEINE** Schreibrechte auf Files
- ❌ **KEINE** Code-Änderungs-Permissions
- ❌ **KEINE** Tool-Calling Abilities
- ✅ **NUR** Lese-Zugriff auf Output
- ✅ **NUR** Evaluation & Feedback

### **Was Gemini sieht:**

1. **Original Goal** - Was User wollte
2. **Subtask Outputs** - Alle Zwischenergebnisse der Subtasks
3. **Merge Result** - Die finale zusammengefügte Antwort (wichtigste Metrik!)
4. **Plan Details** - Welche Subtasks ausgeführt wurden
5. **Execution Time** - Wie lange die gesamte Pipeline dauerte
6. **Files Changed** - Welche Files geändert wurden (via git diff)

### **Was Gemini NICHT sieht:**

- ❌ Kompletter Code-Inhalt (nur Output-Snippets)
- ❌ API Keys oder Secrets
- ❌ Private User-Daten

---

## 📁 Score Speicherung

Alle Bewertungen werden gespeichert in:

```
memory/judge_scores/
├── README.md
├── 20251217-150000_erstelle-dokumentation_score.json
├── 20251217-151200_fix-bug_score.json
└── 20251217-152000_refactor-code_score.json
```

### **Score-File Format:**

```json
{
  "task_completion": 9.0,
  "code_quality": 7.5,
  "efficiency": 8.5,
  "goal_adherence": 8.0,
  "overall_score": 85.0,
  "traffic_light": "🟢",
  "summary": "Task erfolgreich...",
  "strengths": ["...", "..."],
  "weaknesses": ["..."],
  "recommendations": ["...", "..."]
}
```

---

## 🚀 Usage

### **Automatic Evaluation**

Nach jedem `/plan` wird **automatisch** evaluiert:

```bash
Du: /plan Erstelle eine README Datei

SelfAI: [Führt Plan aus...]
        Plan erfolgreich ausgeführt. ✅

        🤖 Gemini Judge evaluiert die Ausführung...

        [Shows score with traffic light]
```

### **Manual Check Scores**

```bash
# View latest score
cat memory/judge_scores/*.json | tail -1 | jq .

# View all scores
ls -lt memory/judge_scores/*.json
```

---

## 📈 Use Cases

### **1. Quality Assurance**

```
Nach jedem Task → Siehst du sofort ob Qualität stimmt
🟢 Green = Ship it!
🟡 Yellow = Review needed
🔴 Red = Redo required
```

### **2. Learning & Improvement**

```
Gemini's Recommendations helfen:
- Wo sind Schwachstellen?
- Was kann verbessert werden?
- Wie kann man effizienter sein?
```

### **3. Historical Analysis**

```bash
# Compare scores over time
jq '.overall_score' memory/judge_scores/*.json

# See improvement trend
# 50 → 65 → 75 → 85 = SelfAI lernt! 📈
```

---

## ⚙️ Configuration

### **Judge Settings** (in selfai.py)

```python
# Line 1983: Initialize judge
judge = GeminiJudge(
    gemini_cli_path="gemini"  # Custom path if needed
)

# Line 2010: Evaluate with custom settings
score = judge.evaluate_task(
    original_goal=goal_text,
    execution_output=output,
    plan_data=plan_data,
    execution_time=exec_time,
    files_changed=files
)
```

### **Disable Judge** (if needed)

Kommentiere aus in `selfai.py` (Zeile 1977-2029):

```python
# # GEMINI AS JUDGE: Evaluate execution
# try:
#     from selfai.core.gemini_judge import ...
#     ...
# except Exception:
#     pass
```

---

## 🐛 Troubleshooting

### **"Gemini CLI nicht verfügbar"**

**Problem:** Gemini CLI nicht installiert

**Lösung:**
```bash
# Install Gemini CLI (Node.js required)
npm install -g @google/generative-ai-cli

# Or via yarn
yarn global add @google/generative-ai-cli

# Verify
gemini --version
```

### **"Gemini Judge Fehler: Timeout"**

**Problem:** Gemini antwortet nicht schnell genug

**Lösung:** Timeout erhöhen in `gemini_judge.py` (Zeile 82):

```python
result = subprocess.run(
    ...,
    timeout=60  # Increase from 30 to 60
)
```

### **"Parse error: Invalid JSON"**

**Problem:** Gemini gibt kein gültiges JSON zurück

**Lösung:** Automatischer Fallback zu neutralem Score (50/100, 🟡)

---

## 💡 Best Practices

### **1. Review Scores Regularly**

```bash
# Weekly review
ls -lt memory/judge_scores/ | head -10
```

### **2. Learn from Weaknesses**

Gemini's Weaknesses sind Verbesserungs-Opportunities!

### **3. Track Improvement**

```bash
# Plot scores over time
jq '.overall_score' memory/judge_scores/*.json | \
  python -c "
import sys
scores = [float(x) for x in sys.stdin]
print(f'Average: {sum(scores)/len(scores):.1f}')
print(f'Trend: {scores[-5:]}')
"
```

### **4. Use for Decision-Making**

```
🟢 85+ = Production-ready
🟡 65-84 = Needs review
🟡 50-64 = Significant improvements needed
🔴 <50 = Redo task
```

---

## 🔮 Future Enhancements

Planned features:

- [ ] **Historical Trend Graphs** - Visualize score history
- [ ] **Category-Specific Judges** - Different judges for different task types
- [ ] **Multi-Judge Consensus** - Ask multiple LLMs and average
- [ ] **Auto-Improvement Loop** - If Red → Trigger /selfimprove
- [ ] **Leaderboard** - Track best-scoring tasks
- [ ] **Judge Training** - Fine-tune on past evaluations

---

## 📚 Technical Architecture

```
/plan Command
    ↓
Execute Plan (dispatcher.run())
    ↓
Execute Merge Phase (merge.run())
    ↓
Collect Complete Results:
  - User goal (original input)
  - All subtask outputs
  - Merge result (final answer)
  - Execution time (total)
  - Files changed (git diff)
    ↓
Gemini CLI Evaluation (ONE-SHOT MODE):
  - Read complete output (READ-ONLY!)
  - Evaluate quality (Task/Code/Efficiency/Goal)
  - Generate JSON scores
  - NO SESSION SAVED
    ↓
Display Traffic Light + Scores
    ↓
Save to memory/judge_scores/
```

---

## 🎓 Example Evaluations

### **Example 1: Excellent Execution**

```
🟢 OVERALL SCORE: 92.0/100

Metrics:
  Task Completion:  9.5/10
  Code Quality:     9.0/10
  Efficiency:       9.0/10
  Goal Adherence:   9.5/10

Strengths:
  • Perfect implementation
  • Clean, well-documented code
  • Efficient execution

Weaknesses:
  • None significant

Recommendations:
  • Add integration tests
  • Consider edge cases
```

### **Example 2: Needs Improvement**

```
🟡 OVERALL SCORE: 68.0/100

Metrics:
  Task Completion:  7.0/10
  Code Quality:     6.0/10
  Efficiency:       7.5/10
  Goal Adherence:   7.0/10

Strengths:
  • Task completed
  • Basic functionality works

Weaknesses:
  • Missing error handling
  • Code duplication
  • No documentation

Recommendations:
  • Add try-catch blocks
  • Refactor duplicated code
  • Write docstrings
```

### **Example 3: Critical Issues**

```
🔴 OVERALL SCORE: 42.0/100

Metrics:
  Task Completion:  5.0/10
  Code Quality:     3.0/10
  Efficiency:       4.5/10
  Goal Adherence:   5.0/10

Strengths:
  • Attempted implementation

Weaknesses:
  • Core functionality incomplete
  • Multiple bugs present
  • Poor code structure
  • Doesn't meet requirements

Recommendations:
  • Redo task with clearer plan
  • Review requirements carefully
  • Add comprehensive testing
  • Consider using /selfimprove
```

---

## 🔒 Security & Privacy

### **What Gemini Can See:**
- ✅ Task goals and objectives
- ✅ Execution output (truncated)
- ✅ Plan structure
- ✅ File names (not content!)
- ✅ Performance metrics

### **What Gemini CANNOT See:**
- ❌ Full source code
- ❌ API keys or secrets
- ❌ Private user data
- ❌ System internals

### **Data Handling:**
- All evaluations stored locally
- No data sent to external servers (except Gemini API for eval)
- Scores can be deleted anytime

---

**Remember:** Gemini Judge ist ein **Helfer**, kein **Richter**!

Nutze das Feedback konstruktiv um besser zu werden! 🚀✨

---

**Last Updated:** 2025-12-17
**Version:** 1.0.0
**Status:** ✅ Production Ready

# 🤖 SelfAI Self-Improvement Guide

## Die selbst-optimierende von Neumann-Maschine

SelfAI kann sich jetzt **selbst verbessern** mit dem `/selfimprove` Command!

## Quick Start

```bash
python selfai/selfai.py

# In SelfAI:
> /selfimprove optimize DPPM execution speed
```

## Wie es funktioniert

### 1. **Command** `/selfimprove <ziel>`
```
/selfimprove optimize token usage
/selfimprove improve error handling
/selfimprove add better logging
```

### 2. **Safety Checks** 🔒
Vor jeder Selbst-Optimierung prüft SelfAI:
- ✅ Git Repository sauber (keine uncommitted changes)
- ✅ pytest verfügbar (für automatische Tests)
- ✅ Aider installiert (für Code-Änderungen)

**Falls Warnungen:** User muss bestätigen mit `y`

### 3. **Code-Analyse** 📊
SelfAI analysiert sich selbst:
- Alle `.py` Dateien in `selfai/`
- Code-Statistiken (Dateien, Zeilen, Module)
- Identifiziert Verbesserungspotentiale

### 4. **DPPM-Plan** 📋
Erstellt automatisch einen Plan:
1. **S1**: Code-Analyse für das Ziel
2. **S2**: Optimierungen mit `run_aider_task` implementieren
3. **S3**: Tests ausführen und validieren
4. **Merge**: Verbesserungsbericht erstellen

### 5. **User-Approval** 🙋
- Plan wird angezeigt
- User bestätigt: `Y/n`
- Execution bestätigen: `Y/n`

### 6. **Execution** ⚡
- Jeder Subtask nutzt `run_aider_task`
- Aider(MiniMax) macht Code-Änderungen
- Automatische Git-Commits von Aider
- Bei Fehlern: `git revert` möglich

### 7. **Merge** 📝
Finale Zusammenfassung:
- Was wurde verbessert?
- Welche Commits?
- Erwartete Performance-Gains?

## Beispiel-Session

```bash
> /selfimprove reduce DPPM planner token usage

ℹ️  Starte Self-Improvement für Ziel: reduce DPPM planner token usage
✅ Safety-Checks passed
ℹ️  Analysiere SelfAI Code-Struktur...
✅ Code-Analyse abgeschlossen: 25 Dateien, 8432 Zeilen
ℹ️  Erstelle Self-Improvement Plan...

[Plan wird angezeigt mit 3 Subtasks]

Plan übernehmen? (Y/n): y
✅ Self-Improvement Plan gespeichert
Plan jetzt ausführen? (Y/n): y

⚡ Parallel Group 1: 1 Tasks gleichzeitig...
✅ Subtask S1: Code-Analyse [completed]

📊 Subtask S1: Code-Analyse
────────────────────────────────────────────────────
Analysiert: planner_minimax_interface.py
Findings: System-Prompt zu lang (1200 tokens)
Vorschlag: Kompaktere Anweisungen, entferne Wiederholungen
────────────────────────────────────────────────────

⚡ Parallel Group 2: 1 Tasks gleichzeitig...
✅ Subtask S2: Optimierungen implementieren [completed]

📊 Subtask S2: Optimierungen implementieren
────────────────────────────────────────────────────
run_aider_task executed:
- Edited: planner_minimax_interface.py
- Git commit: "refactor: reduce planner prompt token usage"
- Token reduction: 1200 → 650 tokens (46% savings)
────────────────────────────────────────────────────

⚡ Parallel Group 3: 1 Tasks gleichzeitig...
✅ Subtask S3: Tests ausführen [completed]

✅ Self-Improvement erfolgreich!

[Merge Report]
```

## Iterative Self-Optimization Loop

```
SelfAI v1.0 (original)
    ↓ /selfimprove optimize execution speed
SelfAI v1.1 (2x faster DPPM)
    ↓ /selfimprove reduce memory usage
SelfAI v1.2 (50% less memory)
    ↓ /selfimprove improve code quality
SelfAI v1.3 (cleaner, documented)
    ↓ ...
```

Jede Iteration macht SelfAI besser!

## Rollback bei Problemen

Falls eine Verbesserung schief geht:

```bash
# Alle Aider-Commits haben klare Messages
git log --oneline

# Rollback des letzten Commits
git revert HEAD

# Oder mehrere Commits
git revert HEAD~3..HEAD
```

## Safety-Features 🛡️

1. **Git-based Versionierung**: Jede Änderung = Commit
2. **User-Approval**: Keine automatischen Änderungen ohne Bestätigung
3. **Test-Validierung**: Subtask S3 führt automatisch Tests aus
4. **Rollback-fähig**: `git revert` jederzeit möglich
5. **Code-Analyse-Phase**: Versteht Code bevor Änderungen

## Best Practices

### ✅ DO:
- Kleine, fokussierte Ziele (`optimize DPPM speed`)
- Ein Ziel pro /selfimprove Session
- Tests schreiben für kritischen Code
- Git commits regelmäßig pushen

### ❌ DON'T:
- Vage Ziele (`make it better`)
- Mehrere Ziele gleichzeitig
- /selfimprove ohne Backups
- Wichtige Änderungen ohne Tests

## Human-in-the-Loop Timing

**Standard**: User-Approval bei:
1. Plan-Erstellung (vor Execution)
2. Vor jeder Execution-Phase
3. Bei Safety-Warnungen

**Gewünscht (Original-Vision)**:
- Alle 5-10 Minuten Checkpoint für Richtungs-Änderung
- *(Noch nicht implementiert, kommt in v2)*

## Advanced: Custom Self-Improvement Agents

Du kannst spezialisierte Agents erstellen:

```yaml
# agents/code_optimizer/config.yaml
agent:
  name: "code_optimizer"
  display_name: "Code Optimizer"
  description: "Specialized in performance optimization"
  tags: ["optimization", "performance"]
```

Dann in `/selfimprove` Plan:
```json
{
  "subtasks": [{
    "agent_key": "code_optimizer",
    "objective": "Optimize hot path in DPPM"
  }]
}
```

## Metrics & Tracking

Track your improvements:

```bash
# Token Usage
git log --grep="token" --oneline

# Performance
git log --grep="speed\|performance" --oneline

# Code Quality
git log --grep="refactor\|quality" --oneline
```

## Troubleshooting

### "Git Repository nicht sauber"
```bash
git add -A
git commit -m "WIP: before self-improvement"
```

### "pytest nicht verfügbar"
```bash
pip install pytest
```

### "Aider nicht installiert"
```bash
pip install aider-chat
```

### "MiniMax API Fehler"
- Check API-Key in `/home/smlflg/AutoCoder/minimax`
- Verify MiniMax API limits nicht überschritten

## Vision: Fully Autonomous Self-Optimization

**Phase 1** (✅ Done): Manual /selfimprove mit User-Approval
**Phase 2** (🔄 Next): Scheduled self-optimization (nightly runs)
**Phase 3** (🔮 Future): Autonomous goal-setting basierend auf Metriken
**Phase 4** (🚀 Dream): Multi-agent self-optimization teams

## Contributing

SelfAI verbessert sich selbst - aber du kannst helfen:

1. Identifiziere Verbesserungs-Ziele
2. Führe `/selfimprove <ziel>` aus
3. Review die Änderungen
4. Share erfolgreiche Optimierungen

## Architecture

```
/selfimprove <goal>
    ↓
_validate_selfimprove_safety()  [Git check, pytest, aider]
    ↓
_analyze_selfai_code()          [Collect .py files, stats]
    ↓
_handle_selfimprove()           [Main orchestration]
    ↓
PlannerMinimaxInterface         [Create DPPM plan]
    ↓
[User-Approval]
    ↓
ExecutionDispatcher             [Run subtasks]
    ↓
run_aider_task                  [Code changes via Aider+MiniMax]
    ↓
Git Commit                      [Automatic by Aider]
    ↓
MergeInterface                  [Synthesize results]
    ↓
Final Report                    [What was improved?]
```

## Credits

Konzept: Selbst-optimierende von Neumann-Maschine
Implementation: SelfAI + Aider(MiniMax) + Claude Code
Inspiration: "A machine that improves itself"

---

**Start improving now:**
```bash
python selfai/selfai.py
> /selfimprove <your goal here>
```

🚀 **The future is self-optimizing!**

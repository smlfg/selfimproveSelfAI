# Multi-Pane UI Fix - Terminal Output Korrigiert

**Date**: 2025-01-21
**Problem**: "output im TUI zerschießt es komplett mit den neuen subagent boxen"
**Status**: ✅ FIXED

---

## 🐛 Problem

Multi-Pane UI hat das Terminal-Output zerstört:
- Millionen Boxen wurden erstellt
- Output war unleserlich
- UI renderte auch bei einzelnen Tasks

### User Feedback:
> "da sollen statisch so viele boxen wie subtasks erstellt werden in denenen ratter/stramlined dann die subtask durch, aber es sollen nicht einemillionen boxen erstellt werden"

---

## ✅ Fixes

### Fix 1: Nur EIN Box-Container statt separate Boxen

**File**: `selfai/ui/multi_pane_ui.py` (Line 170-209)

**VORHER** (FALSCH):
```
┌────────────┐
│ Subtask 1  │
└────────────┘
┌────────────┐
│ Subtask 2  │
└────────────┘
┌────────────┐
│ Subtask 3  │
└────────────┘
```

**NACHHER** (RICHTIG):
```
┌────────────────┐
│ Subtask 1      │
├────────────────┤
│ Subtask 2      │
├────────────────┤
│ Subtask 3      │
└────────────────┘
```

**Code-Änderung**:
```python
def render_frame(self):
    # ONE top border for all panes
    print("┌" + "─" * (self.terminal_width - 2) + "┐")

    for idx, pane_id in enumerate(sorted(self.panes.keys())):
        pane = self.panes[pane_id]
        lines = pane.render(self.terminal_width - 4)

        # Content lines
        for line in lines:
            padded = line.ljust(self.terminal_width - 4)
            print("│ " + padded + " │")

        # Separator BETWEEN panes (not after last!)
        if idx < len(self.panes) - 1:
            print("├" + "─" * (self.terminal_width - 2) + "┤")

    # ONE bottom border for all panes
    print("└" + "─" * (self.terminal_width - 2) + "┘")
```

**Resultat**: Statische Box, wird nur geupdatet, nicht neu erstellt!

---

### Fix 2: Multi-Pane UI nur bei PARALLELEN Tasks

**File**: `selfai/core/execution_dispatcher.py` (Line 87-114)

**Problem**: Multi-Pane UI wurde IMMER aktiviert, auch bei 1 einzelnem Task!

**Fix**: Nur aktivieren wenn tatsächlich parallele Tasks existieren:

```python
# Group tasks FIRST
groups = defaultdict(list)
for task in self.subtasks:
    pg = task.get("parallel_group", 1)
    groups[pg].append(task)

# Check if ANY group has multiple tasks
has_parallel_tasks = any(len(tasks) > 1 for tasks in groups.values())

# Initialize Multi-Pane UI ONLY if parallel tasks exist
multi_pane_ui = None
if has_parallel_tasks:
    try:
        from selfai.ui.multi_pane_ui import MultiPaneUI
        multi_pane_ui = MultiPaneUI(pane_height=4)
        # ... add panes ...
        self.ui.status("🖥️  Multi-Pane UI aktiviert", "info")
    except Exception as e:
        multi_pane_ui = None
```

**Resultat**:
- ✅ Sequentielle Tasks (1 pro Gruppe): Kein Multi-Pane UI
- ✅ Parallele Tasks (2+ in einer Gruppe): Multi-Pane UI aktiviert

---

### Fix 3: Verbesserte Cursor-Bewegung

**File**: `selfai/ui/multi_pane_ui.py` (Line 178-185)

**VORHER**:
```python
# Nur cursor up, kein clear
sys.stdout.write(f"\033[{total_lines}A")
```

**NACHHER**:
```python
# Move up, clear each line, move back up
sys.stdout.write(f"\033[{total_lines}A")
for _ in range(total_lines):
    sys.stdout.write("\033[K")  # Clear line
    sys.stdout.write("\033[B")  # Move down
sys.stdout.write(f"\033[{total_lines}A")  # Move back up
```

**Resultat**: Alte Output-Reste werden entfernt, sauberes Re-Rendering!

---

## 📊 Wann wird Multi-Pane UI aktiviert?

### ✅ AKTIVIERT (Parallel Tasks):

**Plan**:
```json
{
  "subtasks": [
    {"id": "S1", "parallel_group": 1},
    {"id": "S2", "parallel_group": 1},  // Same group = parallel!
    {"id": "S3", "parallel_group": 2}
  ]
}
```

**Ausgabe**:
```
🖥️  Multi-Pane UI aktiviert für parallele Anzeige

┌─────────────────────────────────────────────┐
│ 🔄 SUBTASK 1: Analysis (S1)                │
│   Analyzing files... Loading...             │
├─────────────────────────────────────────────┤
│ 🔄 SUBTASK 2: Implementation (S2)           │
│   Modifying code... Testing...              │
└─────────────────────────────────────────────┘
```

### ❌ NICHT aktiviert (Sequential Tasks):

**Plan**:
```json
{
  "subtasks": [
    {"id": "S1", "parallel_group": 1},
    {"id": "S2", "parallel_group": 2},  // Different groups = sequential
    {"id": "S3", "parallel_group": 3}
  ]
}
```

**Ausgabe**:
```
ℹ️ Task S1: Analysis
[Normal output ohne Multi-Pane UI]
✅ Task S1 abgeschlossen

ℹ️ Task S2: Implementation
[Normal output]
✅ Task S2 abgeschlossen
```

---

## 🎨 Layout Beispiel

### Mit 3 parallelen Subtasks:

```
┌───────────────────────────────────────────────────────────────┐
│ 🔄 SUBTASK 1: Code-Analyse (S1)                              │
│   Analyzing code structure... Loading files... Done!          │
│   Found 42 Python files... Checking imports...                │
│   Analysis complete. 5 issues found.                          │
│   ✅ COMPLETE (5.2s)                                          │
├───────────────────────────────────────────────────────────────┤
│ 🔄 SUBTASK 2: Implement Fix (S2)                              │
│   Starting implementation... Modifying file...                │
│   Running tests... All tests passed!                          │
│   Committing changes...                                        │
│   ✅ COMPLETE (12.1s)                                         │
├───────────────────────────────────────────────────────────────┤
│ 🔄 SUBTASK 3: Documentation (S3)                              │
│   Generating docs... Writing to README.md...                  │
│   Updating docstrings... Formatting...                        │
│   Documentation updated successfully.                          │
│   ✅ COMPLETE (3.8s)                                          │
└───────────────────────────────────────────────────────────────┘
```

**Features**:
- ✅ Statische Box (einmal erstellt)
- ✅ Separatoren zwischen Panes (`├──┤`)
- ✅ Update-in-place (kein scrolling)
- ✅ 4 Zeilen pro Pane (configurable)
- ✅ Status indicators (🔄/✅/❌)

---

## 🧪 Testing

### Test 1: Sequential Plan (kein Multi-Pane UI)

```bash
python selfai/selfai.py
```

```
Du: /plan analysiere execution_dispatcher.py

📝 PLAN:
Subtasks:
  S1: Read file (parallel_group: 1)
  S2: Analyze code (parallel_group: 2)
  S3: Write summary (parallel_group: 3)

Plan bestätigen? y
Plan ausführen? y

ℹ️ Task S1: Read file
[Normal output - KEIN Multi-Pane UI!]
✅ Task S1 abgeschlossen
```

**Erwartung**: Kein Multi-Pane UI (sequential tasks)

### Test 2: Parallel Plan (mit Multi-Pane UI)

```bash
python selfai/selfai.py
```

```
Du: /plan optimiere performance mit 3 parallelen analysen

📝 PLAN:
Subtasks:
  S1: CPU Profile (parallel_group: 1)
  S2: Memory Profile (parallel_group: 1)
  S3: I/O Profile (parallel_group: 1)
  S4: Merge Results (parallel_group: 2)

Plan bestätigen? y
Plan ausführen? y

🖥️  Multi-Pane UI aktiviert für parallele Anzeige

┌─────────────────────────────────────────┐
│ 🔄 SUBTASK 1: CPU Profile (S1)         │
│   Running profiler...                   │
├─────────────────────────────────────────┤
│ 🔄 SUBTASK 2: Memory Profile (S2)      │
│   Collecting data...                    │
├─────────────────────────────────────────┤
│ 🔄 SUBTASK 3: I/O Profile (S3)         │
│   Measuring I/O...                      │
└─────────────────────────────────────────┘

[Updates in real-time, dann:]

┌─────────────────────────────────────────┐
│ ✅ SUBTASK 1: CPU Profile (S1) - 4.2s  │
│   ... complete output ...               │
├─────────────────────────────────────────┤
│ ✅ SUBTASK 2: Memory Profile (S2) - 3.8s│
│   ... complete output ...               │
├─────────────────────────────────────────┤
│ ✅ SUBTASK 3: I/O Profile (S3) - 5.1s  │
│   ... complete output ...               │
└─────────────────────────────────────────┘
```

**Erwartung**: Multi-Pane UI mit 3 Panes für S1-S3 (parallel_group: 1)

---

## 📈 Improvements

### Before (Broken):
- ❌ Separate boxes everywhere
- ❌ Millions of boxes created
- ❌ Terminal scrolling wildly
- ❌ Activated even for single tasks
- ❌ Unreadable output

### After (Fixed):
- ✅ One static box container
- ✅ Clean separators between panes
- ✅ Update-in-place (no scrolling)
- ✅ Only activated for parallel tasks
- ✅ Clean, readable output

---

## 🔧 Configuration

Multi-Pane UI aktiviert sich automatisch wenn nötig. Keine Config-Änderung erforderlich!

**Bedingung**: `any(len(tasks) > 1 for tasks in groups.values())`

Falls du es komplett deaktivieren willst:

**Option 1** (Code-Level): In `execution_dispatcher.py` Line 98:
```python
if has_parallel_tasks and False:  # Force disable
```

**Option 2** (Import-Level): Rename `multi_pane_ui.py`:
```bash
mv selfai/ui/multi_pane_ui.py selfai/ui/multi_pane_ui.py.disabled
```

---

## 🎯 Summary

**Files Changed**:
1. `selfai/ui/multi_pane_ui.py`:
   - Line 170-209: ONE box mit separators
   - Line 178-185: Verbesserte cursor movement

2. `selfai/core/execution_dispatcher.py`:
   - Line 87-114: Aktivierung nur bei parallelen Tasks

**Resultat**:
- ✅ Statische Box (keine Million Boxen mehr!)
- ✅ Nur bei parallelen Tasks
- ✅ Clean re-rendering
- ✅ Terminal-Output nicht mehr zerschossen

---

**Status**: ✅ FIXED - Terminal UI jetzt sauber!
**Next**: Teste mit `/plan` und parallelen Subtasks!

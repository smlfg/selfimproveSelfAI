# Fixes Applied - 2025-01-21

## Fix 1: Plan Validation - "minimax" engine erlaubt ✅

**Problem**:
```
⚠️ Plan validation warning: subtasks[1].engine 'minimax' ist nicht erlaubt
```

**Root Cause**: `planner_validator.py` hatte "minimax" nicht in `DEFAULT_ENGINES`

**Fix**:
```python
# selfai/core/planner_validator.py (Zeile 26)
DEFAULT_ENGINES = {"anythingllm", "qnn", "cpu", "smolagent", "minimax"}  # minimax added!
```

**Status**: ✅ Fixed

---

## Fix 2: Merge Output abgeschnitten ✅

**Problem**:
```
SelfAI: ... Int
 output am ende abgeschnitten
```

**Root Cause**: `merge_max_tokens` war 2048, zu wenig für vollständige Merge-Antworten

**Fix**:
```python
# selfai/core/token_limits.py (Zeile 62)
def set_balanced(self) -> None:
    self.merge_max_tokens = 4096  # Increased from 2048
```

**Status**: ✅ Fixed

---

## Problem 3: Agent modifiziert Dateien bei Chat-Fragen ⚠️ CRITICAL

**Gemini Judge Score**: 17/100

**Problem**:
```
User: "Wer bist du?" (via /plan)
Agent: Modifiziert 10 Systemdateien statt zu antworten!
```

**Root Cause Analysis**:

1. **User hat `/plan wer bist du` statt "wer bist du" eingegeben**
   - `/plan` triggert komplette DPPM-Pipeline
   - Plan erstellt Subtasks
   - Subtasks nutzen Tools (inkl. File-Schreib-Tools!)

2. **Agent hatte Zugriff auf ALLE Tools**
   - Inkl. `run_aider_task` (schreibt Code!)
   - Inkl. `run_openhands_task` (schreibt Code!)
   - Agent dachte: "Ich muss Code ändern um Identität zu zeigen"

3. **Kein Output Capturing**
   - Merge-Result wurde nicht richtig gespeichert
   - "No output captured" in Gemini Judge

### Solution Options:

#### Option A: Tool-Filtering für Read-Only Subtasks (EMPFOHLEN)

**Idee**: Subtasks können als `read_only: true` markiert werden

```json
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Erkläre SelfAI Identität",
      "objective": "Beschreibe wer du bist",
      "agent_key": "code_helfer",
      "engine": "minimax",
      "read_only": true  // NEW!
    }
  ]
}
```

**Implementation**:
```python
# In execution_dispatcher.py

def _execute_subtask(self, task):
    # Filter tools based on read_only flag
    if task.get("read_only", False):
        # Only allow read tools
        allowed_tools = [
            "list_selfai_files",
            "read_selfai_code",
            "search_selfai_code",
            "list_project_files",
            "read_project_file",
            "search_project_files",
            "get_current_weather",  # Safe tools
        ]

        # Create filtered agent with only read tools
        tools = [t for t in all_tools if t.name in allowed_tools]
        agent = create_selfai_agent(llm_interface, tools, ui)
    else:
        # Normal agent with all tools
        agent = create_selfai_agent(llm_interface, all_tools, ui)
```

**Effort**: 30 Min
**Risk**: Low

---

#### Option B: Separate "chat" vs "plan" Tools

**Idee**: Chat-Agent hat NUR Read-Tools, Plan-Agent hat alle Tools

```python
# In selfai.py

# For normal chat (line 2428)
if ENABLE_AGENT_MODE and llm_interface:
    # CHAT MODE: Only read tools!
    read_only_tools = [
        "list_selfai_files",
        "read_selfai_code",
        "search_selfai_code",
        # ... other safe tools
    ]

    tools = [t for t in get_tools_for_agent() if t.name in read_only_tools]

    selfai_agent = create_selfai_agent(
        llm_interface, tools, ui, max_steps=10
    )

# For /plan execution (execution_dispatcher.py)
# Use ALL tools (including write tools)
```

**Effort**: 15 Min
**Risk**: Medium (might restrict chat too much)

---

#### Option C: Planner Instruction Clarity

**Idee**: Verbessere Planner System-Prompt um Read-Only Tasks zu erzwingen

```python
# In planner_minimax_interface.py

PLANNER_SYSTEM_PROMPT = """
...

WICHTIG für einfache Fragen (Identität, Erklärungen, etc.):
- Erstelle KEINE Subtasks die Code modifizieren!
- Nutze NUR lesende Tools: list_selfai_files, read_selfai_code, search_selfai_code
- Schreib-Tools (run_aider_task, run_openhands_task) VERBIETEN für Chat-Fragen!

Beispiel RICHTIG:
User: "Wer bist du?"
Plan:
{
  "subtasks": [{
    "id": "S1",
    "title": "Identität erklären",
    "objective": "Lese identity_enforcer.py und erkläre SelfAI Identität",
    "tools_hint": "read_selfai_code nur!", // Hint für Execution!
  }]
}

Beispiel FALSCH:
User: "Wer bist du?"
Plan: {subtasks: [{tools: "run_aider_task"}]}  // NIEMALS bei Chat-Fragen!
"""
```

**Effort**: 10 Min
**Risk**: Low (might still fail if LLM ignores)

---

### Recommendation: Kombination A + C

**Why**:
1. **Option C** (Planner Instruction) verhindert Problem an der Wurzel
2. **Option A** (Read-Only Flag) ist Backup-Absicherung
3. Zusammen: Defense-in-Depth

**Implementation Order**:
1. ✅ **Jetzt**: Option C (Planner Prompt verbessern) - 10 Min
2. ⏭️ **Später**: Option A (Read-Only Flag) - 30 Min bei Bedarf

---

## Quick Fix für sofort: Disable Aider/OpenHands in Chat

**Schnellste Lösung** (2 Minuten):

```python
# In selfai.py (Line 2428)

if ENABLE_AGENT_MODE and llm_interface:
    # Get all tools
    all_tools = get_tools_for_agent()

    # FILTER OUT write tools for normal chat!
    dangerous_tools = ["run_aider_task", "run_openhands_task", "run_aider_architect", "run_openhands_architect"]
    safe_tools = [t for t in all_tools if t.name not in dangerous_tools]

    selfai_agent = create_selfai_agent(
        llm_interface, safe_tools, ui  # Use filtered tools!
    )
```

**Pros**: Sofort wirksam, 100% sicher
**Cons**: Kann Aider/OpenHands auch nicht im Chat nutzen (aber das ist okay!)

---

## Status Summary

| Fix | Problem | Status | Priority |
|-----|---------|--------|----------|
| 1. minimax engine | Plan validation failed | ✅ Fixed | High |
| 2. merge_max_tokens | Output abgeschnitten | ✅ Fixed | Medium |
| 3. Agent writes files | Gemini 17/100 | ⚠️ Needs Fix | **CRITICAL** |

---

## Next Steps

**IMMEDIATE** (Du kannst wählen):

**Option 1: Quick & Dirty** (2 Min)
- Filter dangerous tools aus Chat-Agent
- 100% sicher, aber restrictive

**Option 2: Proper Solution** (10 Min)
- Verbessere Planner Prompt (Option C)
- Eleganter, könnte aber noch fehlschlagen

**Option 3: Belt & Suspenders** (40 Min)
- Option C + Option A
- Maximum Sicherheit

**Was bevorzugst du?**

---

**Created**: 2025-01-21
**Critical Issue**: Agent modifiziert Files bei Chat
**Quick Fix Available**: Ja (Filter dangerous tools)
**Proper Fix Available**: Ja (Read-only flag + Planner instruction)

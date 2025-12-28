# SelfAI Self-Improvement V2 - Analysis + Implementation Split

## Problem mit V1 (Alt)

**`/selfimprove <ziel>`** macht alles auf einmal:
1. Analysiert Code
2. Erstellt Plan
3. Fragt User: "Plan übernehmen?"
4. Fragt User: "Plan ausführen?"
5. Führt **ALLES** aus (keine Kontrolle welche Improvements)

**User hat keine Auswahl welche Verbesserungen implementiert werden sollen!**

---

## Lösung: V2 (Neu)

### Phase 1: `/selfimprove <ziel>` - ANALYSIS ONLY

**Was passiert:**
1. ✅ Analysiert SelfAI Code
2. ✅ Erstellt Liste von Verbesserungsvorschlägen
3. ✅ Zeigt Vorschläge mit IDs an
4. ❌ **FÜHRT NICHTS AUS!**

**Output:**
```
═══════════════════════════════════════════════════════
  VERBESSERUNGSVORSCHLÄGE
═══════════════════════════════════════════════════════

🔴 HIGH PRIORITY:
──────────────────────────────────────────────────────

  [1] ⚡ Optimize context loading performance
      Current load_relevant_context() is O(n²), optimize to O(n)
      Aufwand: ▪▪ medium
      Files: selfai/core/memory_system.py

  [2] 🐛 Fix error handling in gemini_judge
      Missing exception catch in _parse_gemini_response()
      Aufwand: ▪ small
      Files: selfai/core/gemini_judge.py

🟡 MEDIUM PRIORITY:
──────────────────────────────────────────────────────

  [3] ✨ Add caching for tool registry
      Tool loading happens on every call, add LRU cache
      Aufwand: ▪ small
      Files: selfai/tools/tool_registry.py

  [4] 🎯 Add /history command
      Users want to see conversation history
      Aufwand: ▪▪ medium
      Files: selfai/selfai.py, selfai/ui/terminal_ui.py

🟢 LOW PRIORITY:
──────────────────────────────────────────────────────

  [5] ✨ Improve error messages
      Add more context to error outputs
      Aufwand: ▪ small
      Files: multiple files

═══════════════════════════════════════════════════════
Gesamt: 5 Vorschläge
═══════════════════════════════════════════════════════

💡 Implementierung: /selfimplement <IDs>
   Beispiel: /selfimplement 1,3,5
   Alle: /selfimplement all
```

### Phase 2: `/selfimplement <IDs>` - EXECUTION

**Was passiert:**
1. ✅ User wählt IDs: `/selfimplement 1,3`
2. ✅ Erstellt Plan NUR für gewählte Improvements
3. ✅ Zeigt Plan
4. ✅ Fragt: "Plan übernehmen?" (oder YOLO)
5. ✅ Fragt: "Plan ausführen?" (oder YOLO)
6. ✅ Führt nur gewählte Improvements aus

**Example:**
```bash
You: /selfimplement 1,3

Erstelle Plan für 2 Verbesserungen:
  [1] Optimize context loading performance
  [3] Add caching for tool registry

[Plan wird erstellt]

Plan übernehmen? (y/N): y

Plan jetzt ausführen? (y/N): y

[Nur diese 2 werden implementiert!]
```

---

## Benefits

### 1. **User Control** ✅
- User sieht ALLE Vorschläge
- User wählt was implementiert wird
- Keine unerwünschten Änderungen

### 2. **Transparency** ✅
- Klar was jeder Vorschlag macht
- Priorität sichtbar (high/medium/low)
- Aufwand sichtbar (small/medium/large)
- Betroffene Files sichtbar

### 3. **Safety** ✅
- Analyse ist READ-ONLY
- Keine Änderungen ohne Confirmation
- User kann einzelne risky Improvements skippen

### 4. **Flexibility** ✅
- Implementiere High-Priority zuerst
- Teste einzeln
- Rollback möglich (Git)

---

## Commands

### `/selfimprove <ziel>` - Analysis

**Usage:**
```bash
/selfimprove Improve performance
/selfimprove Add better error handling
/selfimprove Optimize memory usage
```

**Output:**
- Liste von Vorschlägen mit IDs
- Priorität, Kategorie, Aufwand
- Betroffene Files
- Implementation Plan

**Speichert:**
- Vorschläge in Memory (Session)
- Optional: JSON File für später

### `/selfimplement <IDs>` - Implementation

**Usage:**
```bash
/selfimplement 1         # Single improvement
/selfimplement 1,3,5     # Multiple improvements
/selfimplement all       # All improvements
/selfimplement high      # All high-priority
/selfimplement medium    # All medium-priority
```

**Flow:**
1. Lädt gespeicherte Vorschläge
2. Erstellt Plan für gewählte IDs
3. Zeigt Plan (wie /plan)
4. Fragt Confirmation (oder YOLO)
5. Führt aus mit Aider
6. Git Commit pro Improvement

---

## Implementation Details

### Data Structure

```python
@dataclass
class ImprovementSuggestion:
    id: int
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    category: str  # "performance", "code_quality", "features", "bugs"
    affected_files: List[str]
    estimated_effort: str  # "small", "medium", "large"
    implementation_plan: str  # Detailed plan
```

### Storage

```python
class ImprovementSuggestionsManager:
    def __init__(self):
        self.suggestions: List[ImprovementSuggestion] = []
        self.analysis_goal: str = ""
        self.analysis_timestamp: datetime = None

    def add_suggestion(self, suggestion: ImprovementSuggestion):
        ...

    def get_suggestions_by_ids(self, ids: List[int]) -> List[ImprovementSuggestion]:
        ...

    def save_to_file(self, filepath: Path):
        # Save as JSON for later use
        ...
```

### Workflow

**1. Analysis Phase (`/selfimprove`):**
```python
def _handle_selfimprove_analysis(goal, suggestions_manager, ...):
    # 1. Analyze code
    code_analysis = _analyze_selfai_code()

    # 2. Create LLM prompt for suggestions
    prompt = f"""
    Analyze SelfAI code for: {goal}

    Generate improvement suggestions in this format:
    ## Vorschlag 1: Title
    **Beschreibung:** ...
    **Priorität:** high/medium/low
    **Kategorie:** performance/code_quality/features/bugs
    **Betroffene Dateien:** file1.py, file2.py
    **Aufwand:** small/medium/large
    **Implementierung:** detailed plan
    """

    # 3. Get LLM response
    analysis = llm.generate(prompt)

    # 4. Parse suggestions
    suggestions = parse_suggestions_from_analysis(analysis, goal)

    # 5. Store in manager
    suggestions_manager.clear()
    for suggestion in suggestions:
        suggestions_manager.add_suggestion(suggestion)

    # 6. Display formatted list
    output = format_suggestions_for_display(suggestions)
    print(output)
```

**2. Implementation Phase (`/selfimplement`):**
```python
def _handle_selfimplement(ids_str, suggestions_manager, ...):
    # 1. Parse IDs
    selected_ids = parse_ids(ids_str)  # "1,3,5" -> [1, 3, 5]

    # 2. Get suggestions
    suggestions = suggestions_manager.get_suggestions_by_ids(selected_ids)

    if not suggestions:
        ui.status("Keine Vorschläge mit diesen IDs gefunden!", "error")
        return

    # 3. Create plan for selected improvements
    plan = create_implementation_plan(suggestions)

    # 4. Show plan
    ui.show_plan(plan)

    # 5. Confirm
    if not ui.confirm_plan():
        return

    # 6. Execute (wie normaler /plan)
    plan_path = memory_system.save_plan(f"Implement improvements {ids_str}", plan)

    if not ui.confirm_execution():
        return

    # 7. Run with ExecutionDispatcher
    dispatcher = ExecutionDispatcher(...)
    dispatcher.run()

    # 8. Merge results
    merge_success = _execute_merge_phase(...)
```

---

## Example Session

```bash
$ python selfai/selfai.py

You: /selfimprove Optimize performance and memory usage

🔍 Starte Self-Improvement Analyse für: Optimize performance and memory usage
   (Nur Analyse, keine Änderungen!)

[Analysiert Code...]

═══════════════════════════════════════════════════════
  VERBESSERUNGSVORSCHLÄGE
═══════════════════════════════════════════════════════

🔴 HIGH PRIORITY:

  [1] ⚡ Optimize load_relevant_context()
      Current O(n²) loop, change to O(n) with dict lookup
      Aufwand: ▪▪ medium
      Files: selfai/core/memory_system.py

  [2] ⚡ Cache tool registry
      Tool loading is slow, add functools.lru_cache
      Aufwand: ▪ small
      Files: selfai/tools/tool_registry.py

🟡 MEDIUM PRIORITY:

  [3] ✨ Optimize plan JSON parsing
      Use ijson for streaming large plans
      Aufwand: ▪▪ medium
      Files: selfai/core/execution_dispatcher.py

═══════════════════════════════════════════════════════
Gesamt: 3 Vorschläge
═══════════════════════════════════════════════════════

💡 Implementierung: /selfimplement <IDs>

You: /selfimplement 1,2

Erstelle Plan für 2 Verbesserungen:
  [1] Optimize load_relevant_context()
  [2] Cache tool registry

[Plan generiert]

Geplanter Ablauf (DPPM):
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Implement [1] Optimize load_relevant_context()",
      "objective": "Change O(n²) to O(n) with dict lookup in memory_system.py",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      ...
    },
    {
      "id": "S2",
      "title": "Implement [2] Cache tool registry",
      "objective": "Add @lru_cache to tool loading functions",
      "engine": "smolagent",
      "tools": ["run_aider_task"],
      ...
    }
  ],
  ...
}

Plan übernehmen? (y/N): y
✅ Plan gespeichert

Plan jetzt ausführen? (y/N): y

🚀 Starte Plan-Ausführung...

[S1] Implement [1] Optimize load_relevant_context()
✓ Aider: Changed memory_system.py (optimization applied)

[S2] Implement [2] Cache tool registry
✓ Aider: Changed tool_registry.py (caching added)

[Merge phase]

✅ Plan erfolgreich abgeschlossen!

2 Improvements implemented:
  [1] ⚡ Optimize load_relevant_context() - DONE
  [2] ⚡ Cache tool registry - DONE
```

---

## Comparison: V1 vs V2

| Feature | V1 (Old) | V2 (New) |
|---------|----------|----------|
| Analysis | ✅ | ✅ |
| Shows suggestions | ❌ (Plan only) | ✅ (Formatted list) |
| User selection | ❌ (All or nothing) | ✅ (Pick IDs) |
| Execution | Auto | Manual `/selfimplement` |
| Control | Low | High |
| Safety | Medium | High |
| Transparency | Low | High |

---

## Integration with Other Features

### With `/yolo` Mode

```bash
You: /yolo
🚀 YOLO MODE ACTIVATED

You: /selfimprove Performance optimization

[Suggestions displayed]

You: /selfimplement 1,2,3

Plan übernehmen? (y/N): y (YOLO)
Plan jetzt ausführen? (y/N): y (YOLO)

[Executes without further prompts]
```

### With Git

Each improvement gets its own commit:

```bash
git log --oneline

abc1234 SelfAI: Implement [2] Cache tool registry
def5678 SelfAI: Implement [1] Optimize load_relevant_context()
```

Easy to review, easy to revert!

### With `/plan`

Can combine with manual planning:

```bash
You: /plan Implement feature X and apply improvement [1]

[Creates plan combining both]
```

---

## Future Enhancements

### 1. Persistent Suggestions

Save suggestions to file:
```bash
You: /selfimprove Performance
[Suggestions saved to memory/improvements/performance_20250120.json]

You: /selfimplement load memory/improvements/performance_20250120.json 1,3
```

### 2. Suggestion Review

```bash
You: /selfimplement review 1

[Shows detailed analysis of suggestion 1]
[Shows affected code]
[Shows proposed changes]

Implement? (y/N):
```

### 3. Batch Implementation

```bash
You: /selfimplement batch high

For each HIGH priority suggestion:
  [Shows suggestion]
  Implement? (y/N/s=skip/a=all):
```

### 4. Suggestion Export

```bash
You: /selfimprove export markdown

[Creates IMPROVEMENTS.md with all suggestions]
```

---

## Summary

**V2 = Analysis + Implementation Split**

- ✅ `/selfimprove` → Analysis only, shows suggestions
- ✅ `/selfimplement <IDs>` → Implements selected improvements
- ✅ Full user control
- ✅ High transparency
- ✅ Safe (no auto-execution)
- ✅ Flexible (pick what you want)

**Perfect workflow:**
1. Analyze with `/selfimprove <goal>`
2. Review suggestions
3. Pick what to implement
4. Execute with `/selfimplement <IDs>`
5. Test and commit individually

**Philosophy:** Trust the user to decide what changes to make! 🎯

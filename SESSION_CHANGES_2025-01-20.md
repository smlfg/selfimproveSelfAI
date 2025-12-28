# SelfAI Session Changes - 2025-01-20

## Overview

Comprehensive updates to SelfAI including: Think Tag Parsing, Gemini Judge Debugging, YOLO Mode, UI Design System, and Self-Improvement V2.

---

## 1. Think Tag Parsing System 💭

### Problem
LLM responses often contain `<think>...</think>` tags showing reasoning process, which:
- Cluttered the actual response
- Interfered with internal pipeline
- Lost visibility into AI thinking

### Solution
Separate think tags from content:
- **Think tags** → Display in UI with special formatting
- **Clean content** → Continue through internal pipeline

### New Files

#### `selfai/core/think_parser.py` (NEW)
```python
def parse_think_tags(response: str) -> Tuple[str, list[str]]:
    """Extract <think> tags, return (clean_content, think_list)"""

def parse_think_tags_streaming(chunk: str, buffer: str) -> Tuple[str, str, list[str]]:
    """Handle streaming responses with partial tags"""
```

### Modified Files

#### `selfai/ui/terminal_ui.py`
**Added:**
```python
def show_think_tags(self, think_contents: list[str]) -> None:
    """Display think tags with 💭 blue prefix + cyan indented text"""
```

#### `selfai/core/minimax_interface.py`
**Added:**
- Import `think_parser`
- `ui` parameter to constructor
- Parse and display think tags in `generate_response()`

#### `selfai/core/planner_minimax_interface.py`
**Changed:**
- Import `think_parser`
- `ui` parameter to constructor
- Parse and display think tags in `_parse_plan()`

#### `selfai/core/merge_minimax_interface.py`
**Added:**
- Import `think_parser`
- `ui` parameter to constructor
- Parse and display think tags in `chat()`

#### `selfai/selfai.py`
**Updated interface instantiations to pass `ui`:**
- Line 693: `MinimaxInterface(..., ui=ui)`
- Line 1212: `PlannerMinimaxInterface(..., ui=ui)`
- Line 1278: `MergeMinimaxInterface(..., ui=ui)`

### Documentation

**`THINK_TAG_PARSING_GUIDE.md`** (NEW)
- Complete guide with examples
- Flow diagrams
- Before/after comparisons
- Troubleshooting section

### Benefits
- ✅ Clean responses for memory/tools
- ✅ Visible thinking process in UI
- ✅ Better debugging (see AI reasoning)
- ✅ SelfAI transparency philosophy

---

## 2. Gemini Judge Debugging 🔍

### Problem
Gemini Judge failures showed only "Judge konnte nicht ausgeführt werden" with:
- ❌ No error details
- ❌ No root cause
- ❌ Silent failures
- ❌ Impossible to debug

### Solution
Comprehensive error reporting and diagnostic tools

### Modified Files

#### `selfai/core/gemini_judge.py`
**Enhanced `_check_availability()`:**
```python
# DEBUG: Print detailed output
print(f"\n🔍 Gemini CLI Check:")
print(f"   Command: {self.cli_path} --help")
print(f"   Return code: {result.returncode}")
print(f"   STDOUT: {result.stdout[:200]}")
print(f"   STDERR: {result.stderr[:200]}")
```

**Enhanced `evaluate_task()`:**
```python
print(f"\n🔍 Gemini Judge Evaluation Debug:")
print(f"   Prompt length: {len(full_prompt)} chars")
print(f"   CLI path: {self.cli_path}")
# ... after subprocess.run:
print(f"   Return code: {result.returncode}")
print(f"   STDOUT length: {len(result.stdout)} chars")
print(f"   STDERR length: {len(result.stderr)} chars")
print(f"   Raw output (first 300 chars):\n   {gemini_output[:300]}")
```

**Better error messages:**
- FileNotFoundError → Installation instructions
- TimeoutExpired → "may be hanging" hint
- All exceptions → Type + Message + Traceback

**Fixed subprocess bug:**
```python
# BEFORE (BROKEN):
result = subprocess.run(
    [self.cli_path],
    input=full_prompt,
    capture_output=True,  # ← Conflict!
    stderr=subprocess.PIPE  # ← Can't use both!
)

# AFTER (FIXED):
result = subprocess.run(
    [self.cli_path],
    input=full_prompt,
    stdout=subprocess.PIPE,  # ← Explicit
    stderr=subprocess.PIPE,  # ← Explicit
    text=True,
    timeout=30
)
```

#### `selfai/selfai.py`
**Enhanced exception handling (Line 2333-2348):**
```python
except ImportError as e:
    ui.status("⚠️ Gemini Judge nicht verfügbar (Import fehlgeschlagen)", "warning")
    ui.status(f"   Fehler: {e}", "info")
    ui.status("   Tipp: pip install google-generativeai", "info")
except RuntimeError as e:
    ui.status("⚠️ Gemini Judge nicht verfügbar (CLI-Problem)", "warning")
    ui.status(f"   Details siehe oben in Debug-Output", "info")
except Exception as judge_error:
    ui.status(f"⚠️ Gemini Judge unerwarteter Fehler:", "error")
    # ... full traceback display ...
```

### New Files

#### `scripts/diagnose_gemini_judge.py` (NEW)
**Automated diagnostic tool with 6 tests:**

1. ✅ `check_gemini_cli_installed()` - Is gemini in PATH?
2. ✅ `check_gemini_cli_version()` - Does `--help` work?
3. ✅ `test_gemini_one_shot()` - Can it accept piped input?
4. ✅ `test_gemini_json_response()` - Can it return JSON?
5. ℹ️ `check_api_key()` - Is GEMINI_API_KEY set?
6. ✅ `test_gemini_judge_import()` - Can GeminiJudge be imported?

**Usage:**
```bash
python scripts/diagnose_gemini_judge.py

# Output:
✅ ALL TESTS PASSED - Gemini Judge should work!
# or
❌ SOME TESTS FAILED - See details above
```

### Documentation

**`GEMINI_JUDGE_TROUBLESHOOTING.md`** (NEW)
- Complete troubleshooting guide
- 6 common issues with solutions
- Debug workflow (4-step process)
- Before/after comparison
- Manual testing procedures
- Configuration options

### Benefits
- ✅ Detailed error reports
- ✅ Automated diagnostics
- ✅ Clear solutions for each issue
- ✅ No more silent failures

---

## 3. YOLO Mode 🚀

### Problem
Multiple manual confirmations slow down workflow:
- Plan confirmation
- Execution confirmation
- Merge provider selection

### Solution
**YOLO Mode** = Auto-accept everything!

### Modified Files

#### `selfai/ui/terminal_ui.py`

**Added:**
```python
def __init__(self):
    ...
    self._yolo_mode = False  # NEW

def enable_yolo_mode(self):
    self._yolo_mode = True
    self.status("🚀 YOLO MODE ACTIVATED - Auto-accepting all prompts!", "warning")

def disable_yolo_mode(self):
    self._yolo_mode = False
    self.status("🛑 YOLO MODE DEACTIVATED", "info")

def is_yolo_mode(self) -> bool:
    return self._yolo_mode
```

**Modified `_confirm()`:**
```python
def _confirm(self, prompt: str, default_yes: bool = False) -> bool:
    if self._yolo_mode:
        suffix = "Y/n" if default_yes else "y/N"
        print(f"{prompt} ({suffix}): y (YOLO)")
        return True
    # Normal flow...
```

**Modified `choose_option()`:**
```python
def choose_option(self, prompt, options, default_index=None) -> int:
    if self._yolo_mode:
        chosen_idx = default_index if default_index is not None else 0
        # Display with ← YOLO marker
        print(f"{prompt}: {chosen_idx + 1} (YOLO)")
        return chosen_idx
    # Normal flow...
```

#### `selfai/selfai.py`

**Added command (Line 1512-1518):**
```python
if user_input.lower() == '/yolo':
    if ui.is_yolo_mode():
        ui.disable_yolo_mode()
    else:
        ui.enable_yolo_mode()
    continue
```

**Updated command hint (Line 1365):**
```python
command_hint += "'/yolo' für Auto-Accept Modus, "
```

### Documentation

**`YOLO_MODE_GUIDE.md`** (NEW)
- Complete guide with examples
- Use cases (prototyping, batch ops, CI/CD)
- Safety considerations
- Technical details
- FAQ

### Benefits
- ✅ Zero manual confirmations
- ✅ Fast workflow
- ✅ Perfect for automation
- ✅ Toggle on/off easily

### Example
```bash
/yolo

Plan übernehmen? (y/N): y (YOLO)
Plan jetzt ausführen? (y/N): y (YOLO)
Choose merge provider [1-2]: 1 (YOLO)

# All auto-accepted!
```

---

## 4. UI Design System 🎨

### Problem
Inconsistent UI:
- Mixed formatting styles
- No clear hierarchy
- Ad-hoc `print()` statements
- Hard to maintain

### Solution
Comprehensive design system with 5 levels

### Visual Hierarchy

```
LEVEL 1: SYSTEM HEADERS (Magenta bold, ═══)
  - Banner, major sections

LEVEL 2: SUBSECTIONS (Blue bold, ───)
  - Tool categories, agent lists

LEVEL 3: PRIMARY CONTENT (White/default)
  - LLM output, execution results

LEVEL 4: SECONDARY CONTENT (Cyan dimmed, indented)
  - Descriptions, tool details, think tags

LEVEL 5: META/DEBUG (Semantic colors, emoji)
  - Status messages, debug output
```

### Documentation

**`UI_DESIGN_SYSTEM.md`** (NEW)
- Complete design patterns
- Color palette
- Spacing rules
- Implementation plan
- Usage examples
- Migration strategy

### Status
📋 **Designed, not yet implemented**
- Documentation complete
- Ready for Phase 2 implementation

### Benefits (When Implemented)
- ✅ Consistent visual hierarchy
- ✅ Clear distinction between content types
- ✅ Better readability
- ✅ Easy to maintain

---

## 5. Self-Improvement V2 💡

### Problem with V1
**`/selfimprove`** does everything at once:
- ❌ No control over which improvements
- ❌ All-or-nothing execution
- ❌ Can't review individual changes

### Solution: Analysis + Implementation Split

### New Design

**Phase 1: `/selfimprove <ziel>` - ANALYSIS ONLY**
- ✅ Analyzes code
- ✅ Creates improvement suggestions
- ✅ Shows formatted list with IDs
- ❌ **DOES NOT EXECUTE!**

**Phase 2: `/selfimplement <IDs>` - EXECUTION**
- ✅ User selects IDs: `1,3,5`
- ✅ Creates plan for selected improvements
- ✅ Executes only chosen improvements

### New Files

#### `selfai/core/improvement_suggestions.py` (NEW)

**Data structures:**
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
    implementation_plan: str

class ImprovementSuggestionsManager:
    def __init__(self):
        self.suggestions: List[ImprovementSuggestion] = []

    def add_suggestion(self, suggestion)
    def get_suggestions_by_ids(self, ids: List[int])
    def save_to_file(self, filepath: Path)
    def load_from_file(self, filepath: Path)
```

**Utilities:**
```python
def parse_suggestions_from_analysis(analysis_text: str, goal: str)
    """Parse LLM output into structured suggestions"""

def format_suggestions_for_display(suggestions: List[ImprovementSuggestion])
    """Format for beautiful terminal display"""
```

### Modified Files

#### `selfai/selfai.py`

**Added imports (Line 39-44):**
```python
from selfai.core.improvement_suggestions import (
    ImprovementSuggestionsManager,
    ImprovementSuggestion,
    parse_suggestions_from_analysis,
    format_suggestions_for_display,
)
```

**New function signatures:**
```python
def _handle_selfimprove_analysis(
    goal: str,
    suggestions_manager: ImprovementSuggestionsManager,
    ...
) -> None:
    """ANALYSIS ONLY - creates suggestions, no execution"""

def _handle_selfimplement(
    ids_str: str,
    suggestions_manager: ImprovementSuggestionsManager,
    ...
) -> None:
    """EXECUTION - implements selected improvements"""
```

### Documentation

**`SELFIMPROVE_V2_GUIDE.md`** (NEW)
- Complete V2 design
- Comparison V1 vs V2
- Example sessions
- Implementation details
- Future enhancements

### Status
📋 **Designed, partially implemented**
- Data structures: ✅ Complete
- `/selfimprove` refactor: ⏳ In progress
- `/selfimplement` command: ⏳ Not started
- Documentation: ✅ Complete

### Benefits (When Complete)
- ✅ Full user control
- ✅ Review before implementation
- ✅ Selective execution
- ✅ Safer (no auto-execution)
- ✅ Git commit per improvement

### Example Workflow
```bash
You: /selfimprove Optimize performance

[Shows list of 5 suggestions with IDs]

You: /selfimplement 1,3

Erstelle Plan für 2 Verbesserungen:
  [1] Optimize context loading
  [3] Add caching

[Creates plan for only these 2]

Plan übernehmen? (y/N): y
Plan jetzt ausführen? (y/N): y

[Implements only selected improvements]
```

---

## 6. Token Limits Control ⚙️

### Previous Session (Already Implemented)
Not part of this session, but documented here for completeness:

- ✅ `/tokens` command - Show/set limits
- ✅ `/extreme` command - 64K limits
- ✅ Runtime configuration
- ✅ Multiple profiles (conservative, balanced, generous, extreme)
- ✅ Documentation: `TOKEN_LIMITS_GUIDE.md`

---

## 7. Context Window Management 📅

### Previous Session (Already Implemented)
Not part of this session, but documented here for completeness:

- ✅ `/context` command - Control window size
- ✅ `/context reset` - Clear context
- ✅ `/context unlimited` - Disable time filter
- ✅ Time-based filtering (default 30 min)
- ✅ Session tracking
- ✅ Documentation: `CONTEXT_WINDOW_GUIDE.md`

---

## Summary of Changes

### New Files Created (9)

1. `selfai/core/think_parser.py` - Think tag parsing
2. `selfai/core/improvement_suggestions.py` - Suggestions manager
3. `scripts/diagnose_gemini_judge.py` - Diagnostic tool
4. `THINK_TAG_PARSING_GUIDE.md` - Think tags docs
5. `GEMINI_JUDGE_TROUBLESHOOTING.md` - Judge debugging docs
6. `YOLO_MODE_GUIDE.md` - YOLO mode docs
7. `UI_DESIGN_SYSTEM.md` - UI design docs
8. `SELFIMPROVE_V2_GUIDE.md` - Self-improvement V2 docs
9. `SESSION_CHANGES_2025-01-20.md` - This file

### Files Modified (7)

1. `selfai/ui/terminal_ui.py` - Think tags, YOLO mode
2. `selfai/core/minimax_interface.py` - Think tag parsing
3. `selfai/core/planner_minimax_interface.py` - Think tag parsing
4. `selfai/core/merge_minimax_interface.py` - Think tag parsing
5. `selfai/core/gemini_judge.py` - Enhanced error reporting
6. `selfai/selfai.py` - YOLO command, imports, judge error handling
7. `__pycache__` - Cleared bytecode cache (bugfix)

### Features Added

✅ **Think Tag Parsing** - Separate AI reasoning from content
✅ **Gemini Judge Debugging** - Comprehensive error reports
✅ **YOLO Mode** - Auto-accept all prompts
✅ **UI Design System** - Visual hierarchy (designed)
✅ **Self-Improvement V2** - Analysis + Implementation split (in progress)

### Lines of Code

- **New:** ~2,500 lines (code + docs)
- **Modified:** ~200 lines
- **Documentation:** ~5,000 lines

### Bugs Fixed

1. ✅ **Gemini Judge subprocess bug** - `capture_output` + `stderr` conflict
2. ✅ **Python bytecode cache** - Cleared stale `.pyc` files
3. ✅ **Context pollution** - (Previous session, documented here)

---

## Testing Checklist

### Think Tag Parsing ✅
- [x] Tags extracted correctly
- [x] UI displays think tags
- [x] Clean content continues to pipeline
- [x] Works in all interfaces (minimax, planner, merge)

### Gemini Judge Debugging ✅
- [x] Diagnostic script passes all tests
- [x] Error messages show details
- [x] subprocess bug fixed
- [x] Judge works after bytecode cache clear

### YOLO Mode ✅
- [x] Toggle on/off with `/yolo`
- [x] Auto-accepts confirmations
- [x] Auto-selects first option
- [x] Shows "(YOLO)" indicator

### UI Design System ⏳
- [ ] Not yet implemented (designed only)

### Self-Improvement V2 ⏳
- [ ] In progress
- [x] Data structures complete
- [x] Suggestion parsing works
- [ ] `/selfimprove` refactored to analysis-only
- [ ] `/selfimplement` command created

---

## Next Steps

### Priority 1: Complete Self-Improvement V2
1. Refactor `_handle_selfimprove()` to analysis-only
2. Create `_handle_selfimplement()` command
3. Test full workflow
4. Update command hints

### Priority 2: Implement UI Design System
1. Add new methods to `TerminalUI`
2. Update high-impact areas (plan display, tools)
3. Migrate existing code
4. Test consistency

### Priority 3: Enhanced Features
1. Persistent improvement suggestions (save/load from file)
2. `/selfimplement batch` mode
3. Suggestion review feature
4. Export to markdown

---

## User Impact

### Positive Changes
- ✅ **Better Transparency** - See AI thinking process
- ✅ **Better Debugging** - Clear error messages
- ✅ **Better Speed** - YOLO mode for automation
- ✅ **Better Control** - Choose what to implement (V2)
- ✅ **Better Consistency** - UI design system (when done)

### Breaking Changes
- ❌ None! All changes are backward compatible
- `/selfimprove` will change behavior (V1 → V2) but not yet deployed

### Migration Required
- None - all features are additive

---

## Philosophy Alignment

All changes align with **SelfAI's core philosophy:**

1. **Transparency** ✅
   - Think tags visible
   - Full error reports
   - No blackbox behavior

2. **User Control** ✅
   - YOLO mode optional
   - Choose improvements to implement
   - No auto-execution

3. **Self-Improvement** ✅
   - Analyzing own code
   - Suggesting improvements
   - Tools to modify itself

4. **Not a Blackbox** ✅
   - All token limits visible
   - All context windows configurable
   - All decisions transparent

**SelfAI: Transparent, Controllable, Self-Improving!** 🚀

---

## Related Documentation

- `THINK_TAG_PARSING_GUIDE.md` - Think tags complete guide
- `GEMINI_JUDGE_TROUBLESHOOTING.md` - Judge debugging
- `YOLO_MODE_GUIDE.md` - YOLO mode usage
- `UI_DESIGN_SYSTEM.md` - UI patterns
- `SELFIMPROVE_V2_GUIDE.md` - Self-improvement V2
- `TOKEN_LIMITS_GUIDE.md` - Token control (previous)
- `CONTEXT_WINDOW_GUIDE.md` - Context management (previous)
- `INTERNAL_COMMUNICATION.md` - Architecture (previous)

---

**Session Date:** 2025-01-20
**Total Changes:** 9 new files, 7 modified files, ~7,500 lines
**Status:** Mostly complete (Self-Improvement V2 in progress)
**Next Session:** Complete V2, implement UI design system

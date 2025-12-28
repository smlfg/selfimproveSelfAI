# SelfAI UI Design System

## Current UI Categories (Analyzed)

### 1. **Status Messages** (`status()`)
- **Types:** info, success, warning, error
- **Current:** Emoji + colored text
- **Used for:** System feedback, operations status

### 2. **Headers/Sections**
- **Current:** Bold text, colored separators
- **Used for:** Section titles, plan displays, tool lists

### 3. **LLM Output**
- **Current:** `stream_prefix()` + plain text
- **Used for:** AI responses, streaming output

### 4. **Think Tags** (`show_think_tags()`)
- **Current:** 💭 blue prefix + cyan indented text
- **Used for:** LLM reasoning process

### 5. **Tools/Lists**
- **Current:** Category headers (magenta) + bullet points (cyan)
- **Used for:** Tool listings, agent listings

### 6. **Commands/Prompts**
- **Current:** Yellow text for input prompts
- **Used for:** User confirmations, option selection

### 7. **Separators/Spacing**
- **Current:** Colored lines (─), manual `\n`
- **Used for:** Visual structure

### 8. **Descriptions/Explanations**
- **Current:** Cyan text, plain text
- **Used for:** Agent descriptions, tool descriptions

### 9. **Debug Output**
- **Current:** 🔍 prefix + structured info
- **Used for:** Error reports, diagnostics

---

## Proposed Design System

### Visual Hierarchy (5 Levels)

```
┌─────────────────────────────────────────────────────────────┐
│                  LEVEL 1: SYSTEM HEADERS                    │
│  - Banner, Major sections (PLAN, EXECUTION, MERGE)          │
│  - Color: Magenta/Cyan bold                                 │
│  - Separator: ═══ (double line)                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  LEVEL 2: SUBSECTIONS                       │
│  - Tool categories, Agent lists, Think tags                 │
│  - Color: Blue/Cyan bold                                    │
│  - Separator: ─── (single line)                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  LEVEL 3: PRIMARY CONTENT                   │
│  - LLM output, Execution results                            │
│  - Color: White/default (no color for readability)          │
│  - Prefix: "SelfAI [Backend]:"                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  LEVEL 4: SECONDARY CONTENT                 │
│  - Descriptions, Tool details, Think content                │
│  - Color: Cyan (dimmed), Indented                           │
│  - Prefix: "  •" or indentation                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  LEVEL 5: META/DEBUG                        │
│  - Status messages, Debug output, Errors                    │
│  - Color: Semantic (green/yellow/red)                       │
│  - Prefix: Emoji (ℹ️ ✅ ⚠️ ❌ 🔍)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Patterns

### Pattern 1: System Header
```
════════════════════════════════════════════════════════════
  🚀 SECTION NAME (MAGENTA BOLD)
════════════════════════════════════════════════════════════
```

### Pattern 2: Subsection
```
────────────────────────────────────────
📦 Subsection Name (Blue Bold)
────────────────────────────────────────
```

### Pattern 3: LLM Output
```
SelfAI [MiniMax]: <white text, no color>
This is the actual response from the AI.
It should be easy to read without colors.
```

### Pattern 4: Think Tags (Special)
```
💭 [Thinking 1] (Blue)
  <cyan dimmed, indented>
  This is the reasoning process
  Multi-line support
```

### Pattern 5: List Items
```
  • Item name (Cyan)
    Description text (default/dimmed)
```

### Pattern 6: Status Messages
```
✅ Success message (Green)
⚠️  Warning message (Yellow)
❌ Error message (Red)
ℹ️  Info message (Cyan)
🔍 Debug message (Blue)
```

### Pattern 7: Prompts/Input
```
❓ Question text? (Yellow)
   1. Option A (Cyan)
   2. Option B (Cyan)
   Choose [1-2]: _
```

---

## Color Palette

### Semantic Colors
- **Success:** Green (`\033[92m`)
- **Warning:** Yellow (`\033[93m`)
- **Error:** Red (`\033[91m`)
- **Info:** Cyan (`\033[96m`)

### Hierarchy Colors
- **Level 1 Headers:** Magenta (`\033[95m`) + Bold
- **Level 2 Headers:** Blue (`\033[94m`) + Bold
- **Level 3 Content:** Default/White (no color)
- **Level 4 Secondary:** Cyan (`\033[96m`) dimmed
- **Level 5 Meta:** Semantic colors

### Special Elements
- **Think Tags:** Blue header, Cyan content
- **Separators:** Cyan
- **Prompts:** Yellow
- **Highlights:** Magenta

---

## Spacing Rules

### Vertical Spacing

```python
# Between major sections (Level 1)
print("\n\n")  # 2 blank lines

# Between subsections (Level 2)
print("\n")    # 1 blank line

# Between list items
print()        # No extra space (natural flow)

# After think tags
print()        # 1 blank line (already implemented)
```

### Horizontal Spacing

```python
# Indentation levels
INDENT_0 = ""          # Headers, main content
INDENT_1 = "  "        # Subsections, list items
INDENT_2 = "    "      # Descriptions, nested content
INDENT_3 = "      "    # Deep nesting (rare)
```

---

## Implementation Plan

### New Methods to Add

```python
class TerminalUI:
    # Spacing constants
    INDENT_1 = "  "
    INDENT_2 = "    "
    INDENT_3 = "      "

    # Separator styles
    SEPARATOR_HEAVY = "═" * 60  # Level 1
    SEPARATOR_LIGHT = "─" * 60  # Level 2
    SEPARATOR_THIN = "·" * 60   # Level 3 (optional)

    def section_header(self, title: str, emoji: str = ""):
        """Level 1 header with heavy separator"""

    def subsection_header(self, title: str, emoji: str = ""):
        """Level 2 header with light separator"""

    def llm_output_start(self, backend_label: str = ""):
        """Start LLM output block (Level 3)"""

    def description(self, text: str, indent: int = 1):
        """Dimmed description text (Level 4)"""

    def debug(self, message: str, data: dict = None):
        """Debug output with structured data (Level 5)"""

    def list_item(self, name: str, description: str = "", indent: int = 1):
        """Formatted list item with optional description"""

    def vertical_space(self, lines: int = 1):
        """Consistent vertical spacing"""
```

---

## Usage Examples

### Example 1: Plan Display

**Before:**
```python
print(self.colorize("\nGeplanter Ablauf (DPPM):", "bold"))
formatted = json.dumps(plan, indent=2, ensure_ascii=False)
print(formatted)
```

**After:**
```python
ui.section_header("GEPLANTER ABLAUF (DPPM)", "📋")
ui.vertical_space(1)
formatted = json.dumps(plan, indent=2, ensure_ascii=False)
ui.llm_output(formatted)  # Or specialized plan formatter
```

### Example 2: Tool List

**Before:**
```python
print(self.colorize("\n📦 Verfügbare Tools:", "bold"))
print(self.colorize("─" * 60, "cyan"))
# ... tools ...
print(self.colorize("\n" + "─" * 60, "cyan"))
```

**After:**
```python
ui.subsection_header("Verfügbare Tools", "📦")
for tool in tools:
    ui.list_item(
        name=tool["name"],
        description=tool["description"],
        indent=1
    )
ui.subsection_footer()  # Closes with separator
```

### Example 3: LLM Response

**Before:**
```python
prefix = self.colorize("SelfAI", "magenta")
backend_text = f"[{backend_label}]" if backend_label else ""
print(f"{prefix} {backend_text}: ", end="", flush=True)
```

**After:**
```python
ui.llm_output_start(backend_label="MiniMax")
# Then stream content (no color!)
for chunk in stream:
    ui.streaming_chunk(chunk)
ui.llm_output_end()
```

### Example 4: Status Messages (Already Good!)

```python
# Current implementation is already clean:
ui.status("Operation successful", "success")  # ✅ Green
ui.status("Check this", "warning")            # ⚠️  Yellow
ui.status("Failed!", "error")                 # ❌ Red
ui.status("Processing...", "info")            # ℹ️  Cyan
```

### Example 5: Think Tags (Already Good!)

```python
# Current implementation is already clean:
ui.show_think_tags(think_contents)

# Output:
# 💭 [Thinking 1] (Blue)
#   <cyan indented text>
```

---

## Migration Strategy

### Phase 1: Add New Methods (Don't Break Existing)
- Implement all new methods in `terminal_ui.py`
- Keep existing methods working
- No breaking changes

### Phase 2: Update High-Impact Areas
- Plan display (`show_plan()`)
- Tool listing (`show_available_tools()`)
- Agent listing (`list_agents()`)
- LLM output (`stream_prefix()`, `streaming_chunk()`)

### Phase 3: Update Remaining Areas
- All `ui.status()` calls (check consistency)
- All separator usage
- All spacing

### Phase 4: Deprecate Old Patterns
- Mark old methods as deprecated
- Add warnings if using inconsistent patterns

---

## Benefits

### 1. **Consistency**
- Every type of content has ONE correct way to display
- No more ad-hoc `print()` statements

### 2. **Readability**
- Clear visual hierarchy
- LLM output easily distinguished from system messages
- Think tags visually separate from main content

### 3. **Maintainability**
- Centralized styling
- Easy to change design globally
- Clear documentation of patterns

### 4. **Accessibility**
- Semantic colors (green=success, red=error)
- Works without color (text-only fallback)
- Screen reader friendly (emoji labels)

---

## Open Questions

1. **LLM Output Color?**
   - Option A: No color (pure white) for max readability
   - Option B: Very light cyan for distinction
   - **Recommendation:** No color - easier to read

2. **Separator Characters?**
   - Option A: Unicode box drawing (═ ─ │)
   - Option B: ASCII fallback (= - |)
   - **Recommendation:** Unicode with ASCII fallback

3. **Indentation Width?**
   - Current: 2 spaces
   - Alternative: 4 spaces (more visual)
   - **Recommendation:** Keep 2 spaces (terminal width limited)

4. **Debug Output Always Visible?**
   - Option A: Always show (current)
   - Option B: Only with `--debug` flag
   - Option C: Collapsible sections
   - **Recommendation:** Add `--debug` flag, hide by default in production

---

## Next Steps

1. ✅ Create this design document
2. ⏳ Implement new methods in `terminal_ui.py`
3. ⏳ Update `show_plan()` as proof-of-concept
4. ⏳ Update `show_available_tools()`
5. ⏳ Update LLM output streaming
6. ⏳ Document all changes
7. ⏳ Test in real usage

---

**Goal:** Professional, consistent, readable UI that makes SelfAI a joy to use! 🎨

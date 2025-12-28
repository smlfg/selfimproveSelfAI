# SelfAI Think Tag Parsing

## Problem Statement

**User Request (Original German):**
> "oft wenn ich mit selfai arbeite kommen die <think> tokens in den weg, können wir das so parsen( egrep -n bsp) die thinktags kommen ins Ui, der rest geht weiter in der internen kommuniktionspipline"

**Translation:**
> "often when working with SelfAI, the <think> tokens get in the way, can we parse them (like egrep -n example) - the think tags come into the UI, the rest continues through the internal communication pipeline"

### The Issue

When LLM models generate responses, they often include `<think>...</think>` tags to show their reasoning process. This creates two problems:

1. **Interference with workflow**: The think tags clutter the actual response content
2. **Lost visibility**: The thinking process is valuable but gets mixed with the final answer

### The Solution

**Separate think tags from content:**
- **Think tags** → Display in UI with special formatting (💭 blue, indented)
- **Clean content** → Continue through internal communication pipeline

---

## Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Response (Raw)                       │
│  "Let me analyze <think>checking requirements...</think>   │
│   this problem. <think>considering options</think> Here's   │
│   my solution."                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  parse_think_tags()   │
         │  (think_parser.py)    │
         └──────┬────────┬───────┘
                │        │
       ┌────────┘        └────────┐
       │                          │
       ▼                          ▼
┌──────────────┐          ┌──────────────────┐
│ Think Tags   │          │ Clean Content    │
│ ["checking   │          │ "Let me analyze  │
│  requirements│          │  this problem.   │
│  ...",       │          │  Here's my       │
│  "considering│          │  solution."      │
│  options"]   │          │                  │
└──────┬───────┘          └────────┬─────────┘
       │                           │
       ▼                           ▼
┌──────────────────┐      ┌───────────────────┐
│ UI Display       │      │ Internal Pipeline │
│ show_think_tags()│      │ (Memory, Tools,   │
│                  │      │  Execution, etc.) │
│ 💭 [Thinking 1]  │      │                   │
│   checking req...│      │ Clean content     │
│ 💭 [Thinking 2]  │      │ used for:         │
│   considering... │      │ - Memory save     │
└──────────────────┘      │ - Tool calls      │
                          │ - Plan execution  │
                          │ - Merge synthesis │
                          └───────────────────┘
```

---

## Implementation

### 1. Core Parser Module: `think_parser.py`

**Location:** `selfai/core/think_parser.py`

**Key Functions:**

#### `parse_think_tags(response: str) -> Tuple[str, list[str]]`

Parses and removes `<think>...</think>` tags from LLM responses.

**Input:**
```python
response = "Let me <think>analyzing...</think> answer this. <think>considering</think> Done."
```

**Output:**
```python
clean_response = "Let me answer this. Done."
think_contents = ["analyzing...", "considering"]
```

**Features:**
- Case-insensitive matching (`<think>`, `<Think>`, `<THINK>`)
- Multiline support (think tags can span multiple lines)
- Cleans up extra spaces/newlines created by removal

#### `parse_think_tags_streaming(chunk: str, buffer: str) -> Tuple[str, str, list[str]]`

Handles streaming responses where think tags might span multiple chunks.

**Purpose:** Prevent partial think tags from appearing in output during streaming.

**Example:**
```python
# Chunk 1: "Let me <thi"
# Chunk 2: "nk>analyzing</think> answer"
# Buffer accumulates until complete tags are found
```

**Usage:**
```python
buffer = ""
for chunk in stream:
    clean_chunk, buffer, thinks = parse_think_tags_streaming(chunk, buffer)
    if clean_chunk:
        display(clean_chunk)  # Safe to display
    if thinks:
        ui.show_think_tags(thinks)  # Complete thinks
```

### 2. UI Display: `terminal_ui.py`

**Location:** `selfai/ui/terminal_ui.py`

**New Method:** `show_think_tags(think_contents: list[str])`

**Display Format:**
```
💭 [Thinking 1]
  analyzing the requirements...
  checking constraints...

💭 [Thinking 2]
  considering option A vs B
```

**Features:**
- 💭 emoji prefix
- Blue color (uses `self.colorize(..., "blue")`)
- Indented content (2 spaces)
- Cyan text for readability
- Numbered if multiple thinks
- Extra line after all thinks

### 3. Integration Points

#### A. MinimaxInterface (`minimax_interface.py`)

**Changes:**
```python
# Constructor
def __init__(self, ..., ui=None):
    self.ui = ui  # Optional UI for displaying think tags

# generate_response()
raw_content = result["choices"][0]["message"]["content"]

# Parse and display think tags separately
clean_content, think_contents = parse_think_tags(raw_content)
if self.ui and think_contents:
    self.ui.show_think_tags(think_contents)

# Return clean content for internal pipeline
return clean_content
```

#### B. PlannerMinimaxInterface (`planner_minimax_interface.py`)

**Changes:**
```python
# Constructor
def __init__(self, ..., ui=None):
    self.ui = ui  # Optional UI for displaying think tags

# _parse_plan()
# OLD: cleaned = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL)
# NEW:
cleaned, think_contents = parse_think_tags(raw_response)
if self.ui and think_contents:
    self.ui.show_think_tags(think_contents)
```

**Benefits:**
- Planner thinking process visible in UI
- Clean JSON plan for parsing (no think tag interference)

#### C. MergeMinimaxInterface (`merge_minimax_interface.py`)

**Changes:**
```python
# Constructor
def __init__(self, ..., ui=None):
    self.ui = ui  # Optional UI for displaying think tags

# chat()
raw_content = choices[0]["message"]["content"]

# Parse and display think tags separately
clean_content, think_contents = parse_think_tags(raw_content)
if self.ui and think_contents:
    self.ui.show_think_tags(think_contents)

return clean_content
```

**Benefits:**
- Merge thinking process visible
- Clean synthesis for final output

#### D. Main Initialization (`selfai.py`)

**Changes:**
```python
# Pass UI to all interfaces that support think tag parsing

# MiniMax Interface (line 689)
interface = MinimaxInterface(
    ...,
    ui=ui  # Pass UI for think tag display
)

# Planner Interface (line 1206)
interface = PlannerMinimaxInterface(
    ...,
    ui=ui,  # Pass UI for think tag display
)

# Merge Interface (line 1272)
interface = MergeMinimaxInterface(
    ...,
    ui=ui,  # Pass UI for think tag display
)
```

---

## Usage Examples

### Example 1: Normal Chat with Think Tags

**User Input:**
```
You: Explain the difference between async and sync code
```

**LLM Response (Raw):**
```
<think>
Need to explain this clearly.
Should cover:
- Blocking vs non-blocking
- Use cases
- Performance implications
</think>

The main difference between async and sync code is how they handle waiting for operations to complete.

<think>
Good start. Now explain blocking.
</think>

Synchronous code blocks execution while waiting, while asynchronous code can continue with other work.
```

**What User Sees:**

```
💭 [Thinking 1]
  Need to explain this clearly.
  Should cover:
  - Blocking vs non-blocking
  - Use cases
  - Performance implications

💭 [Thinking 2]
  Good start. Now explain blocking.

SelfAI [MiniMax]: The main difference between async and sync code is how they handle waiting for operations to complete.

Synchronous code blocks execution while waiting, while asynchronous code can continue with other work.
```

**What Goes to Memory:**
```
---
User:
Explain the difference between async and sync code
---
SelfAI:
The main difference between async and sync code is how they handle waiting for operations to complete.

Synchronous code blocks execution while waiting, while asynchronous code can continue with other work.
```

**Result:** Think tags visible in UI, but NOT saved to memory!

### Example 2: Planning with Think Tags

**User Input:**
```
You: /plan Build a REST API with authentication
```

**Planner Response (Raw):**
```json
<think>
This requires multiple components:
1. API endpoints
2. Auth middleware
3. Database models
4. Tests
Let me create parallel subtasks.
</think>

{
  "subtasks": [
    {
      "id": "S1",
      "title": "Design API endpoints",
      ...
    },
    ...
  ]
}
```

**What User Sees:**

```
💭 [Thinking 1]
  This requires multiple components:
  1. API endpoints
  2. Auth middleware
  3. Database models
  4. Tests
  Let me create parallel subtasks.

Geplanter Ablauf (DPPM):
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Design API endpoints",
      ...
    }
  ]
}
```

**Result:** Planner's reasoning process visible, but JSON plan is clean for parsing!

### Example 3: Merge with Think Tags

**Merge Prompt:**
```
Synthesize the results from subtasks S1, S2, S3
```

**Merge Response (Raw):**
```
<think>
S1 analyzed requirements
S2 designed architecture
S3 implemented tests
Need to combine these coherently.
</think>

Based on the analysis from S1, we implemented the architecture from S2, verified by tests from S3. The final solution provides...
```

**What User Sees:**

```
💭 [Thinking 1]
  S1 analyzed requirements
  S2 designed architecture
  S3 implemented tests
  Need to combine these coherently.

SelfAI: Based on the analysis from S1, we implemented the architecture from S2, verified by tests from S3. The final solution provides...
```

**Result:** Merge thinking visible, clean synthesis for final output!

---

## Technical Details

### Regex Pattern

```python
think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL | re.IGNORECASE)
```

**Explanation:**
- `<think>` - Opening tag (case-insensitive)
- `(.*?)` - Content (non-greedy, captured)
- `</think>` - Closing tag (case-insensitive)
- `re.DOTALL` - `.` matches newlines
- `re.IGNORECASE` - Case-insensitive matching

### Cleanup After Removal

```python
# Remove multiple consecutive newlines
clean_response = re.sub(r'\n\n+', '\n\n', clean_response)

# Remove multiple consecutive spaces
clean_response = re.sub(r' {2,}', ' ', clean_response)
```

**Why:** Removing think tags can create awkward spacing. Cleanup ensures natural-looking text.

### Streaming Buffer Management

**Problem:** Think tags might span chunks:
```
Chunk 1: "text <thi"
Chunk 2: "nk>content</think> more"
```

**Solution:** Buffer content until complete tags are found:
```python
buffer += chunk
# Extract completed tags only
completed_pattern.findall(buffer)
# Keep incomplete tags in buffer
```

---

## Benefits

### 1. Improved User Experience
- ✅ Clean responses without tag clutter
- ✅ Visible thinking process (transparency)
- ✅ Easy to distinguish thought from final answer

### 2. Clean Internal Pipeline
- ✅ Memory saves clean content (no tags)
- ✅ Tool calls use clean input
- ✅ Plan execution not confused by tags
- ✅ Merge synthesis uses clean results

### 3. Debugging Support
- ✅ See LLM reasoning process
- ✅ Understand why certain decisions were made
- ✅ Identify if model is "thinking" correctly

### 4. Philosophy Alignment

**User's Original Goal:**
> "SelfAI wie der name schon sagt" (SelfAI as the name suggests)

This feature aligns with SelfAI's philosophy:
- **Transparency:** Show the thinking process
- **Control:** Separate concerns (thinking vs output)
- **Competence:** Clean data flow through pipeline

**NOT a blackbox** (like Claude Code) - user sees everything!

---

## Testing

### Test Case 1: Basic Parsing
```python
from selfai.core.think_parser import parse_think_tags

response = "Answer: <think>reasoning</think> Final answer."
clean, thinks = parse_think_tags(response)

assert clean == "Answer: Final answer."
assert thinks == ["reasoning"]
```

### Test Case 2: Multiple Think Tags
```python
response = "<think>A</think> Text <think>B</think> More <think>C</think>"
clean, thinks = parse_think_tags(response)

assert clean == "Text More"
assert thinks == ["A", "B", "C"]
```

### Test Case 3: Multiline Think Tags
```python
response = """
<think>
Step 1: Analyze
Step 2: Plan
</think>
Final output.
"""
clean, thinks = parse_think_tags(response)

assert "Step 1" in thinks[0]
assert "Step 2" in thinks[0]
assert "Final output." in clean
```

### Test Case 4: No Think Tags
```python
response = "Just normal text here."
clean, thinks = parse_think_tags(response)

assert clean == "Just normal text here."
assert thinks == []
```

### Test Case 5: Case Insensitive
```python
response = "<Think>A</Think> <THINK>B</THINK> <think>C</think>"
clean, thinks = parse_think_tags(response)

assert thinks == ["A", "B", "C"]
```

---

## Troubleshooting

### Issue: Think tags still appearing in output

**Possible Causes:**
1. Interface not passing UI instance
2. UI instance is None
3. Think tags use different format (e.g., `<thinking>`)

**Solution:**
```python
# Check interface initialization
interface = MinimaxInterface(..., ui=ui)  # Make sure ui is passed

# Check UI instance
if self.ui and think_contents:  # Make sure self.ui is not None
    self.ui.show_think_tags(think_contents)

# Check tag format
# Parser only handles <think>...</think> (case-insensitive)
# For other formats, extend the regex pattern
```

### Issue: Think tags not displayed in UI

**Possible Causes:**
1. `show_think_tags()` not called
2. Think contents empty
3. UI color support disabled

**Solution:**
```python
# Debug: Print think contents
clean, thinks = parse_think_tags(response)
print(f"Found {len(thinks)} think tags")  # Should be > 0

# Debug: Check UI call
if self.ui:
    print("UI available")
    if think_contents:
        print(f"Displaying {len(think_contents)} thinks")
        self.ui.show_think_tags(think_contents)
```

### Issue: Incomplete think tags in streaming

**Possible Causes:**
1. Not using `parse_think_tags_streaming()`
2. Buffer not maintained across chunks

**Solution:**
```python
# Correct streaming usage
buffer = ""
for chunk in stream:
    clean_chunk, buffer, completed_thinks = parse_think_tags_streaming(chunk, buffer)

    # Display clean chunk immediately
    if clean_chunk:
        print(clean_chunk, end="", flush=True)

    # Display completed thinks as they arrive
    if completed_thinks:
        ui.show_think_tags(completed_thinks)

# Don't forget remaining buffer at end!
if buffer:
    final_clean, final_thinks = parse_think_tags(buffer)
    if final_clean:
        print(final_clean)
    if final_thinks:
        ui.show_think_tags(final_thinks)
```

---

## Future Enhancements

### 1. Configurable Display
```yaml
# config.yaml
think_tags:
  enabled: true          # Enable/disable parsing
  display_in_ui: true    # Show in UI or just remove
  save_to_memory: false  # Optionally save to memory
  display_style: "blue"  # Color: blue, cyan, grey
```

### 2. Different Tag Formats
Support other thinking tag formats:
- `<thinking>...</thinking>`
- `<reasoning>...</reasoning>`
- `<internal>...</internal>`

### 3. Think Tag Analysis
```python
# Analyze quality of thinking process
def analyze_thinking(think_contents: list[str]) -> dict:
    return {
        "num_steps": len(think_contents),
        "avg_length": sum(len(t) for t in think_contents) / len(think_contents),
        "contains_questions": any("?" in t for t in think_contents),
        "quality_score": calculate_thinking_quality(think_contents)
    }
```

### 4. Think History
Save think tags to separate file for analysis:
```
memory/thinks/
  code_helfer_20250118-150000_thinks.txt
```

### 5. Interactive Think Display
```
💭 [Thinking 1] [Show/Hide]  ← Clickable in terminal
```

---

## Comparison with Other Tools

### Claude Code (Blackbox Approach)
- ❌ No visibility into reasoning
- ❌ Think tags hidden or mixed with output
- ❌ No control over display

### SelfAI (Transparent Approach)
- ✅ Full visibility into reasoning
- ✅ Separate display of thinking vs output
- ✅ Clean data pipeline
- ✅ User control and transparency

**SelfAI Philosophy:** Everything visible, nothing hidden, user in control!

---

## Summary

### Problem
`<think>` tags from LLM responses interfered with workflow and cluttered output.

### Solution
- **Parse** think tags from responses
- **Display** them separately in UI (💭 blue, indented)
- **Pass** clean content through internal pipeline

### Implementation
- Created `think_parser.py` with parsing functions
- Added `show_think_tags()` to `terminal_ui.py`
- Integrated into all MiniMax interfaces
- Updated all interface instantiations to pass UI

### Result
- ✅ Clean responses for internal pipeline
- ✅ Visible thinking process in UI
- ✅ Better user experience
- ✅ Maintains SelfAI's transparency philosophy

**SelfAI Think Tag Parsing: Transparency, Control, Clean Data Flow!** 🚀

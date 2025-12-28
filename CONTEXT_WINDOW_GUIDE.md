# SelfAI Context Window Management

## Problem: Stale Context Pollution

### What Was Happening:

```
Session 1 (14:00):
You: "Erkläre mir RAG"
SelfAI: "RAG ist Retrieval Augmented Generation..."
[saves to memory/code_helfer/code_helfer_20250118-140000.txt]

[NEUSTART 15:30]

Session 2 (15:30):
You: "Wie geht es dir?"
SelfAI: "Bezüglich RAG, das wir vorhin besprochen haben..." ❌

WHY? Old context from 1.5 hours ago was still loaded!
```

### Root Cause:

The `load_relevant_context()` function had NO time filtering:
- Loaded up to 50 most recent files
- Filtered by tag relevance (threshold 0.35)
- If no relevant tags → fallback to newest files **regardless of age**
- Files from hours/days ago would pollute context

## Solution: Time-Based Context Window

### Default Behavior (NEW):

- **Context Window:** 30 minutes (configurable)
- **Session Tracking:** Each restart = new session
- **Time Filter:** Only loads files modified within window
- **Clean Slate:** Old conversations don't leak into new topics

### How It Works:

```python
# memory_system.py
class MemorySystem:
    def __init__(self, memory_dir):
        self.session_start = datetime.now()  # NEW
        self.context_window_minutes = 30     # NEW (configurable)

    def load_relevant_context(...):
        # Filter by time BEFORE tag scoring
        cutoff_time = time.time() - (self.context_window_minutes * 60)
        candidate_files = [
            f for f in candidate_files
            if f.stat().st_mtime >= cutoff_time  # Only recent files!
        ]
```

### Timeline Example:

```
15:00 - Session Start
        context_window_minutes = 30

15:05 - "Erkläre RAG"
        → File created: code_helfer_20250118-150500.txt

15:15 - "Python Basics"
        → File created: code_helfer_20250118-151500.txt

15:35 - "Wie geht es dir?"
        Cutoff: 15:05 (30 min ago)
        ✓ Loads: 151500.txt (20 min old) - IN WINDOW
        ✗ Ignores: 150500.txt (30+ min old) - OUTSIDE WINDOW

        Result: No RAG context! Clean conversation! ✅
```

---

## Commands

### 1. `/context` - Show Current Settings

```bash
/context
```

**Output:**
```
📅 Context Window Settings:
  • Window: 30 Minuten
  • Session Start: 2025-01-18 15:00:00
  • Session Age: 35.2 Minuten

💡 Available commands:
  /context <minutes>  - Set context window (e.g., /context 15)
  /context reset      - Reset session (clear context)
  /context unlimited  - Load all history (no time filter)
```

### 2. `/context <minutes>` - Set Window Size

```bash
/context 15
```

**Effect:**
- Sets context window to 15 minutes
- Only files from last 15 minutes will be loaded
- Immediate effect on next message

**Use Cases:**
- **Short Window (5-15 min):** Quick context switches, debugging
- **Medium Window (30-60 min):** Normal conversation flow (default)
- **Long Window (120-240 min):** Complex multi-hour sessions

**Limits:**
- Minimum: 1 minute
- Maximum: 1440 minutes (24 hours)

### 3. `/context reset` - Clear Context

```bash
/context reset
```

**Effect:**
- Resets session start to NOW
- Clears all previous context
- Next message will have empty history

**Use Cases:**
- Switching topics completely
- RAG discussion → now want to discuss Python
- Clear confusion from previous topic
- Start fresh without restart

**Example:**
```bash
You: "Erkläre RAG im Detail"
SelfAI: [Long RAG explanation...]

You: /context reset
✓ Session reset! Context cleared.

You: "Was ist Python?"
SelfAI: [No RAG context! Clean Python explanation]
```

### 4. `/context unlimited` - Disable Time Filter

```bash
/context unlimited
```

**Effect:**
- Sets window to 99999 minutes (~69 days)
- Loads ALL history regardless of age
- **Warning:** May cause context pollution!

**Use Cases:**
- Need to reference very old conversations
- Long-term project context
- Historical debugging

**Warning:**
```
♾️  Context Window: UNLIMITED (all history loaded)
⚠️  This may cause context pollution! Use /context reset to clear.
```

---

## Best Practices

### 1. Default Window (30 min) - Good for Most Cases

```bash
# No need to change, works well by default
# Covers typical conversation session length
```

### 2. Topic Switching - Use Reset

```bash
You: [Long discussion about RAG...]

You: /context reset  # Clear RAG context
You: "Tell me about Docker"  # Fresh start
```

### 3. Quick Debugging - Short Window

```bash
/context 5  # Only last 5 minutes
# Quickly iterate without old context interfering
```

### 4. Long Sessions - Increase Window

```bash
/context 120  # 2 hours
# Maintain context across longer work sessions
```

### 5. Multi-Hour Projects - But Reset Between Topics

```bash
# Morning: Work on Feature A
/context 60

# Afternoon: Switch to Feature B
/context reset  # Clear Feature A context
/context 60     # New 60-min window for Feature B
```

---

## Technical Details

### File Age Calculation

```python
import time

# Get file modification time
file_mtime = file.stat().st_mtime  # Unix timestamp (seconds)

# Calculate cutoff
cutoff_time = time.time() - (context_window_minutes * 60)

# Filter
if file_mtime >= cutoff_time:
    # File is within window → load it
else:
    # File is too old → ignore it
```

### Session Management

```python
# On SelfAI startup:
memory_system = MemorySystem(memory_dir)
memory_system.session_start = datetime.now()  # Mark session start

# On /context reset:
memory_system.session_start = datetime.now()  # Reset to now

# Files older than session_start + window → ignored
```

### Interaction with Tag Scoring

```python
# 1. Filter by TIME (NEW - first step)
candidate_files = [f for f in files if f.mtime >= cutoff]

# 2. Filter by TAG RELEVANCE (existing logic)
scored_files = [...]
relevant = [f for f in scored_files if f.score >= 0.35]

# Result: Only relevant AND recent files
```

### Memory Persistence

- Context window setting: **Runtime only** (resets on restart)
- Default on startup: **30 minutes**
- Session start: **Always = startup time**
- Files on disk: **Never deleted** (window only affects loading)

---

## Comparison: Before vs After

### Before (Broken):

```
Neustart at 15:30
↓
load_relevant_context()
  ↓ Get 50 newest files (no time filter!)
  ↓ RAG file from 14:00 still in candidates
  ↓ No relevant tags for "Wie geht es dir?"
  ↓ Fallback: Take newest files anyway
  ↓ RAG context loaded! ❌
```

### After (Fixed):

```
Neustart at 15:30
↓
load_relevant_context()
  ↓ Filter by time: cutoff = 15:00 (30 min ago)
  ↓ RAG file from 14:00 → FILTERED OUT ✓
  ↓ Only files from 15:00-15:30 remain
  ↓ Score by tags (clean candidates)
  ↓ No RAG context! ✓
```

---

## FAQ

**Q: Why 30 minutes default?**
A: Covers typical conversation session without being too restrictive.

**Q: What if I need longer context?**
A: Use `/context 120` for 2 hours, or `/context unlimited` for all history.

**Q: Does this delete old files?**
A: No! Files are never deleted. Window only affects what's LOADED.

**Q: Can I make 60 minutes the permanent default?**
A: Not yet, but coming soon in config.yaml support.

**Q: What happens on restart?**
A: Session resets, window resets to 30 min, old context ignored.

**Q: How do I clear context without restart?**
A: Use `/context reset` - instant context clear!

**Q: Can I see which files are in current window?**
A: Not yet, but good feature idea! Coming soon.

**Q: Does this affect plans?**
A: No, plans are separate. This only affects conversation context.

**Q: What about memory commands like `/memory`?**
A: `/memory` shows ALL files. Context window only affects LLM history.

---

## Troubleshooting

### Issue: "SelfAI still references old topic"

**Solution:**
```bash
/context reset  # Clear context immediately
```

### Issue: "Context too short, losing important info"

**Solution:**
```bash
/context 60  # Increase to 1 hour
```

### Issue: "Want to reference conversation from yesterday"

**Solution:**
```bash
/context unlimited  # Load all history
# ... do your lookup ...
/context 30  # Reset to normal after
```

### Issue: "Multiple topics in one session"

**Solution:**
```bash
# Topic 1: RAG discussion
[conversation...]

/context reset  # Clear

# Topic 2: Python discussion
[conversation...]

/context reset  # Clear

# Topic 3: Docker discussion
[conversation...]
```

---

## Summary

### The Problem:
- Old context polluted new conversations
- "RAG" discussion from hours ago leaked into current chat
- No way to clear context except restart

### The Solution:
- ✅ Time-based context window (default 30 min)
- ✅ `/context reset` to clear instantly
- ✅ `/context <minutes>` to adjust window
- ✅ Session tracking from startup
- ✅ Clean slate after restart

### Result:
- 🎯 Focused conversations
- 🧹 Clean context management
- ⚡ Fast topic switching
- 🔒 No cross-contamination

**SelfAI Context: Clear, Controlled, Configurable!** 🚀

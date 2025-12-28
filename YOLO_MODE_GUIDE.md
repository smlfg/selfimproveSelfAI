# YOLO Mode - You Only Live Once 🚀

## Quick Start

```bash
/yolo  # Toggle YOLO mode ON/OFF
```

## What is YOLO Mode?

**YOLO Mode** = Auto-accept everything, no questions asked!

When activated:
- ✅ All confirmations → Automatic "yes"
- ✅ All choices → First option (or default)
- ✅ Plan execution → Immediately starts
- ✅ Merge provider → Always uses first provider

**Use Case:** Speed up workflows when you're confident and don't want to confirm every step.

---

## How It Works

### Before YOLO Mode

```
You: /plan Create a REST API

[Plan is generated]

Plan übernehmen? (y/N): _  ← You must type 'y'

[After accepting]

Plan jetzt ausführen? (y/N): _  ← You must type 'y' again

[If multiple merge providers]

Choose merge provider [1-2]: _  ← You must choose

[Execution starts]
```

**Result:** 3 manual confirmations!

### With YOLO Mode

```
You: /yolo
🚀 YOLO MODE ACTIVATED - Auto-accepting all prompts!

You: /plan Create a REST API

[Plan is generated]

Plan übernehmen? (y/N): y (YOLO)  ← Auto-accepted!

[Immediately starts execution without asking]

Plan jetzt ausführen? (y/N): y (YOLO)  ← Auto-accepted!

[If multiple merge providers]

Choose merge provider [1-2]: 1 (YOLO)  ← Auto-selected first!

[Execution continues automatically]
```

**Result:** Zero manual confirmations! 🚀

---

## Commands

### Activate YOLO Mode

```bash
/yolo
```

**Output:**
```
🚀 YOLO MODE ACTIVATED - Auto-accepting all prompts!
```

### Deactivate YOLO Mode

```bash
/yolo  # Same command toggles ON/OFF
```

**Output:**
```
🛑 YOLO MODE DEACTIVATED
```

### Check Status

YOLO mode status is visible in all prompts:

```
Plan übernehmen? (y/N): y (YOLO)  ← Shows "(YOLO)" when active
```

---

## What Gets Auto-Accepted?

### 1. Plan Confirmation
```python
Plan übernehmen? (y/N): y (YOLO)
```

**Normal:** You must manually confirm
**YOLO:** Auto-accepts plan

### 2. Execution Confirmation
```python
Plan jetzt ausführen? (y/N): y (YOLO)
```

**Normal:** You must manually confirm
**YOLO:** Auto-starts execution

### 3. Multiple Choice (Merge Provider, etc.)
```python
Choose merge provider [1-2]: 1 (YOLO)
```

**Normal:** You must choose provider
**YOLO:** Auto-selects first option (index 0) or default

### 4. Any Generic Confirmation
```python
ui.confirm("Delete file?", default_yes=False)
→ Delete file? (y/N): y (YOLO)
```

**Normal:** You must confirm
**YOLO:** Auto-accepts

---

## Use Cases

### 1. Rapid Prototyping
```bash
/yolo
/plan Create 10 different API endpoints
# Automatically executes without confirmations
```

### 2. Batch Operations
```bash
/yolo
/plan Fix all linting errors in project
# Runs without interruption
```

### 3. Testing Workflows
```bash
/yolo
/plan Test feature X
/plan Test feature Y
/plan Test feature Z
# All execute automatically
```

### 4. CI/CD Integration
```bash
# In automated scripts
echo "/yolo" | selfai
echo "/plan Run full test suite" | selfai
# No human intervention needed
```

---

## Safety Considerations

### ⚠️ When NOT to Use YOLO Mode

**1. Destructive Operations**
```bash
# DON'T:
/yolo
/plan Delete all files in project  # Dangerous!
```

**2. Complex Plans You Haven't Reviewed**
```bash
# DON'T:
/yolo
/plan Refactor entire codebase  # Review first!
```

**3. Production Systems**
```bash
# DON'T:
/yolo
/plan Deploy to production  # Always review!
```

### ✅ When to Use YOLO Mode

**1. Trusted, Well-Tested Workflows**
```bash
/yolo
/plan Run standard test suite  # Safe, routine
```

**2. Development Environment**
```bash
/yolo
/plan Create new feature branch  # Low risk
```

**3. Repetitive Tasks**
```bash
/yolo
/plan Update dependencies  # Can review git diff later
```

---

## Technical Details

### Implementation

**TerminalUI Class:**
```python
class TerminalUI:
    def __init__(self):
        self._yolo_mode = False  # Default: OFF

    def enable_yolo_mode(self):
        self._yolo_mode = True

    def disable_yolo_mode(self):
        self._yolo_mode = False

    def _confirm(self, prompt, default_yes=False):
        if self._yolo_mode:
            # Auto-accept
            print(f"{prompt}: y (YOLO)")
            return True
        # Normal flow
        ...

    def choose_option(self, prompt, options, default_index=None):
        if self._yolo_mode:
            # Auto-select first or default
            chosen = default_index if default_index is not None else 0
            print(f"{prompt}: {chosen + 1} (YOLO)")
            return chosen
        # Normal flow
        ...
```

### Affected Methods

All UI confirmation methods check `self._yolo_mode`:

1. **`_confirm()`** - Base confirmation method
2. **`confirm_plan()`** - Plan acceptance
3. **`confirm_execution()`** - Execution start
4. **`confirm()`** - Generic confirmations
5. **`choose_option()`** - Multiple choice selection

### Session Persistence

**YOLO mode is SESSION-ONLY:**
- Activated with `/yolo` command
- Stays active until:
  - You type `/yolo` again (toggles OFF)
  - SelfAI restarts
- **NOT** saved to config (intentionally for safety)

---

## Examples

### Example 1: Complete Workflow

```bash
$ python selfai/selfai.py

You: /yolo
🚀 YOLO MODE ACTIVATED - Auto-accepting all prompts!

You: /plan Create a simple calculator app

[Plan generated]

Plan übernehmen? (y/N): y (YOLO)

✅ Plan gespeichert

Plan jetzt ausführen? (y/N): y (YOLO)

🚀 Starte Plan-Ausführung...

[Subtasks execute]

[Merge phase]

Choose merge provider [1-2]: 1 (YOLO)

[Merge completes]

✅ Plan erfolgreich abgeschlossen!
```

**Total confirmations:** 0 (all auto-accepted)

### Example 2: Toggle On/Off

```bash
You: /yolo
🚀 YOLO MODE ACTIVATED - Auto-accepting all prompts!

You: /plan Simple task
Plan übernehmen? (y/N): y (YOLO)  ← Auto-accepted

You: /yolo
🛑 YOLO MODE DEACTIVATED

You: /plan Important task
Plan übernehmen? (y/N): _  ← Manual confirmation required
```

---

## Merge Provider Selection

### Why Do We Have Multiple Merge Providers?

**Answer:** Fallback chain for reliability!

**Config Example:**
```yaml
merge:
  enabled: true
  providers:
    - name: "merge-minimax"    # Provider 1 (Primary)
      type: "minimax"
      model: "MiniMax-M2"
      max_tokens: 2048

    - name: "merge-ollama"     # Provider 2 (Fallback)
      type: "local_ollama"
      model: "gemma3:3b"
      max_tokens: 2048
```

**Normal Behavior:**
1. Try Provider 1 (minimax)
2. If fails → Try Provider 2 (ollama)
3. If all fail → Internal SelfAI fallback

**YOLO Mode Behavior:**
- Always uses Provider 1 (index 0)
- If Provider 1 fails → Still falls back to Provider 2 (automatic)
- No manual choice needed

**Benefit:** Speed without sacrificing reliability!

---

## FAQ

**Q: Is YOLO mode dangerous?**
A: Only if you use it carelessly. It's safe for trusted workflows but risky for destructive operations.

**Q: Can I set YOLO mode as default?**
A: No, it's intentionally session-only for safety. You must activate it each time.

**Q: Does YOLO mode skip error handling?**
A: No! YOLO only skips confirmations. Errors are still caught and reported normally.

**Q: What if I want to review plans even in YOLO mode?**
A: Deactivate YOLO mode (`/yolo` again) before running `/plan`.

**Q: Can YOLO mode be used in scripts?**
A: Yes! Perfect for CI/CD pipelines where human interaction isn't possible.

**Q: Does YOLO mode affect tool execution?**
A: No, only UI confirmations. Tool execution follows normal safety checks.

**Q: What about the merge provider choice - why not choose best instead of first?**
A: "First" IS usually the best (primary provider). If it fails, automatic fallback still happens.

---

## Comparison: Normal vs YOLO

| Feature | Normal Mode | YOLO Mode |
|---------|-------------|-----------|
| Plan confirmation | Manual (y/N) | Auto-yes |
| Execution confirmation | Manual (y/N) | Auto-yes |
| Merge provider choice | Manual (1-2) | Auto-first |
| Generic confirmations | Manual | Auto-yes |
| Error handling | Full | Full (unchanged) |
| Safety | High | User responsibility |
| Speed | Slower | Fast 🚀 |
| Use case | Production, critical | Dev, testing, trusted |

---

## Best Practices

### DO ✅

```bash
# 1. Use for trusted, repetitive tasks
/yolo
/plan Run test suite

# 2. Use in development environment
/yolo
/plan Create new component

# 3. Use for CI/CD automation
echo "/yolo" | selfai
echo "/plan Full build pipeline" | selfai

# 4. Toggle off for critical operations
/yolo  # Turn OFF
/plan Deploy to production  # Review carefully
```

### DON'T ❌

```bash
# 1. Don't use for destructive ops
/yolo
/plan Delete entire database  # DANGER!

# 2. Don't use without reviewing plans first
/yolo
/plan Refactor 1000 files  # Review plan first!

# 3. Don't leave YOLO mode on permanently
# Always toggle off after your task

# 4. Don't use on production systems without review
/yolo
/plan Modify prod config  # Too risky!
```

---

## Summary

**YOLO Mode = Speed + Trust**

- ✅ **Activate:** `/yolo`
- ✅ **Auto-accepts:** All confirmations
- ✅ **Auto-selects:** First option in choices
- ✅ **Use case:** Trusted workflows, automation, rapid iteration
- ⚠️ **Caution:** User responsibility for safety

**Perfect for:** Development, testing, automation
**Dangerous for:** Production, destructive operations, unreviewed plans

**Philosophy:** SelfAI trusts you when you say "YOLO"! 🚀

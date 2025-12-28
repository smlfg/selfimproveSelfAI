# 🔧 SelfAI Error Correction System - `/errorcorrection` Command

## Overview

The `/errorcorrection` command enables **SelfAI to analyze its own errors, learn from them, and automatically fix itself**. This creates a self-healing, continuously improving system that gets better with each error encountered.

## 🧠 Core Concept

```
Errors → Analysis → Fix Options → User Choice → Auto-Fix → Learning
   ↓                                                          ↓
   └──────────────────← Knowledge Base ←─────────────────────┘
```

SelfAI maintains a **knowledge base** of successful fixes that improves over time, making future error corrections faster and more accurate.

---

## Usage

### Basic Command

```bash
/errorcorrection
```

### What Happens

```
Step 1: Log Scanning
   🔍 Scans all .log files
   📊 Classifies errors by severity
   📈 Groups similar errors into patterns

Step 2: Error Selection
   Shows top error patterns
   User selects which to fix

Step 3: AI Analysis
   🤖 MiniMax analyzes root cause
   💡 Generates fix options (Quick/Better/Best)
   ⚖️  Estimates complexity & risk

Step 4: User Choice
   User selects preferred fix approach
   Reviews impact and changes

Step 5: Auto-Fix Execution
   🛠️  Creates DPPM plan
   🔨 Executes fix with Aider
   ✅ Validates changes

Step 6: Learning
   💾 Saves successful fix to knowledge base
   📚 Improves future recommendations
```

---

## Example Session

### Full Walkthrough

```bash
Du: /errorcorrection

SelfAI: 🔍 Starting Error Correction System...
        Scanning logs in /memory...

        📊 Error Analysis:
           Total errors: 15
           Unique patterns: 3
           Critical: 0
           Errors: 12
           Warnings: 3

        🔝 Top 3 Error Patterns:

        1. 🟡 AttributeError (8x)
           Location: memory_system.py:456
           Message: 'NoneType' object has no attribute 'load_context'...

        2. 🟡 TimeoutError (4x)
           Location: planner_minimax_interface.py:123
           Message: Request timed out after 60 seconds...

        3. 🟡 KeyError (3x)
           Location: tool_registry.py:234
           Message: 'run_aider_task' not found in registry...

        Which error should I analyze? (Enter number or 'all' or 'skip')

Du: 1

SelfAI: 🔬 Analyzing: AttributeError

        📋 Analysis:
        Root Cause: Missing null-check before accessing object method
        Details: The code attempts to call load_context() on a variable that
        can be None. This happens when memory_system.get_agent() returns None
        for non-existent agents...

        🛠️  Fix Options:

        [A] Quick null-check (5 min)
            Add simple if-check before method call
            Complexity: quick | Risk: 🟢 low
            Files: memory_system.py

        [B] Refactor with Optional type (15 min)
            Improve type hints and add comprehensive null handling
            Complexity: moderate | Risk: 🟡 medium
            Files: memory_system.py, agent_manager.py

        [C] Redesign API contract (30 min)
            Change API to raise exception instead of returning None
            Complexity: complex | Risk: 🔴 high
            Files: memory_system.py, agent_manager.py, 5 other files

        💡 Recommended: Option A

        Select option [A/B/C/Skip]:

Du: B

SelfAI: ✅ Selected: Refactor with Optional type

        Creating DPPM plan...

        PLAN: ErrorFix - AttributeError
        ├─ S1: Analyze error location
        │  └─ Read memory_system.py and agent_manager.py
        ├─ S2: Apply Refactor with Optional type
        │  └─ Add Optional types, null checks, improve error handling
        └─ S3: Validate fix
           └─ Check syntax, run tests

        Execute this fix plan? [Yes/No]:

Du: Yes

SelfAI: Plan saved: 20251217-142800_ErrorFix-AttributeError.json

        ▶️  Executing S1: Analyze error location...
        ✓ Completed

        ▶️  Executing S2: Apply fix...
        🛠️  Running Aider...
        ✓ Changes applied to memory_system.py
        ✓ Changes applied to agent_manager.py

        ▶️  Executing S3: Validate fix...
        ✓ Syntax check passed
        ✓ No new errors introduced

        ✓ Fix plan executed successfully!

        💾 Saved to knowledge base:
           - Fix type: "Refactor with Optional type"
           - Success rate: 100% (1/1 attempts)
           - Future: This fix will be prioritized for similar errors

        ✅ Error Correction completed!
```

---

## Architecture

### Components

#### 1. **Error Analyzer** (`selfai/core/error_analyzer.py`)

```python
class ErrorAnalyzer:
    """
    Scans logs and extracts errors
    - Parses Python tracebacks
    - Classifies by severity
    - Groups similar errors
    - Extracts context (file, line, message)
    """
```

**Features:**
- Multi-format log parsing
- Regex-based traceback extraction
- Smart error grouping by signature
- Severity classification (Critical/Error/Warning/Info)
- Statistical analysis

#### 2. **Fix Generator** (`selfai/core/fix_generator.py`)

```python
class FixGenerator:
    """
    Generates fix strategies using LLM
    - Creates multiple fix options
    - Estimates complexity & risk
    - Generates DPPM plans
    - Tracks success rates
    """
```

**Features:**
- LLM-powered root cause analysis
- Multi-option fix generation (Quick/Better/Best)
- Complexity & risk estimation
- DPPM plan creation
- Historical success tracking

#### 3. **Knowledge Base** (`memory/error_fixes/`)

Stores successful fixes for learning:

```json
{
  "error_type": "AttributeError",
  "fixes": [
    {
      "title": "Add null-check",
      "description": "...",
      "complexity": "quick",
      "total_attempts": 5,
      "successful_attempts": 5,
      "success_rate": 1.0
    }
  ]
}
```

---

## Error Classification

### Severity Levels

| Level | Symbol | Description | Examples |
|-------|--------|-------------|----------|
| **CRITICAL** | 🔴 | System crashes, data loss | MemoryError, SystemExit |
| **ERROR** | 🟡 | Feature broken, exception | AttributeError, KeyError |
| **WARNING** | 🟠 | Potential issues | DeprecationWarning |
| **INFO** | ℹ️  | Informational | Performance warnings |

### Fix Complexity

| Complexity | Time | Description |
|------------|------|-------------|
| **QUICK** | < 5 min | One-liner fix, safe |
| **MODERATE** | 5-15 min | Multiple changes |
| **COMPLEX** | 15-30 min | Refactoring required |
| **MAJOR** | > 30 min | Architectural change |

### Risk Levels

| Risk | Symbol | Description |
|------|--------|-------------|
| **LOW** | 🟢 | Safe, tested pattern |
| **MEDIUM** | 🟡 | Some risk, needs testing |
| **HIGH** | 🔴 | Breaking changes possible |
| **CRITICAL** | ⛔ | Major system impact |

---

## Advanced Features

### 1. **Multi-Error Fixing**

Fix all errors at once:

```bash
Du: /errorcorrection
Choice: all

SelfAI: Analyzing 3 error patterns...
        [Processes each error sequentially]
```

### 2. **Knowledge Base Learning**

SelfAI remembers successful fixes:

```
First time:
  [A] Quick fix (unknown success rate)
  [B] Better fix (unknown success rate)

After 5 successful fixes:
  [A] Quick fix ✅ 100% success (5/5) ⭐ RECOMMENDED
  [B] Better fix ⚠️ 60% success (3/5)
```

### 3. **DPPM Integration**

Error fixes use full DPPM pipeline:
- Planning phase: Analyze error context
- Execution phase: Apply fix with Aider
- Merge phase: Validate and summarize

### 4. **Automatic Prevention**

SelfAI suggests preventive measures:

```
Prevention Suggestions:
  • Add type hints with Optional[]
  • Use mypy for static type checking
  • Add unit tests for edge cases
  • Implement input validation
```

---

## File Structure

```
selfai/
├── core/
│   ├── error_analyzer.py      # Log scanning & error extraction
│   ├── fix_generator.py       # Fix strategy generation
│   └── ...
└── ...

memory/
└── error_fixes/               # Knowledge base
    ├── README.md
    ├── AttributeError.json    # Fix history for this error type
    ├── KeyError.json
    └── TimeoutError.json

Log locations (scanned):
├── memory/*.log               # Primary location
├── selfai.log                 # Main SelfAI log
├── aider.log                  # Aider execution logs
└── *.log                      # Any .log files
```

---

## Configuration

### Log Directory

By default, scans `memory/` directory. Customize in code:

```python
# In selfai.py, line 1532
log_dir = project_root.parent / "memory"
```

### Error Limit

Show top N errors (default 5):

```python
# Line 1555
top_patterns = analyzer.get_top_errors(limit=5)
```

### Fix Timeout

Adjust execution timeout (default 60s):

```python
# Line 1684
llm_timeout=60.0
```

---

## Tips & Best Practices

### ✅ DO

1. **Run regularly** - Weekly error correction sessions
2. **Review fixes** - Always review before applying
3. **Start with Quick fixes** - Low risk, fast results
4. **Use knowledge base** - Trust high success rate fixes
5. **Test after fixes** - Verify no regressions

### ❌ DON'T

1. **Auto-apply CRITICAL risk fixes** - Always review carefully
2. **Fix all errors blindly** - Understand each error first
3. **Ignore prevention suggestions** - They prevent future errors
4. **Skip validation step** - Always verify fixes work
5. **Ignore knowledge base warnings** - Low success rate = risky

---

## Troubleshooting

### No Errors Found

**Cause:** No .log files or no errors in logs

**Solution:**
- Check log directory path
- Verify logs are being created
- Trigger some errors to test

### Fix Execution Failed

**Possible causes:**
- Aider not available
- File permissions
- Syntax errors in generated fix

**Solution:**
- Check Aider installation
- Review error message
- Try simpler fix option

### Knowledge Base Not Learning

**Cause:** Write permissions or JSON errors

**Solution:**
```bash
# Check permissions
ls -la memory/error_fixes/

# Validate JSON files
cat memory/error_fixes/AttributeError.json | jq .
```

---

## Integration with Other Features

### 1. `/selfimprove` Integration

Use error correction as part of self-improvement:

```bash
/selfimprove Eliminate all AttributeErrors
# Automatically triggers /errorcorrection
```

### 2. `/toolcreate` Integration

Create tools to prevent errors:

```bash
# After fixing null-check errors
/toolcreate validate_not_null "Validates objects are not None"
```

### 3. Agent Memory Integration

Error fixes are saved to agent memory for context in future conversations.

---

## Metrics & Analytics

### Success Rate Tracking

```json
{
  "fixes": [
    {
      "title": "Add null-check",
      "total_attempts": 10,
      "successful_attempts": 9,
      "success_rate": 0.9
    }
  ]
}
```

### Error Statistics

View via error analyzer:

```python
stats = analyzer.get_error_stats()
# {
#   'total_errors': 15,
#   'unique_patterns': 3,
#   'by_severity': {...},
#   'top_error_types': {...}
# }
```

---

## Roadmap

Future enhancements:

- [ ] **Auto-correction mode** - Fix low-risk errors automatically
- [ ] **Scheduled scans** - Daily background error analysis
- [ ] **Error prediction** - Predict errors before they occur
- [ ] **Multi-file fixes** - Fix errors across multiple files simultaneously
- [ ] **Regression detection** - Detect if fixes introduce new errors
- [ ] **Fix rollback** - Automatic rollback on test failure
- [ ] **Cloud knowledge base** - Share successful fixes across instances
- [ ] **Integration with CI/CD** - Run during build pipeline

---

## Safety & Security

### User Approval Required

All fixes require explicit user approval:
1. ✅ Error selection
2. ✅ Fix option choice
3. ✅ Plan execution confirmation

### Backup & Rollback

- Git commits created before changes
- Rollback via `git revert`
- Backup files stored temporarily

### Risk Warnings

High-risk fixes show clear warnings:
```
⛔ CRITICAL RISK
This fix will modify API contracts.
Breaking changes possible in 7 files.
Review carefully before applying!
```

---

## Support

### Getting Help

1. Read this guide
2. Check error messages
3. Review knowledge base
4. Test with simple errors first
5. Report bugs via GitHub issues

### Common Issues

See **Troubleshooting** section above.

---

**Last Updated:** 2025-12-17
**Version:** 1.0.0
**Status:** ✅ Production Ready

---

## Quick Reference

```bash
# Start error correction
/errorcorrection

# User input prompts:
Choice: 1                    # Select error #1
Select option: A             # Choose fix option A
Execute this fix plan?: Yes  # Confirm execution

# Knowledge base location:
memory/error_fixes/*.json
```

**Remember:** SelfAI learns from every fix. The more you use `/errorcorrection`, the smarter it becomes! 🧠✨

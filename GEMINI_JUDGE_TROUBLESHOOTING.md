# Gemini Judge Troubleshooting Guide

## Problem: "Judge konnte nicht ausgeführt werden"

**Symptom:** Nach Plan-Execution erscheint:
```
⚠️  WEAKNESSES:
   • Judge konnte nicht ausgeführt werden

💡 RECOMMENDATIONS:
   • Gemini CLI überprüfen
```

**Root Cause:** Der Gemini Judge ist ein Fallback-Score, wenn die eigentliche Evaluation fehlschlägt.

---

## Diagnostic Tool (WICHTIG: Zuerst ausführen!)

```bash
python scripts/diagnose_gemini_judge.py
```

Dieses Script testet:
1. ✅ Ist `gemini` CLI installiert?
2. ✅ Funktioniert `gemini --help`?
3. ✅ Kann gemini Input via Pipe empfangen?
4. ✅ Kann gemini JSON zurückgeben?
5. ℹ️  Ist API Key konfiguriert?
6. ✅ Kann `GeminiJudge` importiert werden?

**Output:**
```
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍
  GEMINI JUDGE DIAGNOSTIC TOOL
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍

============================================================
  1. Checking if 'gemini' is in PATH
============================================================
✅ Found: /usr/local/bin/gemini

... (weitere Tests)

============================================================
  SUMMARY
============================================================

Test Results:
  ✅ PASS  cli_installed
  ✅ PASS  cli_works
  ✅ PASS  oneshot_works
  ✅ PASS  json_works
  ✅ PASS  import_works
```

---

## Improved Error Reporting (NEU!)

**Was wurde verbessert:**

### 1. Initialization Check (gemini_judge.py:77-115)
```python
def _check_availability(self) -> None:
    """Check if Gemini CLI is available with detailed error reporting"""
    try:
        result = subprocess.run(
            [self.cli_path, "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # DEBUG: Print detailed output
        print(f"\n🔍 Gemini CLI Check:")
        print(f"   Command: {self.cli_path} --help")
        print(f"   Return code: {result.returncode}")
        print(f"   STDOUT: {result.stdout[:200] if result.stdout else '(empty)'}")
        print(f"   STDERR: {result.stderr[:200] if result.stderr else '(empty)'}")
        ...
```

**Was du jetzt siehst:**
```
🔍 Gemini CLI Check:
   Command: gemini --help
   Return code: 0
   STDOUT: Usage: gemini [options] [prompt]...
   STDERR: (empty)
```

### 2. Evaluation Debug (gemini_judge.py:152-212)
```python
print(f"\n🔍 Gemini Judge Evaluation Debug:")
print(f"   Prompt length: {len(full_prompt)} chars")
print(f"   CLI path: {self.cli_path}")

result = subprocess.run([self.cli_path], ...)

print(f"   Return code: {result.returncode}")
print(f"   STDOUT length: {len(result.stdout) if result.stdout else 0} chars")
print(f"   STDERR length: {len(result.stderr) if result.stderr else 0} chars")
print(f"   Raw output (first 300 chars):\n   {gemini_output[:300]}")
```

**Was du jetzt siehst:**
```
🔍 Gemini Judge Evaluation Debug:
   Prompt length: 1234 chars
   CLI path: gemini
   Return code: 0
   STDOUT length: 567 chars
   STDERR length: 0 chars
   Raw output (first 300 chars):
   {
     "task_completion": 8.5,
     ...
```

### 3. Enhanced Error Messages (selfai.py:2333-2348)
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
    ui.status(f"   Type: {type(judge_error).__name__}", "warning")
    ui.status(f"   Message: {judge_error}", "warning")
    # ... full traceback ...
```

---

## Common Issues & Solutions

### Issue 1: Gemini CLI nicht installiert

**Error:**
```
🔍 Gemini CLI Check:
   Command: gemini --help
FileNotFoundError: [Errno 2] No such file or directory: 'gemini'
```

**Solution:**
```bash
# Option 1: Python package
pip install google-generativeai-cli

# Option 2: npm package
npm install -g @google/generative-ai-cli

# Verify installation
which gemini
gemini --help
```

### Issue 2: API Key nicht konfiguriert

**Error:**
```
🔍 Gemini Judge Evaluation Debug:
   Return code: 1
   STDERR: Error: API key not configured
```

**Solution:**
```bash
# Get API key from:
# https://makersuite.google.com/app/apikey

# Set environment variable (Linux/Mac)
export GEMINI_API_KEY='your-api-key-here'

# Set environment variable (Windows)
set GEMINI_API_KEY=your-api-key-here

# Or add to .bashrc/.zshrc for persistence
echo 'export GEMINI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc

# Or create config file
mkdir -p ~/.config/gemini
echo '{"apiKey": "your-key"}' > ~/.config/gemini/config.json
```

**Verify:**
```bash
echo $GEMINI_API_KEY  # Should show your key
python scripts/diagnose_gemini_judge.py  # Run full test
```

### Issue 3: Gemini timeout (>30s)

**Error:**
```
🔍 Gemini Judge Evaluation Debug:
   Prompt length: 1234 chars
   CLI path: gemini
   ❌ Gemini CLI timeout (>30s)
```

**Possible Causes:**
1. Network issues (slow connection to Google API)
2. API rate limiting
3. Gemini stuck waiting for interactive input

**Solution:**
```bash
# Test network connectivity
curl -I https://generativelanguage.googleapis.com

# Test gemini directly with simple prompt
echo "Say hello" | gemini

# If hangs, check if gemini is in interactive mode
# (should accept piped input in non-interactive mode)

# Check gemini version
gemini --version

# Update gemini CLI
pip install --upgrade google-generativeai-cli
```

### Issue 4: Invalid JSON response

**Error:**
```
🔍 Gemini Judge Evaluation Debug:
   Raw output (first 300 chars):
   I'm sorry, I cannot provide JSON in that format...
   ❌ Parse error: JSONDecodeError
```

**Possible Causes:**
- Gemini not following JSON instruction
- Gemini returning explanation text instead of pure JSON
- Markdown code fences not properly extracted

**Solution:**
The code already handles markdown fences:
```python
if "```json" in gemini_output:
    # Extract from ```json ... ```
elif "```" in gemini_output:
    # Extract from ``` ... ```
```

**Manual Test:**
```bash
cat <<EOF | gemini
Respond ONLY with valid JSON, no other text.

{
  "test": "success",
  "number": 42
}
EOF
```

**Expected Output:**
```json
{
  "test": "success",
  "number": 42
}
```

If gemini adds explanation text, the extraction may fail.

### Issue 5: Gemini CLI hangs / no response

**Error:**
```
# Command never completes:
echo "test" | gemini
```

**Possible Causes:**
1. Gemini in interactive mode (ignoring piped input)
2. Waiting for API key prompt
3. Stuck on first-run setup

**Solution:**
```bash
# Try running gemini interactively first
gemini

# Complete any first-run setup prompts
# Then Ctrl+C to exit

# Try piped input again
echo "test" | gemini

# Check if gemini config file exists
ls -la ~/.config/gemini/
cat ~/.config/gemini/config.json

# If all else fails, reinstall
pip uninstall google-generativeai-cli
pip install google-generativeai-cli
```

### Issue 6: Import Error (module not found)

**Error:**
```
⚠️ Gemini Judge nicht verfügbar (Import fehlgeschlagen)
   Fehler: No module named 'selfai.core.gemini_judge'
```

**Solution:**
```bash
# Check if file exists
ls -la selfai/core/gemini_judge.py

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Run from correct directory
cd /path/to/SelfAi-NPU-AGENT
python selfai/selfai.py

# Or set PYTHONPATH
export PYTHONPATH=/path/to/SelfAi-NPU-AGENT:$PYTHONPATH
```

---

## Manual Testing

### Test 1: Basic Gemini CLI

```bash
# Simple test
echo "Say 'hello world' and nothing else" | gemini

# Expected: "hello world" (or similar short response)
```

### Test 2: JSON Response

```bash
cat <<'EOF' | gemini
Respond ONLY with valid JSON, no other text.

{
  "task_completion": 8.5,
  "code_quality": 7.0,
  "summary": "Test successful"
}
EOF

# Expected: Valid JSON (may be in markdown code fence)
```

### Test 3: GeminiJudge Import

```python
from selfai.core.gemini_judge import GeminiJudge, format_score_for_terminal

# This will run availability check
judge = GeminiJudge()

# Should print debug output:
# 🔍 Gemini CLI Check:
#    Command: gemini --help
#    Return code: 0
#    ...
```

### Test 4: Full Evaluation

```python
from selfai.core.gemini_judge import GeminiJudge, format_score_for_terminal

judge = GeminiJudge()

score = judge.evaluate_task(
    original_goal="Create a hello world program",
    execution_output="print('Hello World')",
    plan_data=None,
    execution_time=1.5,
    files_changed=["hello.py"]
)

print(format_score_for_terminal(score))

# Should print:
# 🔍 Gemini Judge Evaluation Debug:
#    Prompt length: ... chars
#    CLI path: gemini
#    Return code: 0
#    ...
# ============================================================
# 🟢 GEMINI JUDGE EVALUATION
# ============================================================
# ...
```

---

## Understanding the Fallback Score

When Gemini Judge fails, you see this **fallback score**:

```python
def _create_fallback_score(self, reason: str) -> JudgeScore:
    return JudgeScore(
        task_completion=5.0,
        code_quality=5.0,
        efficiency=5.0,
        goal_adherence=5.0,
        overall_score=50.0,
        traffic_light=TrafficLight.YELLOW,
        summary=f"Bewertung fehlgeschlagen: {reason}",
        strengths=["Automatische Fallback-Bewertung"],
        weaknesses=["Judge konnte nicht ausgeführt werden"],
        recommendations=["Gemini CLI überprüfen"]
    )
```

**This is NOT your actual score!** It's a placeholder indicating the judge failed.

**Real scores** look like:
```
🟢 GEMINI JUDGE EVALUATION

🎯 OVERALL SCORE: 85.0/100

📊 DETAILED METRICS:
   Task Completion:  8.5/10  ████████
   Code Quality:     8.0/10  ████████
   Efficiency:       9.0/10  █████████
   Goal Adherence:   8.5/10  ████████

💬 SUMMARY:
   Excellent implementation with clean code and good documentation.

✅ STRENGTHS:
   • Clear code structure
   • Comprehensive error handling
   • Good documentation

⚠️  WEAKNESSES:
   • Could add more unit tests
   • Performance optimization possible

💡 RECOMMENDATIONS:
   • Add pytest test suite
   • Profile for bottlenecks
```

---

## Debug Workflow

**Step 1: Run Diagnostic**
```bash
python scripts/diagnose_gemini_judge.py
```

**Step 2: Check Debug Output**

When running `/plan` in SelfAI, you should now see:
```
🤖 Gemini Judge evaluiert die gesamte Ausführung (Plan + Merge)...

🔍 Gemini CLI Check:
   Command: gemini --help
   Return code: 0
   STDOUT: Usage: gemini...
   STDERR: (empty)

🔍 Gemini Judge Evaluation Debug:
   Prompt length: 1234 chars
   CLI path: gemini
   Return code: 0
   STDOUT length: 567 chars
   STDERR length: 0 chars
   Raw output (first 300 chars):
   {
     "task_completion": 8.5,
     ...
   Extracted from ```json block
   ✅ Parsing successful! Overall score: 85.0/100

============================================================
🟢 GEMINI JUDGE EVALUATION
============================================================
...
```

**Step 3: Identify Failure Point**

Look for:
- ❌ Marks in debug output
- Return code != 0
- Empty STDOUT
- Error messages in STDERR
- Parse errors
- Timeout messages

**Step 4: Apply Solution**

Based on error type (see "Common Issues" above)

---

## Configuration

### Custom Gemini CLI Path

If `gemini` is not in PATH:

```python
# In selfai.py, when initializing GeminiJudge:
judge = GeminiJudge(gemini_cli_path="/custom/path/to/gemini")
```

### Timeout Adjustment

If Gemini regularly times out, increase timeout:

```python
# In gemini_judge.py, evaluate_task():
result = subprocess.run(
    [self.cli_path],
    input=full_prompt,
    capture_output=True,
    text=True,
    timeout=60,  # Increase from 30 to 60 seconds
    stderr=subprocess.PIPE
)
```

### Disable Gemini Judge

If you don't want to use Gemini Judge at all:

**Option 1: Comment out in selfai.py**
```python
# Line 2267-2348
# Comment out entire try-except block:
# try:
#     from selfai.core.gemini_judge import ...
#     ...
# except ...:
#     ...
```

**Option 2: Skip on error** (already implemented)
The code already gracefully falls back if judge fails - you just won't see the evaluation.

---

## Troubleshooting Checklist

- [ ] **Gemini CLI installed?** → `which gemini`
- [ ] **Gemini CLI works?** → `gemini --help`
- [ ] **API key configured?** → `echo $GEMINI_API_KEY`
- [ ] **Piped input works?** → `echo "test" | gemini`
- [ ] **JSON response works?** → Test with manual prompt
- [ ] **Import works?** → `python -c "from selfai.core.gemini_judge import GeminiJudge"`
- [ ] **Run diagnostic?** → `python scripts/diagnose_gemini_judge.py`
- [ ] **Check debug output?** → Look for 🔍 sections in SelfAI output
- [ ] **Network connectivity?** → `curl -I https://generativelanguage.googleapis.com`
- [ ] **Gemini version current?** → `pip install --upgrade google-generativeai-cli`

---

## Alternative: Use Different Judge

If Gemini doesn't work, you could implement alternative judges:

### Option 1: Local LLM Judge
```python
class LocalLLMJudge:
    def __init__(self, model_path):
        # Use llama-cpp-python or similar
        pass

    def evaluate_task(...):
        # Same interface as GeminiJudge
        pass
```

### Option 2: Rule-Based Judge
```python
class RuleBasedJudge:
    def evaluate_task(self, goal, output, ...):
        # Simple heuristics:
        # - Did plan complete? +points
        # - Any errors? -points
        # - Files changed? +points
        # - Fast execution? +points
        pass
```

### Option 3: OpenAI Judge
```python
class OpenAIJudge:
    def __init__(self, api_key):
        import openai
        self.client = openai.OpenAI(api_key=api_key)

    def evaluate_task(...):
        # Use GPT-4 for evaluation
        pass
```

---

## Summary

### What Was Fixed

1. ✅ **Detailed Error Reporting** - Debug output shows exactly what's failing
2. ✅ **Diagnostic Script** - Automated testing of all components
3. ✅ **Better Error Messages** - Clear instructions when something fails
4. ✅ **Comprehensive Guide** - This document with all solutions

### What You Should Do Now

1. **Run diagnostic:**
   ```bash
   python scripts/diagnose_gemini_judge.py
   ```

2. **Fix identified issues** (usually API key or installation)

3. **Run `/plan` again** and check debug output

4. **Report findings:**
   - Which test failed in diagnostic?
   - What does debug output show?
   - Any error messages?

### Expected Behavior (Working)

```
🤖 Gemini Judge evaluiert die gesamte Ausführung (Plan + Merge)...

🔍 Gemini CLI Check:
   Command: gemini --help
   Return code: 0
   STDOUT: Usage: gemini...
   STDERR: (empty)

🔍 Gemini Judge Evaluation Debug:
   Prompt length: 1234 chars
   CLI path: gemini
   Return code: 0
   STDOUT length: 567 chars
   STDERR length: 0 chars
   Raw output (first 300 chars):
   ```json
   {
     "task_completion": 8.5,
     ...
   Extracted from ```json block
   ✅ Parsing successful! Overall score: 85.0/100

============================================================
🟢 GEMINI JUDGE EVALUATION
============================================================

🎯 OVERALL SCORE: 85.0/100
...
```

### Expected Behavior (Broken)

```
🤖 Gemini Judge evaluiert die gesamte Ausführung (Plan + Merge)...

🔍 Gemini CLI Check:
   Command: gemini --help
   Return code: 127
   STDOUT: (empty)
   STDERR: gemini: command not found

⚠️ Gemini Judge Initialisierung fehlgeschlagen:
   Gemini CLI not found at: gemini
   Please install: pip install google-generativeai-cli
   Or check PATH: which gemini
   Error: [Errno 2] No such file or directory: 'gemini'
```

Now you'll **see exactly what's wrong** instead of silent failure!

---

**Questions? Issues?**
1. Run `python scripts/diagnose_gemini_judge.py`
2. Check debug output in SelfAI
3. Consult this guide
4. Report specific error messages

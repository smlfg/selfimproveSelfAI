# SelfAI UI A/B Testing Guide

## Overview

SelfAI now supports **A/B testing** to compare two UI variants:
- **V1 (TerminalUI)**: Original terminal interface with rich formatting
- **V2 (GeminiUI)**: Modern, structured interface designed with Gemini AI

This guide explains how to use, test, and analyze both UI variants to determine which provides a better user experience.

---

## Quick Start

### Test UI V1 (TerminalUI - Original)

```bash
# Default - no environment variable needed
python selfai/selfai.py
```

### Test UI V2 (GeminiUI - New)

```bash
# Set environment variable before starting
SELFAI_UI_VARIANT=v2 python selfai/selfai.py
```

---

## UI Variants Comparison

### TerminalUI (V1) - Original

**Design Philosophy**: Rich, colorful terminal output with animations

**Key Features**:
- ASCII art banner with animated gradient
- Extensive use of emojis and colors
- Dynamic spinners and progress bars
- Streaming response animation
- Typing effect for AI responses

**Best For**:
- Users who prefer visual richness
- Long-form conversations
- Debugging with detailed output

**Example Output**:
```
╔══════════════════════════════════════════════════════════════╗
║                    🚀 SelfAI v2.0 🚀                         ║
║          Hybrid Intelligence System (NPU & CPU)              ║
╚══════════════════════════════════════════════════════════════╝

ℹ️  Konfiguration geladen.
✓ Agent 'Code Helper' geladen
⠋ Analysiere Anfrage...
```

---

### GeminiUI (V2) - Modern

**Design Philosophy**: Structured, clean hierarchy with semantic emphasis

**Key Features**:
- 5-level visual hierarchy (headers, subsections, content, metadata, debug)
- Consistent box-drawing characters
- Semantic color coding (green=success, red=error, blue=info)
- Minimalist design reduces visual clutter
- Card-based agent/tool display

**Best For**:
- Users who prefer clarity over decoration
- Quick scanning for information
- Production/professional use

**Example Output**:
```
╔══════════════════════════════════════════════════════════════╗
║    🚀  SelfAI NextGen Interface  🚀                         ║
║          Hybrid Intelligence System (NPU & CPU)              ║
╚══════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
 ℹ️  SYSTEM STATUS
═══════════════════════════════════════════════════════════════

ℹ️  Konfiguration geladen.
✅ Agent 'Code Helper' geladen
⠋ Analysiere Anfrage...
```

---

## How to Use A/B Testing

### 1. Switch UI Variant

**Option A: Environment Variable (Recommended)**

```bash
# Test V1 (Original)
python selfai/selfai.py

# Test V2 (New)
SELFAI_UI_VARIANT=v2 python selfai/selfai.py

# Alternative syntax
SELFAI_UI_VARIANT=gemini python selfai/selfai.py
```

**Option B: Runtime Command**

```bash
# Inside SelfAI
You: /ui

# Output:
ℹ️  Aktuelles UI: TerminalUI (V1)
ℹ️  Verfügbare Varianten: v1 (TerminalUI), v2 (GeminiUI)
ℹ️  Wechsel mit: /ui v1 oder /ui v2
ℹ️  Oder setze Umgebungsvariable: SELFAI_UI_VARIANT=v2

You: /ui v2

# Output:
⚠️  UI-Wechsel erfordert Neustart von SelfAI
ℹ️  Starte neu mit: SELFAI_UI_VARIANT=v2 python selfai/selfai.py
```

---

### 2. Collect Metrics Automatically

**Metrics are automatically collected** for every session:

- **Session ID**: Unique identifier
- **UI Variant**: Which UI was used (V1 or V2)
- **Total Interactions**: Number of user inputs
- **Commands Used**: Which commands were executed
- **Plans Created/Executed**: Planning activity
- **Agent Switches**: How often agents were changed
- **YOLO Mode Toggles**: Auto-accept usage
- **Errors Encountered**: Error count
- **Session Duration**: Time spent in SelfAI

**Storage**: Metrics saved to `memory/ui_metrics/ui_metrics_<timestamp>.json`

---

### 3. View Metrics Analysis

```bash
# Inside SelfAI
You: /uimetrics
```

**Output**:

```
╔═══════════════════════════════════════════════════════════╗
║              SESSION METRICS SUMMARY                      ║
╚═══════════════════════════════════════════════════════════╝

UI Variant: GeminiUI (V2)
Session Duration: 15.3 minutes

Total Interactions: 42
Commands Used: 38
Plans Created: 2
Plans Executed: 2
Agent Switches: 3
Errors Encountered: 1
YOLO Mode Toggles: 1

Most Used Commands:
  • /plan: 12x
  • /switch: 3x
  • /memory: 2x
  • /yolo: 1x
  • /uimetrics: 1x

ℹ️  Analysiere alle Sessions...

╔═══════════════════════════════════════════════════════════╗
║           UI A/B TESTING ANALYSIS REPORT                  ║
╚═══════════════════════════════════════════════════════════╝

TerminalUI (V1):
  Sessions: 8
  Avg Interactions: 35.2
  Avg Plans: 1.8
  Avg Errors: 2.1
  Avg Agent Switches: 2.3

GeminiUI (V2):
  Sessions: 5
  Avg Interactions: 41.6
  Avg Plans: 2.4
  Avg Errors: 0.8
  Avg Agent Switches: 1.6

Recommendation:
  ✅ GeminiUI (V2) shows better engagement and fewer errors.
```

---

## Testing Workflow

### Recommended Testing Process

**Week 1: Baseline with V1**

```bash
# Use original UI for 5+ sessions
python selfai/selfai.py

# Perform typical tasks:
# - Create plans with /plan
# - Switch agents with /switch
# - Use tools (Aider, shell, filesystem)
# - Test error handling
```

**Week 2: Compare with V2**

```bash
# Use new UI for 5+ sessions
SELFAI_UI_VARIANT=v2 python selfai/selfai.py

# Perform SAME tasks as Week 1:
# - Same types of plans
# - Same agent workflows
# - Same tool usage patterns
```

**Week 3: Analysis**

```bash
# View comparison
You: /uimetrics

# Decision:
# - If V2 shows better metrics → Adopt V2 as default
# - If V1 shows better metrics → Keep V1, improve V2
# - If similar → User preference wins
```

---

## What to Test

### Feature Comparison Checklist

Test each feature in BOTH UI variants:

#### ✅ Core Features

- [ ] Banner display on startup
- [ ] Status messages (info, success, warning, error)
- [ ] Agent list display (`/switch`)
- [ ] Tool list display
- [ ] Streaming LLM responses
- [ ] Think tag display (`<think>...</think>`)
- [ ] Plan visualization (`/plan`)
- [ ] Error messages
- [ ] Spinner animations
- [ ] YOLO mode (`/yolo`)

#### ✅ Commands

- [ ] `/plan` - Plan creation and execution
- [ ] `/switch` - Agent switching
- [ ] `/memory` - Memory management
- [ ] `/yolo` - YOLO mode toggle
- [ ] `/ui` - UI variant info
- [ ] `/uimetrics` - Metrics display
- [ ] `/tokens` - Token limits
- [ ] `/context` - Context window
- [ ] `/toolcreate` - Tool creation
- [ ] `/errorcorrection` - Error analysis

#### ✅ Edge Cases

- [ ] Very long responses (>1000 chars)
- [ ] Many agents (10+ agents)
- [ ] Many tools (50+ tools)
- [ ] Network errors (AnythingLLM down)
- [ ] Invalid commands
- [ ] Empty inputs
- [ ] Special characters in responses

---

## Metrics Interpretation

### Key Metrics

**1. Total Interactions**
- **Higher = More engaged** (assuming same session duration)
- **V2 > V1**: Users interact more with cleaner UI
- **V1 > V2**: Users prefer rich visual feedback

**2. Errors Encountered**
- **Lower = Better UX** (fewer user mistakes)
- **V2 < V1**: Cleaner UI reduces confusion
- **V1 < V2**: Rich feedback prevents errors

**3. Plans Created vs Executed**
- **Ratio close to 1:1 = Good workflow**
- **Ratio < 1 = Plans abandoned** (UI too complex?)
- **Ratio > 1 = Multiple plans per execution** (good planning)

**4. Agent Switches**
- **Moderate = Healthy exploration**
- **Too high = Users confused about agent roles**
- **Too low = Default agent sufficient**

**5. YOLO Mode Activations**
- **Higher = Users trust the UI** (confident in automation)
- **Lower = Users cautious** (need more control)

---

## Decision Criteria

### When to Adopt V2 (GeminiUI)

✅ **Adopt V2 if:**
- Average interactions **10%+ higher** in V2
- Errors **20%+ lower** in V2
- Users report **subjective preference** for V2
- Metrics show **faster task completion** in V2

### When to Keep V1 (TerminalUI)

✅ **Keep V1 if:**
- Average interactions **similar or higher** in V1
- Errors **similar or lower** in V1
- Users report **visual richness is important**
- Metrics show **equal or better engagement** in V1

### Hybrid Approach

Consider **keeping both** as user-selectable options:

```bash
# Power users who want speed
SELFAI_UI_VARIANT=v2 python selfai/selfai.py

# New users who want guidance
SELFAI_UI_VARIANT=v1 python selfai/selfai.py
```

---

## Implementation Details

### File Structure

```
selfai/
├── ui/
│   ├── terminal_ui.py          # V1 - Original UI
│   └── geminiSelfAI_UI.py      # V2 - Gemini-designed UI
├── core/
│   └── ui_metrics.py           # Metrics collection & analysis
└── selfai.py                   # Main - UI selection logic

memory/
└── ui_metrics/
    ├── ui_metrics_20250120_143022.json
    ├── ui_metrics_20250120_150511.json
    └── ...
```

### Metrics JSON Format

```json
{
  "session_id": "20250120_143022",
  "ui_variant": "GeminiUI (V2)",
  "session_start": "2025-01-20T14:30:22",
  "session_end": "2025-01-20T14:45:33",
  "total_interactions": 42,
  "commands_used": [
    {"command": "/plan", "timestamp": "2025-01-20T14:31:05"},
    {"command": "/switch", "timestamp": "2025-01-20T14:35:12"},
    ...
  ],
  "errors_encountered": 1,
  "plans_created": 2,
  "plans_executed": 2,
  "agent_switches": 3,
  "yolo_mode_activations": 1,
  "ui_variant_checks": 1
}
```

---

## Troubleshooting

### Issue: Metrics not saving

**Symptom**: `/uimetrics` shows "No metrics collected yet"

**Solution**:
1. Ensure `memory/ui_metrics/` directory exists (created automatically)
2. Exit SelfAI with `quit` command (not Ctrl+C) to save metrics
3. Check file permissions on `memory/` directory

### Issue: UI variant not switching

**Symptom**: Setting `SELFAI_UI_VARIANT=v2` doesn't change UI

**Solution**:
1. Verify environment variable is set BEFORE running:
   ```bash
   echo $SELFAI_UI_VARIANT  # Should show "v2"
   ```
2. Check startup message shows correct variant:
   ```
   ℹ️  SelfAI wird gestartet... [UI: GeminiUI (V2)]
   ```
3. If still V1, restart terminal session

### Issue: Metrics show skewed results

**Symptom**: V2 always shows better/worse metrics

**Solution**:
1. Ensure **same tasks** performed in both variants
2. Collect **at least 3-5 sessions** per variant
3. Use **same session duration** (e.g., 15 min each)
4. Test at **same time of day** (fatigue affects metrics)

---

## Best Practices

### 1. Consistent Testing

✅ **DO**:
- Perform identical workflows in both variants
- Use same agent configurations
- Test at similar times of day
- Collect 5+ sessions per variant

❌ **DON'T**:
- Test V1 with simple tasks, V2 with complex tasks
- Use different agents in different variants
- Compare single sessions

### 2. Objective Measurement

✅ **DO**:
- Focus on quantitative metrics (interactions, errors)
- Time task completion
- Record subjective notes separately

❌ **DON'T**:
- Rely solely on "feeling"
- Ignore metrics that contradict preference
- Rush to conclusion after 1-2 sessions

### 3. User Feedback

✅ **DO**:
- Ask multiple users to test both variants
- Collect structured feedback (survey)
- Note specific pain points

❌ **DON'T**:
- Only test yourself
- Use vague feedback ("I like V2 better")
- Ignore edge cases

---

## Future Enhancements

### Planned Features

1. **In-Session Switching**
   - Toggle between V1/V2 without restart
   - Live comparison mode

2. **Advanced Metrics**
   - Task completion time tracking
   - Heatmap of UI element usage
   - Eye-tracking integration (if hardware available)

3. **Automatic Recommendations**
   - ML-based UI variant recommendation per user
   - Adaptive UI that switches based on task type

4. **User Preference Profiles**
   - Save UI preference per user
   - Export/import preference settings

---

## Summary

**SelfAI UI A/B Testing** allows data-driven decisions about UX design:

- ✅ **Two variants**: TerminalUI (V1) vs GeminiUI (V2)
- ✅ **Easy switching**: Environment variable or `/ui` command
- ✅ **Automatic metrics**: Tracks interactions, errors, workflows
- ✅ **Analysis tools**: `/uimetrics` for comparison reports
- ✅ **Evidence-based**: Make decisions from real usage data

**Next Steps**:
1. Test both variants with real workflows
2. Collect 5+ sessions per variant
3. Analyze metrics with `/uimetrics`
4. Choose the better variant (or keep both!)

**Philosophy**: Let the data decide which UI serves users best! 📊

# SelfAI Token Limits Control Guide

## Overview

SelfAI now has **runtime-configurable token limits** for complete transparency and control. No more black boxes - you control exactly how much output each operation can generate!

## Quick Start

### Show Current Limits
```bash
/tokens
```

### Extreme Mode (64K for everything!)
```bash
/extreme
```
or
```bash
/tokens extreme
```

## Available Commands

### 1. `/tokens` - Show current limits
Displays all current token limits for different operations.

### 2. `/tokens extreme` or `/extreme`
Sets all limits to 64000 tokens - SelfAI fully unleashed!

**Use when:**
- You need maximum output quality
- Complex tasks requiring detailed responses
- Cost is not a concern
- You want the full power of the LLM

### 3. `/tokens conservative`
Optimized for speed and cost (fast, cheap).

**Limits:**
- Planner: 512
- Execution: 256
- Merge: 1024
- Tool Creation: 768
- Error Correction: 768
- Self-Improve: 1024
- Chat: 512

**Use when:**
- Quick iterations
- Simple tasks
- Testing/debugging
- Cost-conscious operation

### 4. `/tokens balanced` (Default)
Balanced quality vs cost.

**Limits:**
- Planner: 768
- Execution: 512
- Merge: 2048
- Tool Creation: 1024
- Error Correction: 1024
- Self-Improve: 2048
- Chat: 1024

**Use when:**
- Normal operation
- Good default for most tasks

### 5. `/tokens generous`
High quality, longer outputs.

**Limits:**
- Planner: 2048
- Execution: 1024
- Merge: 4096
- Tool Creation: 2048
- Error Correction: 2048
- Self-Improve: 4096
- Chat: 2048

**Use when:**
- Complex analysis required
- Detailed planning needed
- High-quality output preferred

### 6. `/tokens set <type> <value>`
Set individual limit for specific operation.

**Types:**
- `planner` - Plan generation phase
- `execution` - Subtask execution
- `merge` - Result synthesis
- `tool_creation` - Dynamic tool generation
- `error_correction` - Error analysis & fix generation
- `selfimprove` - Self-improvement operations
- `chat` - Normal chat responses

**Examples:**
```bash
/tokens set planner 4096
/tokens set execution 2048
/tokens set chat 512
```

## Token Limit Impact

### What Each Limit Controls

**Planner (default: 768)**
- Controls plan generation output
- Higher = more detailed plans with more subtasks
- Lower = simpler, faster plans

**Execution (default: 512)**
- Controls subtask output length
- Higher = more detailed subtask results
- Lower = concise, focused results

**Merge (default: 2048)**
- Controls final synthesis length
- Higher = comprehensive final answers
- Lower = brief summaries

**Tool Creation (default: 1024)**
- Controls generated tool code length
- Higher = more features, error handling
- Lower = minimal implementations

**Error Correction (default: 1024)**
- Controls fix analysis depth
- Higher = more thorough analysis, multiple options
- Lower = quick fixes only

**Self-Improve (default: 2048)**
- Controls self-improvement output
- Higher = more detailed code changes
- Lower = focused improvements

**Chat (default: 1024)**
- Controls normal conversation responses
- Higher = detailed explanations
- Lower = brief answers

## Cost vs Quality Trade-offs

### Token Usage ≈ Cost
```
64000 tokens = ~64x cost vs 1000 tokens
```

### Extreme Mode (64K)
- **Cost:** Very High (64x baseline)
- **Quality:** Maximum
- **Speed:** Slowest (more tokens = longer generation)
- **Use Case:** Critical tasks, final production outputs

### Conservative Mode
- **Cost:** Low (0.5x baseline)
- **Quality:** Good for simple tasks
- **Speed:** Fastest
- **Use Case:** Rapid iteration, testing

### Balanced Mode (Default)
- **Cost:** Moderate (1x baseline)
- **Quality:** Good general purpose
- **Speed:** Moderate
- **Use Case:** Day-to-day operation

### Generous Mode
- **Cost:** High (2-4x baseline)
- **Quality:** Very High
- **Speed:** Slower
- **Use Case:** Important production tasks

## Best Practices

### 1. Start Conservative, Scale Up
```bash
/tokens conservative  # Test the task
# If output insufficient:
/tokens balanced      # Try default
# Still not enough:
/tokens generous      # Higher quality
# Need maximum:
/extreme              # Full power
```

### 2. Task-Specific Tuning
For complex planning but simple execution:
```bash
/tokens set planner 4096
/tokens set execution 512
```

### 3. Monitor Output Quality
If responses are truncated (ends with "..."), increase limits:
```bash
/tokens set chat 2048
```

### 4. Cost-Conscious Development
During development/testing:
```bash
/tokens conservative
```

For production:
```bash
/tokens generous
```

### 5. Extreme Mode Strategy
Only use `/extreme` when:
- Final production output
- Complex multi-step tasks
- Need maximum detail and accuracy
- Cost is justified by importance

## Examples

### Example 1: Complex Planning Task
```bash
You: /tokens
[See current limits]

You: /tokens set planner 4096
You: /plan Build a full-stack web app with authentication

[Detailed plan generated with many subtasks]
```

### Example 2: Quick Iteration
```bash
You: /tokens conservative
You: Create a simple hello world function

[Fast, concise response]
```

### Example 3: Production-Ready Output
```bash
You: /extreme
You: /plan Implement comprehensive error handling system

[Maximum detail, thorough analysis, extensive code]
```

### Example 4: Mixed Approach
```bash
# Planning: detailed
You: /tokens set planner 2048

# Execution: moderate
You: /tokens set execution 1024

# Merge: comprehensive
You: /tokens set merge 4096

You: /plan Refactor authentication module
```

## Technical Details

### Where Limits Are Applied

**Planner Phase:**
- PlannerMinimaxInterface uses `planner_max_tokens`
- Affects plan complexity and number of subtasks

**Execution Phase:**
- ExecutionDispatcher uses `execution_max_tokens`
- Affects each subtask's output length

**Merge Phase:**
- MergeMinimaxInterface uses `merge_max_tokens`
- Affects final synthesis detail

**Tool Creation:**
- `/toolcreate` command uses `tool_creation_max_tokens`
- Affects generated tool code length

**Error Correction:**
- `/errorcorrection` command uses `error_correction_max_tokens`
- Affects fix analysis depth

**Self-Improvement:**
- `/selfimprove` command uses `selfimprove_max_tokens`
- Affects improvement scope

**Normal Chat:**
- Regular messages use `chat_max_tokens`
- Affects conversation response length

### Runtime Configuration

Limits are stored in memory during session:
- Changes are immediate
- Not persisted between restarts
- Each session starts with balanced defaults

### Implementation

See `selfai/core/token_limits.py` for the TokenLimits class.

## Comparison with Claude Code

### SelfAI Approach (Transparent Control):
```bash
/tokens              # See exactly what limits are active
/tokens set chat 512 # Precise control
/extreme             # Maximum power when needed
```

### Claude Code (Black Box):
- Hidden token limits
- No user control
- "Trust us" approach

**SelfAI Philosophy:** Full transparency and control. You should know and control every parameter!

## FAQ

**Q: Do limits reset on restart?**
A: Yes, each session starts with balanced defaults.

**Q: Can I save my preferred limits?**
A: Not yet, but coming soon in config.yaml support.

**Q: What happens if I set limits too low?**
A: Responses may be truncated. You'll see incomplete output.

**Q: What happens if I set limits too high?**
A: Slower generation, higher costs, but maximum quality.

**Q: Should I always use /extreme?**
A: No! Use it strategically for important tasks. Most work is fine with balanced/generous.

**Q: How do I know which mode to use?**
A: Start with balanced. If output is insufficient, scale up. If it's overkill, scale down.

**Q: Can limits be different for different agents?**
A: Not yet, but this is planned for future versions.

## Summary

SelfAI gives you **complete control** over token limits:
- `/extreme` - 64K everywhere (maximum power)
- `/tokens conservative` - Fast & cheap
- `/tokens balanced` - Good default (recommended)
- `/tokens generous` - High quality
- `/tokens set <type> <value>` - Precise control

**No black boxes. Full transparency. Complete control.**

That's the SelfAI way! 🚀

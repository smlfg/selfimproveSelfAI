# 🛠️ SelfAI Tool Creation Guide - `/toolcreate` Command

## Overview

The `/toolcreate` command enables **SelfAI to generate new tools dynamically** using LLM-based code generation. This allows the system to expand its capabilities on-the-fly without manual coding.

## Usage

### Basic Syntax

```bash
/toolcreate <tool_name> <description>
```

### Examples

**Simple tool:**
```bash
/toolcreate calculate_fibonacci "Calculate fibonacci numbers up to n"
```

**API client tool:**
```bash
/toolcreate fetch_github_user "Fetch GitHub user profile data"
```

**Data processing tool:**
```bash
/toolcreate parse_csv_file "Parse CSV file and return JSON data"
```

## How It Works

```
User Input: /toolcreate <name> <description>
            ↓
┌───────────────────────────────────────┐
│ 1. Validation                         │
│    - Check tool name format           │
│    - Check for existing tool          │
│    - Validate description             │
└───────────────┬───────────────────────┘
                ↓
┌───────────────────────────────────────┐
│ 2. LLM Code Generation (MiniMax)     │
│    - Generate function signature      │
│    - Implement logic                  │
│    - Add error handling               │
│    - Create docstrings                │
└───────────────┬───────────────────────┘
                ↓
┌───────────────────────────────────────┐
│ 3. Code Cleanup                       │
│    - Remove markdown formatting       │
│    - Validate Python syntax           │
│    - Format code                      │
└───────────────┬───────────────────────┘
                ↓
┌───────────────────────────────────────┐
│ 4. File Creation                      │
│    - Save to tools/generated/         │
│    - Create with UTF-8 encoding       │
└───────────────┬───────────────────────┘
                ↓
┌───────────────────────────────────────┐
│ 5. User Notification                  │
│    ✓ Tool created successfully        │
│    ⚠️  Restart SelfAI to load tool    │
└───────────────────────────────────────┘
```

## Generated Tool Structure

Each generated tool follows this pattern:

```python
import json
from typing import Any

def <tool_name>(**kwargs) -> str:
    """
    <Tool description>

    Args:
        <parameter>: <description>

    Returns:
        JSON string with structure:
        - On success: {"result": ..., "status": "success"}
        - On error: {"error": ..., "status": "failed"}
    """
    try:
        # Input validation
        if not isinstance(param, expected_type):
            return json.dumps({
                "error": "Invalid input",
                "status": "failed"
            })

        # Implementation logic
        result = perform_operation(param)

        # Success response
        return json.dumps({
            "result": result,
            "status": "success"
        })

    except Exception as e:
        # Error handling
        return json.dumps({
            "error": str(e),
            "status": "failed"
        })
```

## File Locations

Generated tools are stored in:
```
selfai/tools/generated/
├── __init__.py           # Package initialization
├── README.md             # Documentation
├── example_tool.py       # Example/demo tool
└── <your_tool>.py        # Your generated tools
```

## Tool Requirements

Generated tools must:
1. ✅ Return JSON string (not dict!)
2. ✅ Include error handling (try-except)
3. ✅ Have comprehensive docstring
4. ✅ Use type hints
5. ✅ Validate input parameters
6. ✅ Follow naming convention (snake_case)

## Loading Generated Tools

### Automatic Loading (Planned)
Tools will be auto-loaded at SelfAI startup (future enhancement).

### Manual Loading (Current)
Currently, you need to **restart SelfAI** after creating a tool:
```bash
# Exit SelfAI
quit

# Restart
python selfai/selfai.py
```

## Advanced Usage (Future)

### Template-based Creation
```bash
/toolcreate --template api_client my_api "API for service X"
```

### Tool Editing
```bash
/toolcreate --edit calculate_fibonacci "Add caching"
```

### Tool Deletion
```bash
/toolcreate --delete calculate_fibonacci
```

### Tool Listing
```bash
/toolcreate --list
```

## Integration with DPPM Planner

Tools can be **automatically created during plan execution**:

```bash
Du: /plan Create a weather dashboard

SelfAI Planner:
  S1: Analyze requirements
  S2: Create tool 'fetch_weather_data'  ← AUTO-CREATES TOOL!
  S3: Create tool 'format_weather_display'
  S4: Implement dashboard UI

# Tools are generated and immediately used in subsequent tasks
```

## Troubleshooting

### "Tool already exists"
Solution: Choose a different name or confirm overwrite

### "Invalid tool name"
Solution: Use only alphanumeric characters and underscores (snake_case)

### "Tool creation failed"
Possible causes:
- LLM backend not available
- Invalid description
- File system permissions

### "Tool not available after creation"
Solution: Restart SelfAI to load the new tool

## Examples

### Example 1: Calculator Tool
```bash
/toolcreate calculate_factorial "Calculate factorial of a number"
```

Generated output:
```python
def calculate_factorial(n: int) -> str:
    """Calculate factorial of a number."""
    try:
        if not isinstance(n, int) or n < 0:
            return json.dumps({"error": "Invalid input", "status": "failed"})

        result = 1
        for i in range(1, n + 1):
            result *= i

        return json.dumps({"result": result, "input": n, "status": "success"})
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})
```

### Example 2: API Tool
```bash
/toolcreate fetch_random_joke "Fetch a random joke from API"
```

Generated output:
```python
import json
import requests

def fetch_random_joke() -> str:
    """Fetch a random joke from API."""
    try:
        response = requests.get("https://official-joke-api.appspot.com/random_joke")
        response.raise_for_status()
        data = response.json()

        joke = f"{data['setup']} - {data['punchline']}"

        return json.dumps({
            "joke": joke,
            "type": data.get("type", "unknown"),
            "status": "success"
        })
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Code Review**: Always review generated code before use in production
2. **Input Validation**: Generated tools validate inputs, but verify this
3. **Sandboxing**: Consider running in isolated environment
4. **Permissions**: Tools run with same permissions as SelfAI
5. **API Keys**: Never hardcode API keys in tools

## Performance

Typical tool creation time:
- Validation: ~0.1s
- LLM Generation: ~5-10s
- File Writing: ~0.1s
- **Total: ~5-10 seconds**

## Roadmap

Future enhancements:
- [ ] Hot-reload (no restart required)
- [ ] Tool templates library
- [ ] Auto-generate unit tests
- [ ] Tool versioning
- [ ] Tool marketplace/sharing
- [ ] Native tool-calling integration
- [ ] Tool composition (combine multiple tools)

## Support

For issues or questions:
1. Check this guide
2. Review generated tool code
3. Check SelfAI logs
4. Report bugs via GitHub issues

---

**Last Updated:** 2025-12-17
**Version:** 1.0.0
**Status:** ✅ Production Ready

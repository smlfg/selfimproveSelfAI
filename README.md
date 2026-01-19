# 🤖 SelfAI - Autonomous Multi-Agent System with Self-Improvement

**SelfAI** is an advanced AI agent system featuring a custom tool-calling loop, self-improvement capabilities, and multi-layer safety mechanisms. Built for **MiniMax M2** with comprehensive identity enforcement and introspection tools.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MiniMax M2](https://img.shields.io/badge/LLM-MiniMax%20M2-green.svg)](https://api.minimax.io/)

---

## 🚀 Key Features

### 1. **Custom Agent Loop** (MiniMax-Compatible)
- ✅ **560-line custom implementation** replacing heavyweight frameworks
- ✅ Native support for MiniMax's `Action: {...}` format
- ✅ Multi-step reasoning with automatic tool chaining
- ✅ Clean, structured UI with progress tracking

### 2. **24 Integrated Tools**
- **Introspection Tools:** `list_selfai_files`, `read_selfai_code`, `search_selfai_code`
- **Filesystem Tools:** `create_file`, `read_file`, `write_file`, `list_directory`
- **Shell Tools:** `execute_shell_command`
- **Test Tools:** `say_hello`, `echo_message`, `count_numbers`

### 3. **Self-Improvement System** (`/selfimprove`)
- 🛡️ **Multi-layer safety:** Protected files, user approvals, automatic backups
- 📊 **Proposal-based workflow:** Analyze → Propose → User selects → Execute
- 🔒 **Anti-sabotage:** Core files are never modified automatically
- 💾 **Git-based rollback:** Every change is versioned

### 4. **Identity Enforcement**
- 🎭 **Identity Core:** Prevents model from claiming to be "an AI assistant"
- 🔍 **Reflection Validation:** Ensures responses maintain SelfAI identity
- 🛡️ **Guardrails:** Auto-correction of identity leaks
- 📈 **Metrics Tracking:** Monitor identity enforcement quality

### 5. **Clean Terminal UI**
- 📦 Structured output blocks (no messy spinners)
- 🔢 Step-by-step progress (`Step 1/15: Analyzing...`)
- 🎨 Color-coded status messages
- 📊 Compact tool call/result display

---

## 📦 Installation

### Prerequisites
- Python 3.12+
- MiniMax API Key ([Get one here](https://api.minimax.io/))
- Git (for version control)

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/smlfg/selfimproveSelfAI.git
cd selfimproveSelfAI

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edit .env and add: MINIMAX_API_KEY=your_key_here

# 5. Run SelfAI
python selfai/selfai.py
```

---

## 🎯 Usage Examples

### Basic Chat with Tool Calling

```bash
$ python selfai/selfai.py

Du: Say hello!

======================================================================
🤖 AGENT REASONING
======================================================================

📝 Step 1/15: Analyzing...
   🔧 Calling: say_hello()
   ✅ Result: 🎉 Hello World! Tool-Calling funktioniert perfekt! 🚀

✅ Complete after 1 step
======================================================================

SelfAI: 🎉 Hello World! Tool-Calling funktioniert perfekt! 🚀
```

### Introspection (Read Own Code)

```bash
Du: Liste alle Tools auf

======================================================================
🤖 AGENT REASONING
======================================================================

📝 Step 1/15: Analyzing...
   🔧 Calling: list_selfai_files(subdirectory='tools')
   ✅ Result: 📁 SelfAI Python Files (12 Dateien) in 'tools/':...

📝 Step 2/15: Analyzing...
   🔧 Calling: read_selfai_code(file_path='tools/tool_registry.py')
   ✅ Result: 📄 File: selfai/tools/tool_registry.py...

✅ Complete after 2 steps
======================================================================
```

### Self-Improvement (Read-Only Analysis)

```bash
Du: /selfimprove analyze selfai architecture without modifying anything

ℹ️ 🔍 Starte Analyse für Ziel: analyze selfai architecture...
ℹ️ Analysiere Projekt-Struktur...
ℹ️ Generiere Verbesserungsvorschläge (LLM)...

============================================================
  📋 VERBESSERUNGSVORSCHLÄGE
============================================================

  [1] Optimize Custom Agent Loop Performance
      Reduce token usage in multi-step reasoning
      Files: selfai/core/custom_agent_loop.py
      Aufwand: 20 min | Impact: 25%

  [2] Add Caching for Introspection Tools
      Cache file listings to reduce disk I/O
      Files: selfai/tools/introspection_tools.py
      Aufwand: 15 min | Impact: 15%

============================================================
Wähle Optionen (z.B. '1', '1,2', 'all') oder 'q' zum Abbrechen.
```

---

## 🛡️ Safety Mechanisms

SelfAI includes comprehensive safety measures to prevent self-sabotage:

### Protected Files (Never Modified)
```python
SELFIMPROVE_PROTECTED_FILES = [
    'selfai/selfai.py',           # Main orchestration
    'selfai/config_loader.py',    # Config system
    'selfai/core/agent_manager.py', # Agent management
    'selfai/tools/tool_registry.py', # Tool system
]
```

### Sensitive Files (User Approval Required)
```python
SELFIMPROVE_SENSITIVE_FILES = [
    'selfai/core/execution_dispatcher.py',
    'selfai/core/planner_minimax_interface.py',
    'selfai/core/memory_system.py',
]
```

### Allowed Patterns (Safe Modifications)
```python
SELFIMPROVE_ALLOWED_PATTERNS = [
    'selfai/core/*_interface.py',  # LLM interfaces
    'selfai/tools/*.py',            # Tools
    'selfai/ui/*.py',               # UI improvements
]
```

**See:** [SELFIMPROVE_SAFETY_SUMMARY.md](SELFIMPROVE_SAFETY_SUMMARY.md) for full documentation.

---

## 📁 Project Structure

```
selfimproveSelfAI/
├── selfai/
│   ├── core/
│   │   ├── custom_agent_loop.py       # Custom agent implementation
│   │   ├── minimax_interface.py       # MiniMax API client
│   │   ├── self_improvement_engine.py # Self-improvement logic
│   │   ├── identity_enforcer.py       # Identity enforcement
│   │   └── ...
│   ├── tools/
│   │   ├── tool_registry.py           # Tool catalog
│   │   ├── introspection_tools.py     # Self-inspection tools
│   │   ├── filesystem_tools.py        # File operations
│   │   └── ...
│   ├── ui/
│   │   └── terminal_ui.py             # Terminal interface
│   └── selfai.py                      # Main entry point
├── config.yaml                         # Configuration
├── .env                                # API keys (not committed)
├── requirements.txt                    # Dependencies
└── README.md                           # This file
```

---

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
# MiniMax Configuration
minimax:
  api_base: "https://api.minimax.io/v1"
  model: "openai/MiniMax-M2"
  enabled: true

# Agent Mode Settings
system:
  enable_agent_mode: true      # Enable tool-calling
  agent_max_steps: 15          # Max reasoning steps
  agent_verbose: true          # Show detailed output
  streaming_enabled: true      # Enable streaming
```

---

## 🧪 Testing

### Test Custom Agent Loop
```bash
python test_custom_agent_loop.py
```

### Test Tool Calling
```bash
python test_tool_calling_direct.py
```

### Test Self-Improvement (Safe Mode)
```bash
./test_selfimprove_quick.sh
```

---

## 📚 Documentation

- **[ANTI_SABOTAGE_SAFETY.md](ANTI_SABOTAGE_SAFETY.md)** - Complete safety documentation
- **[SELFIMPROVE_SAFETY_SUMMARY.md](SELFIMPROVE_SAFETY_SUMMARY.md)** - Quick safety guide
- **[UI_IMPROVEMENTS.md](UI_IMPROVEMENTS.md)** - UI design decisions
- **[CLAUDE.md](CLAUDE.md)** - Architecture overview

---

## 🎓 Use Cases

### 1. **Autonomous Code Analysis**
SelfAI can read and analyze its own codebase, providing insights into architecture and suggesting improvements.

### 2. **Safe Self-Improvement**
With multi-layer safety mechanisms, SelfAI can propose and implement improvements without breaking core functionality.

### 3. **Multi-Step Task Execution**
Complex tasks are automatically broken down into steps with tool calls chained together seamlessly.

### 4. **Identity-Aware Conversations**
Unlike generic chatbots, SelfAI maintains a consistent identity as an autonomous agent system.

---

## 🐛 Known Issues & Fixes

### Issue: `UnboundLocalError` on startup
**Fixed in:** commit `13752fc`
**Solution:** Initialize `selfai_agent = None` before main loop

### Issue: `/selfimprove` JSON parse errors
**Fixed in:** commit `13752fc`
**Solution:** Added XML tag removal and direct API call for structured output

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. **Tool Ecosystem:** Add more specialized tools
2. **Testing:** Expand test coverage
3. **Documentation:** Improve inline documentation
4. **Safety:** Enhance anti-sabotage mechanisms
5. **UI:** Add web-based interface option

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **MiniMax** for the M2 model with excellent tool-calling support
- **Claude Code** for collaborative development assistance
- **smolagents** for initial inspiration (replaced with custom loop)

---

## 📞 Contact

- **GitHub:** [@smlfg](https://github.com/smlfg)
- **Repository:** [selfimproveSelfAI](https://github.com/smlfg/selfimproveSelfAI)

---

## 🚀 Roadmap

- [ ] Add parallel subtask execution in DPPM pipeline
- [ ] Web-based UI with real-time updates
- [ ] Vector database integration for RAG
- [ ] Multi-model ensemble (combine multiple LLMs)
- [ ] Plugin system for custom tool loading
- [ ] Docker containerization

---

**Built with ❤️ by the SelfAI Team**

🤖 *"A self-improving von Neumann machine that's safe to run!"*

# Quick Start Guide

## 5-Minute Setup

### 1. Create Virtual Environment
```bash
cd AI_NPU_AGENT_Projekt
python -m venv .venv
source .venv/bin/activate  # Windows CMD: .\.venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
cp config.yaml.template config.yaml
cp .env.example .env
# Edit .env and add your AnythingLLM API key
# Edit config.yaml as needed
```

### 4. Download Model (for CPU fallback)
```bash
mkdir -p models
# Download from Hugging Face or use existing:
# https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
# Place .gguf file in models/ directory
```

### 5. Run
```bash
python selfai/selfai.py
```

---

## First Commands to Try

### Simple Chat
```
You: What is machine learning?
AI: [Response from available backend]
```

### Task Planning (requires Ollama)
```
You: /plan Create a Python web scraper
[System creates plan with subtasks]
[Executes each subtask]
[Synthesizes final answer]
```

### Agent Switching
```
You: /switch code_helfer
You: How do I write async Python?
AI: [Response from code helper agent]
```

### Memory Management
```
You: /memory
You: /memory clear general
```

---

## Core Concepts

### Three Backends (Auto-Fallback)
1. **AnythingLLM** (NPU) - Fastest, requires setup
2. **QNN** (NPU) - Very fast, direct model support
3. **CPU** (GGUF) - Slow but always works

### Three Phases (Optional Planning)
1. **Planning**: Decompose goal → subtasks
2. **Execution**: Run subtasks → collect results
3. **Merge**: Synthesize → final answer

### Agents
- Specialize in different domains
- Have their own system prompts
- Maintain separate memory
- Switch with `/switch <name>`

---

## File Locations

| Item | Location |
|------|----------|
| Main Script | `selfai/selfai.py` |
| Configuration | `config.yaml` |
| Models | `models/*.gguf` |
| Conversations | `memory/*/` |
| Plans | `memory/plans/` |
| Agents | `agents/*/` |

---

## Key Configuration Settings

```yaml
# config.yaml

# NPU Backend
npu_provider:
  base_url: "http://localhost:3001/api/v1"
  workspace_slug: "main"

# CPU Fallback
cpu_fallback:
  model_path: "Phi-3-mini-4k-instruct.Q4_K_M.gguf"
  n_ctx: 4096

# Streaming Output
system:
  streaming_enabled: true

# Default Agent
agent_config:
  default_agent: "code_helfer"
```

---

## Environment Variables (.env)

```bash
# Required
API_KEY=your-anythingllm-api-key-here

# Optional
OLLAMA_CLOUD_API_KEY=your-ollama-key-if-using-cloud
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API_KEY not set" | Add key to .env file |
| "AnythingLLM not available" | Will auto-fallback to CPU |
| "Planner not working" | Start Ollama: `ollama serve` |
| "Very slow responses" | Using CPU fallback (expected) |
| "Memory growing" | Use `/memory clear` |

---

## Next Steps

1. **Read CLAUDE.md** for detailed architecture
2. **Explore agents/** directory to create custom agents
3. **Check UI_GUIDE.md** for rich terminal features
4. **Enable planning** in config.yaml for advanced workflows

---

## Getting Help

- **CLAUDE.md**: Full architecture documentation
- **README.md**: Project overview
- **UI_GUIDE.md**: Terminal interface features
- **config.yaml.template**: Configuration options with comments

---

## Quick Command Reference

```bash
# Run main pipeline
python selfai/selfai.py

# Interactive commands:
/plan <goal>              # Start planning phase
/memory                   # List memory categories
/memory clear <cat>       # Clear memory category
/switch <agent>           # Switch active agent
/planner list             # List planner backends
quit                      # Exit program
```

---

## System Requirements

- Python 3.12 (ARM64)
- Windows on ARM (preferred)
- 8GB+ RAM
- Optional: AnythingLLM Desktop, Ollama

---

**That's it! You're ready to go. Start with `python selfai/selfai.py` and explore.**

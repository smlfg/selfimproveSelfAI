# Agent Framework Comparison für SelfAI

**Datum**: 2025-01-21
**Ziel**: SelfAI zu einem echten Tool-Using Agent machen
**Kontext**: MiniMax Interface braucht Tool-Calling, smolagents bereits vorhanden

---

## 🎯 Requirements für SelfAI

1. **Tool-Calling Support**: Muss Tools automatisch aufrufen können
2. **MiniMax Kompatibilität**: Funktioniert mit custom LLM (nicht nur OpenAI)
3. **Existing Tools**: Nutzt vorhandene 15 Tools aus tool_registry.py
4. **UI Integration**: Kann Tool-Calls an UI melden
5. **Performance**: Nicht zu viele Extra-Calls
6. **Maintenance**: Aktiv maintained, stabile API

---

## 🔍 Agent Frameworks Übersicht

### 1. smolagents (Hugging Face) ⭐ BEREITS VORHANDEN

**Status**: `smolagents_runner.py` existiert bereits!

**Pros**:
- ✅ Bereits in SelfAI integriert
- ✅ Unterstützt custom LLM via Model Interface
- ✅ Leichtgewichtig (keine schweren Dependencies)
- ✅ Simple API (`ToolCallingAgent`)
- ✅ Tool schema aus tool_registry.py kompatibel
- ✅ Von Hugging Face maintained

**Cons**:
- ⚠️ Relativ neu (weniger mature als LangChain)
- ⚠️ Kleinere Community

**Code Example**:
```python
from smolagents import ToolCallingAgent, Tool

agent = ToolCallingAgent(
    model=custom_model,  # Works with MiniMax!
    tools=tools_list,
    max_steps=10
)

result = agent.run("Welche Tools hast du?")
# Agent calls list_selfai_files automatically!
```

**Integration Effort**: 🟢 Low (30-60 Min) - already has runner!

---

### 2. LangChain Agents

**Package**: `langchain`

**Pros**:
- ✅ Sehr mature, große Community
- ✅ Viele Beispiele und Tutorials
- ✅ Unterstützt custom LLMs via BaseChatModel
- ✅ Flexible Agent Types (ReAct, Structured, etc.)
- ✅ Built-in Tool-Calling

**Cons**:
- ❌ Sehr schwer (viele Dependencies)
- ❌ Komplexe API (viele Abstraktionen)
- ❌ Frequent breaking changes zwischen Versionen
- ❌ Overhead: viele interne Calls

**Code Example**:
```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import Tool

agent = create_tool_calling_agent(
    llm=custom_llm_wrapper,
    tools=tools,
    prompt=prompt_template
)

executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "Welche Tools hast du?"})
```

**Integration Effort**: 🟡 Medium (2-3 Hours) - complex wrapper needed

---

### 3. LlamaIndex Agents (ReAct Agent)

**Package**: `llama-index`

**Pros**:
- ✅ Gute RAG Integration (falls später needed)
- ✅ Unterstützt custom LLMs
- ✅ Einfachere API als LangChain
- ✅ ReAct Agent funktioniert gut

**Cons**:
- ⚠️ Fokus auf RAG/Retrieval (Overhead für reine Tool-Calling)
- ⚠️ Mittlere Dependencies
- ❌ Tools müssen als FunctionTool gewrappt werden

**Code Example**:
```python
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool

tools = [FunctionTool.from_defaults(fn=tool.run) for tool in tools_list]

agent = ReActAgent.from_tools(
    tools=tools,
    llm=custom_llm,
    verbose=True
)

result = agent.chat("Welche Tools hast du?")
```

**Integration Effort**: 🟡 Medium (1-2 Hours) - tool wrapping needed

---

### 4. Autogen (Microsoft)

**Package**: `pyautogen`

**Pros**:
- ✅ Multi-agent conversations
- ✅ Code execution capabilities
- ✅ Von Microsoft maintained

**Cons**:
- ❌ Overkill für single-agent use case
- ❌ Fokus auf multi-agent (nicht was wir brauchen)
- ❌ Komplexere Setup

**Integration Effort**: 🔴 High (3+ Hours) - too complex for our needs

---

### 5. OpenAI Assistants API (Native)

**Package**: `openai`

**Pros**:
- ✅ Native OpenAI Tool-Calling
- ✅ Sehr einfache API

**Cons**:
- ❌ NUR für OpenAI Models (nicht MiniMax!)
- ❌ Cloud-only (keine custom LLMs)
- ❌ Nicht relevant für SelfAI

**Integration Effort**: ❌ Not Applicable (doesn't support MiniMax)

---

### 6. CrewAI

**Package**: `crewai`

**Pros**:
- ✅ Multi-agent orchestration
- ✅ Role-based agents

**Cons**:
- ❌ Fokus auf multi-agent teams (Overkill)
- ❌ Wrapper um LangChain (noch mehr Overhead)
- ❌ Zu komplex für unseren Use Case

**Integration Effort**: 🔴 High - unnecessary complexity

---

### 7. Simple Custom Loop (DIY)

**No Package** - Pure Python

**Pros**:
- ✅ Volle Kontrolle
- ✅ Keine Dependencies
- ✅ Genau auf SelfAI zugeschnitten
- ✅ Leichtgewichtig

**Cons**:
- ❌ Müssen alles selbst bauen
- ❌ Tool-Call Parsing selbst implementieren
- ❌ Retry-Logik selbst bauen
- ❌ Mehr Maintenance

**Code Example**:
```python
def run_agent_loop(llm, user_input, tools, max_steps=10):
    for step in range(max_steps):
        response = llm.generate(user_input)

        # Parse tool call from response
        if "<tool_call>" in response:
            tool_name, args = parse_tool_call(response)
            result = execute_tool(tool_name, args)
            user_input = f"Tool result: {result}"
        else:
            return response  # Final answer

    return "Max steps reached"
```

**Integration Effort**: 🟡 Medium (2-3 Hours) - but full control

---

## 📊 Comparison Matrix

| Framework | Effort | MiniMax Support | Lightweight | Mature | Tool UI | Score |
|-----------|--------|-----------------|-------------|--------|---------|-------|
| **smolagents** | 🟢 Low | ✅ Yes | ✅ Yes | ⚠️ Medium | ✅ Easy | **9/10** ⭐ |
| **LangChain** | 🟡 Med | ✅ Yes | ❌ Heavy | ✅ High | ⚠️ Complex | 6/10 |
| **LlamaIndex** | 🟡 Med | ✅ Yes | ⚠️ Medium | ✅ High | ⚠️ Medium | 7/10 |
| **Autogen** | 🔴 High | ⚠️ Maybe | ❌ Heavy | ✅ High | ❌ Complex | 4/10 |
| **DIY Loop** | 🟡 Med | ✅ Yes | ✅ Yes | ❌ None | ✅ Full Control | 7/10 |
| **CrewAI** | 🔴 High | ⚠️ Maybe | ❌ Heavy | ⚠️ Medium | ❌ Complex | 3/10 |

---

## 🏆 Recommendation: smolagents + Custom Enhancements

### Why smolagents wins:

1. **Already Integrated**: `smolagents_runner.py` exists!
2. **Works with MiniMax**: Custom Model interface
3. **Lightweight**: No bloat, fast
4. **Easy UI Integration**: Simple to hook into tool calls
5. **Lowest Effort**: 30-60 min implementation

### Enhancement Strategy:

**Keep smolagents BUT enhance it with custom features:**

```python
# Enhanced smolagents runner with SelfAI features

class SelfAIAgent(ToolCallingAgent):
    """Enhanced smolagents agent with UI feedback."""

    def __init__(self, model, tools, ui=None, **kwargs):
        super().__init__(model, tools, **kwargs)
        self.ui = ui

    def execute_tool_call(self, tool_call):
        tool_name = tool_call.name
        args = tool_call.arguments

        # UI Feedback BEFORE execution
        if self.ui:
            self.ui.show_tool_call(tool_name, args)

        # Execute tool (original smolagents logic)
        result = super().execute_tool_call(tool_call)

        return result
```

**Benefits**:
- ✅ Best of both worlds: smolagents stability + custom control
- ✅ UI integration built-in
- ✅ Can add SelfAI-specific features later
- ✅ Minimal code changes

---

## 🚀 Implementation Plan (smolagents Enhanced)

### Phase 1: Core Integration (30 Min)

**File**: `selfai/core/selfai_agent.py` (NEW)

```python
"""SelfAI Enhanced Agent with Tool-Calling and UI Feedback."""

from smolagents import ToolCallingAgent
from typing import Any, Optional, List

class SelfAIAgent(ToolCallingAgent):
    """
    Enhanced smolagents ToolCallingAgent with:
    - UI feedback for tool calls
    - SelfAI-specific logging
    - Integration with tool_registry
    """

    def __init__(
        self,
        model,
        tools: List[Any],
        ui=None,
        max_steps: int = 10,
        verbose: bool = True,
        **kwargs
    ):
        super().__init__(
            model=model,
            tools=tools,
            max_steps=max_steps,
            **kwargs
        )
        self.ui = ui
        self.verbose = verbose

    def execute_tool_call(self, tool_call):
        """Override to add UI feedback."""
        tool_name = tool_call.name
        args = tool_call.arguments

        # UI Feedback (Auge-Emoji für Introspection Tools!)
        if self.ui:
            self.ui.show_tool_call(tool_name, args)

        # Optional: Verbose logging
        if self.verbose:
            print(f"[Agent] Executing: {tool_name}")

        # Execute tool via smolagents
        result = super().execute_tool_call(tool_call)

        return result
```

---

### Phase 2: SelfAI Main Loop Integration (30 Min)

**File**: `selfai/selfai.py`

```python
# At top
from selfai.core.selfai_agent import SelfAIAgent
from selfai.core.smolagents_runner import _SelfAIModel
from selfai.tools.tool_registry import get_all_tool_schemas

# In main loop configuration
ENABLE_AGENT_MODE = config.system.get('enable_agent_mode', True)

# Convert tools to smolagents format
def prepare_tools_for_agent():
    """Convert registered tools to smolagents format."""
    from selfai.tools.tool_registry import _TOOL_REGISTRY

    smol_tools = []
    for tool in _TOOL_REGISTRY.values():
        smol_tools.append(tool.to_smol_tool())

    return smol_tools

# In main loop - REPLACE direct LLM call with Agent
if not user_input.startswith('/') and ENABLE_AGENT_MODE:
    # Use SelfAI Agent instead of direct LLM
    if not hasattr(locals(), 'selfai_agent'):
        # Initialize agent once
        model = _SelfAIModel(llm_interface)
        tools = prepare_tools_for_agent()

        selfai_agent = SelfAIAgent(
            model=model,
            tools=tools,
            ui=ui,
            max_steps=10
        )

    # Run agent
    ui.start_spinner("SelfAI denkt nach...")
    try:
        response = selfai_agent.run(user_input)
        ui.stop_spinner()
        print(f"\nSelfAI: {response}")
    except Exception as e:
        ui.stop_spinner(f"Agent Fehler: {e}", "error")

else:
    # Fallback: Direct LLM call (for /commands or if agent disabled)
    # ... existing code ...
```

---

### Phase 3: Config Integration (5 Min)

**File**: `config.yaml`

```yaml
system:
  streaming_enabled: true
  enable_agent_mode: true  # NEW: Toggle agent on/off
  agent_max_steps: 10      # NEW: Max tool-calling iterations
  agent_verbose: true      # NEW: Verbose logging
```

---

## 🧪 Testing Plan

### Test 1: Basic Tool-Calling

```bash
python selfai/selfai.py
```

```
Du: Welche Tools hast du?

Expected:
👁️ 📁 Inspiziere Dateien: list_selfai_files → tools/
👁️ 📄 Lese Code: read_selfai_code → tools/tool_registry.py

SelfAI: Ich habe 15 registrierte Tools: ...
```

### Test 2: Multi-Step Reasoning

```
Du: Wie funktioniert dein Execution Dispatcher? Lies den Code!

Expected:
👁️ 🔍 Durchsuche Code: search_selfai_code → 'ExecutionDispatcher'
👁️ 📄 Lese Code: read_selfai_code → core/execution_dispatcher.py

SelfAI: Der ExecutionDispatcher ist in core/execution_dispatcher.py...
```

### Test 3: Aider Integration

```
Du: Füge eine Funktion add(a, b) zu math_utils.py hinzu

Expected:
🤖 Aider Task: run_aider_task

SelfAI: Ich habe Aider aufgerufen...
```

---

## 📈 Benefits

### With Agent Framework:

**Before** (Direct LLM):
```
User: Welche Tools hast du?
MiniMax: Ich habe verschiedene Tools... (HALLUZINATION)
```

**After** (Agent + Tools):
```
User: Welche Tools hast du?
Agent: 👁️ 📁 list_selfai_files("tools")
        👁️ 📄 read_selfai_code("tools/tool_registry.py")
        → "Ich habe 15 Tools: ..." (FACTUAL!)
```

### Advantages:

1. ✅ **Autonomous Tool Usage**: Agent entscheidet WANN Tools zu nutzen
2. ✅ **No Hallucinations**: Liest echten Code statt zu raten
3. ✅ **Visual Feedback**: User sieht was passiert (Auge-Emoji!)
4. ✅ **Multi-Step Reasoning**: Agent kann mehrere Tools kombinieren
5. ✅ **Introspection Tools WORK**: Self-Awareness funktioniert!

---

## 🎯 Timeline

| Phase | Aufgabe | Zeit | Status |
|-------|---------|------|--------|
| 1 | Create `selfai_agent.py` | 30 Min | 🔜 Next |
| 2 | Integrate into `selfai.py` | 30 Min | 🔜 Next |
| 3 | Add config options | 5 Min | 🔜 Next |
| 4 | Test introspection tools | 15 Min | 🔜 Next |
| 5 | Document & refine | 10 Min | 🔜 Next |
| **Total** | | **90 Min** | |

---

## 🔄 Alternative: Hybrid Approach

**If smolagents has issues**, fallback to:

### DIY Tool-Calling Loop

```python
def run_selfai_agent(llm, user_input, tools, ui, max_steps=10):
    """Custom lightweight agent loop."""

    history = []

    for step in range(max_steps):
        # 1. Get LLM response with tool options
        prompt = build_prompt_with_tools(user_input, tools, history)
        response = llm.generate(prompt)

        # 2. Check if tool call in response
        tool_call = parse_tool_call(response)

        if tool_call:
            tool_name, args = tool_call

            # UI Feedback
            ui.show_tool_call(tool_name, args)

            # Execute
            result = execute_tool(tool_name, args, tools)

            # Add to history
            history.append({
                "tool": tool_name,
                "args": args,
                "result": result
            })

            # Continue with result
            user_input = f"Tool result: {result}. Continue."
        else:
            # Final answer
            return response

    return "Max steps reached"
```

**Effort**: 2-3 Hours
**Use if**: smolagents incompatible with MiniMax API

---

## ✅ Final Recommendation

### Primary: smolagents Enhanced (90 Min) ⭐

**Why**:
- Already have `smolagents_runner.py`
- Proven to work with custom LLMs
- Lightweight, fast
- UI integration trivial
- Lowest risk

**Implementation**:
1. Create `SelfAIAgent` class (extends ToolCallingAgent)
2. Add UI callbacks
3. Integrate into main loop
4. Test with introspection tools

### Fallback: DIY Loop (if needed)

**Use if**: smolagents doesn't work well with MiniMax

---

**Created**: 2025-01-21
**Next Action**: Implement `SelfAIAgent` with smolagents
**Expected Result**: SelfAI becomes autonomous tool-using agent with visual feedback!

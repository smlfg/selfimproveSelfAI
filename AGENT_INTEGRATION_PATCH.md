# Agent Integration Patch für selfai.py

**Datum**: 2025-01-21
**Ziel**: Füge Tool-Calling Agent in normalen Chat ein

---

## Änderungen in selfai.py

### 1. Imports hinzufügen (nach Zeile 30)

```python
# Agent Framework Integration
from selfai.core.selfai_agent import create_selfai_agent
from selfai.tools.tool_registry import get_tools_for_agent
```

### 2. Agent Initialisierung (nach Zeile 300, nach llm_interface Setup)

```python
# =============================================================================
# Agent Setup (Tool-Calling)
# =============================================================================

# Config option für Agent Mode
ENABLE_AGENT_MODE = config.system.get('enable_agent_mode', True)
AGENT_MAX_STEPS = config.system.get('agent_max_steps', 10)
AGENT_VERBOSE = config.system.get('agent_verbose', False)

selfai_agent = None  # Will be initialized on first use

if ENABLE_AGENT_MODE:
    ui.status("Agent-Modus aktiviert: SelfAI kann Tools nutzen!", "info")
```

### 3. Normal Chat Ersetzung (Zeile 2415-2550 ersetzen)

**VORHER** (Zeile 2415):
```python
        system_prompt = agent_manager.active_agent.system_prompt
        history = memory_system.load_relevant_context(
            agent_manager.active_agent,
            user_input,
            limit=2,
        )
        response_text = None
        streamed = False
        last_error = None
        order = [active_chat_backend_index] + [
            idx for idx in range(len(execution_backends)) if idx != active_chat_backend_index
        ]

        for backend_index in order:
            backend = execution_backends[backend_index]
            # ... direct LLM call ...
```

**NACHHER**:
```python
        # =============================================================================
        # Normal Chat with Agent (Tool-Calling)
        # =============================================================================

        system_prompt = agent_manager.active_agent.system_prompt
        response_text = None
        last_error = None

        # AGENT MODE: Use tool-calling agent
        if ENABLE_AGENT_MODE and llm_interface:
            try:
                # Initialize agent lazily (once per session)
                if selfai_agent is None:
                    ui.status("Initialisiere Agent mit Tools...", "info")

                    # Get all tools in smolagents format
                    tools = get_tools_for_agent()
                    ui.status(f"✅ {len(tools)} Tools geladen", "success")

                    # Create agent
                    selfai_agent = create_selfai_agent(
                        llm_interface=llm_interface,
                        tools=tools,
                        ui=ui,
                        max_steps=AGENT_MAX_STEPS,
                        verbose=AGENT_VERBOSE,
                    )

                # Run agent with user input
                ui.start_spinner("Agent denkt nach und nutzt Tools...")

                # Agent automatically calls tools as needed!
                response_text = selfai_agent.run(user_input)

                ui.stop_spinner()

                # Display response
                print(f"\n{ui.colorize('SelfAI', 'magenta')}: {response_text}\n")

                # Save to memory
                memory_system.save_conversation(
                    agent_manager.active_agent,
                    user_input,
                    response_text,
                )

            except Exception as e:
                ui.stop_spinner(f"Agent-Fehler: {e}", "error")
                last_error = str(e)

                # Fallback to direct LLM (code below)
                ui.status("Fallback: Nutze direkten LLM-Call ohne Tools", "warning")
                selfai_agent = None  # Reset agent
                ENABLE_AGENT_MODE = False  # Disable for this session

        # FALLBACK MODE: Direct LLM call (no tools)
        if not ENABLE_AGENT_MODE or response_text is None:
            # Original code: direct LLM streaming/generation
            history = memory_system.load_relevant_context(
                agent_manager.active_agent,
                user_input,
                limit=2,
            )
            streamed = False
            order = [active_chat_backend_index] + [
                idx for idx in range(len(execution_backends)) if idx != active_chat_backend_index
            ]

            for backend_index in order:
                backend = execution_backends[backend_index]
                # ... rest of existing code (streaming, etc.) ...
```

---

## Config Changes (config.yaml)

```yaml
system:
  streaming_enabled: true
  enable_agent_mode: true   # NEW: Enable tool-calling agent
  agent_max_steps: 10       # NEW: Max tool iterations
  agent_verbose: false      # NEW: Verbose logging
```

---

## Komplette Integration (Minimal)

**Für schnellste Integration** - füge NUR dies nach Zeile 2414 ein:

```python
        # === AGENT MODE (Tool-Calling) ===
        if config.system.get('enable_agent_mode', True) and llm_interface:
            try:
                from selfai.core.selfai_agent import create_selfai_agent
                from selfai.tools.tool_registry import get_tools_for_agent

                # Initialize agent (once)
                if not hasattr(self, '_agent'):
                    tools = get_tools_for_agent()
                    self._agent = create_selfai_agent(
                        llm_interface=llm_interface,
                        tools=tools,
                        ui=ui,
                        max_steps=10
                    )

                # Run with tools!
                ui.start_spinner("Agent arbeitet...")
                response_text = self._agent.run(user_input)
                ui.stop_spinner()

                print(f"\nSelfAI: {response_text}\n")

                memory_system.save_conversation(
                    agent_manager.active_agent,
                    user_input,
                    response_text,
                )
                continue  # Skip fallback code

            except Exception as e:
                ui.status(f"Agent-Fehler: {e}, nutze Fallback", "warning")
                # Falls through to original code below

        # === ORIGINAL CODE (Fallback) ===
        system_prompt = agent_manager.active_agent.system_prompt
        # ... rest of existing code ...
```

**Das war's!** Nur ~30 Zeilen Code, Agent funktioniert!

---

## Testing

```bash
python selfai/selfai.py
```

```
Du: Welche Tools hast du?

Expected Output:
👁️ 📁 Inspiziere Dateien: list_selfai_files → tools/
👁️ 📄 Lese Code: read_selfai_code → tools/tool_registry.py

SelfAI: Ich habe 15 registrierte Tools:
1. get_current_weather
2. list_selfai_files
3. read_selfai_code
...
```

**Tools werden automatisch genutzt!** 🎉

---

**Created**: 2025-01-21
**Integration Complexity**: 🟢 MINIMAL (30 Zeilen)

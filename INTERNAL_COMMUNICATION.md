# SelfAI Internal Communication & Data Flow

Vollständige technische Dokumentation der internen Kommunikationsstruktur, Datenflüsse und Komponenten-Interaktionen.

---

## Table of Contents

1. [Startup & Initialization](#1-startup--initialization)
2. [Normal Chat Flow](#2-normal-chat-flow-ohne-plan)
3. [DPPM Pipeline Flow](#3-dppm-pipeline-flow-mit-plan)
4. [Tool Execution (Smolagents)](#4-tool-execution-smolagents)
5. [External Process Communication](#5-external-process-communication)
6. [Memory System](#6-memory-system)
7. [Context Loading](#7-context-loading)
8. [Parallel Execution](#8-parallel-execution)
9. [Error Handling & Retry](#9-error-handling--retry)
10. [Data Structures](#10-data-structures)

---

## 1. Startup & Initialization

### Entry Point: `main()` in `selfai/selfai.py:1077`

```
python selfai/selfai.py
    ↓
main() function executes
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 1: Initialize UI                               │
│ ui = TerminalUI()                                   │
│ - Singleton for all output operations               │
│ - Methods: status(), stream_prefix(), typing_anim() │
│ - NOT thread-safe (but output is serialized)        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: Initialize AgentManager                     │
│ agent_manager = AgentManager(agents_dir)            │
│                                                     │
│ Scans: agents/ directory                            │
│ For each subdirectory:                              │
│   - Reads system_prompt.md → agent.system_prompt    │
│   - Reads memory_categories.txt → List[str]         │
│   - Reads workspace_slug.txt → str                  │
│   - Reads description.txt → str                     │
│                                                     │
│ Creates: List[Agent] objects                        │
│ Storage: In-memory list                             │
│ Active: agent_manager.active_agent (Agent | None)   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: Initialize MemorySystem                     │
│ memory_system = MemorySystem(memory_dir)            │
│                                                     │
│ Structure: memory/                                  │
│   ├── {category}/                                   │
│   │   └── {agent}_{timestamp}.txt                   │
│   └── plans/                                        │
│       └── {timestamp}_{goal}.json                   │
│                                                     │
│ Methods:                                            │
│   - save_conversation() → writes .txt file          │
│   - load_relevant_context() → reads + filters       │
│   - save_plan() → writes .json file                 │
│                                                     │
│ Storage: Filesystem (NO database!)                  │
│                                                     │
│ NEW: Context Window                                 │
│   - session_start = datetime.now()                  │
│   - context_window_minutes = 30 (default)           │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: Initialize TokenLimits                      │
│ token_limits = TokenLimits()                        │
│ token_limits.set_balanced()  # Default profile      │
│                                                     │
│ Fields (all int):                                   │
│   - planner_max_tokens: 768                         │
│   - execution_max_tokens: 512                       │
│   - merge_max_tokens: 2048                          │
│   - tool_creation_max_tokens: 1024                  │
│   - error_correction_max_tokens: 1024               │
│   - selfimprove_max_tokens: 2048                    │
│   - chat_max_tokens: 1024                           │
│                                                     │
│ Storage: In-memory (runtime only)                   │
│ Control: /tokens, /extreme commands                 │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 5: Load LLM Backends                           │
│ execution_backends: List[Dict]                      │
│                                                     │
│ Priority Order:                                     │
│ 1. MiniMax (Cloud API)                              │
│    if config.minimax:                               │
│      interface = MinimaxInterface(...)              │
│      execution_backends.append({                    │
│        "interface": interface,                      │
│        "label": "MiniMax",                          │
│        "name": "minimax",                           │
│        "type": "cloud"                              │
│      })                                             │
│                                                     │
│ 2. CPU Fallback (llama-cpp-python)                  │
│    if config.cpu_fallback:                          │
│      interface = LocalLLMInterface(...)             │
│      execution_backends.append({                    │
│        "interface": interface,                      │
│        "label": "CPU Fallback",                     │
│        "name": "cpu",                               │
│        "type": "local"                              │
│      })                                             │
│                                                     │
│ Result: At least 1 backend must be available        │
│ Fallback Chain: MiniMax → CPU                       │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 6: Load Planner Providers (Optional)           │
│ planner_providers: Dict[str, Dict]                  │
│                                                     │
│ Example:                                            │
│ {                                                   │
│   "minimax-planner": {                              │
│     "interface": PlannerMinimaxInterface(...),      │
│     "type": "minimax",                              │
│     "model": "abab6.5s-chat",                       │
│     "max_tokens": 768,                              │
│     "base_url": "...",                              │
│     "timeout": 180.0                                │
│   }                                                 │
│ }                                                   │
│                                                     │
│ Active: active_planner_provider (str | None)        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 7: Load Merge Providers (Optional)             │
│ merge_providers: Dict[str, Dict]                    │
│ Similar structure to planner_providers              │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 8: Enter Main Loop                             │
│ while True:                                         │
│   user_input = input("\nDu: ")                      │
│   # Process commands or chat                        │
└─────────────────────────────────────────────────────┘
```

---

## 2. Normal Chat Flow (OHNE /plan)

### User Input: "Erkläre mir Python"

```
User types: "Erkläre mir Python"
    ↓
input() returns string
    ↓
Check for commands (/, quit)
    ↓ No command → Normal Chat
┌─────────────────────────────────────────────────────┐
│ Load Context from Memory                            │
│ history = memory_system.load_relevant_context(      │
│     agent=active_agent,                             │
│     context_hint=user_input,                        │
│     limit=5                                         │
│ )                                                   │
│                                                     │
│ Internal Process:                                   │
│ 1. Get candidate files from agent.memory_categories │
│ 2. Filter by time: mtime >= cutoff (NEW!)          │
│ 3. Extract tags from current input                  │
│ 4. Score each file by tag overlap                   │
│ 5. Filter by threshold (0.35)                       │
│ 6. Sort by (score, mtime) DESC                      │
│ 7. Take top N, re-sort chronologically              │
│                                                     │
│ Returns: List[Dict[str, str]]                       │
│ [                                                   │
│   {"role": "user", "content": "Previous Q"},        │
│   {"role": "assistant", "content": "Previous A"},   │
│   ...                                               │
│ ]                                                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Select Backend                                      │
│ backend = execution_backends[active_index]          │
│ interface = backend["interface"]  # MinimaxInterface│
│ label = backend["label"]  # "MiniMax"               │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Check Streaming Support                             │
│ use_stream = hasattr(interface, "stream_generate")  │
│                                                     │
│ If streaming:                                       │
│   for chunk in interface.stream_generate_response():│
│     ui.streaming_chunk(chunk)                       │
│   response = "".join(chunks)                        │
│                                                     │
│ Else (blocking):                                    │
│   response = interface.generate_response(...)       │
│   ui.typing_animation(response)                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ LLM Interface (MinimaxInterface)                    │
│                                                     │
│ Build Request:                                      │
│ {                                                   │
│   "model": "abab6.5s-chat",                         │
│   "messages": [                                     │
│     {                                               │
│       "role": "system",                             │
│       "content": agent.system_prompt                │
│     },                                              │
│     ...history messages...,                         │
│     {                                               │
│       "role": "user",                               │
│       "content": user_input                         │
│     }                                               │
│   ],                                                │
│   "max_tokens": token_limits.chat_max_tokens,      │
│   "temperature": 0.7,                               │
│   "stream": true                                    │
│ }                                                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ HTTP POST to MiniMax API                            │
│ POST https://api.minimax.chat/v1/text/chatcompletion│
│ Headers:                                            │
│   Authorization: Bearer {api_key}                   │
│   Content-Type: application/json                    │
│                                                     │
│ Response (SSE Stream):                              │
│ data: {"choices":[{"delta":{"content":"Python"}}]}  │
│ data: {"choices":[{"delta":{"content":" ist"}}]}    │
│ data: {"choices":[{"delta":{"content":"..."}}]}     │
│ data: [DONE]                                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stream Processing                                   │
│ for line in response_stream:                        │
│   if line.startswith("data: "):                     │
│     json_str = line[6:]  # Remove "data: "          │
│     if json_str == "[DONE]":                        │
│       break                                         │
│     data = json.loads(json_str)                     │
│     chunk = data["choices"][0]["delta"]["content"]  │
│     yield chunk  # Generator pattern                │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Display Output                                      │
│ ui.stream_prefix("MiniMax")  # Shows "MiniMax: "    │
│ ui.streaming_chunk("Python")                        │
│ ui.streaming_chunk(" ist")                          │
│ ui.streaming_chunk("...")                           │
│ print()  # Newline after stream complete            │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Save to Memory                                      │
│ memory_system.save_conversation(                    │
│     agent=active_agent,                             │
│     user_message=user_input,                        │
│     assistant_message=response                      │
│ )                                                   │
│                                                     │
│ Internal Process:                                   │
│ 1. Determine category (agent.memory_categories[0])  │
│ 2. Create category dir: memory/{category}/          │
│ 3. Generate filename: {slug}_{timestamp}.txt        │
│ 4. Extract tags from conversation                   │
│ 5. Format content:                                  │
│    ---                                              │
│    Agent: {display_name}                            │
│    AgentKey: {key}                                  │
│    Timestamp: {iso_datetime}                        │
│    Tags: {tags}                                     │
│    ---                                              │
│    System Prompt:                                   │
│    {system_prompt}                                  │
│    ---                                              │
│    User:                                            │
│    {user_message}                                   │
│    ---                                              │
│    SelfAI:                                          │
│    {assistant_message}                              │
│ 6. Write to file                                    │
│                                                     │
│ Result: Path to saved file                          │
│ Example: memory/code_helfer/main_20250118-142305.txt│
└─────────────────────────────────────────────────────┘
    ↓
Back to Main Loop (while True)
```

### Data Flow Diagram:

```
┌─────────┐
│  User   │
└────┬────┘
     │ "Erkläre Python"
     ↓
┌────────────┐
│ Main Loop  │
└─────┬──────┘
      │
      ├─→ MemorySystem.load_relevant_context()
      │   └─→ Returns: history (List[Dict])
      │
      ├─→ Backend.generate_response()
      │   ├─→ HTTP POST to MiniMax API
      │   ├─→ SSE Stream Response
      │   └─→ Returns: response (str)
      │
      ├─→ UI.display()
      │   └─→ Terminal Output
      │
      └─→ MemorySystem.save_conversation()
          └─→ Filesystem Write
```

---

## 3. DPPM Pipeline Flow (MIT /plan)

### User Input: "/plan Build REST API"

```
User types: "/plan Build REST API"
    ↓
Detect command: startswith("/plan")
    ↓
Extract goal: "Build REST API"
    ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING                                   │
│ Goal: Decompose into subtasks                       │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Build PlannerContext                                │
│ context = PlannerContext(                           │
│     available_agents=[                              │
│         {"key": "code_helfer", "description": "..."} │
│         {"key": "architect", "description": "..."}   │
│     ],                                              │
│     available_engines=["minimax", "smolagent"],     │
│     memory_summary="15 recent conversations",       │
│     system_info={                                   │
│         "os": "linux",                              │
│         "ram_gb": 16,                               │
│         "cpu_cores": 8                              │
│     }                                               │
│ )                                                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Call Planner                                        │
│ plan_data = planner_interface.plan(                 │
│     goal=goal_text,                                 │
│     context=planner_context,                        │
│     progress_callback=ui.streaming_chunk            │
│ )                                                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ PlannerMinimaxInterface.plan()                      │
│                                                     │
│ Step 1: Build Prompt Template                       │
│ """                                                 │
│ You are a DPPM task planner.                        │
│                                                     │
│ GOAL: {goal}                                        │
│                                                     │
│ AVAILABLE AGENTS:                                   │
│ - code_helfer: Coding assistant                     │
│ - architect: System design                          │
│                                                     │
│ AVAILABLE ENGINES:                                  │
│ - minimax: LLM text generation                      │
│ - smolagent: Tool-calling agent                     │
│                                                     │
│ CONTEXT:                                            │
│ {memory_summary}                                    │
│ {system_info}                                       │
│                                                     │
│ Generate JSON plan:                                 │
│ {                                                   │
│   "subtasks": [                                     │
│     {                                               │
│       "id": "S1",                                   │
│       "title": "...",                               │
│       "objective": "...",                           │
│       "agent_key": "architect",                     │
│       "engine": "minimax",                          │
│       "parallel_group": 1,                          │
│       "depends_on": []                              │
│     }                                               │
│   ],                                                │
│   "merge": {                                        │
│     "strategy": "..."                               │
│   }                                                 │
│ }                                                   │
│ """                                                 │
│                                                     │
│ Step 2: HTTP POST to MiniMax                        │
│ max_tokens: token_limits.planner_max_tokens (768)   │
│                                                     │
│ Step 3: Parse JSON Response                         │
│ response_text = llm_response                        │
│ # Extract JSON (remove markdown if present)         │
│ plan_data = json.loads(response_text)               │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ LLM Returns Plan (Example)                          │
│ {                                                   │
│   "subtasks": [                                     │
│     {                                               │
│       "id": "S1",                                   │
│       "title": "Design API Schema",                 │
│       "objective": "Define REST endpoints...",      │
│       "agent_key": "architect",                     │
│       "engine": "minimax",                          │
│       "parallel_group": 1,                          │
│       "depends_on": []                              │
│     },                                              │
│     {                                               │
│       "id": "S2",                                   │
│       "title": "Implement Routes",                  │
│       "objective": "Code Flask routes...",          │
│       "agent_key": "code_helfer",                   │
│       "engine": "smolagent",                        │
│       "parallel_group": 2,                          │
│       "depends_on": ["S1"],                         │
│       "tools": ["run_aider_task"]                   │
│     },                                              │
│     {                                               │
│       "id": "S3",                                   │
│       "title": "Write Tests",                       │
│       "objective": "Create pytest tests...",        │
│       "agent_key": "code_helfer",                   │
│       "engine": "minimax",                          │
│       "parallel_group": 2,                          │
│       "depends_on": ["S1"]                          │
│     }                                               │
│   ],                                                │
│   "merge": {                                        │
│     "strategy": "Combine schema + code + tests"     │
│   }                                                 │
│ }                                                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Validate Plan                                       │
│ validate_plan_structure(                            │
│     plan_data,                                      │
│     allowed_agent_keys=["code_helfer", "architect"],│
│     allowed_engines=["minimax", "smolagent"]        │
│ )                                                   │
│                                                     │
│ Validation Checks:                                  │
│ 1. All subtasks have required fields                │
│ 2. Agent keys exist in agent_manager                │
│ 3. Engine types are supported                       │
│ 4. No circular dependencies (DFS algorithm)         │
│ 5. depends_on references valid task IDs             │
│ 6. parallel_group is valid integer                  │
│                                                     │
│ Raises: PlanValidationError if invalid             │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Save Plan to Disk                                   │
│ timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")│
│ goal_slug = sanitize_goal("Build REST API")         │
│ filename = f"{timestamp}_{goal_slug}.json"          │
│ plan_path = memory/plans/{filename}                 │
│                                                     │
│ plan_path.write_text(json.dumps(plan_data, indent=2))│
│                                                     │
│ Example: memory/plans/20250118-142305_build-rest-api.json│
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTION                                  │
│ Goal: Execute each subtask                          │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Create ExecutionDispatcher                          │
│ dispatcher = ExecutionDispatcher(                   │
│     plan_path=plan_path,                            │
│     agent_manager=agent_manager,                    │
│     memory_system=memory_system,                    │
│     llm_backends=execution_backends,                │
│     ui=ui,                                          │
│     max_output_tokens=token_limits.execution        │
│ )                                                   │
│                                                     │
│ Loads plan_data from JSON file                      │
│ Extracts: subtasks, merge strategy                  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ dispatcher.run()                                    │
│                                                     │
│ Step 1: Group by parallel_group                     │
│ groups = defaultdict(list)                          │
│ for task in subtasks:                               │
│     groups[task["parallel_group"]].append(task)     │
│                                                     │
│ Result:                                             │
│ {                                                   │
│   1: [S1],        # Sequential group                │
│   2: [S2, S3]     # Parallel group                  │
│ }                                                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Execute Group 1 (Sequential)                        │
│                                                     │
│ for task in group[1]:  # Only S1                    │
│   # Check dependencies                              │
│   for dep_id in task["depends_on"]:                 │
│     if get_task_status(dep_id) != "completed":      │
│       raise ExecutionError("Dependency not met")    │
│                                                     │
│   # Execute                                         │
│   response = _run_subtask(task)                     │
│   task["status"] = "completed"                      │
│   task["result_path"] = save_result(response)       │
│   save_plan()  # Update JSON                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ _run_subtask(S1)                                    │
│                                                     │
│ 1. Get Agent                                        │
│    agent = agent_manager.get("architect")           │
│                                                     │
│ 2. Load Context                                     │
│    history = memory_system.load_relevant_context(   │
│        agent,                                       │
│        hint=S1["objective"],                        │
│        limit=2                                      │
│    )                                                │
│                                                     │
│ 3. Build Prompt                                     │
│    prompt = f"Subtask S1: {S1['objective']}"        │
│    prompt += f"\nNOTES: {S1.get('notes', '')}"      │
│                                                     │
│ 4. Route by Engine                                  │
│    if S1["engine"] == "minimax":                    │
│        response = _invoke_llm(agent, prompt, hist)  │
│    elif S1["engine"] == "smolagent":                │
│        response = _run_smolagent(...)               │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ _invoke_llm()                                       │
│                                                     │
│ Try backends in fallback order:                     │
│ for backend in [MiniMax, CPU]:                      │
│   try:                                              │
│     response = backend.interface.generate_response( │
│         system_prompt=agent.system_prompt,          │
│         user_prompt=prompt,                         │
│         history=history,                            │
│         max_output_tokens=token_limits.execution    │
│     )                                               │
│     return response  # Success!                     │
│   except Exception as e:                            │
│     continue  # Try next backend                    │
│                                                     │
│ raise ExecutionError("All backends failed")         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Save Subtask Result                                 │
│ result_path = memory_system.save_conversation(      │
│     agent=architect,                                │
│     user_message=prompt,                            │
│     assistant_message=response                      │
│ )                                                   │
│                                                     │
│ File: memory/architect/main_20250118-142310.txt     │
│                                                     │
│ Update Plan JSON:                                   │
│ S1["status"] = "completed"                          │
│ S1["result_path"] = str(result_path)                │
│ plan_path.write_text(json.dumps(plan_data))         │
│                                                     │
│ return response                                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Execute Group 2 (PARALLEL!)                         │
│                                                     │
│ Tasks: [S2, S3]                                     │
│                                                     │
│ Check dependencies for all tasks:                   │
│ S2.depends_on = ["S1"] → Check S1.status == "completed" ✓│
│ S3.depends_on = ["S1"] → Check S1.status == "completed" ✓│
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ ThreadPoolExecutor                                  │
│ with ThreadPoolExecutor(max_workers=2):             │
│                                                     │
│   futures = {}                                      │
│   for task in [S2, S3]:                             │
│     future = executor.submit(_run_subtask, task)    │
│     futures[future] = task                          │
│                                                     │
│   Thread 1: _run_subtask(S2) ← PARALLEL!            │
│   Thread 2: _run_subtask(S3) ← PARALLEL!            │
│                                                     │
│   Both execute simultaneously!                      │
│   No shared state (except plan JSON with locks)     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Wait for Completion                                 │
│                                                     │
│ results = {}                                        │
│ for future in as_completed(futures):                │
│   task = futures[future]                            │
│   task_id = task["id"]                              │
│   try:                                              │
│     response = future.result()  # Get result        │
│     results[task_id] = (task, response)             │
│     ui.status(f"✓ Task {task_id} completed")        │
│   except Exception as exc:                          │
│     ui.status(f"✗ Task {task_id} failed: {exc}")    │
│     executor.shutdown(cancel_futures=True)          │
│     raise ExecutionError(f"Task {task_id} failed")  │
│                                                     │
│ Order of completion: UNPREDICTABLE                  │
│ S3 might finish before S2!                          │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Display Results SEQUENTIALLY (NEW!)                 │
│                                                     │
│ Sort tasks by ID: [S2, S3]                          │
│                                                     │
│ ui.status(f"📊 Ergebnisse (Gruppe 2):")             │
│                                                     │
│ for task in sorted([S2, S3], key=lambda t: t["id"]):│
│   task_id = task["id"]                              │
│   _, response = results[task_id]                    │
│   _display_subtask_result(task_id, task["title"],   │
│                           response)                 │
│                                                     │
│ Output (user sees):                                 │
│ ────────────────────────────────────────            │
│ 📊 Subtask S2: Implement Routes                     │
│ ────────────────────────────────────────            │
│ Flask routes implemented...                         │
│ ────────────────────────────────────────            │
│                                                     │
│ ────────────────────────────────────────            │
│ 📊 Subtask S3: Write Tests                          │
│ ────────────────────────────────────────            │
│ Pytest tests created...                             │
│ ────────────────────────────────────────            │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 3: MERGE                                      │
│ Goal: Synthesize all results                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Collect Subtask Results                             │
│                                                     │
│ subtask_results = []                                │
│ for subtask in plan_data["subtasks"]:               │
│   if subtask.get("result_path"):                    │
│     result_file = Path(subtask["result_path"])      │
│     content = result_file.read_text()               │
│     subtask_results.append({                        │
│       "id": subtask["id"],                          │
│       "title": subtask["title"],                    │
│       "result": content[:2000]  # First 2K chars    │
│     })                                              │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ MergeMinimaxInterface.merge()                       │
│                                                     │
│ Build Merge Prompt:                                 │
│ """                                                 │
│ Synthesize these subtask results into coherent      │
│ final answer:                                       │
│                                                     │
│ ORIGINAL GOAL: {goal}                               │
│                                                     │
│ SUBTASK RESULTS:                                    │
│                                                     │
│ S1 (Design API Schema):                             │
│ {S1_result}                                         │
│                                                     │
│ S2 (Implement Routes):                              │
│ {S2_result}                                         │
│                                                     │
│ S3 (Write Tests):                                   │
│ {S3_result}                                         │
│                                                     │
│ MERGE STRATEGY: {merge.strategy}                    │
│                                                     │
│ Create comprehensive final response that:           │
│ 1. Summarizes what was accomplished                 │
│ 2. Shows how parts fit together                     │
│ 3. Provides next steps if needed                    │
│ """                                                 │
│                                                     │
│ HTTP POST to MiniMax:                               │
│ max_tokens: token_limits.merge_max_tokens (2048)    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ LLM Returns Synthesis                               │
│ """                                                 │
│ I've successfully built a complete REST API:        │
│                                                     │
│ 1. API Design (S1):                                 │
│    Created RESTful schema with endpoints for...     │
│                                                     │
│ 2. Implementation (S2):                             │
│    Implemented Flask routes with...                 │
│                                                     │
│ 3. Testing (S3):                                    │
│    Comprehensive test suite with...                 │
│                                                     │
│ The system is production-ready!                     │
│ """                                                 │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Display & Save Merge Result                         │
│ ui.stream_prefix("MiniMax-Merge")                   │
│ ui.typing_animation(merged_response)                │
│                                                     │
│ memory_system.save_conversation(                    │
│     agent=merge_agent,                              │
│     user_message="Merge results",                   │
│     assistant_message=merged_response               │
│ )                                                   │
│                                                     │
│ Update Plan Metadata:                               │
│ plan_data["metadata"]["merge_result_path"] = ...    │
│ save_plan()                                         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 4: JUDGE (Optional)                           │
│ Goal: Evaluate execution quality                    │
└─────────────────────────────────────────────────────┘
    ↓
[See Section 5 for Judge details]
    ↓
Back to Main Loop
```

### DPPM Data Flow Diagram:

```
User: "/plan Build REST API"
    ↓
┌────────────────────┐
│  Planner Phase     │
│  (Decompose)       │
└────────┬───────────┘
         │ plan_data.json
         ↓
┌────────────────────┐
│ Execution Phase    │
│  (Parallel)        │
│                    │
│  Group 1:          │
│    S1 (seq)        │
│  Group 2:          │
│    S2 ║ S3         │
│    (parallel!)     │
└────────┬───────────┘
         │ results
         ↓
┌────────────────────┐
│  Merge Phase       │
│  (Synthesis)       │
└────────┬───────────┘
         │ final_answer
         ↓
┌────────────────────┐
│  Judge Phase       │
│  (Evaluation)      │
└────────────────────┘
```

---

## 4. Tool Execution (Smolagents)

### When engine="smolagent" in subtask:

```
ExecutionDispatcher._run_subtask(task)
    ↓
if task["engine"] == "smolagent":
    ↓
┌─────────────────────────────────────────────────────┐
│ _run_smolagent(task, agent, prompt, history)        │
│                                                     │
│ Extract:                                            │
│ tool_names = task.get("tools", [])                  │
│ # e.g., ["run_aider_task", "read_project_file"]     │
│                                                     │
│ max_steps = task.get("max_steps", 12)               │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ SmolAgentRunner.__init__()                          │
│                                                     │
│ 1. Load tools from tool_registry                    │
│    from selfai.tools.tool_registry import get_tool  │
│    tools = [get_tool(name) for name in tool_names]  │
│                                                     │
│ 2. Convert to smolagents.Tool format                │
│    smol_tools = [tool.to_smol_tool() for tool...]   │
│                                                     │
│ 3. Wrap LLM backend as smolagents.Model             │
│    model = _SelfAIModel(llm_interface)              │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ SmolAgentRunner.run()                               │
│                                                     │
│ agent = ToolCallingAgent(                           │
│     tools=smol_tools,                               │
│     model=model,                                    │
│     max_steps=max_steps                             │
│ )                                                   │
│                                                     │
│ result = agent.run(task=prompt)                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ ToolCallingAgent (smolagents library)               │
│                                                     │
│ Loop (max max_steps iterations):                    │
│                                                     │
│ Step 1: Call LLM with tools schema                  │
│   messages = [                                      │
│     {"role": "system", "content": system_prompt},   │
│     {"role": "user", "content": task},              │
│   ]                                                 │
│                                                     │
│   llm_response = model.generate(messages, tools)    │
│                                                     │
│ Step 2: Parse response for tool calls               │
│   if "[TOOL_CALL]" in llm_response:                 │
│     # Extract: {"tool": "run_aider_task", ...}      │
│     tool_call = parse_tool_call(llm_response)       │
│                                                     │
│ Step 3: Execute tool                                │
│     tool = get_tool(tool_call["tool"])              │
│     result = tool.run(**tool_call["arguments"])     │
│                                                     │
│ Step 4: Inject result back into conversation        │
│     messages.append({                               │
│       "role": "tool",                               │
│       "content": result,                            │
│       "tool_call_id": tool_call["id"]               │
│     })                                              │
│                                                     │
│ Step 5: Continue loop                               │
│   if "[FINAL_ANSWER]" in llm_response:              │
│     break  # Done!                                  │
│                                                     │
│ Return: Final answer text                           │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Tool Execution Example: run_aider_task              │
│                                                     │
│ def run_aider_task(task_description, files="", ...) │
│                                                     │
│   subprocess.run([                                  │
│     "aider",                                        │
│     "--model", "openai/MiniMax-M2",                 │
│     "--message", task_description,                  │
│     "--yes",  # Auto-accept changes                 │
│     *files.split(",")                               │
│   ],                                                │
│   cwd=project_root,                                 │
│   capture_output=True,                              │
│   text=True,                                        │
│   timeout=180                                       │
│   )                                                 │
│                                                     │
│   Aider Process:                                    │
│   1. Reads specified files                          │
│   2. Calls MiniMax API with file content + task     │
│   3. Generates code changes                         │
│   4. Applies edits to files                         │
│   5. Creates git commit                             │
│   6. Returns git diff as result                     │
│                                                     │
│   return json.dumps({                               │
│     "status": "success",                            │
│     "diff": result.stdout,                          │
│     "files_changed": files                          │
│   })                                                │
└─────────────────────────────────────────────────────┘
    ↓
Result returned to ToolCallingAgent
    ↓
Agent injects result, calls LLM again
    ↓
Loop continues until FINAL_ANSWER
    ↓
Return to ExecutionDispatcher
```

### Tool Call Flow Diagram:

```
Subtask (engine=smolagent)
    ↓
SmolAgentRunner
    ↓
┌──────────────────────┐
│ ToolCallingAgent     │
│                      │
│ Loop:                │
│   1. Call LLM        │
│   2. Parse response  │
│   3. If tool call:   │
│      ├─→ Execute tool│
│      └─→ Inject result│
│   4. If final answer:│
│      └─→ Break       │
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Tool Execution       │
│ (subprocess)         │
│                      │
│ Aider/OpenHands/etc  │
└──────────────────────┘
```

---

## 5. External Process Communication

### A. Aider Tool

```
run_aider_task(task_description, files, ...)
    ↓
subprocess.run([
    "aider",
    "--model", "openai/MiniMax-M2",
    "--message", task_description,
    "--yes",
    "file1.py", "file2.py"
],
cwd=project_root,
capture_output=True,
timeout=180
)
    ↓
┌─────────────────────────────────────────────────────┐
│ Aider Process                                       │
│                                                     │
│ 1. Parse command line args                          │
│ 2. Read specified files                             │
│ 3. Build prompt:                                    │
│    "Edit these files to: {task_description}"        │
│ 4. HTTP POST to MiniMax API                         │
│    POST https://api.minimax.chat/...                │
│    {                                                │
│      "model": "abab6.5s-chat",                      │
│      "messages": [                                  │
│        {                                            │
│          "role": "system",                          │
│          "content": "You are aider..."              │
│        },                                           │
│        {                                            │
│          "role": "user",                            │
│          "content": task_description +              │
│                     file_contents                   │
│        }                                            │
│      ]                                              │
│    }                                                │
│ 5. Parse LLM response for edits                     │
│ 6. Apply edits to files                             │
│ 7. Create git commit                                │
│ 8. Output diff to stdout                            │
│ 9. Exit with code 0                                 │
└─────────────────────────────────────────────────────┘
    ↓
stdout captured by run_aider_task()
    ↓
return json.dumps({
    "status": "success",
    "diff": stdout,
    "files_changed": files
})
```

### B. Gemini Judge (CLI)

```
GeminiJudge.evaluate_task(...)
    ↓
Build evaluation prompt
    ↓
subprocess.run([
    "/path/to/gemini",
    "-p", "Respond ONLY with valid JSON"
],
input=evaluation_prompt,
capture_output=True,
stderr=subprocess.DEVNULL  # Suppress startup logs!
)
    ↓
┌─────────────────────────────────────────────────────┐
│ Gemini CLI Process                                  │
│                                                     │
│ 1. Parse -p flag (prompt mode)                      │
│ 2. Read stdin (evaluation_prompt)                   │
│ 3. HTTP POST to Gemini API                          │
│    POST https://generativelanguage.googleapis.com/  │
│    {                                                │
│      "contents": [{                                 │
│        "parts": [{                                  │
│          "text": evaluation_prompt                  │
│        }]                                           │
│      }]                                             │
│    }                                                │
│ 4. Get JSON response from API                       │
│ 5. Write to stdout                                  │
│ 6. Exit                                             │
└─────────────────────────────────────────────────────┘
    ↓
stdout captured by GeminiJudge
    ↓
Parse JSON, create JudgeScore dataclass
    ↓
return JudgeScore(...)
```

### C. OpenHands Tool

```
run_openhands_task(task_description, ...)
    ↓
subprocess.run([
    "poetry", "run", "python",
    "openhands/core/main.py",
    "-t", task_description,
    "-c", "openai/MiniMax-M2",
    "-m", "10"  # max iterations
],
cwd=openhands_dir,
capture_output=True,
timeout=600  # 10 minutes
)
    ↓
OpenHands process (autonomous agent)
    ↓
Similar to Smolagents but in separate process
    ↓
Returns: stdout with results
```

---

## 6. Memory System

### Filesystem Structure:

```
memory/
├── plans/
│   ├── 20250118-140000_build-rest-api.json
│   ├── 20250118-150000_refactor-auth.json
│   └── 20250118-160000_add-tests.json
│
├── code_helfer/  # Category 1
│   ├── main_20250118-140000.txt
│   ├── main_20250118-140500.txt
│   └── main_20250118-141000.txt
│
├── architect/  # Category 2
│   ├── main_20250118-140100.txt
│   └── main_20250118-140600.txt
│
└── general/  # Default category
    └── main_20250118-140200.txt
```

### Memory File Format:

```
---
Agent: Code Helper
AgentKey: code_helfer
Workspace: main
Timestamp: 2025-01-18 14:00:00
Tags: python, debugging, error
---
System Prompt:
You are a helpful coding assistant specializing in...
---
User:
How do I fix this Python error: TypeError...
---
SelfAI:
This error occurs because you're trying to...

The solution is to:
1. Check the variable type
2. Add type conversion
3. Validate inputs

Here's the fixed code:
```python
...
```
```

### Plan File Format (JSON):

```json
{
  "subtasks": [
    {
      "id": "S1",
      "title": "Design API Schema",
      "objective": "Define REST endpoints...",
      "agent_key": "architect",
      "engine": "minimax",
      "parallel_group": 1,
      "depends_on": [],
      "status": "completed",
      "result_path": "memory/architect/main_20250118-142310.txt",
      "error": null,
      "notes": ""
    }
  ],
  "merge": {
    "strategy": "Combine all results...",
    "steps": [...]
  },
  "metadata": {
    "goal": "Build REST API",
    "planner_provider": "minimax-planner",
    "planner_model": "abab6.5s-chat",
    "merge_provider": "minimax-merger",
    "merge_result_path": "memory/architect/main_20250118-142400.txt",
    "created_at": "2025-01-18T14:23:05",
    "fallback": false
  }
}
```

---

## 7. Context Loading

### NEW: Time-Based Context Window

```python
# memory_system.py
def load_relevant_context(self, agent, current_text, limit=3):
    # Step 1: Get candidate files
    categories = agent.memory_categories
    candidate_files = self._get_candidate_files(categories)

    # Step 2: TIME FILTER (NEW!)
    import time
    cutoff_time = time.time() - (self.context_window_minutes * 60)
    candidate_files = [
        f for f in candidate_files
        if f.stat().st_mtime >= cutoff_time
    ]

    if not candidate_files:
        return []  # No files in window!

    # Step 3: Classify current task
    classification = classify_task(current_text, agent.key)
    expected_tags = classification.tags

    # Step 4: Score files by tag relevance
    scored_files = []
    for file_path in candidate_files:
        parsed = self._parse_memory_file(file_path)
        file_tags = parsed.get("tags", [])

        score = calculate_relevance(expected_tags, file_tags)
        scored_files.append({
            "path": file_path,
            "parsed": parsed,
            "score": score,
            "mtime": file_path.stat().st_mtime
        })

    # Step 5: Filter by threshold
    threshold = 0.35
    relevant = [f for f in scored_files if f["score"] >= threshold]

    # Step 6: Fallback if no relevant
    if not relevant:
        relevant = scored_files[:limit]

    # Step 7: Sort by (score, mtime) DESC
    relevant.sort(key=lambda f: (f["score"], f["mtime"]), reverse=True)

    # Step 8: Take top N
    selected = relevant[:limit]

    # Step 9: Re-sort chronologically (oldest first)
    selected.sort(key=lambda f: f["mtime"])

    # Step 10: Build context messages
    context = []
    for entry in selected:
        parsed = entry["parsed"]
        context.append({"role": "user", "content": parsed["user"]})
        context.append({"role": "assistant", "content": parsed["assistant"]})

    return context
```

### Context Timeline:

```
Session Start: 14:00
Window: 30 minutes
Current Time: 14:35

Files:
├── 14:00 - RAG discussion     ← Outside window (14:05 cutoff)
├── 14:10 - Python basics      ← Inside window ✓
├── 14:20 - Django tutorial    ← Inside window ✓
├── 14:30 - Flask API          ← Inside window ✓
└── 14:35 - Current prompt

Cutoff Calculation:
cutoff = 14:35 - 0:30 = 14:05

Filter Result:
RAG (14:00): 14:00 >= 14:05? NO ✗ → FILTERED OUT
Python (14:10): 14:10 >= 14:05? YES ✓ → KEEP
Django (14:20): 14:20 >= 14:05? YES ✓ → KEEP
Flask (14:30): 14:30 >= 14:05? YES ✓ → KEEP

Context Loaded: [Python, Django, Flask]
RAG NOT in context! Clean! ✓
```

---

## 8. Parallel Execution

### Thread Pool Pattern:

```python
# execution_dispatcher.py
with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
    # Submit all tasks
    futures = {}
    for task in tasks:
        future = executor.submit(_run_subtask, task)
        futures[future] = task

    # Wait for completion (order: UNPREDICTABLE)
    results = {}
    for future in as_completed(futures):
        task = futures[future]
        task_id = task["id"]

        try:
            response = future.result()  # Blocking
            results[task_id] = (task, response)
            ui.status(f"✓ Task {task_id} completed")
        except Exception as exc:
            ui.status(f"✗ Task {task_id} failed: {exc}")
            executor.shutdown(cancel_futures=True)
            raise

    # Display in ORDER (by task ID)
    for task in sorted(tasks, key=lambda t: t["id"]):
        task_id = task["id"]
        if task_id in results:
            _, response = results[task_id]
            display_result(task_id, response)
```

### Thread Safety:

| Component | Thread-Safe? | Notes |
|-----------|--------------|-------|
| MemorySystem | ✓ Yes | Filesystem locks (OS-level) |
| Plan JSON | ✓ Yes | Atomic writes |
| TerminalUI | ✗ No | But output is serialized after threads complete |
| LLM Interfaces | ✓ Yes | Each thread has own HTTP connection |
| AgentManager | ✓ Yes | Read-only during execution |

### Execution Timeline:

```
Group 1 (Sequential):
[14:00:00] S1 starts
[14:00:30] S1 completes
           ↓
Group 2 (Parallel):
[14:00:31] S2 starts (Thread 1)
[14:00:31] S3 starts (Thread 2)  ← Same time!
           ║
[14:00:45] S3 completes (Thread 2 faster)
[14:00:50] S2 completes (Thread 1 slower)
           ↓
Display (Sequential):
[14:00:51] Show S2 result (sorted by ID)
[14:00:51] Show S3 result
```

---

## 9. Error Handling & Retry

### Backend Fallback Chain:

```python
def _invoke_llm(agent, prompt, history):
    last_error = None

    # Try each backend in order
    for backend in [MiniMax, CPU]:
        try:
            response = backend.generate_response(
                system_prompt=agent.system_prompt,
                user_prompt=prompt,
                history=history
            )
            return response  # Success!

        except Exception as exc:
            last_error = exc
            ui.status(f"Backend {backend.name} failed: {exc}", "warning")
            continue  # Try next backend

    # All backends failed
    raise ExecutionError(f"All backends failed. Last: {last_error}")
```

### Retry Logic:

```python
# execution_dispatcher.py
retry_attempts = 2
retry_delay = 5.0

for attempt in range(retry_attempts + 1):  # 0, 1, 2
    try:
        response = llm_interface.generate_response(...)
        return response  # Success!

    except Exception as exc:
        last_exception = exc

        if attempt < retry_attempts:
            ui.status(f"Attempt {attempt+1} failed. Retrying in {retry_delay}s...", "warning")
            time.sleep(retry_delay)
            continue

        # All retries exhausted
        raise ExecutionError(f"Failed after {retry_attempts+1} attempts: {exc}")
```

### Error Flow:

```
LLM Call
    ↓
┌─────────────────┐
│ Try MiniMax     │
└────┬────────────┘
     │
     ├─ Success? → Return
     │
     ├─ HTTP Error?
     │  ├─ Retry 1 (5s delay)
     │  ├─ Retry 2 (5s delay)
     │  └─ Still failing?
     │     └─→ Try next backend
     │
     ↓
┌─────────────────┐
│ Try CPU         │
└────┬────────────┘
     │
     ├─ Success? → Return
     │
     ├─ Error?
     │  ├─ Retry 1
     │  ├─ Retry 2
     │  └─ Still failing?
     │     └─→ No more backends
     │
     ↓
ExecutionError raised
```

---

## 10. Data Structures

### A. Agent (Dataclass)

```python
@dataclass
class Agent:
    key: str                      # "code_helfer"
    display_name: str             # "Code Helper"
    description: str              # "Helps with coding tasks"
    system_prompt: str            # Full prompt text (multiline)
    memory_categories: List[str]  # ["python", "debugging"]
    workspace_slug: str           # "main"
```

**Storage:** In-memory (`AgentManager.agents: List[Agent]`)
**Source:** `agents/{key}/` directory files
**Lifetime:** Entire session (loaded at startup)

### B. Plan Data (Dict/JSON)

```python
{
    "subtasks": [
        {
            "id": str,              # "S1", "S2", ...
            "title": str,           # "Design API Schema"
            "objective": str,       # Detailed task description
            "agent_key": str,       # "architect", "code_helfer"
            "engine": str,          # "minimax", "smolagent"
            "parallel_group": int,  # 1, 2, 3, ...
            "depends_on": List[str], # ["S1"], ["S2", "S3"]
            "status": str,          # "pending", "running", "completed", "failed"
            "result_path": str|None, # "memory/architect/main_20250118.txt"
            "error": str|None,      # Error message if failed
            "notes": str,           # Additional context
            "tools": List[str]|None, # ["run_aider_task"] (for smolagent)
            "max_steps": int|None   # Max tool iterations
        }
    ],
    "merge": {
        "strategy": str,            # How to combine results
        "steps": List[Dict]         # Merge steps (optional)
    },
    "metadata": {
        "goal": str,                # Original user goal
        "planner_provider": str,    # "minimax-planner"
        "planner_model": str,       # "abab6.5s-chat"
        "merge_provider": str,      # "minimax-merger"
        "merge_result_path": str,   # Path to merge result
        "created_at": str,          # ISO timestamp
        "fallback": bool            # True if fallback plan
    }
}
```

**Storage:** Filesystem (`memory/plans/{timestamp}_{goal}.json`)
**Updates:** Plan JSON is updated after each subtask (atomic writes)
**Access:** Loaded/saved by `ExecutionDispatcher`

### C. LLM Backend (Dict)

```python
{
    "interface": MinimaxInterface(...),  # Interface instance
    "label": "MiniMax",                  # Display name
    "name": "minimax",                   # Internal identifier
    "type": "cloud"                      # "cloud", "local", "npu"
}
```

**Storage:** In-memory (`execution_backends: List[Dict]`)
**Access:** Indexed list (fallback order = list order)
**Lifetime:** Entire session

### D. Token Limits (Dataclass)

```python
@dataclass
class TokenLimits:
    planner_max_tokens: int = 768
    execution_max_tokens: int = 512
    merge_max_tokens: int = 2048
    tool_creation_max_tokens: int = 1024
    error_correction_max_tokens: int = 1024
    selfimprove_max_tokens: int = 2048
    chat_max_tokens: int = 1024
```

**Storage:** In-memory (runtime only)
**Control:** `/tokens`, `/extreme` commands
**Lifetime:** Current session (resets on restart)

### E. Memory Context (List[Dict])

```python
[
    {
        "role": "user",
        "content": "How do I fix this error?"
    },
    {
        "role": "assistant",
        "content": "The error occurs because..."
    },
    {
        "role": "user",
        "content": "Thanks! What about..."
    },
    {
        "role": "assistant",
        "content": "For that, you can..."
    }
]
```

**Source:** `load_relevant_context()` from memory files
**Usage:** Passed to LLM as conversation history
**Format:** OpenAI-compatible messages format

---

## Summary: Communication Patterns

### Synchronous (Main Thread):
- User Input → Main Loop
- Command Parsing → Command Handlers
- Memory Load/Save → Filesystem I/O
- Plan Validation → In-Memory
- Output Display → Terminal

### HTTP (Async I/O in sync context):
- LLM Interfaces → Cloud APIs (MiniMax, etc.)
- Streaming via SSE (Server-Sent Events)
- Request/Response JSON

### Multi-Threading (Parallel Execution):
- ExecutionDispatcher spawns threads
- Each thread runs subtask independently
- Results collected, displayed sequentially

### Sub-Processes (External Tools):
- Aider: `subprocess.run(["aider", ...])`
- OpenHands: `subprocess.run(["poetry", "run", ...])`
- Gemini CLI: `subprocess.run(["/path/to/gemini", ...])`

### Filesystem (Persistent State):
- Plans: `memory/plans/{timestamp}_{goal}.json`
- Conversations: `memory/{category}/{agent}_{timestamp}.txt`
- Agent Config: `agents/{agent_key}/{files}`

---

**No Message Queue, No Event Bus, No WebSockets between components!**

Everything is **direct function calls** with **Filesystem as shared state** and **HTTP for external APIs**.

**Simple, Transparent, Debuggable.** 🎯

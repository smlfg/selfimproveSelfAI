# SelfAI Code Review - Key Sections for Programmer

## 🌟 COOL/ELEGANT Sections

### 1. DPPM Architecture Pattern (selfai/selfai.py:1870-2034)

**What's Cool**: Three-phase autonomous execution pipeline with automatic evaluation

```python
# Phase 1: Planning (Decompose)
plan_data = planner.generate_plan(goal=goal_text, ...)

# Phase 2: Execution (Parallel)
import time
start_time = time.time()
dispatcher.run()  # Executes subtasks with automatic backend fallback
execution_time = time.time() - start_time

# Phase 3: Merge (Synthesis)
final_result = merger.merge_results(plan_data=plan_data, ...)

# Phase 4: Judge Evaluation (New!)
from selfai.core.gemini_judge import GeminiJudge
judge = GeminiJudge()
score = judge.evaluate_task(
    original_goal=goal_text,
    execution_output=execution_output,
    plan_data=plan_data,
    execution_time=execution_time,
    files_changed=files_changed
)
```

**Why Elegant**: Each phase is independent and composable. Execution can work without planning, merge phase is optional, judge observes read-only.

---

### 2. Error Pattern Recognition Algorithm (selfai/core/error_analyzer.py:180-210)

**What's Cool**: Groups similar errors using normalized signatures for learning

```python
def _create_error_signature(self, error: ErrorEntry) -> str:
    """Create unique signature for grouping similar errors"""
    parts = [
        error.error_type,
        error.file_path or 'unknown',
        str(error.line_number or 0)
    ]

    # Normalize message - remove variable parts
    normalized_msg = re.sub(r'\d+', 'N', error.message)  # 123 -> N
    normalized_msg = re.sub(r"'[^']*'", "'VAR'", normalized_msg)  # 'foo' -> 'VAR'
    normalized_msg = re.sub(r'\b0x[0-9a-f]+\b', '0xADDR', normalized_msg, flags=re.I)  # 0x7f3a -> 0xADDR

    parts.append(normalized_msg[:50])
    return '|'.join(parts)

def _group_errors(self):
    """Group errors by signature"""
    signature_groups: Dict[str, List[ErrorEntry]] = {}
    for error in self.errors:
        sig = self._create_error_signature(error)
        if sig not in signature_groups:
            signature_groups[sig] = []
        signature_groups[sig].append(error)

    # Create ErrorPattern objects
    for sig, errors in signature_groups.items():
        if len(errors) >= 1:  # Even single errors are patterns
            self.patterns.append(ErrorPattern(
                signature=sig,
                error_type=errors[0].error_type,
                occurrences=len(errors),
                examples=errors[:3],  # Keep top 3 examples
                first_seen=min(e.timestamp for e in errors),
                last_seen=max(e.timestamp for e in errors)
            ))
```

**Why Elegant**: Turns noisy error logs into learnable patterns. Normalization removes variable data while keeping structure.

---

### 3. Dynamic Tool Registry (selfai/tools/tool_registry.py:15-85)

**What's Cool**: Tools can be registered at runtime, introspectable, hot-loadable

```python
@dataclass
class RegisteredTool:
    name: str
    func: Callable
    schema: Dict[str, Any]
    category: str = "general"
    enabled: bool = True

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, RegisteredTool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: RegisteredTool):
        """Register a tool - can be called anytime"""
        self._tools[tool.name] = tool
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        self._categories[tool.category].append(tool.name)

    def get_tool(self, name: str) -> Optional[RegisteredTool]:
        """Retrieve tool by name"""
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None,
                   enabled_only: bool = True) -> List[RegisteredTool]:
        """List all tools or by category"""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]
        if enabled_only:
            tools = [t for t in tools if t.enabled]

        return tools

# Global registry
_global_registry = ToolRegistry()

def register_tool(tool: RegisteredTool):
    """Convenience function for registration"""
    _global_registry.register(tool)
```

**Why Elegant**: Enables runtime tool creation (`/toolcreate`), categorical organization, and enable/disable without code changes.

---

### 4. Traffic Light Scoring System (selfai/core/gemini_judge.py:120-180)

**What's Cool**: Visual, quantitative evaluation with automatic color coding

```python
class TrafficLight(Enum):
    GREEN = "🟢"
    YELLOW = "🟡"
    RED = "🔴"

@dataclass
class JudgeScore:
    task_completion: float      # 0-10
    code_quality: float         # 0-10
    efficiency: float           # 0-10
    goal_adherence: float       # 0-10
    overall_score: float        # 0-100 (weighted average)
    traffic_light: TrafficLight
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]

def evaluate_task(self, original_goal, execution_output, plan_data,
                  execution_time, files_changed) -> JudgeScore:
    """Evaluate completed task (READ-ONLY!)"""

    # ... LLM evaluation ...

    # Calculate overall score with weighted metrics
    overall = (
        task_completion * 0.4 +  # Most important - did it work?
        code_quality * 0.2 +     # Is code good?
        efficiency * 0.2 +       # Was it fast?
        goal_adherence * 0.2     # Did it match intent?
    ) * 10  # Scale to 0-100

    # Determine traffic light automatically
    if overall >= 80:
        light = TrafficLight.GREEN
    elif overall >= 50:
        light = TrafficLight.YELLOW
    else:
        light = TrafficLight.RED

    return JudgeScore(
        task_completion=task_completion,
        code_quality=code_quality,
        efficiency=efficiency,
        goal_adherence=goal_adherence,
        overall_score=overall,
        traffic_light=light,
        summary=judge_data.get("summary", ""),
        strengths=judge_data.get("strengths", []),
        weaknesses=judge_data.get("weaknesses", []),
        recommendations=judge_data.get("recommendations", [])
    )

def format_score_for_terminal(score: JudgeScore) -> str:
    """Pretty terminal output"""
    output = []
    output.append("\n" + "="*60)
    output.append(f"  {score.traffic_light.value} GEMINI JUDGE EVALUATION")
    output.append("="*60)
    output.append(f"\n📊 OVERALL SCORE: {score.overall_score:.1f}/100 {score.traffic_light.value}")
    output.append("\n📈 METRICS:")
    output.append(f"  • Task Completion: {score.task_completion:.1f}/10")
    output.append(f"  • Code Quality:    {score.code_quality:.1f}/10")
    output.append(f"  • Efficiency:      {score.efficiency:.1f}/10")
    output.append(f"  • Goal Adherence:  {score.goal_adherence:.1f}/10")
    # ... strengths, weaknesses, recommendations ...
    return "\n".join(output)
```

**Why Elegant**: Human-readable visual feedback + quantitative data. Weighted metrics reflect importance. Read-only design prevents judge from interfering.

---

### 5. Knowledge Base Learning Loop (selfai/core/fix_generator.py:420-480)

**What's Cool**: SelfAI learns from successful fixes and builds expertise over time

```python
def save_fix_result(self, fix_option: FixOption, error_pattern: ErrorPattern,
                    success: bool, applied_changes: Optional[str] = None):
    """Save fix result to knowledge base for future learning"""

    error_type = error_pattern.error_type.replace(" ", "_")
    history_file = self.knowledge_base_path / f"{error_type}.json"

    # Load existing history
    if history_file.exists():
        history = json.loads(history_file.read_text(encoding='utf-8'))
    else:
        history = {"error_type": error_pattern.error_type, "fixes": []}

    # Find or create fix entry
    fix_signature = f"{fix_option.id}_{fix_option.title[:30]}"
    fix_entry = None
    for entry in history["fixes"]:
        if entry["signature"] == fix_signature:
            fix_entry = entry
            break

    if not fix_entry:
        fix_entry = {
            "signature": fix_signature,
            "title": fix_option.title,
            "complexity": fix_option.complexity,
            "risk": fix_option.risk,
            "changes": fix_option.changes,
            "total_attempts": 0,
            "successful_attempts": 0,
            "success_rate": 0.0,
            "last_applied": None,
            "applied_changes_history": []
        }
        history["fixes"].append(fix_entry)

    # Update statistics
    fix_entry["total_attempts"] += 1
    if success:
        fix_entry["successful_attempts"] += 1
    fix_entry["success_rate"] = (
        fix_entry["successful_attempts"] / fix_entry["total_attempts"]
    )
    fix_entry["last_applied"] = datetime.now().isoformat()

    if applied_changes:
        fix_entry["applied_changes_history"].append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "changes": applied_changes
        })

    # Save back
    history_file.write_text(json.dumps(history, indent=2), encoding='utf-8')
```

**Why Elegant**: Incremental learning without retraining. Success rates guide future decisions. History preserved for analysis.

---

## ⚠️ PROBLEMATIC Sections

### 1. Raw LLM Output Without Filtering (selfai/core/execution_dispatcher.py:187)

**Problem**: Tool-call artifacts leak into execution output

```python
# CURRENT CODE (Line 187):
result_text = interface.generate_response(
    system_prompt=subtask_system,
    user_prompt=subtask_objective,
    history=[],
    max_output_tokens=subtask.get("max_tokens", 512)
)

# This prints: "[TOOL_CALL] {tool => "read_project_files", ...} [/TOOL_CALL]"
```

**Why Problematic**: Users see internal tool-calling protocol artifacts instead of clean output.

**Suggested Fix**:
```python
result_text = interface.generate_response(...)

# Filter out tool call artifacts
import re
result_text = re.sub(r'\[TOOL_CALL\].*?\[/TOOL_CALL\]', '', result_text, flags=re.DOTALL)
result_text = re.sub(r'\[TOOL_RESULTS\].*?\[/TOOL_RESULTS\]', '', result_text, flags=re.DOTALL)
result_text = result_text.strip()
```

---

### 2. Silent Exception Handling (selfai/core/planner_minimax_interface.py:315-336)

**Problem**: Validation errors were caught and ignored with `pass`

```python
# OLD CODE (FIXED):
try:
    validate_plan_structure(plan_data, ...)
except PlanValidationError as exc:
    pass  # ⚠️ SILENT FAILURE - falls through to generic fallback

# NEW CODE (CURRENT):
try:
    validate_plan_structure(plan_data, ...)
    return plan_data  # ✅ Return immediately on success
except PlanValidationError as exc:
    print(f"⚠️ Plan validation warning: {exc}")
    print(f"⚠️ Using fallback plan instead")
```

**Why Problematic**: Hard to debug when plans fail. Silent failures hide root cause.

**Note**: This was fixed, but check for similar patterns elsewhere.

---

### 3. Monolithic Main File (selfai/selfai.py - 2000+ lines)

**Problem**: Main orchestration file is massive and handles too many responsibilities

**Current Structure**:
```
selfai/selfai.py (2000+ lines)
├── Configuration loading
├── LLM backend initialization
├── Agent management
├── Command handlers (/plan, /toolcreate, /errorcorrection, etc.)
├── Planning phase
├── Execution phase
├── Merge phase
├── Judge integration
├── Memory management
├── Interactive loop
└── Error handling
```

**Why Problematic**:
- Hard to navigate and maintain
- Changes in one command risk breaking others
- Testing requires full system initialization

**Suggested Refactoring**:
```
selfai/
├── cli/
│   ├── commands/
│   │   ├── plan_command.py
│   │   ├── toolcreate_command.py
│   │   ├── errorcorrection_command.py
│   │   ├── memory_command.py
│   │   └── switch_command.py
│   └── main_loop.py
├── orchestrator.py  (DPPM pipeline)
└── selfai.py  (Entry point only - 50 lines)
```

---

### 4. Hardcoded Paths (Multiple files)

**Problem**: Some paths are hardcoded instead of using configuration

**Example 1** (selfai/tools/openhands_tool.py:45):
```python
# HARDCODED:
openhands_dir = Path("/home/smlflg/AutoCoder/OpenHands")

# SHOULD BE:
from config_loader import load_configuration
config = load_configuration()
openhands_dir = Path(config.system.openhands_path)
```

**Example 2** (selfai/core/gemini_judge.py:88):
```python
# HARDCODED:
self.cli_path = "/home/smlflg/AutoCoder/GeminiCLI/gemini"

# SHOULD BE:
from config_loader import load_configuration
config = load_configuration()
self.cli_path = Path(config.system.gemini_cli_path)
```

**Why Problematic**: Won't work on other machines, requires code changes to reconfigure.

---

## ✅ ESSENTIAL Sections

### 1. Multi-Backend LLM Fallback Chain (selfai/selfai.py:1550-1650)

**Why Essential**: Ensures SelfAI always works even without NPU/GPU

```python
def main():
    # Load multiple backends in priority order
    execution_backends = []

    # 1. Try AnythingLLM (NPU-accelerated)
    if config.npu_provider and config.npu_provider.api_key:
        try:
            from selfai.core.anythingllm_interface import AnythingLLMInterface
            npu_interface = AnythingLLMInterface(
                base_url=config.npu_provider.base_url,
                workspace_slug=current_agent.workspace_slug,
                api_key=config.npu_provider.api_key
            )
            execution_backends.append({
                "interface": npu_interface,
                "label": "AnythingLLM (NPU)",
                "name": "anythingllm"
            })
        except Exception as e:
            ui.status(f"AnythingLLM nicht verfügbar: {e}", "warning")

    # 2. Try QNN models (direct NPU)
    try:
        from selfai.core.npu_llm_interface import NpuLLMInterface
        qnn_interface = NpuLLMInterface(models_root)
        execution_backends.append({
            "interface": qnn_interface,
            "label": "QNN (NPU)",
            "name": "qnn"
        })
    except Exception as e:
        ui.status(f"QNN nicht verfügbar: {e}", "warning")

    # 3. CPU Fallback (guaranteed to work)
    if config.cpu_fallback and config.cpu_fallback.model_path:
        try:
            from selfai.core.local_llm_interface import LocalLLMInterface
            cpu_interface = LocalLLMInterface(
                model_path=str(models_root / config.cpu_fallback.model_path),
                n_ctx=config.cpu_fallback.n_ctx
            )
            execution_backends.append({
                "interface": cpu_interface,
                "label": "CPU Fallback",
                "name": "cpu"
            })
        except Exception as e:
            ui.status(f"CPU Fallback fehlgeschlagen: {e}", "error")

    if not execution_backends:
        ui.status("Keine Execution-Backends verfügbar!", "error")
        return

    # Use first available backend as primary
    primary_backend = execution_backends[0]
```

**Why Essential**: Without this, SelfAI only works with specific hardware. Fallback guarantees functionality.

---

### 2. Plan Validation Logic (selfai/core/planner_validator.py:80-180)

**Why Essential**: Prevents invalid plans from executing and corrupting state

```python
def validate_plan_structure(
    plan_data: dict,
    allowed_agent_keys: Optional[list[str]] = None,
    allowed_engines: Optional[list[str]] = None,
) -> None:
    """Validate DPPM plan structure - raises PlanValidationError on issues"""

    # 1. Check required top-level fields
    if "subtasks" not in plan_data:
        raise PlanValidationError("Plan missing 'subtasks' field")

    subtasks = plan_data.get("subtasks", [])
    if not isinstance(subtasks, list):
        raise PlanValidationError("'subtasks' must be a list")

    if len(subtasks) == 0:
        raise PlanValidationError("Plan has no subtasks")

    # 2. Validate each subtask
    seen_ids = set()
    for idx, subtask in enumerate(subtasks):
        # Required fields
        for field in ["id", "title", "objective", "agent_key"]:
            if field not in subtask:
                raise PlanValidationError(f"Subtask {idx} missing '{field}'")

        # Unique IDs
        task_id = subtask["id"]
        if task_id in seen_ids:
            raise PlanValidationError(f"Duplicate subtask ID: {task_id}")
        seen_ids.add(task_id)

        # Valid agent
        if allowed_agent_keys:
            if subtask["agent_key"] not in allowed_agent_keys:
                raise PlanValidationError(
                    f"Subtask {task_id} uses unknown agent: {subtask['agent_key']}"
                )

        # Valid engine
        if allowed_engines:
            engine = subtask.get("engine", "anythingllm")
            if engine not in allowed_engines:
                raise PlanValidationError(
                    f"Subtask {task_id} uses unknown engine: {engine}"
                )

        # Dependency validation
        depends_on = subtask.get("depends_on", [])
        if not isinstance(depends_on, list):
            raise PlanValidationError(
                f"Subtask {task_id} 'depends_on' must be a list"
            )

        for dep_id in depends_on:
            if dep_id not in seen_ids and dep_id != task_id:
                raise PlanValidationError(
                    f"Subtask {task_id} depends on unknown task: {dep_id}"
                )

    # 3. Check for circular dependencies
    _check_circular_dependencies(subtasks)

    # 4. Validate merge section (optional)
    if "merge" in plan_data:
        merge = plan_data["merge"]
        if not isinstance(merge, dict):
            raise PlanValidationError("'merge' must be a dict")

        if "strategy" not in merge:
            raise PlanValidationError("Merge section missing 'strategy'")

def _check_circular_dependencies(subtasks: list[dict]):
    """Detect circular dependencies using DFS"""
    def has_cycle(task_id, visited, rec_stack):
        visited.add(task_id)
        rec_stack.add(task_id)

        task = next((t for t in subtasks if t["id"] == task_id), None)
        if task:
            for dep_id in task.get("depends_on", []):
                if dep_id not in visited:
                    if has_cycle(dep_id, visited, rec_stack):
                        return True
                elif dep_id in rec_stack:
                    return True

        rec_stack.remove(task_id)
        return False

    visited = set()
    for task in subtasks:
        if task["id"] not in visited:
            if has_cycle(task["id"], visited, set()):
                raise PlanValidationError(
                    f"Circular dependency detected involving task: {task['id']}"
                )
```

**Why Essential**: Invalid plans cause crashes, infinite loops, or corrupted execution state. Validation is the safety net.

---

### 3. Agent System Prompt Loading (selfai/core/agent_manager.py:60-120)

**Why Essential**: Defines agent personality and capabilities - core to multi-agent architecture

```python
def _load_agents(self) -> List[Agent]:
    """Load all agents from agents/ directory"""
    agents = []

    if not self.agents_root.exists():
        return agents

    for agent_dir in self.agents_root.iterdir():
        if not agent_dir.is_dir():
            continue

        agent_key = agent_dir.name

        # Load components
        system_prompt_file = agent_dir / "system_prompt.md"
        description_file = agent_dir / "description.txt"
        memory_categories_file = agent_dir / "memory_categories.txt"
        workspace_slug_file = agent_dir / "workspace_slug.txt"

        # System prompt (required)
        if not system_prompt_file.exists():
            print(f"⚠️ Agent {agent_key} missing system_prompt.md, skipping")
            continue
        system_prompt = system_prompt_file.read_text(encoding='utf-8').strip()

        # Description
        description = ""
        if description_file.exists():
            description = description_file.read_text(encoding='utf-8').strip()

        # Memory categories
        memory_categories = ["general"]
        if memory_categories_file.exists():
            memory_categories = [
                line.strip()
                for line in memory_categories_file.read_text(encoding='utf-8').split('\n')
                if line.strip()
            ]

        # Workspace slug
        workspace_slug = "main"
        if workspace_slug_file.exists():
            workspace_slug = workspace_slug_file.read_text(encoding='utf-8').strip()

        # Create agent
        agent = Agent(
            key=agent_key,
            display_name=agent_key.replace('_', ' ').title(),
            description=description,
            system_prompt=system_prompt,
            memory_categories=memory_categories,
            workspace_slug=workspace_slug
        )
        agents.append(agent)

    return agents
```

**Why Essential**: Without this, SelfAI has no personality, no tool access control, no memory organization.

---

### 4. Subtask Execution with Retry Logic (selfai/core/execution_dispatcher.py:150-250)

**Why Essential**: Core execution engine - handles failures, retries, backend switching

```python
def _execute_subtask(self, subtask: dict) -> dict:
    """Execute single subtask with retry logic"""

    task_id = subtask["id"]
    title = subtask["title"]
    objective = subtask["objective"]
    agent_key = subtask.get("agent_key", self.default_agent_key)

    self.ui.status(f"Executing subtask {task_id}: {title}", "info")

    # Get agent
    agent = self.agent_manager.get_agent(agent_key)
    if not agent:
        return {"status": "failed", "error": f"Agent {agent_key} not found"}

    # Build prompt
    subtask_system = agent.system_prompt
    subtask_objective = objective

    # Try each backend with retries
    last_error = None
    for attempt in range(self.retry_attempts):
        for backend in self.backends:
            try:
                self.ui.status(
                    f"Attempt {attempt+1}/{self.retry_attempts} using {backend['label']}",
                    "info"
                )

                interface = backend["interface"]
                result_text = interface.generate_response(
                    system_prompt=subtask_system,
                    user_prompt=subtask_objective,
                    history=[],
                    max_output_tokens=subtask.get("max_tokens", 512)
                )

                # Success! Save result
                result_file = self.results_dir / f"{task_id}.txt"
                result_file.write_text(result_text, encoding='utf-8')

                return {
                    "status": "completed",
                    "result_path": str(result_file),
                    "backend": backend["name"]
                }

            except Exception as e:
                last_error = str(e)
                self.ui.status(
                    f"Backend {backend['label']} failed: {e}",
                    "warning"
                )
                # Try next backend
                continue

        # All backends failed this attempt - wait before retry
        if attempt < self.retry_attempts - 1:
            time.sleep(self.retry_delay)

    # All retries exhausted
    return {
        "status": "failed",
        "error": f"All backends failed after {self.retry_attempts} attempts. Last error: {last_error}"
    }
```

**Why Essential**: This is where actual work happens. Retry logic + backend fallback ensures reliability.

---

## 🔥 BAD/NEEDS IMPROVEMENT Sections

### 1. No Type Hints in Older Code (selfai/tools/filesystem_tools.py)

**Problem**: Many functions lack type hints, making IDE support and refactoring harder

```python
# CURRENT (BAD):
def read_project_file(file_path):
    """Read file from project"""
    full_path = Path.cwd() / file_path
    if not full_path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})
    return full_path.read_text(encoding='utf-8')

# SHOULD BE (GOOD):
from typing import Dict, Any
import json

def read_project_file(file_path: str) -> str:
    """Read file from project"""
    full_path = Path.cwd() / file_path
    if not full_path.exists():
        error_dict: Dict[str, str] = {"error": f"File not found: {file_path}"}
        return json.dumps(error_dict)
    return full_path.read_text(encoding='utf-8')
```

**Why Bad**: Type hints enable better IDE completion, catch bugs at development time, serve as documentation.

---

### 2. Incomplete Error Handling in CLI Integrations (selfai/tools/openhands_tool.py:120-150)

**Problem**: Subprocess calls don't handle all failure modes

```python
# CURRENT (INCOMPLETE):
def run_openhands_task(task_description: str, files: str = "",
                       model: str = "openai/MiniMax-M2",
                       max_iterations: int = 10) -> str:
    """Run OpenHands task"""

    result = subprocess.run(
        ["poetry", "run", "python", "openhands/core/main.py", ...],
        cwd=openhands_dir,
        capture_output=True,
        text=True,
        timeout=600  # 10 minutes
    )

    # ⚠️ Only checks returncode, not stderr content
    if result.returncode != 0:
        return json.dumps({"error": result.stderr})

    return result.stdout

# SHOULD BE (COMPLETE):
def run_openhands_task(task_description: str, files: str = "",
                       model: str = "openai/MiniMax-M2",
                       max_iterations: int = 10) -> str:
    """Run OpenHands task"""

    try:
        result = subprocess.run(
            ["poetry", "run", "python", "openhands/core/main.py", ...],
            cwd=openhands_dir,
            capture_output=True,
            text=True,
            timeout=600
        )

        # Check for errors in stderr even if returncode == 0
        if result.returncode != 0:
            return json.dumps({
                "error": "OpenHands failed",
                "stderr": result.stderr,
                "stdout": result.stdout
            })

        # Check for error keywords in output
        if "error" in result.stderr.lower() or "failed" in result.stderr.lower():
            return json.dumps({
                "warning": "Completed with warnings",
                "stderr": result.stderr,
                "result": result.stdout
            })

        return result.stdout

    except subprocess.TimeoutExpired:
        return json.dumps({"error": "OpenHands timed out after 10 minutes"})
    except FileNotFoundError:
        return json.dumps({"error": "OpenHands not found. Is poetry installed?"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {type(e).__name__}: {e}"})
```

**Why Bad**: Silent failures, timeout not caught, missing dependencies not detected until runtime.

---

### 3. Global State in Tool Registry (selfai/tools/tool_registry.py:200)

**Problem**: Uses module-level singleton instead of dependency injection

```python
# CURRENT (GLOBAL STATE):
_global_registry = ToolRegistry()

def register_tool(tool: RegisteredTool):
    _global_registry.register(tool)

def get_tool(name: str):
    return _global_registry.get_tool(name)

# PROBLEM: Hard to test, causes state pollution between tests
```

**Why Bad**:
- Can't create isolated registries for testing
- Changes persist across test runs
- Can't run multiple SelfAI instances with different tool configs

**Suggested Fix**:
```python
# BETTER: Dependency injection
class SelfAI:
    def __init__(self, config: AppConfig):
        self.tool_registry = ToolRegistry()  # Instance, not global
        self._load_tools()

    def _load_tools(self):
        """Load tools into this instance's registry"""
        from selfai.tools.filesystem_tools import create_filesystem_tools
        for tool in create_filesystem_tools():
            self.tool_registry.register(tool)
```

---

### 4. Inconsistent Logging (Throughout codebase)

**Problem**: Mix of `print()`, `ui.status()`, and no logging at all

```python
# Example from selfai/selfai.py:
print(f"⚠️ Plan validation warning: {exc}")  # Line 330
ui.status("Planner nicht verfügbar", "warning")  # Line 450
# Some places have no output at all
```

**Why Bad**: Can't control verbosity, can't redirect to files, hard to grep logs.

**Suggested Fix**:
```python
import logging

logger = logging.getLogger("selfai")

# Instead of:
print(f"⚠️ Plan validation warning: {exc}")

# Use:
logger.warning(f"Plan validation warning: {exc}")

# Configure logging level in main():
logging.basicConfig(
    level=logging.INFO,  # Can be changed to DEBUG, WARNING, etc.
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('selfai.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
```

---

## 🎯 SUMMARY FOR PROGRAMMER

### What Makes This Project Special:

1. **Self-improving AI**: SelfAI can analyze its own errors, generate fixes, and learn from successes
2. **Resilient Architecture**: Multi-backend fallback ensures it works on any hardware (NPU → QNN → CPU)
3. **Autonomous Task Decomposition**: DPPM planning breaks complex goals into executable subtasks
4. **Dynamic Tool Creation**: Can generate its own tools at runtime
5. **Read-only Evaluation**: Gemini Judge scores without interfering with execution

### What Needs Attention:

1. **Refactor Main File**: `selfai.py` is 2000+ lines - extract command handlers into separate modules
2. **Add Type Hints**: Many older functions lack type annotations
3. **Improve Error Handling**: CLI integrations need comprehensive exception handling
4. **Fix Global State**: Tool registry should use dependency injection
5. **Standardize Logging**: Replace `print()` calls with proper logging framework
6. **Configuration Management**: Move hardcoded paths to config.yaml

### Quick Wins:

1. Filter `[TOOL_CALL]` artifacts in execution output (1 line fix)
2. Add type hints to `filesystem_tools.py` (30 minutes)
3. Create `config_defaults.py` for hardcoded paths (1 hour)
4. Extract command handlers to `selfai/cli/commands/` (4 hours)

### Architecture Highlights to Show:

- **Error pattern recognition algorithm** (elegant normalization)
- **Knowledge base learning loop** (incremental learning without retraining)
- **Traffic light scoring** (visual + quantitative feedback)
- **DPPM pipeline** (decompose → execute → merge → judge)
- **Dynamic tool registry** (runtime extensibility)

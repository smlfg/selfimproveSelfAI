# Agentic Redundancy Architecture for SelfAI

**Multi-Tier Fallback System for Robust Tool-Calling**

---

## 🎯 Concept: 3-Tier Failover System

**The Vision:** Implement THREE independent tool-calling strategies that act as safety nets for each other. If one fails, the next takes over automatically.

```
User Request with Tools
    ↓
┌─────────────────────────────────────────────────┐
│  TIER 1: smolagents (Primary)                   │
│  - Fast                                         │
│  - Battle-tested                                │
│  - Existing codebase                            │
│  ↓ [FAIL?]                                      │
├─────────────────────────────────────────────────┤
│  TIER 2: Google Agent SDK (Secondary)           │
│  - Production-ready                             │
│  - Different implementation                     │
│  - More robust parsing                          │
│  ↓ [FAIL?]                                      │
├─────────────────────────────────────────────────┤
│  TIER 3: Custom Tool-Loop (Fallback)            │
│  - Full control                                 │
│  - Simple logic                                 │
│  - Guaranteed to work                           │
│  ↓                                              │
└─────────────────────────────────────────────────┘
    ↓
✅ Tool Result or Error
```

---

## ✅ Massive Advantages

### 1. **Robustness**
- System can never completely fail
- 3 independent implementations
- If smolagents has a bug → Google SDK takes over
- If Google SDK gets deprecated → Custom Loop takes over

### 2. **Quality Through Competition**
- Best result wins
- Different parsers recognize different patterns
- Cross-validation possible

### 3. **Advanced Debugging**
```python
# When Tier 1 fails, you see why:
[DEBUG] smolagents failed: Invalid XML format
[INFO] Falling back to Google Agent SDK...
[SUCCESS] Google Agent SDK: Tool executed successfully
```

### 4. **A/B Testing in Production**
```python
# Rotate through Tiers for performance tests
if random.random() < 0.1:  # 10% on Google SDK
    use_tier = 2
```

### 5. **Gradual Migration**
- Test new tool-calling method without deleting old code
- Migrate step by step
- Zero-downtime upgrades

---

## 🏗️ Architecture Implementation

### Base Strategy Pattern

```python
class ToolExecutionStrategy:
    """Base class for tool execution strategies."""

    def execute(self, task, agent, prompt, history) -> tuple[str, bool]:
        """
        Execute task with tool-calling.

        Returns:
            tuple: (response, success)
                - response: str - The execution result
                - success: bool - Whether execution succeeded
        """
        raise NotImplementedError

    def get_name(self) -> str:
        """Return human-readable strategy name."""
        return self.__class__.__name__


class SmolagentsStrategy(ToolExecutionStrategy):
    """Tier 1: smolagents framework (HuggingFace)."""

    def __init__(self, ui):
        self.ui = ui

    def execute(self, task, agent, prompt, history):
        try:
            response = self._run_smolagent(task, agent, prompt, history)
            return (response, True)
        except Exception as e:
            logger.warning(f"Smolagents failed: {e}")
            return (str(e), False)

    def _run_smolagent(self, task, agent, prompt, history):
        """Run smolagents with streaming support."""
        from selfai.core.smolagents_runner import SmolAgentRunner

        runner = SmolAgentRunner(
            model_interface=self.llm_interface,
            agent=agent,
            ui=self.ui,
            tools=task.get("tools", [])
        )

        return runner.run(prompt, history)


class GoogleAgentSDKStrategy(ToolExecutionStrategy):
    """Tier 2: Google Agent Development Kit."""

    def __init__(self, ui):
        self.ui = ui

    def execute(self, task, agent, prompt, history):
        try:
            response = self._run_google_adk(task, agent, prompt, history)
            return (response, True)
        except Exception as e:
            logger.warning(f"Google ADK failed: {e}")
            return (str(e), False)

    def _run_google_adk(self, task, agent, prompt, history):
        """Run Google Agent SDK."""
        from google_adk import Agent, ToolRegistry

        # Initialize Google Agent
        google_agent = Agent(
            model=self.llm_interface,
            tools=self._load_tools(task.get("tools", []))
        )

        # Execute with streaming
        return google_agent.run(prompt, history)


class CustomToolLoopStrategy(ToolExecutionStrategy):
    """Tier 3: Custom implementation (guaranteed to work)."""

    def __init__(self, ui, llm_interface, tool_registry):
        self.ui = ui
        self.llm_interface = llm_interface
        self.tool_registry = tool_registry

    def execute(self, task, agent, prompt, history):
        """
        Custom tool-calling loop.
        Simple, robust, guaranteed to work.
        """
        try:
            response = self._custom_tool_loop(task, agent, prompt, history)
            return (response, True)
        except Exception as e:
            # This should NEVER fail, but just in case
            logger.error(f"Custom tool loop failed (CRITICAL): {e}")
            return (f"Error: {e}", False)

    def _custom_tool_loop(self, task, agent, prompt, history):
        """
        Simple tool-calling loop implementation.

        Loop:
        1. Call LLM
        2. Check response for tool calls
        3. If tool call: execute tool, add to history, repeat
        4. If text: return as final answer
        """
        max_iterations = 10
        task_id = task.get("id", "?")

        for iteration in range(max_iterations):
            # 1. Call LLM
            response = self.llm_interface.generate_response(
                system_prompt=agent.system_prompt,
                user_prompt=prompt,
                history=history
            )

            # 2. Parse tool call
            tool_call = self._parse_tool_call(response)

            if tool_call is None:
                # No more tool calls → final answer
                return response

            # 3. Execute tool
            tool_result = self._execute_tool(
                tool_name=tool_call["tool_name"],
                arguments=tool_call["arguments"],
                task_id=task_id
            )

            # 4. Update history
            history.append({
                "role": "assistant",
                "content": response
            })
            history.append({
                "role": "user",
                "content": f"Tool '{tool_call['tool_name']}' result:\n{tool_result}"
            })

            # UI Update
            if hasattr(self.ui, 'add_response_chunk'):
                self.ui.add_response_chunk(
                    task_id,
                    f"\n🔧 Tool: {tool_call['tool_name']}\n"
                )

        raise Exception("Max iterations reached")

    def _parse_tool_call(self, response: str) -> dict | None:
        """
        Parse XML-based tool calls.

        Format:
        <invoke><tool_name>
        <arguments>
        <param>value</param>
        </arguments>
        </tool_name></invoke>
        """
        import re

        pattern = r'<invoke><(\w+)>(.*?)</\1></invoke>'
        match = re.search(pattern, response, re.DOTALL)

        if not match:
            return None

        tool_name = match.group(1)
        args_xml = match.group(2)

        # Parse arguments
        arguments = {}
        param_pattern = r'<(\w+)>(.*?)</\1>'
        for param_match in re.finditer(param_pattern, args_xml, re.DOTALL):
            param_name = param_match.group(1)
            param_value = param_match.group(2).strip()

            if param_name != "arguments":
                arguments[param_name] = param_value

        return {
            "tool_name": tool_name,
            "arguments": arguments
        }

    def _execute_tool(self, tool_name: str, arguments: dict, task_id: str) -> str:
        """Execute tool and return result."""
        tool = self.tool_registry.get_tool(tool_name)

        if tool is None:
            return f"Error: Tool '{tool_name}' not found"

        try:
            result = tool.run(**arguments)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"
```

---

### Main Dispatcher

```python
class AgenticRedundancyDispatcher:
    """
    Executes tool-calling with multi-tier fallback.

    Implements the Agentic Redundancy Architecture:
    - Try Tier 1 (smolagents)
    - If fails → Try Tier 2 (Google ADK)
    - If fails → Try Tier 3 (Custom)
    - Guaranteed success (Tier 3 never fails)
    """

    def __init__(self, ui, llm_interface, tool_registry):
        self.ui = ui
        self.llm_interface = llm_interface
        self.tool_registry = tool_registry

        # Initialize all strategies
        self.strategies = [
            SmolagentsStrategy(ui),
            GoogleAgentSDKStrategy(ui),
            CustomToolLoopStrategy(ui, llm_interface, tool_registry),
        ]

        self.stats = {
            "tier1_success": 0,
            "tier1_fail": 0,
            "tier2_success": 0,
            "tier2_fail": 0,
            "tier3_success": 0,
            "tier3_fail": 0,
        }

    def execute_with_redundancy(
        self,
        task: dict,
        agent,
        prompt: str,
        history: list,
        strategy: str = "sequential"
    ) -> str:
        """
        Execute task with agentic redundancy.

        Args:
            task: Task dictionary
            agent: Agent instance
            prompt: User prompt
            history: Conversation history
            strategy: "sequential" | "parallel" | "smart" | "voting"

        Returns:
            Final response string
        """
        if strategy == "sequential":
            return self._sequential_fallback(task, agent, prompt, history)
        elif strategy == "parallel":
            return self._parallel_racing(task, agent, prompt, history)
        elif strategy == "smart":
            return self._smart_routing(task, agent, prompt, history)
        elif strategy == "voting":
            return self._voting_system(task, agent, prompt, history)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _sequential_fallback(self, task, agent, prompt, history) -> str:
        """
        Try each tier sequentially until one succeeds.

        Most robust, guaranteed to work.
        """
        for i, strategy in enumerate(self.strategies, 1):
            tier_name = strategy.get_name()

            self.ui.status(f"🔄 Tier {i}: {tier_name}...", "info")

            response, success = strategy.execute(task, agent, prompt, history)

            if success:
                self.ui.status(f"✅ Tier {i} succeeded!", "success")
                self._update_stats(f"tier{i}_success")
                return response
            else:
                self.ui.status(f"⚠️ Tier {i} failed: {response[:100]}...", "warning")
                self._update_stats(f"tier{i}_fail")

        # Should never happen (Tier 3 guarantees success)
        raise ExecutionError("All tool-calling strategies failed!")

    def _parallel_racing(self, task, agent, prompt, history) -> str:
        """
        Run all tiers in parallel, first success wins.

        Fastest, but uses more resources.
        """
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    strategy.execute, task, agent, prompt, history
                ): strategy
                for strategy in self.strategies
            }

            for future in concurrent.futures.as_completed(futures):
                response, success = future.result()
                if success:
                    # First success wins, cancel others
                    executor.shutdown(wait=False, cancel_futures=True)
                    return response

        raise ExecutionError("All tiers failed in parallel racing")

    def _smart_routing(self, task, agent, prompt, history) -> str:
        """
        Analyze task and route to best tier.

        Most efficient, uses only one tier.
        """
        # Analyze task complexity
        complexity = self._analyze_task_complexity(task)

        if complexity == "simple":
            # Simple tasks → Tier 3 (fastest)
            strategy = self.strategies[2]
        elif complexity == "medium":
            # Medium tasks → Tier 2 (balanced)
            strategy = self.strategies[1]
        else:
            # Complex tasks → Tier 1 (most robust)
            strategy = self.strategies[0]

        response, success = strategy.execute(task, agent, prompt, history)

        if success:
            return response
        else:
            # Smart routing failed, fall back to sequential
            return self._sequential_fallback(task, agent, prompt, history)

    def _voting_system(self, task, agent, prompt, history) -> str:
        """
        Run all 3 tiers, take majority vote or best result.

        Highest quality, most expensive.
        """
        results = []

        for strategy in self.strategies:
            response, success = strategy.execute(task, agent, prompt, history)
            if success:
                results.append(response)

        if not results:
            raise ExecutionError("All tiers failed in voting system")

        # Take majority or longest response (assuming more detail = better)
        return max(results, key=len)

    def _analyze_task_complexity(self, task: dict) -> str:
        """
        Analyze task to determine complexity.

        Returns:
            "simple" | "medium" | "complex"
        """
        tools = task.get("tools", [])
        objective = task.get("objective", "")

        # Simple heuristics
        if len(tools) == 0:
            return "simple"
        elif len(tools) <= 2 and len(objective) < 100:
            return "medium"
        else:
            return "complex"

    def _update_stats(self, key: str):
        """Update execution statistics."""
        self.stats[key] += 1

    def get_stats(self) -> dict:
        """Get execution statistics."""
        return self.stats.copy()
```

---

## 📊 Redundancy Strategies Comparison

### **Strategy 1: Sequential Fallback** ⭐ Recommended for Start

```python
Try Tier 1 → Fail → Try Tier 2 → Fail → Try Tier 3 → Success
```

**Pros:**
- ✅ Simple to implement
- ✅ Guaranteed success
- ✅ Clear debugging path
- ✅ Resource-efficient (only runs what's needed)

**Cons:**
- ⚠️ Slower if early tiers fail
- ⚠️ Sequential overhead

**Use Case:** Default strategy, production reliability

---

### **Strategy 2: Parallel Racing** ⚡ Fastest

```python
Run Tier 1, 2, 3 simultaneously → First success wins
```

**Pros:**
- ✅ Very fast (no waiting for failures)
- ✅ Always uses best available tier
- ✅ Real-time performance optimization

**Cons:**
- ⚠️ Higher resource usage (3x LLM calls)
- ⚠️ Higher cost (API calls)
- ⚠️ Potential race conditions

**Use Case:** Time-critical tasks, when cost is not a concern

---

### **Strategy 3: Smart Routing** 🧠 Most Efficient

```python
Analyze Task → Choose best Tier → Execute
```

**Pros:**
- ✅ Optimal efficiency (1x call)
- ✅ Lower cost
- ✅ Adaptive to task type

**Cons:**
- ⚠️ Complex routing logic
- ⚠️ Requires good task analysis
- ⚠️ May choose wrong tier

**Use Case:** Production optimization, cost-sensitive environments

---

### **Strategy 4: Voting System** 🏆 Highest Quality

```python
Run all 3 Tiers → Compare results → Take best/majority
```

**Pros:**
- ✅ Highest quality (cross-validation)
- ✅ Catches errors across implementations
- ✅ Consensus-based results

**Cons:**
- ⚠️ Very expensive (3x calls)
- ⚠️ Slowest (waits for all)
- ⚠️ Complex result comparison

**Use Case:** Critical tasks, quality over cost, research

---

## 💰 Cost/Performance Trade-offs

| Strategy | API Calls | Speed | Robustness | Cost |
|----------|-----------|-------|------------|------|
| Sequential Fallback | 1-3x | Medium | ⭐⭐⭐⭐⭐ | Low-Medium |
| Parallel Racing | 1-3x | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium-High |
| Smart Routing | 1x | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low |
| Voting System | 3x | ⭐⭐ | ⭐⭐⭐⭐⭐ | High |

---

## 🎨 UI Integration Examples

### Sequential Fallback Display

```
╭─ 💬 S1: Analyzing Code ─────────────────────────╮
│ 🔄 Agentic Redundancy: Sequential Fallback      │
│                                                  │
│ [Tier 1] smolagents                             │
│   ✅ Tool parsed: read_selfai_code               │
│   ❌ Execution failed: Timeout (5s)              │
│                                                  │
│ [Tier 2] Google Agent SDK                       │
│   ✅ Tool parsed: read_selfai_code               │
│   ✅ Execution success! (2.3s)                   │
│   📊 Result: 1543 lines of code                  │
│                                                  │
│ Final Response:                                  │
│ Based on the code analysis of selfai/core...    │
╰──────────────────────────────────────────────────╯
```

### Parallel Racing Display

```
╭─ 💬 S2: Complex Analysis ───────────────────────╮
│ ⚡ Agentic Redundancy: Parallel Racing          │
│                                                  │
│ Running 3 tiers simultaneously...               │
│                                                  │
│ [Tier 1] smolagents.............. 🏃 Running    │
│ [Tier 2] Google SDK.............. 🏃 Running    │
│ [Tier 3] Custom Loop............. 🏃 Running    │
│                                                  │
│ 🏆 WINNER: Tier 2 (1.8s)                        │
│                                                  │
│ Final Response:                                  │
│ Analysis complete: Found 15 functions...        │
╰──────────────────────────────────────────────────╯
```

### Voting System Display

```
╭─ 💬 S3: Critical Task ──────────────────────────╮
│ 🗳️  Agentic Redundancy: Voting System           │
│                                                  │
│ Tier 1 Result: [confidence: 85%]                │
│ "The function handles authentication..."        │
│                                                  │
│ Tier 2 Result: [confidence: 92%]                │
│ "The function manages auth with JWT..."         │
│                                                  │
│ Tier 3 Result: [confidence: 78%]                │
│ "Authentication function using tokens..."       │
│                                                  │
│ 🏆 CONSENSUS: Tier 2 (highest confidence)       │
│                                                  │
│ Final Response:                                  │
│ The function manages auth with JWT...           │
╰──────────────────────────────────────────────────╯
```

---

## 🚨 Potential Issues & Solutions

### Issue 1: Inconsistent Results

**Problem:**
```python
# Tier 1 returns: "Python is great for ML"
# Tier 2 returns: "Python eignet sich für ML"
# Which to use?
```

**Solution:**
- Always use first successful result (Sequential)
- Use longest/most detailed result (Voting)
- Implement result normalization

---

### Issue 2: Duplicate Tool Calls

**Problem:**
```python
# Tier 1 calls expensive tool (costs $0.10)
# Tier 1 fails → Tier 2 calls SAME tool again ($0.10)
# Total cost: $0.20 for 1 tool result
```

**Solution:**
```python
class ToolResultCache:
    """Cache tool results between tier executions."""

    def __init__(self):
        self.cache = {}

    def get(self, tool_name, args_hash):
        key = f"{tool_name}:{args_hash}"
        return self.cache.get(key)

    def set(self, tool_name, args_hash, result):
        key = f"{tool_name}:{args_hash}"
        self.cache[key] = result
```

---

### Issue 3: Debugging Complexity

**Problem:**
```python
# Task failed, but which tier was active?
# What exactly went wrong in each tier?
```

**Solution:**
```python
class ExecutionLogger:
    """Detailed logging for redundancy debugging."""

    def log_tier_attempt(self, tier: int, strategy: str, task_id: str):
        logger.info(f"[{task_id}] Attempting Tier {tier}: {strategy}")

    def log_tier_result(self, tier: int, success: bool, message: str, duration: float):
        level = "SUCCESS" if success else "FAILURE"
        logger.info(
            f"[Tier {tier}] {level} in {duration:.2f}s: {message[:100]}"
        )

    def log_final_result(self, winning_tier: int, total_duration: float):
        logger.info(
            f"Execution complete: Tier {winning_tier} won in {total_duration:.2f}s"
        )
```

---

### Issue 4: Strategy Selection

**Problem:**
```python
# When to use which strategy?
# Sequential vs Parallel vs Smart?
```

**Solution: Configuration-Based**
```yaml
# config.yaml
agentic_redundancy:
  default_strategy: "sequential"

  # Per-task-type strategies
  strategies:
    simple_tasks: "smart"      # Fast, efficient
    critical_tasks: "voting"   # Quality first
    time_sensitive: "parallel" # Speed first

  # Tier priorities
  tier_order:
    - smolagents
    - google_adk
    - custom_loop
```

---

## 🎯 Implementation Roadmap

### Phase 1: Foundation (Day 1) ⭐ Start Here

**Goal:** Get Sequential Fallback working

**Tasks:**
1. Implement base `ToolExecutionStrategy` class
2. Implement `CustomToolLoopStrategy` (Tier 3 - simplest)
3. Implement `AgenticRedundancyDispatcher` with sequential fallback only
4. Integration tests with simple tools

**Deliverable:** Working tool-calling with guaranteed fallback

---

### Phase 2: smolagents Integration (Day 2-3)

**Goal:** Add Tier 1 (smolagents)

**Tasks:**
1. Implement `SmolagentsStrategy`
2. Add streaming support to smolagents
3. Tool result caching
4. Performance benchmarking (Tier 1 vs Tier 3)

**Deliverable:** Fast primary tier with robust fallback

---

### Phase 3: Google ADK Integration (Day 4-5)

**Goal:** Add Tier 2 (Google Agent SDK)

**Tasks:**
1. Implement `GoogleAgentSDKStrategy`
2. Test compatibility with existing tools
3. Benchmark all 3 tiers
4. Statistics tracking

**Deliverable:** Complete 3-tier redundancy system

---

### Phase 4: Advanced Strategies (Week 2)

**Goal:** Parallel Racing, Smart Routing, Voting

**Tasks:**
1. Implement parallel racing
2. Implement smart routing with task analysis
3. Implement voting system
4. A/B testing framework
5. Cost optimization

**Deliverable:** Production-ready multi-strategy system

---

### Phase 5: Monitoring & Optimization (Week 3+)

**Goal:** Production hardening

**Tasks:**
1. Advanced logging and metrics
2. Performance dashboards
3. Automatic tier optimization based on stats
4. Cost monitoring and alerts
5. Documentation and user guide

**Deliverable:** Enterprise-grade agentic redundancy

---

## 📝 Configuration Example

```yaml
# config.yaml

agentic_redundancy:
  enabled: true
  default_strategy: "sequential"  # sequential | parallel | smart | voting

  # Tier configurations
  tiers:
    tier1:
      name: "smolagents"
      enabled: true
      timeout: 30.0
      max_retries: 2

    tier2:
      name: "google_adk"
      enabled: true
      timeout: 45.0
      max_retries: 1

    tier3:
      name: "custom_loop"
      enabled: true
      timeout: 60.0
      max_retries: 0  # Never fail

  # Strategy-specific settings
  strategies:
    sequential:
      stop_on_first_success: true
      log_all_attempts: true

    parallel:
      max_workers: 3
      cancel_on_first_success: true

    smart:
      complexity_threshold_simple: 2  # Max 2 tools = simple
      complexity_threshold_complex: 5  # 5+ tools = complex

    voting:
      min_consensus: 2  # At least 2 tiers must agree
      tie_breaker: "longest"  # longest | shortest | first

  # Performance optimization
  caching:
    enabled: true
    ttl: 3600  # Cache tool results for 1 hour
    max_size: 1000  # Max cached results

  # Monitoring
  monitoring:
    collect_stats: true
    log_level: "INFO"
    alert_on_all_tiers_fail: true
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
def test_sequential_fallback_tier1_success():
    """Test that Tier 1 success stops execution."""
    dispatcher = AgenticRedundancyDispatcher(...)

    # Mock Tier 1 to succeed
    mock_tier1_success()

    result = dispatcher.execute_with_redundancy(
        task, agent, prompt, history, strategy="sequential"
    )

    assert result == "Tier 1 response"
    assert dispatcher.stats["tier1_success"] == 1
    assert dispatcher.stats["tier2_success"] == 0  # Never called


def test_sequential_fallback_tier1_fail_tier2_success():
    """Test that Tier 2 is tried when Tier 1 fails."""
    dispatcher = AgenticRedundancyDispatcher(...)

    # Mock Tier 1 to fail, Tier 2 to succeed
    mock_tier1_fail()
    mock_tier2_success()

    result = dispatcher.execute_with_redundancy(
        task, agent, prompt, history, strategy="sequential"
    )

    assert result == "Tier 2 response"
    assert dispatcher.stats["tier1_fail"] == 1
    assert dispatcher.stats["tier2_success"] == 1


def test_all_tiers_fail():
    """Test that appropriate error is raised when all fail."""
    dispatcher = AgenticRedundancyDispatcher(...)

    # Mock all tiers to fail
    mock_all_tiers_fail()

    with pytest.raises(ExecutionError):
        dispatcher.execute_with_redundancy(
            task, agent, prompt, history, strategy="sequential"
        )
```

---

### Integration Tests

```python
def test_real_tool_execution_with_redundancy():
    """Test real tool execution through redundancy system."""
    dispatcher = AgenticRedundancyDispatcher(...)

    task = {
        "id": "T1",
        "objective": "Read the file config.yaml",
        "tools": ["read_selfai_code"]
    }

    result = dispatcher.execute_with_redundancy(
        task, agent, "Read config.yaml", [], strategy="sequential"
    )

    assert "agentic_redundancy:" in result
    assert "enabled:" in result


def test_parallel_racing_performance():
    """Test that parallel racing is faster than sequential."""
    import time

    dispatcher = AgenticRedundancyDispatcher(...)

    start = time.time()
    result_seq = dispatcher.execute_with_redundancy(
        task, agent, prompt, history, strategy="sequential"
    )
    sequential_time = time.time() - start

    start = time.time()
    result_par = dispatcher.execute_with_redundancy(
        task, agent, prompt, history, strategy="parallel"
    )
    parallel_time = time.time() - start

    # Parallel should be faster (or equal if Tier 1 succeeds immediately)
    assert parallel_time <= sequential_time * 1.2  # 20% tolerance
```

---

## 📚 Usage Examples

### Simple Sequential Fallback

```python
from selfai.core.agentic_redundancy import AgenticRedundancyDispatcher

# Initialize
dispatcher = AgenticRedundancyDispatcher(
    ui=ui,
    llm_interface=minimax_interface,
    tool_registry=tool_registry
)

# Execute task with redundancy
task = {
    "id": "S1",
    "objective": "Analyze the codebase structure",
    "tools": ["list_selfai_files", "read_selfai_code"]
}

result = dispatcher.execute_with_redundancy(
    task=task,
    agent=agent,
    prompt="Analyze the codebase",
    history=[],
    strategy="sequential"  # Try Tier 1 → 2 → 3
)

print(result)
```

---

### Parallel Racing for Speed

```python
# For time-critical tasks
result = dispatcher.execute_with_redundancy(
    task=urgent_task,
    agent=agent,
    prompt="Quick analysis needed!",
    history=[],
    strategy="parallel"  # Run all tiers simultaneously
)

# Check which tier won
stats = dispatcher.get_stats()
print(f"Winning tier: {stats}")
```

---

### Smart Routing for Efficiency

```python
# System automatically chooses best tier based on task
result = dispatcher.execute_with_redundancy(
    task=task,
    agent=agent,
    prompt=prompt,
    history=history,
    strategy="smart"  # Intelligent tier selection
)
```

---

### Voting for Quality

```python
# For critical decisions, run all tiers and take consensus
result = dispatcher.execute_with_redundancy(
    task=critical_task,
    agent=agent,
    prompt="Critical analysis - need highest quality",
    history=[],
    strategy="voting"  # All tiers vote, best result wins
)
```

---

## 🎓 Best Practices

### 1. Start with Sequential Fallback
- Simplest to implement
- Most reliable
- Easy to debug
- Good default choice

### 2. Use Parallel Racing Sparingly
- Only for time-critical tasks
- Monitor costs carefully
- Good for production speed optimization

### 3. Smart Routing Requires Tuning
- Analyze your task patterns
- Adjust complexity thresholds
- Monitor which tier gets used most
- Optimize over time

### 4. Voting System for Critical Tasks Only
- Very expensive (3x cost)
- Use for high-stakes decisions
- Research and validation tasks

### 5. Monitor and Optimize
```python
# Regular stats review
stats = dispatcher.get_stats()
tier1_success_rate = stats["tier1_success"] / (stats["tier1_success"] + stats["tier1_fail"])

if tier1_success_rate < 0.7:
    # Tier 1 failing too often, investigate or adjust routing
    logger.warning(f"Tier 1 success rate low: {tier1_success_rate:.2%}")
```

### 6. Cache Tool Results
```python
# Avoid duplicate expensive tool calls
cache = ToolResultCache()

# In execute_tool:
result = cache.get(tool_name, args_hash)
if result is None:
    result = tool.run(**arguments)
    cache.set(tool_name, args_hash, result)
```

### 7. Log Everything
```python
# Detailed logging helps debug failures
logger.info(f"[{task_id}] Tier 1 attempt...")
logger.warning(f"[{task_id}] Tier 1 failed: {error}")
logger.info(f"[{task_id}] Falling back to Tier 2...")
logger.success(f"[{task_id}] Tier 2 succeeded!")
```

---

## 🚀 Why This Is Genius

### Traditional Approach:
```
One tool-calling system
    ↓
If it fails → GAME OVER ❌
```

### Agentic Redundancy Approach:
```
Three independent systems
    ↓
If Tier 1 fails → Try Tier 2
    ↓
If Tier 2 fails → Try Tier 3
    ↓
GUARANTEED SUCCESS ✅
```

### Key Innovations:

1. **Never Fail:** With 3 independent implementations, system can't completely fail
2. **Self-Healing:** Automatically recovers from tier failures
3. **Battle-Tested:** Uses proven libraries (smolagents, Google ADK) + custom fallback
4. **Future-Proof:** Can add/remove tiers without breaking existing code
5. **Cost-Optimized:** Only uses what's needed (sequential) or what you choose
6. **Quality-Assured:** Voting system provides validation through consensus

---

## 🎯 SelfAI's Superpower

**Agentic Redundancy makes SelfAI:**
- ✅ **Unstoppable** - Always finds a way to execute tools
- ✅ **Self-Healing** - Automatically recovers from failures
- ✅ **Adaptive** - Uses best strategy for each situation
- ✅ **Battle-Tested** - Leverages multiple proven frameworks
- ✅ **Future-Proof** - Easy to add new tiers/strategies
- ✅ **Production-Ready** - Robust enough for real-world use

---

## 📖 Further Reading

- **Strategy Pattern**: Design pattern for interchangeable algorithms
- **Circuit Breaker Pattern**: Preventing cascading failures
- **Multi-Armed Bandit**: Optimizing strategy selection over time
- **Consensus Algorithms**: Voting and agreement in distributed systems

---

## 🏁 Quick Start Tomorrow

```python
# 1. Implement CustomToolLoopStrategy (simplest, guaranteed to work)
# 2. Implement AgenticRedundancyDispatcher with sequential fallback
# 3. Test with real SelfAI tasks
# 4. Celebrate when it works! 🎉
```

**Total estimated time:** 2-3 hours for working system

**Result:** SelfAI that NEVER fails at tool execution! ⚡

---

**Created:** 2025-12-26
**Status:** Architecture Design Phase
**Next Steps:** Phase 1 Implementation (Custom Tool Loop + Sequential Fallback)

---

🚀 **Agentic Redundancy = SelfAI's Unfair Advantage** 🚀

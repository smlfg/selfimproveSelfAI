# Quick Start: Tool-Calling Agent Implementation for MiniMax

## Choose Your Path

### Path A: MVP Fast Track (1-2 hours) - Custom Loop
**When:** You need working prototype NOW
**Outcome:** Working agent with 18 tools, no framework overhead

### Path B: Production Ready (8 hours) - LangChain
**When:** Requirements are clear, plan to scale
**Outcome:** Maintainable framework-based solution with easy model switching

### Path C: Enterprise Grade (16+ hours) - LangGraph
**When:** You foresee complex multi-agent scenarios
**Outcome:** Production-grade state machine with observability

---

## Path A: Custom Agent Loop (RECOMMENDED FOR MVP)

### Step 1: System Prompt Template
```python
SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.

When you need to use a tool, respond ONLY with JSON in this format:
Action: {"tool": "tool_name", "args": {"param1": "value1", "param2": "value2"}}

IMPORTANT: Only output JSON when calling tools. Otherwise respond naturally.

Available tools:
{tools_description}
"""
```

### Step 2: Tool Executor
```python
import json
import re

def parse_action(response_text: str):
    """Extract Action: {...} from response"""
    match = re.search(r'Action:\s*({.*?})', response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None

def execute_tool(tool_name: str, args: dict, tools_registry: dict) -> str:
    """Execute tool and return result"""
    if tool_name not in tools_registry:
        return f"Error: Tool {tool_name} not found"

    try:
        result = tools_registry[tool_name](**args)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
```

### Step 3: Main Agent Loop
```python
from minimax_sdk import MiniMaxAPI

def agent_loop(query: str, api_key: str, max_iterations: int = 10):
    """Main agent loop"""
    client = MiniMaxAPI(api_key=api_key)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(
            tools_description=get_tools_description()
        )},
        {"role": "user", "content": query}
    ]

    for iteration in range(max_iterations):
        # Call MiniMax
        response = client.messages.create(
            model="minimax-m2",
            messages=messages
        )

        agent_response = response.content[0].text
        messages.append({"role": "assistant", "content": agent_response})

        # Check for tool call
        action = parse_action(agent_response)

        if action is None:
            # No tool call, return final response
            return agent_response

        # Execute tool
        tool_name = action.get("tool")
        args = action.get("args", {})
        tool_result = execute_tool(tool_name, args, TOOLS_REGISTRY)

        # Add observation to messages
        messages.append({
            "role": "user",
            "content": f"Tool {tool_name} returned: {tool_result}"
        })

    return "Max iterations reached"

# Tools registry
TOOLS_REGISTRY = {
    "get_weather": weather_tool,
    "read_file": file_read_tool,
    "write_file": file_write_tool,
    # ... 18 tools total
}

def get_tools_description() -> str:
    """Generate tool descriptions for system prompt"""
    descriptions = []
    for name, tool_func in TOOLS_REGISTRY.items():
        doc = tool_func.__doc__ or "No description"
        descriptions.append(f"- {name}: {doc}")
    return "\n".join(descriptions)
```

### Step 4: Test
```python
if __name__ == "__main__":
    result = agent_loop(
        query="What's the weather today?",
        api_key="your-minimax-key"
    )
    print("Agent:", result)
```

**Total Time:** 1-2 hours
**LOC:** ~150-200
**Dependencies:** Just MiniMax SDK + your tools

---

## Path B: LangChain with Custom Prompt (RECOMMENDED FOR SCALING)

### Step 1: Create Custom Prompt Template
```python
from langchain_core.prompts import PromptTemplate

ACTION_FORMAT = """Respond ONLY with JSON when calling tools:
Action: {"tool": "tool_name", "args": {...}}"""

custom_prompt = PromptTemplate(
    input_variables=["tools", "input", "agent_scratchpad"],
    template="""You are a helpful AI assistant.

{ACTION_FORMAT}

{tools}

Question: {input}

{agent_scratchpad}"""
)
```

### Step 2: Create Tool Definitions
```python
from langchain.tools import Tool

weather_tool = Tool(
    name="get_weather",
    func=get_weather,
    description="Get weather for a location"
)

# Create 18 tools this way
tools = [weather_tool, ...]
```

### Step 3: Create Agent
```python
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI  # or your MiniMax wrapper

llm = ChatOpenAI(model="minimax-m2")  # If MiniMax has OpenAI wrapper
# OR use custom LLM wrapper:
from your_minimax_wrapper import MiniMaxLLM
llm = MiniMaxLLM()

agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=custom_prompt
)

executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10
)

result = executor.invoke({"input": "What's the weather?"})
```

### Step 4: Optional - Add Memory
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(memory_key="chat_history")

# Integrate with executor
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    max_iterations=10
)
```

**Total Time:** 4-8 hours
**LOC:** ~250-300
**Benefits:** Framework features, easy model switching, larger ecosystem

---

## Path C: LangGraph (ENTERPRISE)

### Step 1: Define State
```python
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated

class AgentState(TypedDict):
    messages: list
    tools: list

graph_builder = StateGraph(AgentState)
```

### Step 2: Define Nodes
```python
def agent_node(state):
    """LLM decision node"""
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": messages + [response]}

def tool_node(state):
    """Tool execution node"""
    # Extract tool calls and execute
    return {"messages": state["messages"] + [results]}
```

### Step 3: Build Graph
```python
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges("agent", route_to_tool_or_end)
graph_builder.add_edge("tools", "agent")

graph = graph_builder.compile()
```

**Total Time:** 16+ hours
**LOC:** ~300+
**Use Case:** Complex multi-agent systems, production monitoring

---

## Decision Matrix

```
┌─────────────────────────────────────────────────────────┐
│ Choose your path based on your answers:                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Q1: How much time do you have?                         │
│   - Today/tomorrow → Path A (Custom Loop)              │
│   - This week     → Path B (LangChain)                 │
│   - This month    → Path C (LangGraph)                 │
│                                                         │
│ Q2: Will you need to switch LLMs later?                │
│   - No            → Path A works fine                  │
│   - Maybe         → Path B (easier switching)          │
│   - Yes           → Path B or C                        │
│                                                         │
│ Q3: Do you need multi-agent coordination?              │
│   - No            → Path A or B                        │
│   - Yes           → Path B or C                        │
│   - Advanced      → Path C (LangGraph)                 │
│                                                         │
│ Default: Choose Path B (LangChain)                     │
│ Reasoning: Best balance of speed and features         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Migration Path (If Starting with A, Upgrading to B)

**From Custom Loop → LangChain:**

1. Copy your tool definitions to Tool objects (1 hour)
2. Create custom prompt template (30 min)
3. Wrap agent loop in AgentExecutor (1 hour)
4. Test and adjust (1 hour)

**Total upgrade time:** ~4 hours

---

## Verification Checklist

### Path A (Custom Loop)
- [ ] System prompt defined with `Action: {...}` format
- [ ] Parse function correctly extracts JSON
- [ ] Tool executor handles all 18 tools
- [ ] Agent loop runs 5+ iterations successfully
- [ ] No format confusion after tool execution

### Path B (LangChain)
- [ ] Custom prompt template created
- [ ] All tools converted to LangChain Tool objects
- [ ] Agent created with create_tool_calling_agent()
- [ ] Executor runs successfully
- [ ] Tool results propagate back correctly

### Path C (LangGraph)
- [ ] State schema defined
- [ ] All nodes implemented
- [ ] Graph edges configured
- [ ] Routing logic works
- [ ] Multi-agent scenarios tested

---

## Testing Strategy

```python
# Test queries for 18-tool agent:
TEST_QUERIES = [
    # Single tool: "What's the weather in Paris?"
    # File operations: "Read /path/to/file"
    # Writing: "Write 'hello' to /tmp/test.txt"
    # Multi-step: "Check weather, then save to file"
    # Error handling: "Use invalid tool"
    # Tool dependency: "Get weather, format as JSON"
]

for query in TEST_QUERIES:
    result = agent(query)
    print(f"✓ {query[:50]}... -> {result[:100]}...")
```

---

## Common Issues & Solutions

### Issue: MiniMax gets confused after first tool call
**Solution:** Ensure prompt template maintains `Action: {...}` format consistency across all interactions. Use Path A or B with full prompt control.

### Issue: Tool results not feeding back correctly
**Solution:** Verify that after tool execution, result is added back to messages/context in same conversation. Message history must be complete.

### Issue: Agent gets stuck in infinite loop
**Solution:** Set `max_iterations` limit (default 10). Add logging to see what tools are being called.

### Issue: Tool calls not being recognized
**Solution:** Verify regex pattern matches your exact JSON format. Test parse_action() independently first.

---

## Resources

- **Custom Loop:** https://sketch.dev/blog/agent-loop
- **LangChain Docs:** https://python.langchain.com/docs/
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **MiniMax Docs:** Check MiniMax API documentation

---

## Next Steps

1. **Pick your path** (recommended: Path B for balance)
2. **Run the quick start code** from above
3. **Add your 18 tools** to the tool registry
4. **Test with sample queries**
5. **Monitor for format consistency** with MiniMax
6. **Plan future upgrades** if needs change

**Estimated Total Implementation Time:**
- Path A: 2 hours
- Path B: 8 hours
- Path C: 16+ hours

Start with Path A for MVP, upgrade to Path B in Phase 2.

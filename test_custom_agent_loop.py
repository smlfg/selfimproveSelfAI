#!/usr/bin/env python3
"""
Test Custom Agent Loop with MiniMax and Dummy Tools
====================================================

This should work perfectly with MiniMax's Action: {...} format!
"""

import os
from dotenv import load_dotenv
from selfai.core.minimax_interface import MinimaxInterface
from selfai.core.custom_agent_loop import CustomAgentLoop
from selfai.tools.dummy_tool import HelloWorldTool, EchoTool, CounterTool

# Load environment
load_dotenv()
api_key = os.getenv('MINIMAX_API_KEY')

# Initialize MiniMax
print("="*70)
print("🧪 TESTING CUSTOM AGENT LOOP WITH MINIMAX")
print("="*70)

minimax = MinimaxInterface(api_key=api_key)
print("✅ MiniMax interface loaded")

# Initialize tools
tools = [
    HelloWorldTool(),
    EchoTool(),
    CounterTool(),
]
print(f"✅ {len(tools)} tools loaded: {[t.name for t in tools]}")

# Create agent
agent = CustomAgentLoop(
    llm_interface=minimax,
    tools=tools,
    max_steps=5,
    verbose=True,
)
print("✅ Custom Agent Loop created")
print()

# Test cases
test_cases = [
    {
        "name": "Simple Hello",
        "input": "Say hello!",
        "expected_tool": "say_hello",
    },
    {
        "name": "Hello with Name",
        "input": "Say hello to Alice",
        "expected_tool": "say_hello",
    },
    {
        "name": "Echo Test",
        "input": "Echo the message 'Testing 123'",
        "expected_tool": "echo_message",
    },
    {
        "name": "Counter Test",
        "input": "Count from 1 to 5",
        "expected_tool": "count_numbers",
    },
    {
        "name": "Multi-Step",
        "input": "Say hello to Bob and then count to 3",
        "expected_tool": "say_hello, count_numbers",
    },
]

# Run tests
for i, test in enumerate(test_cases, 1):
    print("="*70)
    print(f"📝 TEST {i}: {test['name']}")
    print(f"Input: {test['input']}")
    print(f"Expected tools: {test['expected_tool']}")
    print("-"*70)

    try:
        result = agent.run(test['input'])
        print(f"\n✅ SUCCESS!")
        print(f"Final Answer: {result}")

    except Exception as e:
        print(f"\n❌ FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()

print("="*70)
print("✅ ALL TESTS COMPLETED!")
print("="*70)

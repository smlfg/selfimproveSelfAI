#!/usr/bin/env python3
"""
Test Full SelfAI Integration with Custom Agent Loop
====================================================

This script tests the custom agent loop integration in the full SelfAI environment
with all 24 tools (including 3 dummy test tools and 21 real tools).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

from config_loader import load_configuration
from selfai.core.minimax_interface import MinimaxInterface
from selfai.core.custom_agent_loop import CustomAgentLoop
from selfai.tools.tool_registry import get_tools_for_agent
from selfai.ui.terminal_ui import TerminalUI

print("=" * 70)
print("🧪 TESTING FULL SELFAI INTEGRATION WITH CUSTOM AGENT LOOP")
print("=" * 70)

# Load configuration
config = load_configuration()
print("✅ Configuration loaded")

# Initialize UI
ui = TerminalUI()
print("✅ Terminal UI initialized")

# Initialize MiniMax interface
api_key = os.getenv('MINIMAX_API_KEY')
minimax = MinimaxInterface(api_key=api_key)
print(f"✅ MiniMax interface loaded")

# Get all tools
tools = get_tools_for_agent()
print(f"✅ {len(tools)} tools loaded")

# Initialize custom agent loop
agent = CustomAgentLoop(
    llm_interface=minimax,
    tools=tools,
    max_steps=getattr(config.system, 'agent_max_steps', 10),
    ui=ui,
    verbose=True,
)
print("✅ Custom Agent Loop initialized")
print()

# Test cases
test_cases = [
    {
        "name": "Test 1: Dummy Tool - Say Hello",
        "input": "Say hello!",
        "expected": "Should call say_hello tool",
    },
    {
        "name": "Test 2: Dummy Tool - Echo",
        "input": "Echo the message 'Integration test works!'",
        "expected": "Should call echo_message tool",
    },
    {
        "name": "Test 3: Dummy Tool - Counter",
        "input": "Count from 1 to 3",
        "expected": "Should call count_numbers tool",
    },
    {
        "name": "Test 4: Real Tool - List Files",
        "input": "List Python files in the selfai directory",
        "expected": "Should call ls tool",
    },
    {
        "name": "Test 5: Real Tool - Search Files",
        "input": "Search for 'CustomAgentLoop' in Python files",
        "expected": "Should call grep tool",
    },
    {
        "name": "Test 6: Multi-Step - List SelfAI Files",
        "input": "List all SelfAI files in the core directory",
        "expected": "Should call list_selfai_files tool",
    },
]

# Run tests
for i, test in enumerate(test_cases, 1):
    print("=" * 70)
    print(f"📝 {test['name']}")
    print(f"Input: {test['input']}")
    print(f"Expected: {test['expected']}")
    print("-" * 70)

    try:
        result = agent.run(test['input'])
        print(f"\n✅ SUCCESS!")
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")

    except Exception as e:
        print(f"\n❌ FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()

print("=" * 70)
print("✅ INTEGRATION TESTS COMPLETED!")
print("=" * 70)

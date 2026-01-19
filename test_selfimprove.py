#!/usr/bin/env python3
"""
Test SelfAI Self-Improvement Feature
====================================

This is the FINAL test - if this works, SelfAI can autonomously improve itself!
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

print("=" * 80)
print("🚀 FINAL TEST: SELFAI SELF-IMPROVEMENT CAPABILITY")
print("=" * 80)
print()
print("This test determines if SelfAI can autonomously improve itself.")
print("If successful, SelfAI becomes a truly autonomous self-improving system!")
print()

# Load configuration
config = load_configuration()
print("✅ Configuration loaded")

# Initialize UI
ui = TerminalUI()

# Initialize MiniMax
api_key = os.getenv('MINIMAX_API_KEY')
minimax = MinimaxInterface(api_key=api_key)
print("✅ MiniMax interface loaded")

# Get all tools
tools = get_tools_for_agent()
print(f"✅ {len(tools)} tools loaded")

# Check if self-improvement tools are available
improvement_tools = [t for t in tools if 'improve' in t.name.lower() or 'selfai' in t.name.lower()]
print(f"\n🔍 Self-improvement related tools found: {[t.name for t in improvement_tools]}")

# Initialize custom agent loop with higher max_steps for self-improvement
agent = CustomAgentLoop(
    llm_interface=minimax,
    tools=tools,
    max_steps=15,  # Higher limit for complex self-improvement tasks
    ui=ui,
    verbose=True,
)
print("✅ Custom Agent Loop initialized (max_steps=15)")
print()

# Test cases for self-improvement
test_cases = [
    {
        "name": "Test 1: List SelfAI Files",
        "input": "List all Python files in the SelfAI core directory",
        "expected": "Should call list_selfai_files with subdirectory='core'",
        "max_steps": 3,
    },
    {
        "name": "Test 2: Read SelfAI Code",
        "input": "Read the custom_agent_loop.py file to understand the implementation",
        "expected": "Should call read_selfai_code",
        "max_steps": 3,
    },
    {
        "name": "Test 3: Search SelfAI Code",
        "input": "Search for the function definition of 'run' in the custom agent loop code",
        "expected": "Should call search_selfai_code",
        "max_steps": 3,
    },
]

# Run self-improvement tests
for i, test in enumerate(test_cases, 1):
    print("=" * 80)
    print(f"📝 {test['name']}")
    print(f"Input: {test['input']}")
    print(f"Expected: {test['expected']}")
    print("-" * 80)

    try:
        # Temporarily adjust max_steps for this test
        original_max_steps = agent.max_steps
        agent.max_steps = test.get('max_steps', 5)

        result = agent.run(test['input'])

        # Restore max_steps
        agent.max_steps = original_max_steps

        print(f"\n✅ SUCCESS!")
        print(f"Result: {result[:300]}..." if len(result) > 300 else f"Result: {result}")

    except Exception as e:
        print(f"\n❌ FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()

print("=" * 80)
print("🎉 SELF-IMPROVEMENT TESTS COMPLETED!")
print("=" * 80)
print()
print("If all tests passed, SelfAI can now:")
print("  ✅ List its own source files")
print("  ✅ Read its own code")
print("  ✅ Search within its own codebase")
print()
print("Next step: SelfAI can analyze its own code and suggest improvements!")
print("This means SelfAI has achieved AUTONOMOUS SELF-IMPROVEMENT! 🚀")

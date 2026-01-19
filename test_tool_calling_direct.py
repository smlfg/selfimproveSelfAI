#!/usr/bin/env python3
"""
Direct test of tool-calling without SelfAI agent framework.
Tests if MiniMax understands tool-calling instructions.
"""

import os
from dotenv import load_dotenv
from selfai.core.minimax_interface import MinimaxInterface

# Load API key
load_dotenv()
api_key = os.getenv('MINIMAX_API_KEY')

# Create MiniMax interface
minimax = MinimaxInterface(api_key=api_key)

# Tool-calling system prompt (simplified)
system_prompt = """You are a helpful AI assistant with access to tools.

When the user asks you to do something that requires a tool, you MUST respond with:
Action: {"name": "tool_name", "arguments": {"arg1": "value1"}}

Available Tools:
1. say_hello(name: str | None) - Returns a greeting message

Examples:
User: Say hello!
Assistant: Action: {"name": "say_hello", "arguments": {}}

User: Say hello to Alice
Assistant: Action: {"name": "say_hello", "arguments": {"name": "Alice"}}

IMPORTANT: When using a tool, ONLY output the Action line, nothing else!
"""

# Test messages
test_cases = [
    "Say hello!",
    "Say hello to Max",
    "What's the weather?",  # Should say "no tool available"
]

print("="*70)
print("🧪 TESTING TOOL-CALLING WITH MINIMAX")
print("="*70)

for i, user_input in enumerate(test_cases, 1):
    print(f"\n📝 Test {i}: {user_input}")
    print("-"*70)

    try:
        response = minimax.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_input,
            max_tokens=200,
            temperature=0.1,  # Low temperature for consistent tool-calling
        )

        print(f"🤖 MiniMax Response:")
        print(response)

        # Check if it's a valid tool call
        if "Action:" in response and '{"name"' in response:
            print("✅ VALID TOOL CALL DETECTED!")
        elif i <= 2:  # First two should use tools
            print("❌ EXPECTED TOOL CALL, GOT TEXT RESPONSE")
        else:
            print("✅ CORRECTLY REFUSED (NO TOOL AVAILABLE)")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()

print("="*70)
print("📊 CONCLUSION:")
print("If MiniMax consistently returns 'Action: {...}' for tool requests,")
print("then the issue is in the smolagents integration, not MiniMax itself.")
print("="*70)

#!/usr/bin/env python3
"""
Test smolagents ToolCallingAgent directly with MiniMax.
"""

import os
from dotenv import load_dotenv
from smolagents import ToolCallingAgent, Tool
from selfai.core.minimax_interface import MinimaxInterface
from selfai.core.smolagents_runner import _SelfAIModel

# Load API key
load_dotenv()
api_key = os.getenv('MINIMAX_API_KEY')

# Create MiniMax interface
minimax_interface = MinimaxInterface(api_key=api_key)

# Wrap as smolagents Model
model = _SelfAIModel(minimax_interface, model_id="MiniMax-M2")

# Define simple test tool
class SayHelloTool(Tool):
    name = "say_hello"
    description = "Returns a friendly greeting message"
    inputs = {
        "name": {
            "type": "string",
            "description": "Optional name to greet",
            "nullable": True,
        }
    }
    output_type = "string"

    def forward(self, name: str = None):
        if name:
            return f"🎉 Hello {name}! Tool-Calling works!"
        return "🎉 Hello World! Tool-Calling works!"

# Create agent
print("="*70)
print("🧪 TESTING SMOLAGENTS WITH MINIMAX")
print("="*70)

try:
    agent = ToolCallingAgent(
        tools=[SayHelloTool()],
        model=model,
    )

    print("\n✅ Agent created successfully!")
    print(f"📋 Agent has {len(agent.tools)} tool(s)")

    # Test 1: Simple hello
    print("\n" + "="*70)
    print("📝 Test 1: Say hello!")
    print("-"*70)

    result = agent.run("Say hello!")
    print(f"\n🤖 Agent Result: {result}")

    # Test 2: Hello with name
    print("\n" + "="*70)
    print("📝 Test 2: Say hello to Alice")
    print("-"*70)

    result = agent.run("Say hello to Alice")
    print(f"\n🤖 Agent Result: {result}")

    print("\n" + "="*70)
    print("✅ SUCCESS! smolagents tool-calling works with MiniMax!")
    print("="*70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "="*70)
    print("❌ FAILED! There's an issue with smolagents integration.")
    print("="*70)

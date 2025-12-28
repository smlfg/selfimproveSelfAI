#!/usr/bin/env python3
"""
Quick test script to execute a pre-made plan JSON file.
Usage: python test_plan_execution.py <plan_file.json>
"""

import sys
import json
from pathlib import Path

# Add selfai to path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import load_configuration
from selfai.core.agent_manager import AgentManager
from selfai.core.memory_system import MemorySystem
from selfai.core.execution_dispatcher import ExecutionDispatcher
from selfai.ui.terminal_ui import TerminalUI
from selfai.ui.ui_adapter import create_ui
from selfai.core.minimax_interface import MiniMaxInterface


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_plan_execution.py <plan_file.json>")
        print("\nAvailable test plans:")
        print("  - memory/plans/test_simple.json      (3 parallel tasks)")
        print("  - memory/plans/test_sequential.json  (3 sequential tasks)")
        sys.exit(1)

    plan_file = Path(sys.argv[1])
    if not plan_file.exists():
        print(f"Error: Plan file not found: {plan_file}")
        sys.exit(1)

    # Load plan
    print(f"📋 Loading plan: {plan_file}")
    with open(plan_file, 'r', encoding='utf-8') as f:
        plan_data = json.load(f)

    goal = plan_data.get("metadata", {}).get("goal", "Unknown goal")
    num_subtasks = len(plan_data.get("subtasks", []))
    print(f"🎯 Goal: {goal}")
    print(f"📊 Subtasks: {num_subtasks}")
    print()

    # Initialize system
    print("⚙️  Initializing SelfAI...")
    config = load_configuration()

    # Setup UI
    ui = create_ui(config)
    ui.show_banner()

    # Setup agents
    agent_manager = AgentManager(project_root=Path.cwd() / "agents")
    agent_manager.load_agents()

    if config.agent_config and config.agent_config.default_agent:
        agent_manager.set_active_agent(config.agent_config.default_agent)

    # Setup memory
    memory_system = MemorySystem(memory_dir=Path("memory"))

    # Setup LLM backend
    ui.status("Initializing MiniMax backend...", "info")
    llm_interface = MiniMaxInterface(config=config)
    llm_backends = [
        {
            "interface": llm_interface,
            "label": "MiniMax",
            "name": "minimax"
        }
    ]

    # Create executor
    ui.status("Creating execution dispatcher...", "info")
    dispatcher = ExecutionDispatcher(
        plan_data=plan_data,
        llm_backends=llm_backends,
        agent_manager=agent_manager,
        memory_system=memory_system,
        ui=ui,
        project_root=Path.cwd(),
    )

    # Execute plan
    print()
    ui.status("🚀 Starting plan execution...", "info")
    print()

    try:
        dispatcher.execute()
        ui.status("✅ Plan execution completed!", "success")
    except Exception as e:
        ui.status(f"❌ Plan execution failed: {e}", "error")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

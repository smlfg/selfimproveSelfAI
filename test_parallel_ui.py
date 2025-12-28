#!/usr/bin/env python3
"""
Test Script für Parallel Stream UI

Simuliert parallele Subtask-Ausführung mit Thinking/Response Chunks.

Usage:
    # Mit Parallel UI:
    SELFAI_PARALLEL_UI=true python test_parallel_ui.py

    # Ohne (Fallback zu TerminalUI):
    python test_parallel_ui.py
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from selfai.ui.ui_adapter import create_ui


def simulate_subtask_streaming(ui, subtask_id: str, delay: float = 0.1):
    """Simuliert Streaming Output für einen Subtask."""

    # Thinking phase
    thinking_chunks = [
        "Ich analysiere die Anfrage...\n",
        "Die Hauptaspekte sind:\n",
        "1. Identität klären\n",
        "2. Fähigkeiten erklären\n",
        "3. Einsatzgebiete nennen\n"
    ]

    for chunk in thinking_chunks:
        if hasattr(ui, 'add_thinking_chunk'):
            ui.add_thinking_chunk(subtask_id, chunk)
        else:
            ui.status(f"💭 [{subtask_id}] {chunk.strip()}", "info")
        time.sleep(delay)

    # Response phase
    response_chunks = [
        "Ich bin SelfAI, ",
        "ein Multi-Agent System ",
        "mit DPPM-Pipeline.\n\n",
        "Meine Kernfähigkeiten:\n",
        "• Planning (DPPM)\n",
        "• Multi-Backend Execution\n",
        "• Self-Improvement\n",
        "• Tool Integration\n"
    ]

    for chunk in response_chunks:
        if hasattr(ui, 'add_response_chunk'):
            ui.add_response_chunk(subtask_id, chunk)
        else:
            ui.streaming_chunk(chunk)
        time.sleep(delay)

    # Mark complete
    if hasattr(ui, 'mark_subtask_complete'):
        ui.mark_subtask_complete(subtask_id, success=True)


def main():
    """Test Parallel UI."""
    print("=" * 60)
    print("SelfAI Parallel Stream UI - Test")
    print("=" * 60)
    print()

    # Create UI
    ui = create_ui()

    # Show UI info
    from selfai.ui.ui_adapter import get_ui_info
    info = get_ui_info()
    print(f"UI Info:")
    print(f"  Parallel Available: {info['parallel_available']}")
    print(f"  Parallel Enabled:   {info['parallel_enabled']}")
    print(f"  Active UI:          {info['active_ui']}")
    print()
    if sys.stdin.isatty():
        input("Press ENTER to start test...")
    else:
        print("Non-interactive mode, starting automatically...")
        time.sleep(1)
    print()

    # Simulate plan execution
    plan_goal = "Wer bist du?"

    subtasks_info = [
        {"id": "S1", "title": "Analyse Identität", "agent_key": "analyzer"},
        {"id": "S2", "title": "Erkläre Fähigkeiten", "agent_key": "explainer"},
        {"id": "S3", "title": "Nenne Einsatzgebiete", "agent_key": "demo"},
    ]

    # Start parallel view
    if hasattr(ui, 'start_parallel_view'):
        ui.start_parallel_view(plan_goal, subtasks_info)
        time.sleep(0.5)  # Let layout render

        # Start subtask threads
        threads = []
        for i, info in enumerate(subtasks_info):
            t = threading.Thread(
                target=simulate_subtask_streaming,
                args=(ui, info["id"], 0.15)
            )
            t.start()
            threads.append(t)
            time.sleep(0.3)  # Stagger start

        # Wait for completion
        for t in threads:
            t.join()

        # Hold display for viewing
        time.sleep(3)

        # Stop parallel view
        ui.stop_parallel_view()

    else:
        # Fallback: Sequential output
        ui.status(f"📋 Plan: {plan_goal}", "info")
        ui.status(f"   {len(subtasks_info)} Subtasks (sequential)", "info")

        for info in subtasks_info:
            ui.status(f"\n▶ {info['title']}", "info")
            simulate_subtask_streaming(ui, info["id"], delay=0.05)

    print("\n" + "=" * 60)
    print("Test abgeschlossen!")
    print("=" * 60)


if __name__ == "__main__":
    main()

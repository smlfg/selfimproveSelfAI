#!/usr/bin/env python3
"""
Helper functions for Claude Code to use SelfAI with MiniMax efficiently.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def run_selfai_task(
    prompt: str,
    working_dir: str = "/home/smlflg/AutoCoder/Selfai/SelfAi-NPU-AGENT",
    timeout: int = 120
) -> Dict[str, Any]:
    """
    Run a single SelfAI task with MiniMax.

    Args:
        prompt: The coding task prompt
        working_dir: SelfAI project directory
        timeout: Timeout in seconds

    Returns:
        Dictionary with success status and output
    """
    selfai_path = Path(working_dir) / "selfai" / "selfai.py"

    # Add quit command to exit after task
    full_prompt = f"{prompt}\nquit\n"

    try:
        result = subprocess.run(
            [sys.executable, str(selfai_path)],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def run_selfai_plan(
    goal: str,
    working_dir: str = "/home/smlflg/AutoCoder/Selfai/SelfAi-NPU-AGENT",
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Run SelfAI with planning mode for complex tasks.

    Args:
        goal: High-level goal to accomplish
        working_dir: SelfAI project directory
        timeout: Timeout in seconds

    Returns:
        Dictionary with success status and output
    """
    prompt = f"/plan {goal}\ny\nquit\n"  # y to confirm plan execution
    return run_selfai_task(prompt, working_dir, timeout)

def generate_code_with_minimax(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2048
) -> str:
    """
    Direct MiniMax API call for code generation (no SelfAI overhead).

    Args:
        system_prompt: System instructions
        user_prompt: User request
        max_tokens: Max response tokens

    Returns:
        Generated text
    """
    import os
    sys.path.insert(0, "/home/smlflg/AutoCoder/Selfai/SelfAi-NPU-AGENT")

    from config_loader import load_configuration
    from selfai.core.minimax_interface import MinimaxInterface

    config = load_configuration()

    interface = MinimaxInterface(
        api_key=config.minimax_config.api_key,
        api_base=config.minimax_config.api_base,
        model=config.minimax_config.model
    )

    response = interface.generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens
    )

    return response

# Example usage
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("="*60)
    print("Testing SelfAI Helper for Claude Code")
    print("="*60)

    # Test 1: Simple task
    print("\n[Test 1] Simple code generation...")
    result = run_selfai_task(
        "ERSTELLE test_helper.py mit einer Funktion hello_world() die 'Hello!' printet"
    )
    print(f"Success: {result['success']}")

    # Test 2: Direct MiniMax call
    print("\n[Test 2] Direct MiniMax API...")
    try:
        response = generate_code_with_minimax(
            system_prompt="Du bist ein Python Expert.",
            user_prompt="Schreibe eine fibonacci Funktion in einer Zeile.",
            max_tokens=200
        )
        print(f"Response: {response[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "="*60)
    print("Tests complete!")

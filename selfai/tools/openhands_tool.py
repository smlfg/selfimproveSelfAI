"""
OpenHands Tool for SelfAI

Wrapper for OpenHands (formerly OpenDevin) - an autonomous coding agent.
Better than Aider for complex, multi-file tasks.

Usage:
    run_openhands_task(
        task_description="Implement user authentication system",
        files=["src/auth.py", "tests/test_auth.py"],
        model="anthropic/claude-3-5-sonnet-20241022"
    )
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, List


def run_openhands_task(
    task_description: str,
    files: Optional[str] = None,
    model: str = "openai/MiniMax-M2",
    timeout: int = 300,
    max_iterations: int = 10,
    working_dir: Optional[str] = None
) -> str:
    """
    Execute a coding task using OpenHands autonomous agent.

    OpenHands is better than Aider for:
    - Complex multi-file refactoring
    - System-level changes
    - Tasks requiring file exploration
    - Autonomous debugging

    Args:
        task_description: Detailed description of the coding task
        files: Optional comma-separated list of files to focus on
        model: LLM model to use (default: MiniMax-M2)
        timeout: Maximum execution time in seconds (default: 300)
        max_iterations: Max agent iterations (default: 10)
        working_dir: Working directory (default: current dir)

    Returns:
        JSON string with:
        - status: "success" or "failed"
        - output: Agent output/result
        - changes: List of modified files
        - iterations: Number of iterations used
        - error: Error message if failed

    Example:
        >>> result = run_openhands_task(
        ...     task_description="Add logging to all API endpoints",
        ...     files="src/api/endpoints.py,src/api/middleware.py",
        ...     model="anthropic/claude-3-5-sonnet-20241022"
        ... )
        >>> print(result)
        {"status": "success", "changes": ["src/api/endpoints.py"], ...}
    """
    try:
        # Set working directory
        if working_dir is None:
            working_dir = os.getcwd()
        working_dir = Path(working_dir).resolve()

        # Parse files list
        file_list = []
        if files and isinstance(files, str):
            file_list = [f.strip() for f in files.split(',') if f.strip()]

        # Build task instruction
        task_instruction = task_description.strip()

        if file_list:
            task_instruction += f"\n\nFocus on these files:\n" + "\n".join(f"- {f}" for f in file_list)

        # Create temp config file for OpenHands
        config = {
            "agent": {
                "type": "CodeActAgent",  # Best agent for coding
                "model": model,
                "max_iterations": max_iterations
            },
            "task": task_instruction,
            "workspace": str(working_dir),
            "sandbox": {
                "type": "local",
                "workspace_dir": str(working_dir)
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
            json.dump(config, f, indent=2)

        # Build OpenHands command
        # Note: Adjust path to your OpenHands installation
        openhands_path = Path.home() / "AutoCoder" / "OpenHands"

        if not openhands_path.exists():
            return json.dumps({
                "status": "failed",
                "error": f"OpenHands not found at {openhands_path}. Please install or update path.",
                "output": ""
            })

        # Prepare environment
        env = os.environ.copy()

        # Set API keys based on model
        if "anthropic" in model.lower():
            if "ANTHROPIC_API_KEY" not in env:
                return json.dumps({
                    "status": "failed",
                    "error": "ANTHROPIC_API_KEY not set for Anthropic models",
                    "output": ""
                })
        elif "openai" in model.lower() or "minimax" in model.lower():
            # MiniMax uses OpenAI-compatible API
            api_key_file = Path.home() / "AutoCoder" / "minimax"
            if api_key_file.exists():
                env["OPENAI_API_KEY"] = api_key_file.read_text().strip()
                env["OPENAI_API_BASE"] = "https://api.minimax.io/v1"
            elif "OPENAI_API_KEY" not in env:
                return json.dumps({
                    "status": "failed",
                    "error": "OPENAI_API_KEY not set and minimax file not found",
                    "output": ""
                })

        # Run OpenHands CLI
        cmd = [
            "python3",
            "-m", "openhands.core.main",
            "--config", config_file,
            "--task", task_instruction,
            "--max-iterations", str(max_iterations)
        ]

        result = subprocess.run(
            cmd,
            cwd=str(openhands_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Cleanup temp config
        try:
            os.unlink(config_file)
        except OSError:
            pass

        # Parse output
        output = result.stdout.strip()
        error_output = result.stderr.strip()

        if result.returncode == 0:
            # Try to extract changed files from output
            changed_files = []
            for line in output.split('\n'):
                if 'modified:' in line.lower() or 'created:' in line.lower():
                    # Extract filename from line
                    parts = line.split()
                    if len(parts) > 1:
                        changed_files.append(parts[-1])

            return json.dumps({
                "status": "success",
                "output": output[:1000],  # Truncate for readability
                "changes": changed_files,
                "iterations": max_iterations,  # Actual count would need parsing
                "model": model,
                "error": ""
            })
        else:
            return json.dumps({
                "status": "failed",
                "error": error_output[:500] if error_output else "Unknown error",
                "output": output[:500] if output else "",
                "changes": []
            })

    except subprocess.TimeoutExpired:
        return json.dumps({
            "status": "failed",
            "error": f"Task timed out after {timeout} seconds",
            "output": "Consider increasing timeout or breaking task into smaller parts"
        })
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e),
            "output": ""
        })


def run_openhands_architect(
    design_question: str,
    context_files: Optional[str] = None,
    model: str = "anthropic/claude-3-5-sonnet-20241022",
    timeout: int = 180
) -> str:
    """
    Consult OpenHands in architect mode for design advice (read-only).

    Better than Aider architect mode because:
    - Can explore entire codebase
    - Provides more comprehensive analysis
    - Better at system-level architecture

    Args:
        design_question: Architectural question or design problem
        context_files: Optional comma-separated files for context
        model: LLM model (default: Claude Sonnet - best for architecture)
        timeout: Timeout in seconds (default: 180)

    Returns:
        JSON string with architectural advice

    Example:
        >>> result = run_openhands_architect(
        ...     design_question="How should I structure the authentication system?",
        ...     context_files="src/auth.py,src/models.py"
        ... )
    """
    # For architect mode, we just need analysis, not code changes
    task = f"[ARCHITECT MODE - READ ONLY]\n\n{design_question}\n\nProvide architectural recommendations without modifying code."

    if context_files:
        task += f"\n\nConsider these files:\n{context_files}"

    return run_openhands_task(
        task_description=task,
        files=context_files,
        model=model,
        timeout=timeout,
        max_iterations=3  # Fewer iterations for analysis
    )


def compare_coding_tools(
    task_description: str,
    complexity: str = "medium"
) -> str:
    """
    Suggest which coding tool to use for a task.

    Args:
        task_description: Description of the coding task
        complexity: Task complexity (simple/medium/complex)

    Returns:
        JSON string with recommendation:
        - tool: "aider" or "openhands"
        - reason: Why this tool is better
        - confidence: 0-1 score

    Decision Matrix:
        - Simple tasks (1 file, <50 lines): Aider (faster)
        - Medium tasks (2-3 files, refactoring): Either works
        - Complex tasks (multi-file, system-level): OpenHands (more autonomous)
    """
    complexity_lower = complexity.lower()
    task_lower = task_description.lower()

    # Keywords that suggest OpenHands
    complex_keywords = [
        "refactor", "system", "architecture", "multiple files",
        "explore", "analyze", "debug", "investigate", "restructure"
    ]

    # Keywords that suggest Aider
    simple_keywords = [
        "add function", "fix bug", "add comment", "rename",
        "quick fix", "one line", "simple change"
    ]

    # Count matches
    complex_score = sum(1 for kw in complex_keywords if kw in task_lower)
    simple_score = sum(1 for kw in simple_keywords if kw in task_lower)

    # Decision logic
    if complexity_lower == "complex" or complex_score > simple_score:
        return json.dumps({
            "tool": "openhands",
            "reason": "Task requires autonomous exploration or multi-file changes. OpenHands excels at complex, system-level work.",
            "confidence": 0.8 + (complex_score * 0.05),
            "alternative": "aider (for simpler parts)"
        })
    elif complexity_lower == "simple" or simple_score > complex_score:
        return json.dumps({
            "tool": "aider",
            "reason": "Task is straightforward and localized. Aider is faster for simple changes.",
            "confidence": 0.8 + (simple_score * 0.05),
            "alternative": "openhands (if task grows complex)"
        })
    else:
        # Medium/unclear - suggest both
        return json.dumps({
            "tool": "either",
            "reason": "Task complexity unclear. Both tools can handle this. Aider for speed, OpenHands for autonomy.",
            "confidence": 0.6,
            "recommendation": "Try Aider first (faster), fallback to OpenHands if it struggles"
        })

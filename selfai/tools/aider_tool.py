"""Aider AI Coding Assistant Tool for SelfAI"""

import os
import subprocess
import tempfile
from pathlib import Path


def run_aider_task(
    task_description: str,
    files: str = "",
    model: str = "openai/MiniMax-M2",
    timeout: int = 180,
) -> str:
    """
    Executes an Aider coding task with MiniMax backend.

    Args:
        task_description: The coding task to perform (e.g., "Add error handling to function X")
        files: Comma-separated list of file paths to edit (e.g., "src/main.py,tests/test_main.py")
        model: LLM model to use (default: openai/MiniMax-M2)
        timeout: Maximum execution time in seconds (default: 180)

    Returns:
        Aider's output including changes made, git commits, and any errors

    Example:
        run_aider_task(
            task_description="Add type hints to all functions",
            files="src/utils.py",
            model="openai/MiniMax-M2"
        )
    """
    # Validate inputs
    if not task_description.strip():
        return "Error: task_description cannot be empty"

    # Parse file list
    file_list = []
    if files.strip():
        file_list = [f.strip() for f in files.split(",") if f.strip()]

    # Setup environment variables for MiniMax
    env = os.environ.copy()

    # Load API key from minimax file (wie wir es immer machen)
    minimax_key_file = Path("/home/smlflg/AutoCoder/minimax")
    if minimax_key_file.exists():
        try:
            api_key = minimax_key_file.read_text().strip()
            env["OPENAI_API_KEY"] = api_key
        except Exception as e:
            return f"Error reading API key from {minimax_key_file}: {e}"
    else:
        return f"Error: API key file not found at {minimax_key_file}"

    env["OPENAI_API_BASE"] = "https://api.minimax.io/v1"

    # Create temporary file for task description
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(task_description)
        task_file = tmp_file.name

    try:
        # Build aider command
        cmd = [
            "timeout", str(timeout),
            "aider",
            "--yes-always",  # Auto-confirm
            "--no-stream",  # No streaming (easier to parse)
            "--no-show-model-warnings",
            f"--model={model}",
            f"--message-file={task_file}",
        ]

        # Add files if specified
        if file_list:
            cmd.extend(file_list)

        # Execute aider
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        # Format output
        output = []
        output.append(f"=== Aider Task: {task_description[:100]}... ===\n")

        if result.returncode == 124:  # Timeout exit code
            output.append(f"⚠️  Task timed out after {timeout} seconds\n")

        if result.stdout:
            output.append("STDOUT:\n")
            output.append(result.stdout)

        if result.stderr:
            output.append("\nSTDERR:\n")
            output.append(result.stderr)

        if result.returncode == 0:
            output.append("\n✅ Aider task completed successfully!")
        elif result.returncode != 124:
            output.append(f"\n❌ Aider exited with code {result.returncode}")

        return "\n".join(output)

    except FileNotFoundError:
        return (
            "Error: 'aider' command not found. Install it with: pip install aider-chat\n"
            "Or: uv tool install aider-chat"
        )
    except Exception as e:
        return f"Unexpected error running aider: {type(e).__name__}: {e}"
    finally:
        # Cleanup temp file
        try:
            os.unlink(task_file)
        except:
            pass


def run_aider_architect(
    design_question: str,
    context_files: str = "",
    timeout: int = 120,
) -> str:
    """
    Uses Aider in architect mode to design code architecture.

    Args:
        design_question: Architectural question (e.g., "How should I structure a REST API?")
        context_files: Comma-separated list of files for context (optional)
        timeout: Maximum execution time in seconds (default: 120)

    Returns:
        Aider's architectural advice and design recommendations
    """
    if not design_question.strip():
        return "Error: design_question cannot be empty"

    # Parse file list
    file_list = []
    if context_files.strip():
        file_list = [f.strip() for f in context_files.split(",") if f.strip()]

    # Setup environment
    env = os.environ.copy()
    minimax_key_file = Path("/home/smlflg/AutoCoder/minimax")
    if minimax_key_file.exists():
        try:
            api_key = minimax_key_file.read_text().strip()
            env["OPENAI_API_KEY"] = api_key
        except Exception as e:
            return f"Error reading API key: {e}"
    else:
        return "Error: API key file not found"

    env["OPENAI_API_BASE"] = "https://api.minimax.io/v1"

    # Create temp file for question
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(design_question)
        question_file = tmp_file.name

    try:
        # Build command with --architect flag
        cmd = [
            "timeout", str(timeout),
            "aider",
            "--architect",  # Read-only mode, no edits
            "--model=openai/MiniMax-M2",
            "--no-stream",
            f"--message-file={question_file}",
        ]

        if file_list:
            cmd.extend(file_list)

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        output = []
        output.append(f"=== Architectural Design: {design_question[:80]}... ===\n")

        if result.stdout:
            output.append(result.stdout)

        if result.returncode == 0:
            output.append("\n✅ Design consultation completed")
        else:
            output.append(f"\n⚠️  Exited with code {result.returncode}")

        return "\n".join(output)

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
    finally:
        try:
            os.unlink(question_file)
        except:
            pass

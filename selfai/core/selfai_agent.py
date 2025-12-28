"""
SelfAI Enhanced Agent - Tool-Calling Agent mit UI Feedback
===========================================================

Erweitert smolagents ToolCallingAgent um:
- UI-Feedback für Tool-Aufrufe (Auge-Emoji für Introspection!)
- Integration mit SelfAI tool_registry
- Logging und Error-Handling

Author: SelfAI Team
Date: 2025-01-21
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Dict

try:
    from smolagents import ToolCallingAgent
    from smolagents.models import Model
except ImportError as exc:
    raise ImportError(
        "smolagents ist nicht installiert. Installiere mit: pip install smolagents"
    ) from exc


logger = logging.getLogger(__name__)


class SelfAIAgent(ToolCallingAgent):
    """
    Enhanced ToolCallingAgent mit SelfAI-spezifischen Features.

    Features:
    - UI Feedback: Zeigt Tool-Aufrufe mit Emojis an
    - Tool Registry Integration: Nutzt registered tools
    - Verbose Logging: Optional detailliertes Logging
    - Error Handling: Graceful degradation bei Tool-Fehlern
    """

    def __init__(
        self,
        model: Model,
        tools: List[Any],
        ui: Optional[Any] = None,
        max_steps: int = 10,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize SelfAI Agent.

        Args:
            model: smolagents Model instance (wraps LLM interface)
            tools: List of smolagents Tool instances
            ui: Optional TerminalUI instance for visual feedback
            max_steps: Maximum tool-calling iterations
            verbose: Enable verbose logging
            **kwargs: Additional arguments for ToolCallingAgent
        """
        super().__init__(
            model=model,
            tools=tools,
            max_steps=max_steps,
            **kwargs
        )
        self.ui = ui
        self.verbose = verbose
        self.tool_call_count = 0

        if self.verbose:
            logger.info(f"SelfAI Agent initialized with {len(tools)} tools, max_steps={max_steps}")

    def execute_tool_call(self, tool_call: Any) -> Any:
        """
        Execute a tool call with UI feedback.

        Overrides ToolCallingAgent.execute_tool_call to add:
        - UI visualization (show_tool_call)
        - Verbose logging
        - Error handling

        Args:
            tool_call: smolagents tool call object

        Returns:
            Tool execution result
        """
        self.tool_call_count += 1

        # Extract tool info
        tool_name = getattr(tool_call, 'name', str(tool_call))
        tool_args = getattr(tool_call, 'arguments', {})

        # UI Feedback (vor Ausführung!)
        if self.ui:
            try:
                self.ui.show_tool_call(tool_name, tool_args)
            except Exception as e:
                logger.warning(f"UI feedback failed: {e}")

        # Verbose logging
        if self.verbose:
            logger.info(f"[Agent Step {self.tool_call_count}] Executing: {tool_name}")
            if tool_args:
                logger.debug(f"  Arguments: {tool_args}")

        # Execute tool via smolagents parent
        try:
            result = super().execute_tool_call(tool_call)

            if self.verbose:
                result_preview = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                logger.debug(f"  Result: {result_preview}")

            return result

        except Exception as e:
            error_msg = f"Tool '{tool_name}' failed: {str(e)}"
            logger.error(error_msg)

            if self.ui:
                self.ui.status(f"⚠️  Tool-Fehler: {tool_name}", "warning")

            # Return error as string (Agent can handle it)
            return f"Error: {error_msg}"

    def run(self, task: str, **kwargs) -> str:
        """
        Run agent on a task.

        Args:
            task: User input/task description
            **kwargs: Additional arguments for ToolCallingAgent.run

        Returns:
            Final agent response
        """
        # Reset counter
        self.tool_call_count = 0

        if self.verbose:
            logger.info(f"[Agent] Starting task: {task[:100]}...")

        try:
            result = super().run(task, **kwargs)

            if self.verbose:
                logger.info(f"[Agent] Completed in {self.tool_call_count} tool calls")

            return result

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            logger.error(error_msg)

            if self.ui:
                self.ui.status(error_msg, "error")

            # Return graceful error message
            return f"Entschuldigung, es gab einen Fehler: {str(e)}"


def create_selfai_agent(
    llm_interface: Any,
    tools: List[Any],
    ui: Optional[Any] = None,
    max_steps: int = 10,
    verbose: bool = False,
    model_id: Optional[str] = None,
) -> SelfAIAgent:
    """
    Factory function to create SelfAI Agent.

    Args:
        llm_interface: SelfAI LLM interface (MiniMaxInterface, etc.)
        tools: List of smolagents Tool instances
        ui: Optional TerminalUI instance
        max_steps: Max tool-calling iterations
        verbose: Enable verbose logging
        model_id: Optional model identifier

    Returns:
        Configured SelfAIAgent instance
    """
    from selfai.core.smolagents_runner import _SelfAIModel

    # Wrap LLM interface as smolagents Model
    model = _SelfAIModel(llm_interface, model_id=model_id)

    # Create agent
    agent = SelfAIAgent(
        model=model,
        tools=tools,
        ui=ui,
        max_steps=max_steps,
        verbose=verbose,
    )

    return agent

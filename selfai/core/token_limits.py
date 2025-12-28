"""
Centralized token limit management for SelfAI.
Allows runtime control via /commands for full transparency and control.
"""

from dataclasses import dataclass


@dataclass
class TokenLimits:
    """Token limits for different SelfAI operations."""

    # Planning phase
    planner_max_tokens: int = 2048

    # Execution phase (subtasks)
    execution_max_tokens: int = 2048

    # Merge phase
    merge_max_tokens: int = 8192

    # Tool creation
    tool_creation_max_tokens: int = 2048

    # Error correction
    error_correction_max_tokens: int = 2048

    # Self-improvement
    selfimprove_max_tokens: int = 4096

    # Normal chat (without plan)
    chat_max_tokens: int = 2048

    def set_all(self, value: int) -> None:
        """Set all token limits to the same value."""
        self.planner_max_tokens = value
        self.execution_max_tokens = value
        self.merge_max_tokens = value
        self.tool_creation_max_tokens = value
        self.error_correction_max_tokens = value
        self.selfimprove_max_tokens = value
        self.chat_max_tokens = value

    def set_extreme(self) -> None:
        """Set all limits to 64000 for extreme mode."""
        self.set_all(64000)

    def set_conservative(self) -> None:
        """Set all limits to conservative values (fast, cheap)."""
        self.planner_max_tokens = 512
        self.execution_max_tokens = 256
        self.merge_max_tokens = 1024
        self.tool_creation_max_tokens = 768
        self.error_correction_max_tokens = 768
        self.selfimprove_max_tokens = 1024
        self.chat_max_tokens = 512

    def set_balanced(self) -> None:
        """Set all limits to balanced values (default)."""
        self.planner_max_tokens = 2048
        self.execution_max_tokens = 2048 # Increased for better subtask outputs
        self.merge_max_tokens = 8192     # Increased significantly for synthesis
        self.tool_creation_max_tokens = 2048
        self.error_correction_max_tokens = 2048
        self.selfimprove_max_tokens = 4096
        self.chat_max_tokens = 2048

    def set_generous(self) -> None:
        """Set all limits to generous values (high quality)."""
        self.planner_max_tokens = 2048
        self.execution_max_tokens = 1024
        self.merge_max_tokens = 4096
        self.tool_creation_max_tokens = 2048
        self.error_correction_max_tokens = 2048
        self.selfimprove_max_tokens = 4096
        self.chat_max_tokens = 2048

    def as_dict(self) -> dict[str, int]:
        """Return all limits as dictionary."""
        return {
            "planner": self.planner_max_tokens,
            "execution": self.execution_max_tokens,
            "merge": self.merge_max_tokens,
            "tool_creation": self.tool_creation_max_tokens,
            "error_correction": self.error_correction_max_tokens,
            "selfimprove": self.selfimprove_max_tokens,
            "chat": self.chat_max_tokens,
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        lines = [
            "📊 Current Token Limits:",
            f"  • Planner:         {self.planner_max_tokens:>6}",
            f"  • Execution:       {self.execution_max_tokens:>6}",
            f"  • Merge:           {self.merge_max_tokens:>6}",
            f"  • Tool Creation:   {self.tool_creation_max_tokens:>6}",
            f"  • Error Correction:{self.error_correction_max_tokens:>6}",
            f"  • Self-Improve:    {self.selfimprove_max_tokens:>6}",
            f"  • Chat:            {self.chat_max_tokens:>6}",
        ]
        return "\n".join(lines)

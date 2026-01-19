"""
Dummy Tool for Testing SelfAI Tool-Calling
===========================================

Simple test tool that returns "Hello World" to verify the tool-calling system works.

Author: SelfAI Testing
Date: 2025-01-19
"""

from smolagents import Tool


class HelloWorldTool(Tool):
    """
    Simple dummy tool that returns 'Hello World'.

    This tool is useful for:
    - Testing if tool-calling works
    - Verifying agent can execute tools
    - Debugging tool-calling pipeline
    """

    name = "say_hello"
    description = "Returns a friendly 'Hello World' message. Use this to test if tool calling works."

    inputs = {
        "name": {
            "type": "string",
            "description": "Optional name to greet. If provided, says 'Hello {name}!', otherwise 'Hello World!'",
            "nullable": True,  # Required by smolagents for optional parameters
        }
    }

    output_type = "string"

    def forward(self, name: str = None) -> str:
        """
        Execute the tool and return greeting.

        Args:
            name: Optional name to personalize greeting

        Returns:
            Greeting message
        """
        if name and name.strip():
            return f"🎉 Hello {name.strip()}! Tool-Calling funktioniert perfekt! 🚀"
        else:
            return "🎉 Hello World! Tool-Calling funktioniert perfekt! 🚀"


class EchoTool(Tool):
    """
    Another simple test tool that echoes back any message.
    """

    name = "echo_message"
    description = "Echoes back any message you send it. Use this to test tool parameter passing."

    inputs = {
        "message": {
            "type": "string",
            "description": "The message to echo back",
        }
    }

    output_type = "string"

    def forward(self, message: str) -> str:
        """
        Echo the message back.

        Args:
            message: Message to echo

        Returns:
            Echoed message with decoration
        """
        return f"📢 Echo: {message}"


class CounterTool(Tool):
    """
    Test tool that counts from 1 to N.
    """

    name = "count_numbers"
    description = "Counts from 1 to a given number. Use this to test numeric parameter handling."

    inputs = {
        "count_to": {
            "type": "integer",
            "description": "The number to count up to (e.g., 5 will output '1, 2, 3, 4, 5')",
        }
    }

    output_type = "string"

    def forward(self, count_to: int) -> str:
        """
        Count from 1 to count_to.

        Args:
            count_to: Number to count to

        Returns:
            Comma-separated list of numbers
        """
        if not isinstance(count_to, int) or count_to < 1:
            return "❌ Error: count_to must be a positive integer!"

        if count_to > 100:
            return "❌ Error: count_to must be 100 or less!"

        numbers = ", ".join(str(i) for i in range(1, count_to + 1))
        return f"🔢 Counting: {numbers}"

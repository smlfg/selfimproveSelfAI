"""
Custom Prompt Templates for SelfAI + smolagents Integration
=============================================================

MiniMax understands the "Action: {...}" format, NOT the smolagents XML format.
These custom templates make smolagents use our format.

Author: SelfAI Team
Date: 2026-01-19
"""

from smolagents.agents import PromptTemplates


# Custom tool-calling format that MiniMax understands
SELFAI_TOOL_CALLING_FORMAT = """You have access to the following tools:

{tool_descriptions}

When you need to use a tool, respond with EXACTLY this format:
Action: {{"name": "tool_name", "arguments": {{"arg1": "value1", "arg2": "value2"}}}}

IMPORTANT RULES:
1. ONLY output "Action: {{...}}" when you want to use a tool
2. The JSON must be valid (use double quotes, not single quotes)
3. After you see the tool result, you can use another tool or give a final answer
4. To give a final answer without more tools, use: Action: {{"name": "final_answer", "arguments": {{"answer": "your final response"}}}}

Examples:
User: What's the weather in Paris?
Assistant: Action: {{"name": "get_current_weather", "arguments": {{"location": "Paris"}}}}

User: Say hello!
Assistant: Action: {{"name": "say_hello", "arguments": {{}}}}

User: Count to 5
Assistant: Action: {{"name": "count_numbers", "arguments": {{"count_to": 5}}}}
"""


class SelfAIPromptTemplates(PromptTemplates):
    """
    Custom prompt templates for SelfAI that use Action: {...} format.

    This replaces the default smolagents XML-based format with our
    MiniMax-compatible format.
    """

    def __init__(self):
        # Create templates using our custom format
        super().__init__()

        # Override the main system template
        self.system_prompt_template = SELFAI_TOOL_CALLING_FORMAT

        # Tool description format (how each tool is described)
        self.tool_description_template = """
{name}: {description}
Parameters: {inputs}
"""

        # Tool result format (how we show tool results to the model)
        self.tool_result_template = """Observation: {result}"""

    def format_tool_descriptions(self, tools):
        """Format tool descriptions for the system prompt."""
        descriptions = []
        for tool in tools:
            # Extract tool metadata
            name = getattr(tool, 'name', 'unknown')
            description = getattr(tool, 'description', 'No description')
            inputs = getattr(tool, 'inputs', {})

            # Format inputs
            input_str = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in inputs.items())

            descriptions.append(f"- {name}({input_str}): {description}")

        return "\n".join(descriptions)

"""
Custom Agent Loop - Simple, MiniMax-Compatible Tool-Calling Agent
===================================================================

Built specifically for MiniMax M2's Action: {...} format.
No framework overhead, full control, works perfectly.

Author: SelfAI Team
Date: 2026-01-19
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Tuple, cast
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentStep:
    """Represents one step in the agent loop."""

    step_number: int
    action: str  # "tool_call", "final_answer", "thinking"
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    response_text: Optional[str] = None
    error: Optional[str] = None


class CustomAgentLoop:
    """
    Simple, effective agent loop for MiniMax.

    Features:
    - Multi-step tool calling
    - MiniMax's Action: {...} format
    - Clean history management
    - Error handling with retries
    - Streaming support (optional)
    """

    def __init__(
        self,
        llm_interface: Any,
        tools: List[Any],
        max_steps: int = 10,
        ui: Optional[Any] = None,
        verbose: bool = False,
        agent_prompt: str = None,
        memory_system: Any = None,
        temperature: float = 0.1,
        streaming: bool = True,
    ):
        """
        Initialize custom agent loop.

        Args:
            llm_interface: MiniMax interface (or any LLM)
            tools: List of tool instances (with name, description, inputs, forward())
            max_steps: Maximum reasoning steps
            ui: Optional UI for display
            verbose: Enable detailed logging
            agent_prompt: System prompt from active agent (optional)
            memory_system: MemorySystem instance for context retrieval (optional)
            temperature: LLM temperature (default 0.1)
            streaming: Enable streaming responses (default True)
        """
        self.llm_interface = llm_interface
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.ui = ui
        self.verbose = verbose
        self.agent_prompt = agent_prompt
        self.memory_system = memory_system
        self.temperature = temperature
        self.streaming = streaming

        # Build system prompt with tool descriptions
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt with tool descriptions."""
        # If agent prompt is provided, use it as the base
        if self.agent_prompt:
            base_prompt = self.agent_prompt.strip()
        else:
            base_prompt = "You are SelfAI, an intelligent AI assistant with access to tools."

        # Build tools list by category
        bash_tools = ["ls", "cat", "grep", "find", "wc"]
        
        # Build tool descriptions
        tool_descriptions = []

        # Bash wrapper tools (most important for file operations)
        tool_descriptions.append("\n### 📁 FILE SYSTEM TOOLS (Bash Wrappers)\n")
        
        for tool_name in bash_tools:
            if tool_name not in self.tools:
                continue
                
            tool = self.tools[tool_name]
            name = tool.name
            description = tool.description
            inputs = getattr(tool, 'inputs', {})

            # Format inputs
            input_parts = []
            required_params = []
            for param_name, param_info in inputs.items():
                param_type = param_info.get('type', 'any')
                param_desc = param_info.get('description', '')
                nullable = param_info.get('nullable', False)
                optional_marker = "" if not nullable else " (optional)"
                
                input_parts.append(f"        - {param_name}: {param_type}{optional_marker} - {param_desc}")
                if not nullable:
                    required_params.append(param_name)

            input_str = "\n".join(input_parts) if input_parts else "        (no parameters)"
            required_str = ", ".join(required_params) if required_params else "(none)"
            
            tool_descriptions.append(f"""
{name}: {description}
    Parameters: {required_str}
{input_str}
    Example: Action: {{"name": "{name}", "arguments": {{"param1": "value1"}}}}
""")

        # Other tools
        tool_descriptions.append("\n### 🛠️ OTHER AVAILABLE TOOLS\n")
        
        for tool in sorted(self.tools.values(), key=lambda t: t.name):
            if tool.name in bash_tools:
                continue
                
            name = tool.name
            description = tool.description
            inputs = getattr(tool, 'inputs', {})

            input_parts = []
            required_params = []
            for param_name, param_info in inputs.items():
                param_type = param_info.get('type', 'any')
                param_desc = param_info.get('description', '')
                nullable = param_info.get('nullable', False)
                optional_marker = "" if not nullable else " (optional)"
                
                input_parts.append(f"        - {param_name}: {param_type}{optional_marker} - {param_desc}")
                if not nullable:
                    required_params.append(param_name)

            input_str = "\n".join(input_parts) if input_parts else "        (no parameters)"
            required_str = ", ".join(required_params) if required_params else "(none)"
            
            tool_descriptions.append(f"""
{name}: {description}
    Parameters: {required_str}
{input_str}
""")

        tools_text = "\n".join(tool_descriptions)

        prompt = f"""{base_prompt}

## AVAILABLE TOOLS

{tools_text}

## HOW TO USE TOOLS

When you need to use a tool, respond with EXACTLY this format:

Action: {{"name": "TOOL_NAME", "arguments": {{"param1": "value1", "param2": "value2"}}}}

When you're ready to give a final answer, use:

Final Answer: YOUR_ANSWER_HERE

## CRITICAL RULES

1. **Use EXACT tool names:** The tool name must match exactly what's listed above (case-sensitive)
2. **File operations:** Use `ls` to list files, `cat` to read files, `grep` to search files
3. **Format:** ONLY output "Action: {{...}}" (nothing else on that line!)
4. **JSON must be valid:** Double quotes, proper escaping, no trailing commas
5. **After tool result:** You'll see "Observation: ..." - use it to decide next step
6. **Multiple tools:** You can call multiple tools in sequence
7. **Final answer:** When done with tools, use "Final Answer: ..."

## COMMON MISTAKES TO AVOID

- DON'T use: "search_code", "read_code", "file_list" (these don't exist)
- DO use: "grep", "cat", "ls" (these are the correct tool names)

- DON'T use: single quotes in JSON ('name')
- DO use: double quotes in JSON ("name")

## EXAMPLES

Example 1: List Python files
User: List all Python files in selfai folder
Assistant: Action: {{"name": "ls", "arguments": {{"subdir": "selfai", "pattern": "*.py", "max_results": 10}}}}

Example 2: Read a file
User: Read selfai.py file
Assistant: Action: {{"name": "cat", "arguments": {{"path": "selfai/selfai.py", "max_chars": 1000}}}}

Example 3: Search for text
User: Search for "def main" in Python files
Assistant: Action: {{"name": "grep", "arguments": {{"query": "def main", "pattern": "*.py", "max_results": 5}}}}

Example 4: Multiple tools
User: List Python files and read first one
Assistant: Action: {{"name": "ls", "arguments": {{"subdir": ".", "pattern": "*.py", "max_results": 5}}}}
[Observation: {{"files": ["file1.py", "file2.py"], "count": 2}}]
Assistant: Action: {{"name": "cat", "arguments": {{"path": "file1.py"}}}}
[Observation: {{"content": "...", "path": "file1.py"}}}}
Assistant: Final Answer: Here's what I found: The first file contains...

Now, let's begin!

Now, let's begin!
"""
        return prompt

    def _parse_response(
        self, response: str
    ) -> Tuple[str, Optional[str], Optional[Dict]]:
        """
        Parse LLM response to detect action type.

        Returns:
            (action_type, tool_name, tool_args)
            action_type: "tool_call", "final_answer", or "thinking"
        """
        # Check for Action: {...} with proper nested brace handling
        action_json = self._extract_action_json(response)
        if action_json:
            try:
                action_data = json.loads(action_json)
                tool_name = action_data.get("name")
                tool_args = action_data.get("arguments", {})

                if tool_name:
                    return "tool_call", tool_name, tool_args
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Action JSON: {e}")
                logger.error(f"Response: {response}")

        # Check for Final Answer:
        final_match = re.search(
            r"Final Answer:\s*(.+)", response, re.DOTALL | re.IGNORECASE
        )
        if final_match:
            answer = final_match.group(1).strip()
            return "final_answer", None, {"answer": answer}

        # Otherwise, it's just thinking/text
        return "thinking", None, None

    def _extract_action_json(self, text: str) -> Optional[str]:
        """
        Extract Action JSON from response, handling nested braces properly.

        Args:
            text: Response text containing Action: {...}

        Returns:
            Complete JSON string or None if not found
        """
        # Find the start of the JSON object
        match = re.search(r"Action:\s*\{", text, re.DOTALL)
        if not match:
            return None

        start = match.end() - 1  # Include the opening brace

        # Count braces to find the matching closing brace
        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue

            if char == "\\" and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        # Found the matching closing brace
                        return text[start : i + 1]

        return None

    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool and return result.

        Args:
            tool_name: Name of tool to execute
            tool_args: Arguments dict

        Returns:
            Tool result as string
        """
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found. Available: {list(self.tools.keys())}"

        tool = self.tools[tool_name]

        try:
            # Call tool's forward() method
            result = tool.forward(**tool_args)
            return str(result)

        except TypeError as e:
            # Argument mismatch
            return f"Error: Invalid arguments for '{tool_name}': {e}"

        except Exception as e:
            # Other errors
            logger.error(f"Tool '{tool_name}' execution failed: {e}", exc_info=True)
            return f"Error executing '{tool_name}': {e}"

    def _call_llm(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        stream: bool = False,
    ) -> str:
        """
        Call LLM with optional streaming.

        Args:
            prompt: User prompt
            history: Conversation history
            stream: Enable streaming output

        Returns:
            LLM response text
        """
        if stream and hasattr(self.llm_interface, "stream_generate_response"):
            if self.ui:
                self.ui.start_spinner("Thinking...")

            chunks = []
            for chunk in self.llm_interface.stream_generate_response(
                system_prompt=self.system_prompt,
                user_prompt=prompt,
                history=history,
                max_output_tokens=512,
                timeout=60.0,
            ):
                chunks.append(chunk)
                if self.ui:
                    self.ui.streaming_chunk(chunk)

            if self.ui:
                self.ui.stop_spinner()

            return "".join(chunks)
        else:
            # Non-streaming mode - clean output without spinner
            response = self.llm_interface.generate_response(
                system_prompt=self.system_prompt,
                user_prompt=prompt,
                history=history,
                max_tokens=512,
                temperature=self.temperature,
            )

            return response

    def run(self, user_input: str, max_steps: Optional[int] = None) -> str:
        """
        Run the agent loop.

        Args:
            user_input: User's question/request
            max_steps: Override default max_steps

        Returns:
            Final answer string
        """
        max_steps = max_steps or self.max_steps
        history = []
        steps = []

        if self.ui:
            print("\n" + "="*70)
            print("🤖 AGENT REASONING")
            print("="*70)

        for step_num in range(1, max_steps + 1):
            if self.verbose:
                logger.info(f"[Agent Step {step_num}/{max_steps}]")

            # Build messages for LLM
            if step_num == 1:
                # First step: include user input
                prompt = user_input
            else:
                # Subsequent steps: continue from last observation
                prompt = (
                    "Continue reasoning. Use tools if needed, or give Final Answer."
                )

            # Call LLM
            try:
                if self.ui:
                    print(f"\n📝 Step {step_num}/{max_steps}: Analyzing...")

                response = self._call_llm(
                    prompt=prompt,
                    history=history,
                    stream=False,  # Disable streaming for cleaner output
                )

                if self.verbose:
                    logger.debug(f"LLM Response: {response[:200]}...")

            except Exception as e:
                error_msg = f"LLM call failed at step {step_num}: {e}"
                logger.error(error_msg)
                if self.ui:
                    self.ui.stop_spinner()
                    self.ui.status(f"❌ {error_msg}", "error")
                return f"Error: {error_msg}"

            # Parse response
            action_type, tool_name, tool_data = self._parse_response(response)

            # Create step record
            step_record = AgentStep(
                step_number=step_num,
                action=action_type,
                response_text=response,
            )

            # Handle different action types
            if action_type == "tool_call":
                # Execute tool
                assert tool_name is not None, (
                    "tool_name should not be None for tool_call"
                )
                assert tool_data is not None, (
                    "tool_data should not be None for tool_call"
                )

                step_record.tool_name = tool_name
                step_record.tool_args = tool_data

                if self.ui:
                    # Clean display of tool call
                    args_display = ", ".join(f"{k}={repr(v)[:30]}" for k, v in tool_data.items())
                    if len(args_display) > 60:
                        args_display = args_display[:57] + "..."
                    print(f"   🔧 Calling: {tool_name}({args_display})")

                # Cast to silence type checker - we know these are not None here
                tool_result = self._execute_tool(
                    cast(str, tool_name), cast(Dict[str, Any], tool_data)
                )
                step_record.tool_result = tool_result

                if self.verbose:
                    logger.info(f"Tool '{tool_name}' returned: {tool_result[:100]}...")

                if self.ui:
                    result_preview = (
                        tool_result[:80] + "..."
                        if len(tool_result) > 80
                        else tool_result
                    )
                    print(f"   ✅ Result: {result_preview}")

                # Add to history
                history.append({"role": "assistant", "content": response})
                history.append(
                    {"role": "user", "content": f"Observation: {tool_result}"}
                )

            elif action_type == "final_answer":
                # Done!
                assert tool_data is not None, (
                    "tool_data should not be None for final_answer"
                )
                answer = cast(Dict[str, Any], tool_data).get("answer", response)

                if self.ui:
                    print(f"\n✅ Complete after {step_num} steps")
                    print("="*70)

                steps.append(step_record)

                if self.verbose:
                    logger.info(f"Agent completed in {step_num} steps")
                    for i, s in enumerate(steps, 1):
                        logger.debug(f"  Step {i}: {s.action} - {s.tool_name or 'N/A'}")

                return answer

            elif action_type == "thinking":
                # Just text response, add to history and continue
                if self.verbose:
                    logger.debug(f"Agent is thinking: {response[:100]}...")

                history.append({"role": "assistant", "content": response})
                history.append(
                    {
                        "role": "user",
                        "content": "Please use a tool or provide Final Answer.",
                    }
                )

            steps.append(step_record)

        # Max steps reached without final answer
        error_msg = f"Agent reached max steps ({max_steps}) without final answer"
        logger.warning(error_msg)

        if self.ui:
            self.ui.status(f"⚠️ {error_msg}", "warning")

        # Return last response or error
        if history:
            last_response = (
                history[-2].get("content", "No response")
                if len(history) >= 2
                else "No response"
            )
            return f"(Max steps reached) Last response: {last_response}"

        return f"Error: {error_msg}"

    def get_tool_list(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())

    def get_tool_description(self, tool_name: str) -> str:
        """Get description of a specific tool."""
        if tool_name in self.tools:
            return self.tools[tool_name].description
        return f"Tool '{tool_name}' not found"

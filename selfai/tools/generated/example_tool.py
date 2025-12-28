"""
Example generated tool - created by /toolcreate command

This is a demonstration of what a dynamically generated tool looks like.
"""

import json
from typing import Any


def calculate_square(number: int) -> str:
    """
    Calculate the square of a number.

    This tool demonstrates the structure of auto-generated tools.
    It takes a number as input and returns its square.

    Args:
        number: Integer number to square

    Returns:
        JSON string with structure:
        - On success: {"result": <squared_value>, "input": <number>, "status": "success"}
        - On error: {"error": <error_message>, "status": "failed"}

    Example:
        >>> calculate_square(5)
        '{"result": 25, "input": 5, "status": "success"}'
    """
    try:
        # Validate input
        if not isinstance(number, (int, float)):
            return json.dumps({
                "error": f"Expected number, got {type(number).__name__}",
                "status": "failed"
            })

        # Calculate square
        result = number ** 2

        # Return success response
        return json.dumps({
            "result": result,
            "input": number,
            "operation": "square",
            "status": "success"
        })

    except Exception as e:
        # Handle any unexpected errors
        return json.dumps({
            "error": str(e),
            "status": "failed"
        })

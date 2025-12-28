"""
Think Tag Parser - Extract and separate <think> tags from LLM responses.

User Request: "oft wenn ich mit selfai arbeite kommen die <think> tokens in den weg,
können wir das so parsen( egrep -n bsp) die thinktags kommen ins Ui,
der rest geht weiter in der internen kommuniktionspipline"

This module parses <think>...</think> tags from LLM responses, allowing:
- Separate display of thinking process in UI
- Clean content for internal communication pipeline
"""

import re
from typing import Tuple


def parse_think_tags(response: str) -> Tuple[str, list[str]]:
    """
    Extract <think> tags from LLM response.

    Args:
        response: Raw LLM response potentially containing <think>...</think> tags

    Returns:
        Tuple of (clean_response, think_contents)
        - clean_response: Response with all <think> tags removed
        - think_contents: List of extracted think tag contents

    Example:
        >>> response = "Let me think <think>analyzing the problem...</think> about this. <think>considering options</think> Here's my answer."
        >>> clean, thinks = parse_think_tags(response)
        >>> clean
        'Let me think about this. Here's my answer.'
        >>> thinks
        ['analyzing the problem...', 'considering options']
    """
    # Pattern to match <think>...</think> (case insensitive, multiline, non-greedy)
    think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL | re.IGNORECASE)

    # Extract all think tag contents
    think_contents = think_pattern.findall(response)

    # Remove all think tags from response
    clean_response = think_pattern.sub('', response).strip()

    # Clean up multiple consecutive spaces/newlines created by removal
    clean_response = re.sub(r'\n\n+', '\n\n', clean_response)
    clean_response = re.sub(r' {2,}', ' ', clean_response)

    return clean_response, think_contents


def parse_think_tags_streaming(chunk: str, buffer: str = "") -> Tuple[str, str, list[str]]:
    """
    Parse think tags from streaming response chunks.

    For streaming responses, we need to buffer content to handle tags that
    span multiple chunks.

    Args:
        chunk: Current response chunk
        buffer: Accumulated buffer from previous chunks

    Returns:
        Tuple of (clean_chunk, new_buffer, completed_thinks)
        - clean_chunk: Chunk content safe to display (outside think tags)
        - new_buffer: Updated buffer for next chunk
        - completed_thinks: List of completed think tag contents

    Usage:
        buffer = ""
        for chunk in stream:
            clean_chunk, buffer, thinks = parse_think_tags_streaming(chunk, buffer)
            # Display clean_chunk to user
            # Display thinks separately if any
    """
    # Add chunk to buffer
    buffer += chunk

    # Extract all COMPLETED think tags (have both opening and closing tags)
    completed_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL | re.IGNORECASE)
    completed_thinks = completed_pattern.findall(buffer)

    # Remove completed think tags from buffer
    buffer_cleaned = completed_pattern.sub('', buffer)

    # Check if we're inside an incomplete think tag
    open_tag_match = re.search(r'<think>', buffer_cleaned, re.IGNORECASE)

    if open_tag_match:
        # We're inside a think tag, buffer everything after <think>
        before_think = buffer_cleaned[:open_tag_match.start()]
        after_think = buffer_cleaned[open_tag_match.end():]

        # Return content before think tag, buffer the rest
        return before_think, f"<think>{after_think}", completed_thinks
    else:
        # No open think tag, safe to return all cleaned content
        return buffer_cleaned, "", completed_thinks

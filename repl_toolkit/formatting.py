"""
Formatted text utilities for repl_toolkit.

This module provides utilities for working with formatted text in prompt_toolkit,
including auto-detection of format types and smart printing.
"""

import re
from typing import Callable

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import ANSI, HTML

# Pre-compile regex patterns for performance
_ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
_HTML_PATTERN = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*\s*/?>")


def detect_format_type(text: str) -> str:
    """
    Detect the format type of a text string.

    Detects three format types:
    - 'ansi': Text contains ANSI escape codes (e.g., \\x1b[1m)
    - 'html': Text contains HTML-like tags (e.g., <b>, <darkcyan>)
    - 'plain': Plain text with no special formatting

    Args:
        text: Text string to analyze

    Returns:
        Format type: 'ansi', 'html', or 'plain'

    Examples:
        >>> detect_format_type("<b>Bold</b>")
        'html'
        >>> detect_format_type("\\x1b[1mBold\\x1b[0m")
        'ansi'
        >>> detect_format_type("Plain text")
        'plain'
        >>> detect_format_type("a < b and c > d")
        'plain'
    """
    # Check for ANSI escape codes (most specific)
    if _ANSI_PATTERN.search(text):
        return "ansi"

    # Check for HTML tags
    # Valid HTML tag names: start with letter, contain letters/numbers
    if _HTML_PATTERN.search(text):
        return "html"

    # Plain text
    return "plain"


def auto_format(text: str):
    """
    Auto-detect format type and return appropriate formatted text object.

    This function analyzes the input text and wraps it in the appropriate
    prompt_toolkit formatted text type (HTML, ANSI, or plain string).

    Args:
        text: Text string to format

    Returns:
        Formatted text object (HTML, ANSI, or str)

    Examples:
        >>> auto_format("<b>Bold</b>")
        HTML('<b>Bold</b>')
        >>> auto_format("\\x1b[1mBold\\x1b[0m")
        ANSI('\\x1b[1mBold\\x1b[0m')
        >>> auto_format("Plain text")
        'Plain text'
    """
    format_type = detect_format_type(text)

    if format_type == "ansi":
        return ANSI(text)
    elif format_type == "html":
        return HTML(text)
    else:
        return text


def print_auto_formatted(text: str, **kwargs) -> None:
    """
    Print text with auto-detected formatting.

    This function automatically detects the format type (HTML, ANSI, or plain)
    and prints the text with appropriate formatting applied.

    Args:
        text: Text to print (may contain HTML tags, ANSI codes, or be plain)
        **kwargs: Additional arguments passed to print_formatted_text
                 (e.g., end, flush, style, output)

    Examples:
        >>> print_auto_formatted("<b>Bold</b> text")
        Bold text
        >>> print_auto_formatted("\\x1b[1mBold\\x1b[0m text")
        Bold text
        >>> print_auto_formatted("Plain text")
        Plain text
    """
    formatted = auto_format(text)
    print_formatted_text(formatted, **kwargs)


def create_auto_printer() -> Callable:
    """
    Create a printer function with auto-format detection.

    Returns a callable that can be used as a drop-in replacement for print(),
    with automatic detection and application of formatting (HTML or ANSI).

    This is particularly useful for injecting into callback handlers or other
    components that accept a custom printer function.

    Returns:
        Callable printer function with signature: printer(text, **kwargs)

    Examples:
        >>> printer = create_auto_printer()
        >>> printer("<b>Bold</b>", end="", flush=True)
        Bold
        >>> printer(" text\\n")
         text

    Usage with callback handlers:
        >>> from some_library import CallbackHandler
        >>> handler = CallbackHandler(
        ...     response_prefix="<b>Bot:</b> ",
        ...     printer=create_auto_printer()
        ... )
    """

    def printer(text: str, **kwargs):
        """Auto-format and print text."""
        print_auto_formatted(text, **kwargs)

    return printer


__all__ = [
    "detect_format_type",
    "auto_format",
    "print_auto_formatted",
    "create_auto_printer",
    "print_formatted_text",
]

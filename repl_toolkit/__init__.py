"""
repl_toolkit: A modern toolkit for building async REPL interfaces.

This package provides components for creating interactive command-line
interfaces with support for actions (commands and keyboard shortcuts),
auto-completion, and flexible input handling.

Basic usage:
    >>> from repl_toolkit import AsyncREPL
    >>>
    >>> class MyBackend:
    ...     async def handle_input(self, user_input: str) -> bool:
    ...         print(f"Received: {user_input}")
    ...         return True
    >>>
    >>> repl = AsyncREPL()
    >>> await repl.run(MyBackend())

With cancellation support:
    >>> from repl_toolkit import CancellableBackend
    >>>
    >>> class MyCancellableBackend:
    ...     def __init__(self):
    ...         self._cancelled = False
    ...
    ...     async def handle_input(self, user_input: str, **kwargs) -> bool:
    ...         self._cancelled = False
    ...         # ... processing with cancellation checkpoints ...
    ...         return True
    ...
    ...     def cancel(self, message: str = None) -> None:
    ...         self._cancelled = True
"""

import logging

# Add NullHandler to prevent "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "2.2.0"

from .actions import Action, ActionContext, ActionRegistry
from .async_repl import AsyncREPL, run_async_repl
from .completion import PrefixCompleter, ShellExpansionCompleter
from .formatting import (
    auto_format,
    create_auto_printer,
    detect_format_type,
    print_auto_formatted,
    print_formatted_text,
)
from .headless_repl import HeadlessREPL, run_headless_mode
from .images import (
    ImageData,
    ParsedContent,
    detect_media_type,
    iter_content_parts,
    parse_image_references,
    reconstruct_message,
)
from .ptypes import ActionHandler, AsyncBackend, CancellableBackend, Completer

__all__ = [
    # Core REPL
    "AsyncREPL",
    "run_async_repl",
    "HeadlessREPL",
    "run_headless_mode",
    # Actions
    "Action",
    "ActionContext",
    "ActionRegistry",
    # Completion
    "PrefixCompleter",
    "ShellExpansionCompleter",
    # Formatting
    "auto_format",
    "create_auto_printer",
    "detect_format_type",
    "print_auto_formatted",
    "print_formatted_text",
    # Images
    "ImageData",
    "ParsedContent",
    "detect_media_type",
    "parse_image_references",
    "iter_content_parts",
    "reconstruct_message",
    # Protocols
    "ActionHandler",
    "AsyncBackend",
    "CancellableBackend",
    "Completer",
]

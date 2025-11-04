"""
REPL Toolkit - A Python toolkit for building interactive REPL and headless interfaces.

This package provides tools for creating interactive command-line interfaces
with support for both commands and keyboard shortcuts, featuring late backend
binding for resource context scenarios.

Key Features:
- Action system with commands and keyboard shortcuts
- Late backend binding for resource contexts
- Protocol-based architecture for type safety
- Comprehensive test coverage
- Async-native design
- Auto-formatting utilities for HTML and ANSI text
- Custom output handling with configurable printer
- Shell expansion and prefix-based completion

Example:
    >>> import asyncio
    >>> from repl_toolkit import run_async_repl, ActionRegistry
    >>>
    >>> class MyBackend:
    ...     async def handle_input(self, user_input: str) -> bool:
    ...         print(f"You said: {user_input}")
    ...         return True
    >>>
    >>> async def main():
    ...     backend = MyBackend()
    ...     await run_async_repl(backend=backend)
    >>>
    >>> # asyncio.run(main())
"""

__version__ = "1.2.0"
__author__ = "REPL Toolkit Contributors"
__license__ = "MIT"

from .actions import Action, ActionContext, ActionError, ActionRegistry

# Core exports
from .async_repl import AsyncREPL, run_async_repl
from .completion import PrefixCompleter, ShellExpansionCompleter
from .formatting import auto_format, create_auto_printer, detect_format_type, print_auto_formatted
from .headless_repl import HeadlessREPL, run_headless_mode
from .ptypes import ActionHandler, AsyncBackend, Completer

__all__ = [
    # Core classes
    "AsyncREPL",
    "HeadlessREPL",
    "ActionRegistry",
    "Action",
    "ActionContext",
    "ActionError",
    # Convenience functions
    "run_async_repl",
    "run_headless_mode",
    # Protocols/Types
    "AsyncBackend",
    "ActionHandler",
    "Completer",
    # Formatting utilities
    "detect_format_type",
    "auto_format",
    "print_auto_formatted",
    "create_auto_printer",
    # Completion utilities
    "ShellExpansionCompleter",
    "PrefixCompleter",
]

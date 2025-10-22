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

__version__ = "1.0.0"
__author__ = "REPL Toolkit Contributors"
__license__ = "MIT"

# Core exports
from .async_repl import AsyncREPL, run_async_repl
from .headless import run_headless_mode
from .actions import ActionRegistry, Action, ActionContext, ActionError
from .ptypes import AsyncBackend, HeadlessBackend, ActionHandler, Completer

__all__ = [
    # Core classes
    "AsyncREPL",
    "ActionRegistry", 
    "Action",
    "ActionContext",
    "ActionError",
    
    # Convenience functions
    "run_async_repl",
    "run_headless_mode",
    
    # Protocols/Types
    "AsyncBackend",
    "HeadlessBackend", 
    "ActionHandler",
    "Completer",
]
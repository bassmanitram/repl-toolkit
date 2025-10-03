"""
REPL Toolkit - A Python toolkit for building interactive REPL and headless interfaces.

This package provides reusable components for creating conversational applications,
chatbots, and interactive shells with clean abstractions and full type safety.
"""

from .async_repl import AsyncREPL, run_async_repl
from .headless import run_headless_mode
from .ptypes import AsyncBackend, HeadlessBackend, CommandHandler, Completer

__version__ = "0.1.0"
__all__ = [
    # Main interfaces
    "AsyncREPL",
    "run_async_repl", 
    "run_headless_mode",
    
    # Type protocols
    "AsyncBackend",
    "HeadlessBackend", 
    "CommandHandler",
    "Completer",
]
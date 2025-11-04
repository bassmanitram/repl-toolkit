"""
Completion utilities for REPL toolkit.

This module provides completers that can be used with prompt_toolkit:
- ShellExpansionCompleter: Environment variable and shell command expansion
- PrefixCompleter: Static string matching with optional prefix character
"""

from .prefix import PrefixCompleter
from .shell_expansion import ShellExpansionCompleter

__all__ = [
    "ShellExpansionCompleter",
    "PrefixCompleter",
]

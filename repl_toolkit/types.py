"""
Type definitions and protocols for repl_toolkit.

This module defines the core interfaces that backends must implement
to work with the REPL toolkit components.
"""

from typing import Protocol, Optional, List, runtime_checkable
from pathlib import Path


@runtime_checkable
class AsyncBackend(Protocol):
    """
    Protocol for async REPL backends that process user input.
    
    Backends implementing this protocol can be used with AsyncREPL
    to handle user input in an interactive session.
    """
    
    async def handle_input(self, user_input: str) -> bool:
        """
        Process user input asynchronously.
        
        Args:
            user_input: The input string from the user
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        ...


@runtime_checkable  
class HeadlessBackend(Protocol):
    """
    Protocol for headless backends that process input non-interactively.
    
    Backends implementing this protocol can be used with run_headless_mode
    for scripted or piped input processing.
    """
    
    async def handle_input(self, user_input: str) -> bool:
        """
        Process user input asynchronously.
        
        Args:
            user_input: The input string from the user
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        ...


@runtime_checkable
class CommandHandler(Protocol):
    """
    Protocol for handling command input (e.g., /help, /quit).
    
    Command handlers process commands that start with '/' and provide
    additional functionality beyond basic input processing.
    """
    
    async def handle_command(self, command: str) -> None:
        """
        Handle a command string.
        
        Args:
            command: The full command string including the leading '/'
        """
        ...


@runtime_checkable
class Completer(Protocol):
    """
    Protocol for providing tab completion in interactive mode.
    
    Completers suggest possible completions for partial user input
    to improve the interactive experience.
    """
    
    def get_completions(self, document, complete_event) -> List:
        """
        Get completions for the current document state.
        
        Args:
            document: The current document from prompt_toolkit
            complete_event: The completion event from prompt_toolkit
            
        Returns:
            List of Completion objects
        """
        ...


# Type aliases for common use cases
BackendType = AsyncBackend | HeadlessBackend
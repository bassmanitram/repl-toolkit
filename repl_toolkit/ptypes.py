"""
Protocol types for repl_toolkit v2.

Defines the interface contracts that backends and handlers must implement
for compatibility with the REPL toolkit.
"""

from typing import Protocol, runtime_checkable, Optional, List
from pathlib import Path


@runtime_checkable
class AsyncBackend(Protocol):
    """
    Protocol for async backends that process user input.
    
    Backends are responsible for handling user input and generating responses
    in an asynchronous manner, supporting cancellation and error handling.
    """

    async def handle_input(self, user_input: str) -> bool:
        """
        Handle user input asynchronously.
        
        Args:
            user_input: The input string from the user
            
        Returns:
            bool: True if processing was successful, False if there was an error
            
        Note:
            This method should handle its own error reporting to the user.
            The return value indicates success/failure for flow control.
        """
        ...


@runtime_checkable  
class HeadlessBackend(Protocol):
    """
    Protocol for headless backends that process single interactions.
    
    HeadlessBackend is a simplified interface for non-interactive scenarios
    where a single input/output cycle is required.
    """

    async def handle_input(self, user_input: str) -> bool:
        """
        Handle user input in headless mode.
        
        Args:
            user_input: The input string to process
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        ...


@runtime_checkable
class ActionHandler(Protocol):
    """
    Protocol for action handlers in the action system.
    
    ActionHandler defines the interface for handling both command-based
    and keyboard shortcut-based actions in a coherent manner.
    """

    async def execute_action(self, action_name: str, context: "ActionContext") -> None:
        """
        Execute an action by name.
        
        Args:
            action_name: Name of the action to execute
            context: Action context containing relevant information
            
        Raises:
            ActionError: If action execution fails
        """
        ...

    async def handle_command(self, command_string: str) -> None:
        """
        Handle a command string by mapping to appropriate action.
        
        Args:
            command_string: Full command string (e.g., '/help arg1 arg2')
            
        Note:
            This method parses the command and maps it to the appropriate
            action execution with proper context.
        """
        ...

    def validate_action(self, action_name: str) -> bool:
        """
        Validate if an action is supported.
        
        Args:
            action_name: Action name to validate
            
        Returns:
            bool: True if action is supported, False otherwise
        """
        ...

    def list_actions(self) -> List[str]:
        """
        Return a list of all available action names.
        
        Returns:
            List of action names
        """
        ...


@runtime_checkable
class Completer(Protocol):
    """
    Protocol for auto-completion providers.
    
    Completers provide tab-completion suggestions for user input,
    supporting both command completion and context-aware suggestions.
    """

    def get_completions(self, document, complete_event):
        """
        Get completions for the current input.
        
        Args:
            document: Current document state from prompt_toolkit
            complete_event: Completion event from prompt_toolkit
            
        Yields:
            Completion: Individual completion suggestions
            
        Note:
            This follows the prompt_toolkit Completer interface for
            compatibility with the underlying prompt_toolkit system.
        """
        ...
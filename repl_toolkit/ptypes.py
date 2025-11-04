"""
Protocol types for repl_toolkit.

Defines the interface contracts that backends and handlers must implement
for compatibility with the REPL toolkit.
"""

from typing import TYPE_CHECKING, List, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .actions.action import ActionContext  # Avoid circular import


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
class ActionHandler(Protocol):
    """
    Protocol for action handlers in the action system.

    ActionHandler defines the interface for handling both command-based
    and keyboard shortcut-based actions in a coherent manner.
    """

    def execute_action(self, action_name: str, context: "ActionContext") -> None:
        """
        Execute an action by name.

        Args:
            action_name: Name of the action to execute
            context: Action context containing relevant information

        Raises:
            ActionError: If action execution fails
        """
        ...

    def handle_command(self, command_string: str, **kwargs) -> None:
        """
        Handle a command string by mapping to appropriate action.

        Args:
            command_string: Full command string (e.g., '/help arg1 arg2')
            **kwargs: Additional context parameters (e.g., headless_mode, buffer)

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

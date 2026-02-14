"""
Protocol types for repl_toolkit.

Defines the interface contracts that backends and handlers must implement
for compatibility with the REPL toolkit.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .actions.action import ActionContext
    from .images import ImageData


@runtime_checkable
class AsyncBackend(Protocol):
    """
    Protocol for async backends that process user input.

    Backends are responsible for handling user input and generating responses
    in an asynchronous manner, supporting error handling.

    For cancellation support, implement `CancellableBackend` instead.
    """

    async def handle_input(
        self, user_input: str, images: Optional[Dict[str, "ImageData"]] = None, **kwargs
    ) -> bool:
        """
        Handle user input asynchronously.

        Args:
            user_input: The input string from the user
            images: Optional dictionary mapping image IDs to ImageData
            **kwargs: Additional arguments (e.g., cancel_callback for tools)

        Returns:
            bool: True if processing was successful, False if there was an error
        """
        ...


@runtime_checkable
class CancellableBackend(AsyncBackend, Protocol):
    """
    Protocol for async backends that support cooperative cancellation.

    Extends AsyncBackend with a cancel() method that allows the REPL to
    signal cancellation to the backend. The backend should implement
    cooperative cancellation by checking an internal flag at safe points.

    Implementation Guidelines:
        1. cancel() MUST be non-blocking (return immediately)
        2. Set an internal cancellation token/flag
        3. handle_input() should check the flag at safe checkpoints
        4. Reset the flag at the start of each new operation
        5. Kill any child processes if applicable

    Example:
        class MyCancellableBackend:
            def __init__(self):
                self._cancel_token = CancellationToken()

            def cancel(self, message: Optional[str] = None) -> None:
                self._cancel_token.cancel(message)

            async def handle_input(self, user_input: str, **kwargs) -> bool:
                self._cancel_token.reset()
                # ... processing with cancellation checkpoints ...
    """

    def cancel(self, message: Optional[str] = None) -> None:
        """
        Signal cancellation to the backend.

        This method MUST be non-blocking and return immediately. It should
        set an internal flag that handle_input() checks at safe points.

        Args:
            message: Optional message describing the cancellation reason.
                    Typically "Operation cancelled by user".
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
            **kwargs: Additional context parameters
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
        """
        ...

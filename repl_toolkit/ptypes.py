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
    signal cancellation to the backend. The backend can control whether
    the REPL should force-cancel the asyncio task or let it complete gracefully.

    Implementation Guidelines:
        1. cancel() MUST be non-blocking (return immediately)
        2. Set an internal cancellation token/flag
        3. Return value controls REPL behavior:
           - True or None: Force cancel the asyncio task (default, backward compatible)
           - False: Let handle_input() complete gracefully
        4. handle_input() should check the cancellation flag at safe checkpoints
        5. Reset the flag at the start of each new operation

    Backward Compatibility:
        - Backends without cancel() → task is force-cancelled
        - Backends with cancel() returning None → task is force-cancelled
        - This maintains behavior expected by existing implementations

    Example (force cancellation - default/legacy behavior):
        class LegacyBackend:
            def cancel(self, message: Optional[str] = None) -> None:
                self._cancelled = True
                # Returns None → REPL force-cancels the task

    Example (graceful completion - new behavior):
        class GracefulBackend:
            def cancel(self, message: Optional[str] = None) -> bool:
                self._token.cancel(message)
                return False  # Let handle_input() complete, hooks will fire

            async def handle_input(self, user_input: str, **kwargs) -> bool:
                # Process with agent - hooks handle cleanup on cancellation
                return await self.agent.process(user_input)
    """

    def cancel(self, message: Optional[str] = None) -> Optional[bool]:
        """
        Signal cancellation to the backend.

        This method MUST be non-blocking and return immediately. It should
        set an internal flag that handle_input() checks at safe points.

        Args:
            message: Optional message describing the cancellation reason.
                    Typically "Operation cancelled by user".

        Returns:
            Optional[bool]:
                True or None: REPL should force-cancel the asyncio task
                              (handle_input receives CancelledError)
                False: REPL should let handle_input() complete gracefully
                       (allows cleanup hooks to fire)
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

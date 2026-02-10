"""
Protocol types for repl_toolkit.

Defines the interface contracts that backends and handlers must implement
for compatibility with the REPL toolkit.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .actions.action import ActionContext  # Avoid circular import
    from .images import ImageData  # Avoid circular import


@runtime_checkable
class AsyncBackend(Protocol):
    """
    Protocol for async backends that process user input.

    Backends are responsible for handling user input and generating responses
    in an asynchronous manner, supporting cancellation and error handling.

    Optional Cancellation Support:
        Backends can optionally implement a cancel(message: Optional[str] = None)
        method to support cooperative cancellation of long-running operations.
        This is particularly useful when the backend performs blocking operations
        that cannot be immediately cancelled via asyncio.Task.cancel().

        The cancel() method is NOT part of the protocol requirement (not checked
        by isinstance). The REPL checks for it using hasattr() at runtime.

        Implementation Guidelines for cancel():
            1. Method signature: cancel(self, message: Optional[str] = None) -> None
            2. MUST be non-blocking (return immediately)
            3. Set an internal cancellation token/flag that handle_input() can check
            4. handle_input() should check the flag at safe checkpoints
            5. Reset the flag at the start of each new operation

        Example Implementation:
            class CancellableBackend:
                def __init__(self):
                    self._cancel_requested = False

                def cancel(self, message: Optional[str] = None) -> None:
                    '''Signal cancellation.'''
                    self._cancel_requested = True
                    if message:
                        logger.info(f"Cancellation requested: {message}")

                async def handle_input(self, user_input: str, **kwargs) -> bool:
                    '''Process input with cancellation checkpoints.'''
                    # Reset flag at start of operation
                    self._cancel_requested = False

                    try:
                        for step in self._get_processing_steps(user_input):
                            # Checkpoint: Check for cancellation
                            if self._cancel_requested:
                                print("Operation cancelled.")
                                return False

                            # Do work
                            await self._process_step(step)

                        return True

                    except Exception as e:
                        logger.error(f"Error: {e}")
                        return False

        Cancellation Messages:
            The message parameter typically contains one of:
            - "Operation cancelled by user" (Alt+C in interactive mode)
            - "Operation cancelled by user (Ctrl+C)" (Ctrl+C interrupt)
            - "Operation cancelled due to error" (Exception during processing)

        Note:
            - Backends without cancel() will still work correctly
            - They will fall back to asyncio.Task.cancel() only
            - There is a small race condition where the operation might
              complete between the cancellation request and flag check.
              Implementations should handle this gracefully (no-op if already done).
    """

    async def handle_input(
        self, user_input: str, images: Optional[Dict[str, "ImageData"]] = None
    ) -> bool:
        """
        Handle user input asynchronously.

        Args:
            user_input: The input string from the user
            images: Optional dictionary mapping image IDs to ImageData.
                   Image IDs appear in user_input as {{image:img_xxx}} placeholders.

        Returns:
            bool: True if processing was successful, False if there was an error

        Note:
            This method should handle its own error reporting to the user.
            The return value indicates success/failure for flow control.

            Legacy backends can ignore the images parameter for backward compatibility.

            For cancellable operations, implement cancel() method and check the
            cancellation flag at safe checkpoints during processing.
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

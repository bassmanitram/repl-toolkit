"""
Async REPL interface with action support for repl_toolkit.

Provides an interactive chat interface with full UI features including
history, action handling (commands + keyboard shortcuts), and 
robust cancellation of long-running tasks.
"""

import asyncio
from pathlib import Path
import sys
from typing import Optional

from loguru import logger
from prompt_toolkit import HTML, PromptSession, print_formatted_text as print
from prompt_toolkit.application import Application
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.completion import Completer
from prompt_toolkit.keys import Keys
from prompt_toolkit.history import FileHistory

from .ptypes import AsyncBackend, ActionHandler, Completer
from .actions import ActionRegistry, ActionContext

THINKING = HTML("<i><grey>Thinking... (Press Alt+C to cancel)</grey></i>")


class AsyncREPL:
    """
    Manages an interactive async REPL session with action support.
    
    Provides user input handling, action processing (commands and shortcuts),
    and robust cancellation of long-running tasks with a clean, extensible interface.
    
    The v2 AsyncREPL supports late backend binding, allowing initialization without
    a backend for scenarios where the backend is only available within a resource
    context block.
    """

    def __init__(
        self,
        action_registry: Optional[ActionHandler] = None,
        completer: Optional[Completer] = None,
        prompt_string: Optional[str] = None,
        history_path: Optional[Path] = None
    ):
        """
        Initialize the async REPL interface.

        Args:
            action_registry: Action registry for commands and shortcuts (optional)
            completer: Optional tab-completion provider
            prompt_string: Custom prompt string (default: "User: ")
            history_path: Optional path for command history storage
            
        Note:
            Backend is provided later via the run() method to support scenarios
            where the backend is only available within a resource context.
        """
        self.prompt_string = HTML(prompt_string or "User: ")
        self.action_registry = action_registry or ActionRegistry()
        self.session = PromptSession(
            history=self._create_history(history_path),
            key_bindings=self._create_key_bindings(),
            multiline=True,
            completer=completer,
        )
        self.main_app = self.session.app

    def _create_history(self, path: Optional[Path]) -> Optional[FileHistory]:
        """
        Create file history if path is provided.
        
        Args:
            path: Optional path to history file
            
        Returns:
            FileHistory instance or None
        """
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            return FileHistory(str(path))
        return None

    def _create_key_bindings(self) -> KeyBindings:
        """
        Create key bindings for the REPL session.

        This method creates both built-in key bindings and dynamic bindings
        from the action registry, providing a shortcut system.

        Built-in Key Bindings:
        - Enter: Add new line
        - Alt+Enter: Send message
        - Alt+C: Cancel operation (during processing)

        Dynamic bindings are loaded from the action registry.

        Returns:
            KeyBindings instance with configured shortcuts
        """
        bindings = KeyBindings()

        # Built-in bindings for core REPL functionality
        @bindings.add("enter")
        def _(event):
            """Handle Enter key - add new line."""
            event.app.current_buffer.insert_text("\n")

        @bindings.add(Keys.Escape, "enter")  
        def _(event):
            """Handle Alt+Enter - send message."""
            event.app.current_buffer.validate_and_handle()

        # Register dynamic key bindings from action registry
        self._register_action_shortcuts(bindings)

        return bindings
    
    def _register_action_shortcuts(self, bindings: KeyBindings) -> None:
        """
        Register keyboard shortcuts from the action registry.
        
        Args:
            bindings: KeyBindings instance to add shortcuts to
        """
        if not hasattr(self.action_registry, 'key_map'):
            return
            
        for key_combo, action_name in self.action_registry.key_map.items():
            self._register_shortcut(bindings, key_combo, action_name)
    
    def _register_shortcut(self, bindings: KeyBindings, key_combo: str, action_name: str) -> None:
        """
        Register a single keyboard shortcut.
        
        Args:
            bindings: KeyBindings instance
            key_combo: Key combination string (e.g., "F1", "ctrl-s")
            action_name: Name of action to execute
        """
        try:
            # Parse key combination - handle common formats
            keys = self._parse_key_combination(key_combo)
            
            @bindings.add(*keys)
            def _(event):
                # Execute action synchronously
                try:
                    self.action_registry.handle_shortcut(key_combo, event)
                except Exception as e:
                    logger.error(f"Error executing shortcut '{key_combo}': {e}")
                    print(f"Error: {e}")
            
            logger.debug(f"Registered shortcut '{key_combo}' -> '{action_name}'")
            
        except Exception as e:
            logger.error(f"Failed to register shortcut '{key_combo}' for action '{action_name}': {e}")
    
    def _parse_key_combination(self, key_combo: str) -> tuple:
        """
        Parse key combination string into prompt_toolkit format.
        
        Args:
            key_combo: Key combination (e.g., "F1", "ctrl-s", "alt-enter")
            
        Returns:
            Tuple of keys for prompt_toolkit
        """
        # Handle common key formats
        key_combo = key_combo.lower().strip()
        
        # Single function keys
        if key_combo.startswith('f') and key_combo[1:].isdigit():
            return (key_combo,)
        
        # Handle modifier combinations
        if '-' in key_combo:
            parts = key_combo.split('-')
            if len(parts) == 2:
                modifier, key = parts
                
                # Map common modifiers
                if modifier == 'ctrl':
                    return ('c-' + key,)
                elif modifier == 'alt':
                    return (Keys.Escape, key)
                elif modifier == 'shift':
                    return ('s-' + key,)
        
        # Single keys
        return (key_combo,)
    
    async def run(self, backend: AsyncBackend, initial_message: Optional[str] = None):
        """
        Run the async REPL session with the provided backend.
        
        This method accepts the backend at runtime, supporting scenarios where
        the backend is only available within a resource context block.
        
        Args:
            backend: Backend responsible for processing user input
            initial_message: Optional message to process before starting loop
        """
        # Set backend in action registry for action handlers to access
        self.action_registry.backend = backend

        if initial_message:
            print(self.prompt_string, end="")
            print(initial_message)
            await self._process_input(initial_message, backend)
            print()

        while True:
            try:
                user_input = await self.session.prompt_async(self.prompt_string)
                if self._should_exit(user_input):
                    break
                if not user_input.strip():
                    continue
                if user_input.strip().startswith("/"):
                    # Handle commands synchronously
                    self.action_registry.handle_command(user_input.strip())
                    continue

                logger.debug(f"Processing user input: {user_input}")
                await self._process_input(user_input, backend)

            except (KeyboardInterrupt, EOFError):
                print()
                break
            except Exception as e:
                logger.error(f"Error in REPL loop: {e}")
                print(f"An error occurred: {e}", file=sys.stderr)

    def _should_exit(self, user_input: str) -> bool:
        """Check if input is an exit command."""
        return user_input.strip().lower() in ["/exit", "/quit"]

    async def _process_input(self, user_input: str, backend: AsyncBackend):
        """
        Process user input with cancellation support.
        
        Runs the backend processing task concurrently with a cancellation
        listener, allowing users to cancel long-running operations.
        
        Args:
            user_input: Input string to process
            backend: Backend to process the input
        """
        cancel_future = asyncio.Future()

        kb = KeyBindings()
        @kb.add("escape", "c")
        def _(event):
            if not cancel_future.done():
                cancel_future.set_result(None)
            event.app.exit()

        cancel_app = Application(
            key_bindings=kb, output=DummyOutput(), input=create_input()
        )

        backend_task = asyncio.create_task(backend.handle_input(user_input))
        listener_task = asyncio.create_task(cancel_app.run_async())
        print(THINKING)

        try:
            done, pending = await asyncio.wait(
                [backend_task, cancel_future],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if cancel_future in done:
                print("\nOperation cancelled by user.")
                backend_task.cancel()
            else:
                success = backend_task.result()
                if not success:
                    print("Operation failed.")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            if not backend_task.done():
                backend_task.cancel()

        finally:
            # Cleanup
            if not cancel_app.is_done:
                cancel_app.exit()

            await listener_task

            self.main_app.renderer.reset()
            self.main_app.renderer.invalidate()
            await asyncio.sleep(0)


# Convenience function
async def run_async_repl(
    backend: AsyncBackend,
    action_registry: Optional[ActionHandler] = None,
    completer: Optional[Completer] = None,
    initial_message: Optional[str] = None,
    prompt_string: Optional[str] = None,
    history_path: Optional[Path] = None,
):
    """
    Convenience function to create and run an AsyncREPL with action support.
    
    This function creates an AsyncREPL instance and runs it with the provided
    backend, supporting the late backend binding pattern.
    
    Args:
        backend: Backend for processing input
        action_registry: Action registry for commands and shortcuts (optional)
        completer: Optional completer
        initial_message: Optional initial message
        prompt_string: Optional custom prompt
        history_path: Optional history file path
    """
    repl = AsyncREPL(action_registry, completer, prompt_string, history_path)
    await repl.run(backend, initial_message)
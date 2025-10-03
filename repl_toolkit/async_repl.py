"""
Async REPL interface for repl_toolkit.

Provides an interactive chat interface with full UI features including
history, key bindings, and robust cancellation of long-running tasks.
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

from .types import AsyncBackend, CommandHandler, Completer
from .commands.registry import CommandRegistry

THINKING = HTML("<i><grey>Thinking... (Press Alt+C to cancel)</grey></i>")


class AsyncREPL:
    """
    Manages an interactive async REPL session.
    
    Provides user input handling, command processing, and robust cancellation
    of long-running tasks with a clean, extensible interface.
    """

    def __init__(
        self,
        backend: AsyncBackend,
        command_handler: Optional[CommandHandler] = None,
        completer: Optional[Completer] = None,
        prompt_string: Optional[str] = None,
        history_path: Optional[Path] = None
    ):
        """
        Initialize the async REPL interface.

        Args:
            backend: Backend responsible for processing user input
            command_handler: Optional command handler for /commands
            completer: Optional tab-completion provider
            prompt_string: Custom prompt string (default: "User: ")
            history_path: Optional path for command history storage
        """
        self.backend = backend
        self.command_handler = command_handler or CommandRegistry()
        self.prompt_string = HTML(prompt_string or "User: ")

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

        Key Bindings:
        - Enter: Add new line
        - Alt+Enter: Send message

        Returns:
            KeyBindings instance with configured shortcuts
        """
        bindings = KeyBindings()

        @bindings.add("enter")
        def _(event):
            """Handle Enter key - add new line."""
            event.app.current_buffer.insert_text("\n")

        @bindings.add(Keys.Escape, "enter")
        def _(event):
            """Handle Alt+Enter - send message."""
            event.app.current_buffer.validate_and_handle()

        return bindings
    
    async def run(self, initial_message: Optional[str] = None):
        """
        Run the async REPL session.
        
        Processes an optional initial message, then enters the main
        interactive loop until the user exits.
        
        Args:
            initial_message: Optional message to process before starting loop
        """
        if initial_message:
            print(self.prompt_string, end="")
            print(initial_message)
            await self._process_input(initial_message)
            print()

        while True:
            try:
                user_input = await self.session.prompt_async(self.prompt_string)
                if self._should_exit(user_input):
                    break
                if not user_input.strip():
                    continue
                if user_input.strip().startswith("/"):
                    await self.command_handler.handle_command(user_input.strip())
                    continue

                logger.debug(f"Processing user input: {user_input}")
                await self._process_input(user_input)

            except (KeyboardInterrupt, EOFError):
                print()
                break
            except Exception as e:
                logger.error(f"Error in REPL loop: {e}")
                print(f"An error occurred: {e}", file=sys.stderr)

    def _should_exit(self, user_input: str) -> bool:
        """Check if input is an exit command."""
        return user_input.strip().lower() in ["/exit", "/quit"]

    async def _process_input(self, user_input: str):
        """
        Process user input with cancellation support.
        
        Runs the backend processing task concurrently with a cancellation
        listener, allowing users to cancel long-running operations.
        
        Args:
            user_input: Input string to process
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

        backend_task = asyncio.create_task(self.backend.handle_input(user_input))
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
            self.main_app.invalidate()
            await asyncio.sleep(0)


# Convenience function
async def run_async_repl(
    backend: AsyncBackend,
    command_handler: Optional[CommandHandler] = None,
    completer: Optional[Completer] = None,
    initial_message: Optional[str] = None,
    prompt_string: Optional[str] = None,
    history_path: Optional[Path] = None,
):
    """
    Convenience function to create and run an AsyncREPL.
    
    Args:
        backend: Backend for processing input
        command_handler: Optional command handler
        completer: Optional completer
        initial_message: Optional initial message
        prompt_string: Optional custom prompt
        history_path: Optional history file path
    """
    repl = AsyncREPL(backend, command_handler, completer, prompt_string, history_path)
    await repl.run(initial_message)
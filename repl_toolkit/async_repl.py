"""
Async REPL interface with action support for repl_toolkit.

Provides an interactive chat interface with full UI features including
history, action handling (commands + keyboard shortcuts), and
robust cancellation of long-running tasks.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)
from prompt_toolkit import HTML, PromptSession
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.application import Application
from prompt_toolkit.history import FileHistory
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import DummyOutput

from .actions import ActionContext, ActionRegistry
from .images import ImageData, create_paste_image_action
from .ptypes import ActionHandler, AsyncBackend, Completer

THINKING = HTML("<i><grey>Thinking... (Press Ctrl+C or Alt+C to cancel)</grey></i>")


class AsyncREPL:
    """
    Manages an interactive async REPL session with action support.

    Provides user input handling, action processing (commands and shortcuts),
    and robust cancellation of long-running tasks with a clean, extensible interface.

    The AsyncREPL supports late backend binding, allowing initialization without
    a backend for scenarios where the backend is only available within a resource
    context block.
    """

    def __init__(
        self,
        action_registry: Optional[ActionHandler] = None,
        completer: Optional[Completer] = None,
        prompt_string: Optional[str] = None,
        history_path: Optional[Path] = None,
        enable_image_paste: bool = True,
        **kwargs,
    ):
        """
        Initialize the async REPL interface.

        Args:
            action_registry: Action registry for commands and shortcuts (optional)
            completer: Optional tab-completion provider
            prompt_string: Custom prompt string (default: "User: ")
            history_path: Optional path for command history storage
            enable_image_paste: Enable image paste support (default: True)

        Note:
            Backend is provided later via the run() method to support scenarios
            where the backend is only available within a resource context.
        """
        logger.debug("AsyncREPL.__init__() entry")

        self.prompt_string = HTML(prompt_string or "User: ")
        self.action_registry = action_registry or ActionRegistry()

        # Image support
        self._image_buffer: Dict[str, ImageData] = {}
        self._image_counter = 0

        # Register image paste action if enabled
        if enable_image_paste:
            try:
                paste_action = create_paste_image_action()
                self.action_registry.register_action(paste_action)  # type: ignore[attr-defined]
            except Exception as e:
                logger.warning(f"Failed to register image paste action: {e}")

        self.session = PromptSession(  # type: ignore[var-annotated]
            message=self.prompt_string,
            history=self._create_history(history_path),
            key_bindings=self._create_key_bindings(),
            multiline=True,
            completer=completer,  # type: ignore[arg-type]
            **kwargs,
        )
        self.main_app = self.session.app

        logger.debug("AsyncREPL.__init__() exit")

    def add_image(self, img_bytes: bytes, media_type: str) -> str:
        """
        Add image to buffer for next message send.

        Args:
            img_bytes: Raw image bytes
            media_type: MIME type of the image

        Returns:
            image_id: The ID to reference this image
        """
        logger.debug("AsyncREPL.add_image() entry")

        self._image_counter += 1
        image_id = f"img_{self._image_counter:03d}"

        self._image_buffer[image_id] = ImageData(
            data=img_bytes, media_type=media_type, timestamp=time.time()
        )

        logger.debug(f"Added image {image_id} ({media_type}, {len(img_bytes)} bytes)")
        logger.debug("AsyncREPL.add_image() exit")
        return image_id

    def clear_images(self) -> None:
        """Clear all images from the buffer."""
        logger.debug("AsyncREPL.clear_images() entry/exit")
        self._image_buffer.clear()

    def get_images(self) -> Dict[str, ImageData]:
        """Get current image buffer."""
        logger.debug("AsyncREPL.get_images() entry/exit")
        return self._image_buffer.copy()

    def _create_history(self, path: Optional[Path]) -> Optional[FileHistory]:
        """
        Create file history if path is provided.

        Args:
            path: Optional path to history file

        Returns:
            FileHistory instance or None
        """
        logger.debug("AsyncREPL._create_history() entry")

        if path:  # pragma: no cover
            path.parent.mkdir(parents=True, exist_ok=True)
            result = FileHistory(str(path))
            logger.debug("AsyncREPL._create_history() exit - with history")
            return result

        logger.debug("AsyncREPL._create_history() exit - no history")
        return None

    def _create_key_bindings(self) -> KeyBindings:
        """
        Create key bindings for the REPL session.

        This method creates both built-in key bindings and dynamic bindings
        from the action registry, providing a shortcut system.

        Built-in Key Bindings:
        - Enter: Add new line
        - Alt+Enter: Send message
        - Ctrl+C: Cancel operation (during processing)
        - Alt+C: Cancel operation (during processing)

        Dynamic bindings are loaded from the action registry.

        Returns:
            KeyBindings instance with configured shortcuts
        """
        logger.debug("AsyncREPL._create_key_bindings() entry")

        bindings = KeyBindings()

        # Built-in bindings for core REPL functionality
        @bindings.add("enter")  # pragma: no cover
        def _(event):
            """Handle Enter key - add new line."""
            event.app.current_buffer.insert_text("\n")

        @bindings.add(Keys.Escape, "enter")  # pragma: no cover
        def _(event):
            """Handle Alt+Enter - send message."""
            event.app.current_buffer.validate_and_handle()

        # Register dynamic key bindings from action registry
        self._register_action_shortcuts(bindings)

        logger.debug("AsyncREPL._create_key_bindings() exit")
        return bindings

    def _register_action_shortcuts(self, bindings: KeyBindings) -> None:
        """
        Register keyboard shortcuts from the action registry.

        Args:
            bindings: KeyBindings instance to add shortcuts to
        """
        logger.debug("AsyncREPL._register_action_shortcuts() entry")

        if not hasattr(self.action_registry, "key_map"):
            logger.debug("AsyncREPL._register_action_shortcuts() exit - no key_map")
            return

        for key_combo, action_name in self.action_registry.key_map.items():
            self._register_shortcut(bindings, key_combo, action_name)

        logger.debug("AsyncREPL._register_action_shortcuts() exit")

    def _register_shortcut(self, bindings: KeyBindings, key_combo: str, action_name: str) -> None:
        """
        Register a single keyboard shortcut.

        Args:
            bindings: KeyBindings instance
            key_combo: Key combination string (e.g., "F1", "ctrl-s")
            action_name: Name of action to execute
        """
        logger.debug("AsyncREPL._register_shortcut() entry")

        try:
            # Parse key combination - handle common formats
            keys = self._parse_key_combination(key_combo)

            @bindings.add(*keys)  # pragma: no cover
            def _(event):
                # Execute action with full context
                try:
                    context = ActionContext(
                        registry=self.action_registry,
                        repl=self,
                        buffer=event.current_buffer,
                        backend=getattr(self.action_registry, "backend", None),
                        event=event,
                        triggered_by="shortcut",
                    )
                    self.action_registry.execute_action(action_name, context)
                except Exception as e:
                    logger.error(f"Error executing shortcut '{key_combo}': {e}")
                    print(f"Error: {e}")

            logger.debug(f"Registered shortcut '{key_combo}' -> '{action_name}'")
            logger.debug("AsyncREPL._register_shortcut() exit - success")

        except Exception as e:  # pragma: no cover
            logger.error(
                f"Failed to register shortcut '{key_combo}' for action '{action_name}': {e}"
            )
            logger.debug("AsyncREPL._register_shortcut() exit - error")

    def _parse_key_combination(self, key_combo: str) -> tuple:
        """
        Parse key combination string into prompt_toolkit format.

        Args:
            key_combo: Key combination (e.g., "F1", "ctrl-s", "c-s-v")

        Returns:
            Tuple of keys for prompt_toolkit
        """
        logger.debug("AsyncREPL._parse_key_combination() entry")

        # Handle common key formats
        key_combo = key_combo.lower().strip()

        # Single function keys
        if key_combo.startswith("f") and key_combo[1:].isdigit():
            logger.debug("AsyncREPL._parse_key_combination() exit - function key")
            return (key_combo,)

        # Handle modifier combinations
        if "-" in key_combo:
            parts = key_combo.split("-")

            # Three-part combinations (e.g., c-s-v for Ctrl+Shift+V)
            # Already in prompt_toolkit format
            if len(parts) == 3:
                logger.debug("AsyncREPL._parse_key_combination() exit - multi-mod combo")
                return (key_combo,)

            if len(parts) == 2:
                modifier, key = parts

                # Map common modifiers
                if modifier == "ctrl":
                    logger.debug("AsyncREPL._parse_key_combination() exit - ctrl combo")
                    return ("c-" + key,)
                elif modifier == "alt":
                    logger.debug("AsyncREPL._parse_key_combination() exit - alt combo")
                    return (Keys.Escape, key)
                elif modifier == "shift":  # pragma: no cover
                    logger.debug("AsyncREPL._parse_key_combination() exit - shift combo")
                    return ("s-" + key,)

        # Single keys
        logger.debug("AsyncREPL._parse_key_combination() exit - single key")
        return (key_combo,)

    async def run(
        self, backend: AsyncBackend, initial_message: Optional[str] = None
    ):  # pragma: no cover
        """
        Run the async REPL session with the provided backend.

        This method accepts the backend at runtime, supporting scenarios where
        the backend is only available within a resource context block.

        Args:
            backend: Backend responsible for processing user input
            initial_message: Optional message to process before starting loop
        """
        logger.debug("AsyncREPL.run() entry")

        # Set backend in action registry for action handlers to access
        self.action_registry.backend = backend  # type: ignore[attr-defined]

        if initial_message:
            print(self.prompt_string, end="")
            print(initial_message)
            await self._process_input(initial_message, backend)
            print()

        while True:
            try:
                user_input = await self.session.prompt_async()
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

        logger.debug("AsyncREPL.run() exit")

    def _should_exit(self, user_input: str) -> bool:
        """Check if input is an exit command."""
        logger.debug("AsyncREPL._should_exit() entry/exit")
        return user_input.strip().lower() in ["/exit", "/quit"]

    async def _process_input(self, user_input: str, backend: AsyncBackend):  # pragma: no cover
        """
        Process user input with cancellation support.

        Runs the backend processing task concurrently with a cancellation
        listener, allowing users to cancel long-running operations with
        Ctrl+C or Alt+C.

        Args:
            user_input: Input string to process
            backend: Backend to process the input
        """
        logger.debug("AsyncREPL._process_input() entry")

        cancel_future = asyncio.Future()  # type: ignore[var-annotated]

        kb = KeyBindings()

        # Alt+C cancellation
        @kb.add("escape", "c")
        def _(event):
            if not cancel_future.done():
                cancel_future.set_result(None)
            if not event.app.is_done:
                event.app.exit()

        # Ctrl+C cancellation
        @kb.add("c-c")
        def _(event):
            if not cancel_future.done():
                cancel_future.set_result(None)
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        cancel_app = Application(key_bindings=kb, output=DummyOutput(), input=create_input())  # type: ignore[var-annotated]

        # Prepare kwargs for backend - only pass images if present
        kwargs = {}
        if self._image_buffer:
            kwargs["images"] = self._image_buffer

        backend_task = asyncio.create_task(backend.handle_input(user_input, **kwargs))
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
                try:
                    await backend_task
                except asyncio.CancelledError:
                    pass
            else:
                success = backend_task.result()
                if not success:
                    print("Operation failed.")

        except KeyboardInterrupt:
            # Handle Ctrl+C during wait
            print("\nOperation cancelled by user (Ctrl+C).")
            backend_task.cancel()
            try:
                await backend_task
            except asyncio.CancelledError:
                pass
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            if not backend_task.done():
                backend_task.cancel()
                try:
                    await backend_task
                except asyncio.CancelledError:
                    pass

        finally:
            # Clear images after send (success or failure - backend's responsibility now)
            self._image_buffer.clear()

            # Cleanup
            if not cancel_app.is_done:
                cancel_app.exit()

            await listener_task

            self.main_app.renderer.reset()
            self.main_app.invalidate()
            await asyncio.sleep(0)

        logger.debug("AsyncREPL._process_input() exit")


# Convenience function
async def run_async_repl(  # pragma: no cover
    backend: AsyncBackend,
    action_registry: Optional[ActionHandler] = None,
    completer: Optional[Completer] = None,
    initial_message: Optional[str] = None,
    prompt_string: Optional[str] = None,
    history_path: Optional[Path] = None,
    **kwargs,
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
    logger.debug("run_async_repl() entry")

    repl = AsyncREPL(action_registry, completer, prompt_string, history_path, **kwargs)
    await repl.run(backend, initial_message)

    logger.debug("run_async_repl() exit")

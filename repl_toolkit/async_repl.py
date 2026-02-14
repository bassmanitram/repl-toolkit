"""
Async REPL interface with action support for repl_toolkit.

Provides an interactive chat interface with full UI features including
history, action handling (commands + keyboard shortcuts), and
robust cancellation of long-running tasks.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from prompt_toolkit import HTML, PromptSession
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.application import Application
from prompt_toolkit.history import FileHistory
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import print_formatted_text

from .actions import ActionContext, ActionRegistry
from .images import ImageData, create_paste_action
from .ptypes import AsyncBackend, CancellableBackend

logger = logging.getLogger(__name__)

THINKING_MESSAGE = HTML("<i><grey>Thinking... (Press Ctrl+C or Alt+C to cancel)</grey></i>")


class AsyncREPL:
    """
    Manages an interactive async REPL session with action support.

    Provides user input handling, action processing (commands and shortcuts),
    and robust cancellation of long-running tasks.

    The AsyncREPL supports late backend binding, allowing initialization without
    a backend for scenarios where the backend is only available within a resource
    context block.
    """

    def __init__(
        self,
        action_registry: Optional["ActionRegistry"] = None,
        completer: Any = None,
        prompt_string: Optional[str] = None,
        history_path: Optional[Path] = None,
        enable_image_paste: bool = True,
        **kwargs,
    ):
        """
        Initialize the async REPL interface.

        Args:
            action_registry: Action registry for commands and shortcuts
            completer: Optional tab-completion provider
            prompt_string: Custom prompt string (default: "User: ")
            history_path: Optional path for command history storage
            enable_image_paste: Enable image paste support (default: True)
        """
        self.prompt_string = HTML(prompt_string or "User: ")
        self._image_buffer: Dict[str, ImageData] = {}
        self._image_counter = 0

        # Create ActionRegistry with prompt_toolkit printer
        if action_registry is None:
            action_registry = ActionRegistry(printer=lambda msg: print_formatted_text(msg))
        self.action_registry = action_registry

        # Register image paste action if enabled
        if enable_image_paste:
            self._register_image_paste_action()

        self.session: PromptSession = PromptSession(
            message=self.prompt_string,
            history=self._create_history(history_path),
            key_bindings=self._create_key_bindings(),
            multiline=True,
            completer=completer,
            **kwargs,
        )
        self.main_app = self.session.app

    def _register_image_paste_action(self) -> None:
        """Register the image paste action if available."""
        try:
            paste_action = create_paste_action()
            self.action_registry.register_action(paste_action)
        except Exception as e:
            logger.warning(f"Failed to register image paste action: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Image Management
    # ─────────────────────────────────────────────────────────────────────────

    def add_image(self, img_bytes: bytes, media_type: str) -> str:
        """Add image to buffer for next message send."""
        self._image_counter += 1
        image_id = f"img_{self._image_counter:03d}"
        self._image_buffer[image_id] = ImageData(
            data=img_bytes, media_type=media_type, timestamp=time.time()
        )
        logger.debug(f"Added image {image_id} ({media_type}, {len(img_bytes)} bytes)")
        return image_id

    def clear_images(self) -> None:
        """Clear all images from the buffer."""
        self._image_buffer.clear()

    def get_images(self) -> Dict[str, ImageData]:
        """Get current image buffer."""
        return self._image_buffer.copy()

    # ─────────────────────────────────────────────────────────────────────────
    # Session Setup
    # ─────────────────────────────────────────────────────────────────────────

    def _create_history(self, path: Optional[Path]) -> Optional[FileHistory]:
        """Create file history if path is provided."""
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            return FileHistory(str(path))
        return None

    def _create_key_bindings(self) -> KeyBindings:
        """Create key bindings for the REPL session."""
        bindings = KeyBindings()

        @bindings.add("enter")
        def handle_enter(event):
            """Execute command or add new line."""
            buffer_text = event.app.current_buffer.text
            if self.action_registry.is_registered_command(buffer_text):
                event.app.current_buffer.validate_and_handle()
            else:
                event.app.current_buffer.insert_text("\n")

        @bindings.add(Keys.Escape, "enter")
        def handle_alt_enter(event):
            """Send message with Alt+Enter."""
            event.app.current_buffer.validate_and_handle()

        @bindings.add(Keys.F7)
        @bindings.add(Keys.Escape, Keys.Escape)
        def handle_clear(event):
            """Clear buffer with F7 or Escape Escape."""
            event.app.current_buffer.reset()

        self._register_action_shortcuts(bindings)
        return bindings

    def _register_action_shortcuts(self, bindings: KeyBindings) -> None:
        """Register keyboard shortcuts from the action registry."""
        if not hasattr(self.action_registry, "key_map"):
            return

        for key_combo, action_name in self.action_registry.key_map.items():
            self._register_shortcut(bindings, key_combo, action_name)

    def _register_shortcut(self, bindings: KeyBindings, key_combo: str, action_name: str) -> None:
        """Register a single keyboard shortcut."""
        try:
            keys = self._parse_key_combination(key_combo)

            @bindings.add(*keys)
            def handle_shortcut(event, action=action_name):
                try:
                    context = ActionContext(
                        registry=self.action_registry,
                        repl=self,
                        buffer=event.current_buffer,
                        backend=getattr(self.action_registry, "backend", None),
                        event=event,
                        triggered_by="shortcut",
                    )
                    self.action_registry.execute_action(action, context)
                except Exception:
                    logger.exception(f"Error executing shortcut '{key_combo}'")

        except Exception as e:
            logger.error(f"Failed to register shortcut '{key_combo}': {e}")

    def _parse_key_combination(self, key_combo: str) -> tuple:
        """Parse key combination string into prompt_toolkit format."""
        key_combo = key_combo.lower().strip()

        # Function keys (F1, F2, etc.)
        if key_combo.startswith("f") and key_combo[1:].isdigit():
            return (key_combo,)

        # Modifier combinations
        if "-" in key_combo:
            parts = key_combo.split("-")
            if len(parts) == 3:
                return (key_combo,)
            if len(parts) == 2:
                modifier, key = parts
                if modifier == "ctrl":
                    return ("c-" + key,)
                elif modifier == "alt":
                    return (Keys.Escape, key)
                elif modifier == "shift":
                    return ("s-" + key,)

        return (key_combo,)

    # ─────────────────────────────────────────────────────────────────────────
    # Main REPL Loop
    # ─────────────────────────────────────────────────────────────────────────

    async def run(self, backend: AsyncBackend, initial_message: Optional[str] = None):
        """
        Run the async REPL session with the provided backend.

        Args:
            backend: Backend responsible for processing user input
            initial_message: Optional message to process before starting loop
        """
        self.action_registry.backend = backend

        if initial_message:
            print(self.prompt_string, end="")
            print(initial_message)
            await self._process_input(initial_message, backend)
            print()

        while True:
            try:
                with patch_stdout():
                    user_input = await self.session.prompt_async()

                if self._is_exit_command(user_input):
                    break
                if not user_input.strip():
                    continue
                if user_input.strip().startswith("/"):
                    self.action_registry.handle_command(user_input.strip())
                    await asyncio.sleep(0)  # Yield for async cleanup
                    continue

                await self._process_input(user_input, backend)

            except (KeyboardInterrupt, EOFError):
                print()
                break
            except Exception:
                logger.exception("Error in REPL loop")

    def _is_exit_command(self, user_input: str) -> bool:
        """Check if input is an exit command."""
        return user_input.strip().lower() in ["/exit", "/quit"]

    # ─────────────────────────────────────────────────────────────────────────
    # Input Processing with Cancellation
    # ─────────────────────────────────────────────────────────────────────────

    async def _process_input(self, user_input: str, backend: AsyncBackend):
        """
        Process user input with cancellation support.

        Runs the backend processing task concurrently with a cancellation
        listener, allowing users to cancel long-running operations.
        """
        async with self._cancellation_context() as ctx:
            kwargs = self._build_backend_kwargs(ctx["trigger_cancel"])
            backend_task = asyncio.create_task(backend.handle_input(user_input, **kwargs))

            print(THINKING_MESSAGE)

            done, _ = await asyncio.wait(
                [backend_task, ctx["cancel_future"]],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if ctx["cancel_future"] in done:
                await self._handle_cancellation(backend_task, backend)
            elif backend_task in done:
                try:
                    success = backend_task.result()
                    if not success:
                        print("Operation failed.")
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("Backend task raised exception")

    @asynccontextmanager
    async def _cancellation_context(self):
        """
        Context manager for cancellation support.

        Sets up the cancel future, cancel app, and cleanup logic.
        Yields a dict with cancel_future and trigger_cancel callback.
        """
        loop = asyncio.get_event_loop()
        cancel_future: asyncio.Future = asyncio.Future()
        cancel_app: Optional[Application] = None
        listener_task: Optional[asyncio.Task] = None

        def trigger_cancel():
            """Thread-safe callback for tools to trigger cancellation."""

            def _set_cancel():
                if not cancel_future.done():
                    cancel_future.set_result(None)

            loop.call_soon_threadsafe(_set_cancel)

        try:
            cancel_app = self._create_cancel_app(cancel_future)
            listener_task = asyncio.create_task(cancel_app.run_async())

            yield {
                "cancel_future": cancel_future,
                "trigger_cancel": trigger_cancel,
            }

        except KeyboardInterrupt:
            logger.debug("KeyboardInterrupt during input processing")
            if not cancel_future.done():
                cancel_future.set_result(None)

        except Exception:
            logger.exception("Error during input processing")

        finally:
            self._image_buffer.clear()
            await self._cleanup_cancel_context(cancel_app, listener_task)
            self._reset_ui()

    def _create_cancel_app(self, cancel_future: asyncio.Future) -> Application:
        """Create the cancellation key bindings application."""
        kb = KeyBindings()

        @kb.add("escape", "c")
        def handle_alt_c(event):
            if not cancel_future.done():
                cancel_future.set_result(None)
            if not event.app.is_done:
                event.app.exit()

        @kb.add("c-c")
        def handle_ctrl_c(event):
            if not cancel_future.done():
                cancel_future.set_result(None)
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        return Application(key_bindings=kb, output=DummyOutput(), input=create_input())

    def _build_backend_kwargs(self, trigger_cancel: Callable[[], None]) -> Dict[str, Any]:
        """Build kwargs dict for backend.handle_input()."""
        kwargs: Dict[str, Any] = {"cancel_callback": trigger_cancel}
        if self._image_buffer:
            kwargs["images"] = self._image_buffer
        return kwargs

    async def _handle_cancellation(self, backend_task: asyncio.Task, backend: AsyncBackend) -> None:
        """Handle cancellation of the backend task."""
        print("\nOperation cancelled by user.")

        # Signal cancellation to backend if it supports it
        if isinstance(backend, CancellableBackend):
            try:
                backend.cancel("Operation cancelled by user")
            except Exception as e:
                logger.error(f"Error signaling cancellation to backend: {e}")

        # Cancel the asyncio task
        if backend_task and not backend_task.done():
            backend_task.cancel()
            try:
                await backend_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_cancel_context(
        self, cancel_app: Optional[Application], listener_task: Optional[asyncio.Task]
    ) -> None:
        """Cleanup the cancellation app and listener task."""
        try:
            if cancel_app and not cancel_app.is_done:
                cancel_app.exit()

            if listener_task and not listener_task.done():
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            logger.debug(f"Cleanup exception (non-fatal): {e}")

    def _reset_ui(self) -> None:
        """Reset the UI after processing."""
        try:
            self.main_app.renderer.reset()
            self.main_app.invalidate()
        except Exception as e:
            logger.debug(f"UI reset exception (non-fatal): {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Function
# ─────────────────────────────────────────────────────────────────────────────


async def run_async_repl(
    backend: AsyncBackend,
    action_registry: Optional["ActionRegistry"] = None,
    completer: Any = None,
    initial_message: Optional[str] = None,
    prompt_string: Optional[str] = None,
    history_path: Optional[Path] = None,
    **kwargs,
):
    """
    Convenience function to create and run an AsyncREPL with action support.

    Args:
        backend: Backend for processing input
        action_registry: Action registry for commands and shortcuts
        completer: Optional completer
        initial_message: Optional initial message
        prompt_string: Optional custom prompt
        history_path: Optional history file path
    """
    repl = AsyncREPL(action_registry, completer, prompt_string, history_path, **kwargs)
    await repl.run(backend, initial_message)

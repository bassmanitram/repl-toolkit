from typing import Optional

from loguru import logger

from .actions.registry import ActionRegistry
from .ptypes import ActionHandler, AsyncBackend


class HeadlessREPL:
    """
    Headless REPL that reads from stdin and processes through action framework.

    Similar to interactive mode but:
    - Reads from stdin instead of prompt_toolkit
    - Accumulates content in buffer until /send
    - Processes commands through action system
    - Supports multiple /send cycles
    - Auto-sends remaining buffer on EOF
    """

    def __init__(self, action_registry: Optional[ActionHandler] = None):
        """Initialize headless REPL."""
        logger.trace("HeadlessREPL.__init__() entry")

        # Simple string buffer for content accumulation
        self.buffer = ""
        self.action_registry = action_registry or ActionRegistry()

        # State tracking
        self.send_count = 0
        self.total_success = True
        self.running = True

        logger.trace("HeadlessREPL.__init__() exit")

    async def run(self, backend: AsyncBackend, initial_message: Optional[str] = None) -> bool:
        """
        Run headless mode with stdin processing.

        Args:
            backend: Backend for processing input
            initial_message: Optional message to process before stdin loop

        Returns:
            bool: True if all operations succeeded
        """
        logger.trace("HeadlessREPL.run() entry")

        # Set backend in action registry
        self.action_registry.backend = backend  # type: ignore[attr-defined]

        try:
            # Process initial message if provided
            if initial_message:
                logger.info(f"Processing initial message: {initial_message}")
                success = await backend.handle_input(initial_message)
                if not success:
                    logger.warning("Initial message processing failed")
                    self.total_success = False

            # Enter stdin processing loop
            await self._stdin_loop(backend)

            logger.trace("HeadlessREPL.run() exit - success")
            return self.total_success

        except Exception as e:
            logger.error(f"Error in headless processing: {e}")
            logger.trace("HeadlessREPL.run() exit - exception")
            return False

    async def _stdin_loop(self, backend: AsyncBackend):
        """
        Process stdin with synchronous reading, async backend calls.

        Reads lines from stdin synchronously (blocking), processes commands
        through the action system, and accumulates content in buffer until
        /send commands trigger backend processing.

        Args:
            backend: Backend for processing accumulated content
        """
        import sys

        line_num = 0

        while True:
            # Simple synchronous readline - blocks until line available
            # This is perfectly fine! We want to wait for the next line.
            line = sys.stdin.readline()

            if not line:  # EOF
                break

            line_num += 1
            line = line.rstrip("\n\r")

            if line.startswith("/"):
                if line == "/send":
                    await self._execute_send(backend, f"line {line_num}")
                else:
                    # Synchronous command processing
                    self._execute_command(line)
            else:
                # Synchronous buffer addition
                self._add_to_buffer(line)

        await self._handle_eof(backend)

    def _add_to_buffer(self, line: str):
        """
        Add a line to the buffer.

        Args:
            line: Line of text to add to the buffer
        """
        logger.trace("HeadlessREPL._add_to_buffer() entry")

        if self.buffer:
            self.buffer += "\n" + line
        else:
            self.buffer = line

        logger.debug(f"Added line to buffer, total length: {len(self.buffer)}")
        logger.trace("HeadlessREPL._add_to_buffer() exit")

    async def _execute_send(self, backend: AsyncBackend, context_info: str):
        """
        Execute /send command - send buffer to backend and wait.

        Args:
            backend: Backend to send buffer content to
            context_info: Context information for logging (e.g., "line 5", "EOF")
        """
        logger.trace("HeadlessREPL._execute_send() entry")

        buffer_content = self.buffer.strip()

        if not buffer_content:
            logger.debug(f"Send #{self.send_count + 1} at {context_info}: empty buffer, skipping")
            logger.trace("HeadlessREPL._execute_send() exit - empty buffer")
            return

        self.send_count += 1
        logger.info(
            f"Send #{self.send_count} at {context_info}: sending {len(buffer_content)} characters"
        )

        try:
            # Send to backend and wait for completion
            success = await backend.handle_input(buffer_content)

            if success:
                logger.info(f"Send #{self.send_count} completed successfully")
            else:
                logger.warning(f"Send #{self.send_count} completed with backend reporting failure")
                self.total_success = False

            # Clear buffer after send (successful or not)
            self.buffer = ""

        except Exception as e:
            logger.error(f"Send #{self.send_count} failed with exception: {e}")
            self.total_success = False
            # Clear buffer even on exception to continue processing
            self.buffer = ""

        logger.trace("HeadlessREPL._execute_send() exit")

    def _execute_command(self, command: str):
        """
        Execute a command through the action system.

        Args:
            command: Command string to execute (e.g., "/help", "/shortcuts")
        """
        logger.trace("HeadlessREPL._execute_command() entry")

        try:
            self.action_registry.handle_command(command, headless_mode=True, buffer=self.buffer)

        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            # Don't fail entire process for command errors

        logger.trace("HeadlessREPL._execute_command() exit")

    async def _handle_eof(self, backend: AsyncBackend):
        """
        Handle end of stdin - send remaining buffer if not empty.

        Args:
            backend: Backend to send remaining buffer content to
        """
        logger.trace("HeadlessREPL._handle_eof() entry")

        buffer_content = self.buffer.strip()

        if buffer_content:
            logger.info("EOF reached with non-empty buffer, triggering final send")
            await self._execute_send(backend, "EOF")
        else:
            logger.debug("EOF reached with empty buffer")

        logger.trace("HeadlessREPL._handle_eof() exit")


async def run_headless_mode(
    backend: AsyncBackend,
    action_registry: Optional[ActionHandler] = None,
    initial_message: Optional[str] = None,
) -> bool:
    """
    Run headless mode reading from stdin with action framework support.

    Processes an optional initial message, then reads from stdin line by line.
    Content lines are accumulated in a buffer, commands are processed through
    the action system, and /send commands trigger backend processing.

    Args:
        backend: Backend for processing input
        action_registry: Optional action registry for command processing
        initial_message: Optional message to process before stdin loop

    Returns:
        bool: True if all send operations succeeded

    Example:
        # stdin input:
        # Message part 1
        # Message part 2
        # /send           # Send parts 1-2, wait for completion
        # Message part 3
        # /help           # Process command
        # Message part 4
        # /send           # Send parts 3-4, wait for completion
        # Final message
        # ^D              # EOF triggers final send

        success = await run_headless_mode(
            backend=my_backend,
            initial_message="Starting headless session"
        )
    """
    logger.trace("run_headless_mode() entry")

    headless_repl = HeadlessREPL(action_registry)
    result = await headless_repl.run(backend, initial_message)

    logger.trace("run_headless_mode() exit")
    return result

#!/usr/bin/env python3
"""
CancellableBackend protocol example.

Demonstrates how to implement cooperative cancellation support
for backends that perform long-running or blocking operations.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Add repl_toolkit to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from repl_toolkit import CancellableBackend, run_async_repl


class LongRunningBackend(CancellableBackend):
    """
    Example backend with long-running operations that supports cancellation.

    Demonstrates the CancellableBackend protocol implementation:
    1. Implement cancel() method to set internal flag
    2. Check cancellation flag at safe checkpoints
    3. Reset flag at start of each operation
    4. Return False on cancellation to indicate failure
    """

    def __init__(self):
        self._cancelled = False
        self.operation_count = 0

    def cancel(self, message: str = None) -> None:
        """
        Signal cancellation to the backend.

        This method is called by the REPL when user presses Ctrl+C or Alt+C.
        It must be non-blocking and return immediately.
        """
        self._cancelled = True
        if message:
            logging.info(f"Cancellation requested: {message}")
        else:
            logging.info("Cancellation requested")

    async def handle_input(self, user_input: str, **kwargs) -> bool:
        """
        Process user input with cancellation checkpoints.

        Returns:
            bool: True if operation completed successfully, False if cancelled
        """
        # Reset cancellation flag at start of new operation
        self._cancelled = False
        self.operation_count += 1

        print(f"\n[Operation #{self.operation_count}] Starting to process: {user_input}")

        # Simulate long-running operation with multiple steps
        steps = [
            "Analyzing input...",
            "Fetching data...",
            "Processing results...",
            "Generating response...",
            "Finalizing output...",
        ]

        for i, step in enumerate(steps, 1):
            # Checkpoint: Check for cancellation before each step
            if self._cancelled:
                print(f"\n[Operation #{self.operation_count}] Cancelled at step {i}/{len(steps)}")
                print("Cleanup completed. Operation aborted.")
                return False

            print(f"  Step {i}/{len(steps)}: {step}")

            # Simulate work (in real backend, this would be API calls, DB queries, etc.)
            await asyncio.sleep(1.0)

        # Final check before returning result
        if self._cancelled:
            print(f"\n[Operation #{self.operation_count}] Cancelled before output")
            return False

        # Operation completed successfully
        print(f"\n[Operation #{self.operation_count}] Completed successfully!")
        print(f"Result: Processed '{user_input}' through {len(steps)} steps")
        return True


class BlockingOperationBackend(CancellableBackend):
    """
    Example backend that performs blocking operations (subprocesses, HTTP calls).

    Demonstrates cancellation with external processes that need to be killed.
    """

    def __init__(self):
        self._cancelled = False
        self._current_process = None

    def cancel(self, message: str = None) -> None:
        """Signal cancellation and kill any running subprocess."""
        self._cancelled = True
        logging.info(f"Cancellation: {message or 'User requested'}")

        # Kill any running subprocess
        if self._current_process:
            logging.info("Terminating subprocess...")
            try:
                self._current_process.terminate()
            except Exception as e:
                logging.error(f"Error terminating subprocess: {e}")

    async def handle_input(self, user_input: str, **kwargs) -> bool:
        """Process input with subprocess that can be cancelled."""
        self._cancelled = False
        self._current_process = None

        print(f"\nProcessing: {user_input}")

        # Simulate spawning a long-running subprocess
        print("Starting subprocess (simulated with sleep)...")

        # In real code, this would be:
        # self._current_process = await asyncio.create_subprocess_exec(...)

        for i in range(10):
            if self._cancelled:
                print("\nOperation cancelled - subprocess terminated")
                self._current_process = None
                return False

            print(f"  Subprocess running... ({i+1}/10)")
            await asyncio.sleep(0.5)

        self._current_process = None
        print("Subprocess completed successfully")
        return True


class CancellationTokenBackend(CancellableBackend):
    """
    Advanced example using a cancellation token class.

    This pattern is useful for complex backends with multiple components.
    """

    class CancellationToken:
        """Reusable cancellation token."""

        def __init__(self):
            self._cancelled = False
            self._message = None

        def cancel(self, message: str = None):
            """Mark as cancelled."""
            self._cancelled = True
            self._message = message

        def reset(self):
            """Reset for new operation."""
            self._cancelled = False
            self._message = None

        @property
        def is_cancelled(self) -> bool:
            """Check if cancelled."""
            return self._cancelled

        @property
        def message(self) -> str:
            """Get cancellation message."""
            return self._message or "Operation cancelled"

    def __init__(self):
        self._cancel_token = self.CancellationToken()

    def cancel(self, message: str = None) -> None:
        """Signal cancellation via token."""
        self._cancel_token.cancel(message)

    async def handle_input(self, user_input: str, **kwargs) -> bool:
        """Process with cancellation token."""
        self._cancel_token.reset()

        print(f"\nProcessing with token: {user_input}")

        # Pass token to helper methods
        return await self._process_with_token(user_input)

    async def _process_with_token(self, data: str) -> bool:
        """Helper method that checks cancellation token."""
        for i in range(5):
            if self._cancel_token.is_cancelled:
                print(f"\n{self._cancel_token.message}")
                return False

            print(f"  Processing step {i+1}/5...")
            await asyncio.sleep(0.8)

        print("Processing complete!")
        return True


async def main():
    """Run interactive demo with cancellable backend."""
    print("CancellableBackend Protocol Example")
    print("=" * 60)
    print()
    print("This demo shows cooperative cancellation support.")
    print()
    print("The backend performs a long-running operation (5 steps, 1s each).")
    print("You can cancel it at any time by pressing:")
    print("  - Ctrl+C (during operation)")
    print("  - Alt+C  (during operation)")
    print()
    print("Try it:")
    print("  1. Type some text and press Alt+Enter")
    print("  2. Wait a moment, then press Ctrl+C to cancel")
    print("  3. Observe the backend's cleanup message")
    print()
    print("Commands: /help, /exit")
    print("=" * 60)
    print()

    # Choose which backend to demo
    backend = LongRunningBackend()
    # backend = BlockingOperationBackend()
    # backend = CancellationTokenBackend()

    try:
        await run_async_repl(
            backend=backend,
            prompt_string="Cancellable: ",
        )
    except KeyboardInterrupt:
        print("\nGoodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

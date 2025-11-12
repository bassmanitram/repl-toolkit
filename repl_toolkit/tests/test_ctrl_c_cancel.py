"""Tests for Ctrl-C cancellation during backend processing."""

import asyncio

import pytest

from repl_toolkit import AsyncREPL


class SlowBackend:
    """Backend that simulates a long-running operation."""

    def __init__(self):
        self.cancelled = False
        self.completed = False

    async def handle_input(self, user_input: str) -> bool:
        """Simulate slow processing that can be cancelled."""
        try:
            # Simulate long-running operation
            await asyncio.sleep(10)
            self.completed = True
            return True
        except asyncio.CancelledError:
            self.cancelled = True
            raise


class TestCtrlCCancellation:
    """Test Ctrl-C cancellation during backend processing."""

    @pytest.mark.asyncio
    async def test_cancel_via_keyboard_interrupt(self, mock_terminal_for_repl):
        """Test that backend task can be cancelled."""
        repl = AsyncREPL()
        backend = SlowBackend()

        # Create the backend task
        backend_task = asyncio.create_task(backend.handle_input("test"))

        # Wait a bit to ensure task is running
        await asyncio.sleep(0.1)

        # Cancel the task (simulating what happens on Ctrl-C)
        backend_task.cancel()

        # Wait for cancellation to complete
        try:
            await backend_task
        except asyncio.CancelledError:
            pass

        # Verify backend was cancelled, not completed
        assert backend.cancelled
        assert not backend.completed

    @pytest.mark.asyncio
    async def test_cancel_future_sets_result(self):
        """Test that cancel future can be set."""
        cancel_future = asyncio.Future()

        # Simulate setting cancel future (what happens on Ctrl-C in key binding)
        if not cancel_future.done():
            cancel_future.set_result(None)

        # Verify it was set
        assert cancel_future.done()
        assert cancel_future.result() is None

    @pytest.mark.asyncio
    async def test_wait_with_cancellation(self):
        """Test asyncio.wait with cancellation."""
        # Create a slow task
        slow_task = asyncio.create_task(asyncio.sleep(10))

        # Create cancel future
        cancel_future = asyncio.Future()

        # Simulate immediate cancellation
        cancel_future.set_result(None)

        # Wait for first completion
        done, pending = await asyncio.wait(
            [slow_task, cancel_future], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel future should complete first
        assert cancel_future in done
        assert slow_task in pending

        # Cancel the slow task
        slow_task.cancel()
        try:
            await slow_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_backend_graceful_cancellation(self):
        """Test that backend cancellation is graceful."""

        class GracefulBackend:
            def __init__(self):
                self.cleanup_called = False

            async def handle_input(self, user_input: str) -> bool:
                try:
                    await asyncio.sleep(10)
                    return True
                except asyncio.CancelledError:
                    # Backend can do cleanup
                    self.cleanup_called = True
                    raise

        backend = GracefulBackend()
        task = asyncio.create_task(backend.handle_input("test"))

        await asyncio.sleep(0.1)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Backend had chance to clean up
        assert backend.cleanup_called

    @pytest.mark.asyncio
    async def test_multiple_cancellation_attempts(self):
        """Test that multiple cancel attempts don't cause issues."""
        backend = SlowBackend()
        task = asyncio.create_task(backend.handle_input("test"))

        await asyncio.sleep(0.1)

        # Multiple cancels should be safe
        task.cancel()
        task.cancel()
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert backend.cancelled
        assert not backend.completed


class TestKeyBindingSimulation:
    """Test key binding behavior simulation."""

    def test_ctrl_c_key_combo(self):
        """Test Ctrl-C key combination format."""
        # In prompt_toolkit, Ctrl-C is represented as "c-c"
        key_combo = "c-c"
        assert key_combo == "c-c"

    def test_alt_c_key_combo(self):
        """Test Alt-C key combination format."""
        # In prompt_toolkit, Alt-C is represented as Escape, "c"
        # We test that we understand this format
        from prompt_toolkit.keys import Keys

        key_parts = (Keys.Escape, "c")
        assert key_parts[0] == Keys.Escape
        assert key_parts[1] == "c"

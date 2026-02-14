"""
Tests for backend cancellation support.

Tests verify that backends implementing CancellableBackend protocol receive
cancellation signals appropriately while maintaining backward
compatibility with backends that only implement AsyncBackend.
"""

import asyncio
from typing import Dict, Optional

import pytest

from repl_toolkit import AsyncBackend
from repl_toolkit.images import ImageData


class CancellableBackend:
    """Test backend that supports cancellation."""

    def __init__(self):
        self._cancel_requested = False
        self.cancel_messages = []
        self.operations_completed = 0

    def cancel(self, message: Optional[str] = None):
        """Signal cancellation."""
        self._cancel_requested = True
        self.cancel_messages.append(message)

    async def handle_input(
        self, user_input: str, images: Optional[Dict[str, ImageData]] = None
    ) -> bool:
        """Process input with cancellation checkpoints."""
        # Reset flag at start
        self._cancel_requested = False

        # Simulate long-running operation with checkpoints
        for i in range(10):
            # Checkpoint: Check for cancellation at start of each iteration
            if self._cancel_requested:
                return False  # Cancelled

            await asyncio.sleep(0.01)  # Simulated work

        self.operations_completed += 1
        return True


class NonCancellableBackend:
    """Test backend without cancel() support (backward compatibility)."""

    def __init__(self):
        self.operations_completed = 0

    async def handle_input(
        self, user_input: str, images: Optional[Dict[str, ImageData]] = None
    ) -> bool:
        """Process input without cancellation support."""
        await asyncio.sleep(0.05)  # Simulated work
        self.operations_completed += 1
        return True


class TestBackendCancellation:
    """Test backend cancellation functionality."""

    def test_cancellable_backend_has_cancel_method(self):
        """Verify cancellable backend implements cancel()."""
        backend = CancellableBackend()
        assert hasattr(backend, "cancel")
        assert callable(backend.cancel)

    def test_non_cancellable_backend_no_cancel_method(self):
        """Verify non-cancellable backend doesn't have cancel()."""
        backend = NonCancellableBackend()
        assert not hasattr(backend, "cancel")

    def test_cancel_method_sets_flag(self):
        """Verify cancel() sets internal flag."""
        backend = CancellableBackend()
        assert not backend._cancel_requested

        backend.cancel("Test cancellation")
        assert backend._cancel_requested

    def test_cancel_method_records_message(self):
        """Verify cancel() records the message."""
        backend = CancellableBackend()

        backend.cancel("First cancel")
        assert backend.cancel_messages == ["First cancel"]

        backend.cancel("Second cancel")
        assert backend.cancel_messages == ["First cancel", "Second cancel"]

    def test_cancel_method_with_none_message(self):
        """Verify cancel() works with None message."""
        backend = CancellableBackend()

        backend.cancel(None)
        assert backend._cancel_requested
        assert backend.cancel_messages == [None]

    @pytest.mark.asyncio
    async def test_handle_input_respects_cancellation(self):
        """Verify handle_input() checks cancellation flag."""
        backend = CancellableBackend()

        # Start the operation
        task = asyncio.create_task(backend.handle_input("test input"))

        # Cancel immediately after starting
        await asyncio.sleep(0.005)  # Let it start
        backend.cancel("Mid-operation cancel")

        # Should return False (cancelled)
        result = await task
        assert result is False
        assert backend.operations_completed == 0

    @pytest.mark.asyncio
    async def test_handle_input_completes_without_cancellation(self):
        """Verify handle_input() completes normally without cancellation."""
        backend = CancellableBackend()

        result = await backend.handle_input("test input")
        assert result is True
        assert backend.operations_completed == 1

    @pytest.mark.asyncio
    async def test_cancellation_during_operation(self):
        """Verify cancellation works mid-operation."""
        backend = CancellableBackend()

        async def cancel_after_delay():
            await asyncio.sleep(0.02)  # Cancel after 2 iterations
            backend.cancel("Mid-operation cancel")

        # Run both tasks concurrently
        cancel_task = asyncio.create_task(cancel_after_delay())
        result = await backend.handle_input("test input")

        await cancel_task

        # Should be cancelled
        assert result is False
        assert backend.operations_completed == 0

    @pytest.mark.asyncio
    async def test_non_cancellable_backend_completes_normally(self):
        """Verify non-cancellable backend works without cancel()."""
        backend = NonCancellableBackend()

        result = await backend.handle_input("test input")
        assert result is True
        assert backend.operations_completed == 1

    def test_hasattr_check_pattern(self):
        """Verify hasattr() pattern works correctly."""
        cancellable = CancellableBackend()
        non_cancellable = NonCancellableBackend()

        # Pattern used in async_repl.py
        if hasattr(cancellable, "cancel"):
            cancellable.cancel("Test message")

        if hasattr(non_cancellable, "cancel"):
            # This should not execute
            pytest.fail("Non-cancellable backend should not have cancel()")

        # Verify cancellable backend received the message
        assert cancellable.cancel_messages == ["Test message"]

    @pytest.mark.asyncio
    async def test_multiple_operations_reset_flag(self):
        """Verify cancellation flag resets between operations."""
        backend = CancellableBackend()

        # First operation - cancel mid-operation
        task1 = asyncio.create_task(backend.handle_input("input 1"))
        await asyncio.sleep(0.02)
        backend.cancel("First cancel")
        result1 = await task1
        assert result1 is False

        # Second operation - should succeed (flag reset)
        result2 = await backend.handle_input("input 2")
        assert result2 is True
        assert backend.operations_completed == 1

    @pytest.mark.asyncio
    async def test_race_condition_cancel_after_completion(self):
        """Verify cancel() after completion is harmless."""
        backend = CancellableBackend()

        # Complete operation
        result = await backend.handle_input("test input")
        assert result is True

        # Cancel after completion (should be harmless)
        backend.cancel("Post-completion cancel")
        assert backend._cancel_requested  # Flag set but operation already done

        # Next operation should reset and work normally
        result2 = await backend.handle_input("test input 2")
        assert result2 is True
        assert backend.operations_completed == 2


class TestCancellationMessages:
    """Test cancellation message handling."""

    def test_alt_c_message(self):
        """Verify Alt+C cancellation message format."""
        backend = CancellableBackend()
        backend.cancel("Operation cancelled by user")
        assert backend.cancel_messages[0] == "Operation cancelled by user"

    def test_ctrl_c_message(self):
        """Verify Ctrl+C cancellation message format."""
        backend = CancellableBackend()
        backend.cancel("Operation cancelled by user (Ctrl+C)")
        assert backend.cancel_messages[0] == "Operation cancelled by user (Ctrl+C)"

    def test_error_cancellation_message(self):
        """Verify error cancellation message format."""
        backend = CancellableBackend()
        backend.cancel("Operation cancelled due to error")
        assert backend.cancel_messages[0] == "Operation cancelled due to error"


class TestProtocolConformance:
    """Test that cancellable backends conform to AsyncBackend protocol."""

    def test_cancellable_backend_is_async_backend(self):
        """Verify cancellable backend conforms to protocol."""
        backend = CancellableBackend()
        # Protocol check via isinstance
        assert isinstance(backend, AsyncBackend)


class TestHasattrPattern:
    """Test the hasattr() pattern used in async_repl.py."""

    def test_hasattr_pattern_with_cancellable_backend(self):
        """Verify hasattr pattern works with cancellable backend."""
        backend = CancellableBackend()

        # This is the pattern used in async_repl.py
        if hasattr(backend, "cancel"):
            backend.cancel("Test cancellation")

        assert backend.cancel_messages == ["Test cancellation"]

    def test_hasattr_pattern_with_non_cancellable_backend(self):
        """Verify hasattr pattern safely skips non-cancellable backend."""
        backend = NonCancellableBackend()

        # This is the pattern used in async_repl.py
        if hasattr(backend, "cancel"):
            # Should not execute
            pytest.fail("Should not call cancel() on non-cancellable backend")

        # Should reach here safely
        assert True

    def test_no_attribute_error_on_non_cancellable_backend(self):
        """Verify no AttributeError is raised for non-cancellable backend."""
        backend = NonCancellableBackend()

        # Should not raise AttributeError
        try:
            if hasattr(backend, "cancel"):
                backend.cancel("Should not execute")
        except AttributeError:
            pytest.fail("hasattr pattern should not raise AttributeError")

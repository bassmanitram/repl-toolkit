"""
Tests for headless mode functionality with action framework support.
"""

import asyncio
from io import StringIO
from unittest.mock import AsyncMock, Mock, patch

import pytest

from repl_toolkit.actions import Action, ActionRegistry
from repl_toolkit.headless_repl import HeadlessREPL, run_headless_mode


class MockAsyncBackend:
    """Mock backend for headless testing."""

    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.inputs_received = []
        self.call_count = 0

    async def handle_input(self, user_input: str) -> bool:
        self.inputs_received.append(user_input)
        self.call_count += 1
        # Simulate some processing time
        await asyncio.sleep(0.01)
        return self.should_succeed


class TestHeadlessREPL:
    """Test HeadlessREPL class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockAsyncBackend()
        self.action_registry = ActionRegistry()

    def test_headless_repl_initialization(self):
        """Test HeadlessREPL initialization."""
        repl = HeadlessREPL()

        assert repl.buffer == ""
        assert repl.send_count == 0
        assert repl.total_success is True
        assert repl.running is True
        assert isinstance(repl.action_registry, ActionRegistry)

    def test_headless_repl_with_custom_registry(self):
        """Test HeadlessREPL with custom action registry."""
        custom_registry = ActionRegistry()
        repl = HeadlessREPL(action_registry=custom_registry)

        assert repl.action_registry is custom_registry

    def test_add_to_buffer(self):
        """Test buffer management."""
        repl = HeadlessREPL()

        # Add first line
        repl._add_to_buffer("Line 1")
        assert repl.buffer == "Line 1"

        # Add second line
        repl._add_to_buffer("Line 2")
        assert repl.buffer == "Line 1\nLine 2"

        # Add empty line
        repl._add_to_buffer("")
        assert repl.buffer == "Line 1\nLine 2\n"

    @pytest.mark.asyncio
    async def test_execute_send_with_content(self):
        """Test /send execution with buffer content."""
        repl = HeadlessREPL()
        repl._add_to_buffer("Test content")

        await repl._execute_send(self.backend, "test")

        assert repl.send_count == 1
        assert repl.buffer == ""  # Buffer cleared after send
        assert self.backend.inputs_received == ["Test content"]
        assert repl.total_success is True

    @pytest.mark.asyncio
    async def test_execute_send_empty_buffer(self):
        """Test /send execution with empty buffer."""
        repl = HeadlessREPL()

        await repl._execute_send(self.backend, "test")

        assert repl.send_count == 0  # No send occurred
        assert repl.buffer == ""
        assert self.backend.inputs_received == []

    @pytest.mark.asyncio
    async def test_execute_send_backend_failure(self):
        """Test /send execution with backend failure."""
        self.backend.should_succeed = False
        repl = HeadlessREPL()
        repl._add_to_buffer("Test content")

        await repl._execute_send(self.backend, "test")

        assert repl.send_count == 1
        assert repl.buffer == ""  # Buffer still cleared
        assert repl.total_success is False  # Marked as failed
        assert self.backend.inputs_received == ["Test content"]

    @pytest.mark.asyncio
    async def test_execute_send_backend_exception(self):
        """Test /send execution with backend exception."""
        backend = AsyncMock()
        backend.handle_input.side_effect = Exception("Backend error")

        repl = HeadlessREPL()
        repl._add_to_buffer("Test content")

        await repl._execute_send(backend, "test")

        assert repl.send_count == 1
        assert repl.buffer == ""  # Buffer cleared even on exception
        assert repl.total_success is False

    @pytest.mark.asyncio
    async def test_handle_eof_with_content(self):
        """Test EOF handling with buffer content."""
        repl = HeadlessREPL()
        repl._add_to_buffer("Final content")

        await repl._handle_eof(self.backend)

        assert repl.send_count == 1
        assert repl.buffer == ""
        assert self.backend.inputs_received == ["Final content"]

    @pytest.mark.asyncio
    async def test_handle_eof_empty_buffer(self):
        """Test EOF handling with empty buffer."""
        repl = HeadlessREPL()

        await repl._handle_eof(self.backend)

        assert repl.send_count == 0
        assert self.backend.inputs_received == []

    def test_execute_command(self):
        """Test command execution through action system."""
        executed_commands = []

        def mock_handle_command(command, **kwargs):
            executed_commands.append((command, kwargs))

        repl = HeadlessREPL()
        repl.action_registry.handle_command = mock_handle_command

        repl._execute_command("/test arg1 arg2")

        assert len(executed_commands) == 1
        command, kwargs = executed_commands[0]
        assert command == "/test arg1 arg2"
        assert kwargs["headless_mode"] is True
        assert kwargs["buffer"] == ""

    def test_execute_command_with_buffer(self):
        """Test command execution with buffer content."""
        executed_commands = []

        def mock_handle_command(command, **kwargs):
            executed_commands.append((command, kwargs))

        repl = HeadlessREPL()
        repl.action_registry.handle_command = mock_handle_command
        repl._add_to_buffer("Buffer content")

        repl._execute_command("/status")

        assert len(executed_commands) == 1
        command, kwargs = executed_commands[0]
        assert command == "/status"
        assert kwargs["buffer"] == "Buffer content"

    def test_execute_command_exception(self):
        """Test command execution with exception."""

        def mock_handle_command(command, **kwargs):
            raise Exception("Command error")

        repl = HeadlessREPL()
        repl.action_registry.handle_command = mock_handle_command

        # Should not raise exception
        repl._execute_command("/error")

        # REPL should continue functioning
        assert repl.buffer == ""

    @pytest.mark.asyncio
    async def test_run_with_initial_message(self):
        """Test run with initial message."""
        repl = HeadlessREPL()

        with patch.object(repl, "_stdin_loop") as mock_stdin_loop:
            result = await repl.run(self.backend, "Initial message")

            assert result is True
            assert repl.action_registry.backend is self.backend
            assert self.backend.inputs_received == ["Initial message"]
            mock_stdin_loop.assert_called_once_with(self.backend)

    @pytest.mark.asyncio
    async def test_run_without_initial_message(self):
        """Test run without initial message."""
        repl = HeadlessREPL()

        with patch.object(repl, "_stdin_loop") as mock_stdin_loop:
            result = await repl.run(self.backend)

            assert result is True
            assert self.backend.inputs_received == []
            mock_stdin_loop.assert_called_once_with(self.backend)

    @pytest.mark.asyncio
    async def test_run_initial_message_failure(self):
        """Test run with initial message backend failure."""
        self.backend.should_succeed = False
        repl = HeadlessREPL()

        with patch.object(repl, "_stdin_loop") as mock_stdin_loop:
            result = await repl.run(self.backend, "Initial message")

            assert result is False  # Overall failure due to initial message
            assert self.backend.inputs_received == ["Initial message"]
            mock_stdin_loop.assert_called_once_with(self.backend)

    @pytest.mark.asyncio
    async def test_run_exception_handling(self):
        """Test run with exception in stdin loop."""
        repl = HeadlessREPL()

        def mock_stdin_loop(backend):
            raise Exception("stdin error")

        with patch.object(repl, "_stdin_loop", side_effect=mock_stdin_loop):
            result = await repl.run(self.backend)

            assert result is False


class TestStdinProcessing:
    """Test stdin processing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockAsyncBackend()

    @pytest.mark.asyncio
    async def test_stdin_loop_simple_send(self):
        """Test stdin loop with simple content and send."""
        stdin_input = "Line 1\nLine 2\n/send\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 1
        assert repl.buffer == ""  # Cleared after send
        assert self.backend.inputs_received == ["Line 1\nLine 2"]

    @pytest.mark.asyncio
    async def test_stdin_loop_multiple_sends(self):
        """Test stdin loop with multiple send cycles."""
        stdin_input = "Line 1\nLine 2\n/send\nLine 3\nLine 4\n/send\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 2
        assert repl.buffer == ""
        assert self.backend.inputs_received == ["Line 1\nLine 2", "Line 3\nLine 4"]

    @pytest.mark.asyncio
    async def test_stdin_loop_eof_with_content(self):
        """Test stdin loop with EOF and remaining content."""
        stdin_input = "Line 1\nLine 2\n"  # No /send, just EOF

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 1  # EOF triggered send
        assert repl.buffer == ""
        assert self.backend.inputs_received == ["Line 1\nLine 2"]

    @pytest.mark.asyncio
    async def test_stdin_loop_commands_between_content(self):
        """Test stdin loop with commands between content."""
        stdin_input = "Line 1\n/help\nLine 2\n/send\n"

        executed_commands = []

        def mock_handle_command(command, **kwargs):
            executed_commands.append(command)

        repl = HeadlessREPL()
        repl.action_registry.handle_command = mock_handle_command

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 1
        assert self.backend.inputs_received == ["Line 1\nLine 2"]
        assert executed_commands == ["/help"]

    @pytest.mark.asyncio
    async def test_stdin_loop_empty_lines(self):
        """Test stdin loop with empty lines."""
        stdin_input = "Line 1\n\nLine 2\n/send\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert self.backend.inputs_received == ["Line 1\n\nLine 2"]

    @pytest.mark.asyncio
    async def test_stdin_loop_only_commands(self):
        """Test stdin loop with only commands, no content."""
        stdin_input = "/help\n/status\n/send\n"

        executed_commands = []

        def mock_handle_command(command, **kwargs):
            executed_commands.append(command)

        repl = HeadlessREPL()
        repl.action_registry.handle_command = mock_handle_command

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 0  # No send because buffer was empty
        assert self.backend.inputs_received == []
        assert executed_commands == ["/help", "/status"]

    @pytest.mark.asyncio
    async def test_stdin_loop_keyboard_interrupt(self):
        """Test stdin loop with KeyboardInterrupt - should NOT send buffer."""
        repl = HeadlessREPL()
        repl._add_to_buffer("Interrupted content")

        def mock_readline():
            raise KeyboardInterrupt()

        with patch("sys.stdin.readline", side_effect=mock_readline):
            # KeyboardInterrupt should be caught and handled gracefully
            try:
                await repl._stdin_loop(self.backend)
            except (KeyboardInterrupt, Exception):
                pass  # Expected behavior - KeyboardInterrupt propagates

        # KeyboardInterrupt should NOT trigger EOF handling or send buffer
        assert repl.send_count == 0  # No sends should occur
        assert self.backend.inputs_received == []  # No content should be sent
        assert repl.buffer == "Interrupted content"  # Buffer should remain intact


class TestRunHeadlessMode:
    """Test run_headless_mode convenience function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockAsyncBackend()

    @pytest.mark.asyncio
    async def test_run_headless_mode_basic(self):
        """Test basic run_headless_mode functionality."""
        with patch("repl_toolkit.headless_repl.HeadlessREPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock(return_value=True)
            mock_repl_class.return_value = mock_repl

            result = await run_headless_mode(backend=self.backend, initial_message="test message")

            assert result is True
            mock_repl_class.assert_called_once_with(None)  # No custom registry
            mock_repl.run.assert_called_once_with(self.backend, "test message")

    @pytest.mark.asyncio
    async def test_run_headless_mode_with_registry(self):
        """Test run_headless_mode with custom action registry."""
        custom_registry = ActionRegistry()

        with patch("repl_toolkit.headless_repl.HeadlessREPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock(return_value=True)
            mock_repl_class.return_value = mock_repl

            result = await run_headless_mode(
                backend=self.backend,
                action_registry=custom_registry,
                initial_message="test message",
            )

            assert result is True
            mock_repl_class.assert_called_once_with(custom_registry)
            mock_repl.run.assert_called_once_with(self.backend, "test message")

    @pytest.mark.asyncio
    async def test_run_headless_mode_no_initial_message(self):
        """Test run_headless_mode without initial message."""
        with patch("repl_toolkit.headless_repl.HeadlessREPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock(return_value=True)
            mock_repl_class.return_value = mock_repl

            result = await run_headless_mode(backend=self.backend)

            assert result is True
            mock_repl.run.assert_called_once_with(self.backend, None)


class TestActionIntegration:
    """Test integration with action system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockAsyncBackend()
        self.executed_actions = []

        # Create custom action for testing
        def test_handler(context):
            self.executed_actions.append(
                {
                    "name": "test_action",
                    "args": context.args,
                    "triggered_by": context.triggered_by,
                    "headless_mode": getattr(context, "headless_mode", False),
                    "buffer": getattr(context, "buffer", None),
                }
            )

        self.test_action = Action(
            name="test_action",
            description="Test action for headless",
            category="Test",
            handler=test_handler,
            command="/test",
        )

    def test_action_execution_in_headless_mode(self):
        """Test action execution with headless context."""
        registry = ActionRegistry()
        registry.register_action(self.test_action)

        repl = HeadlessREPL(action_registry=registry)
        repl._add_to_buffer("Buffer content")

        repl._execute_command("/test arg1 arg2")

        assert len(self.executed_actions) == 1
        action_data = self.executed_actions[0]
        assert action_data["name"] == "test_action"
        assert action_data["args"] == ["arg1", "arg2"]
        assert action_data["triggered_by"] == "command"
        assert action_data["headless_mode"] is True
        assert action_data["buffer"] == "Buffer content"

    @pytest.mark.asyncio
    async def test_action_with_buffer_manipulation(self):
        """Test action that manipulates the buffer."""

        def buffer_action_handler(context):
            # Action that adds to buffer (if it has access)
            if hasattr(context, "buffer") and context.buffer:
                # In real implementation, actions might modify buffer
                # For test, just record what they received
                self.executed_actions.append(
                    {
                        "buffer_content": context.buffer,
                        "headless_mode": getattr(context, "headless_mode", False),
                    }
                )

        buffer_action = Action(
            name="buffer_action",
            description="Buffer manipulation action",
            category="Test",
            handler=buffer_action_handler,
            command="/buffer",
        )

        registry = ActionRegistry()
        registry.register_action(buffer_action)

        repl = HeadlessREPL(action_registry=registry)
        repl._add_to_buffer("Initial content")

        repl._execute_command("/buffer")

        assert len(self.executed_actions) == 1
        assert self.executed_actions[0]["buffer_content"] == "Initial content"
        assert self.executed_actions[0]["headless_mode"] is True

    @pytest.mark.asyncio
    async def test_builtin_actions_in_headless(self):
        """Test built-in actions work in headless mode."""
        repl = HeadlessREPL()

        # Test help action (should not raise exception)
        repl._execute_command("/help")

        # Test shortcuts action (should not raise exception)
        repl._execute_command("/shortcuts")


class TestErrorHandling:
    """Test error handling in headless mode."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockAsyncBackend()

    @pytest.mark.asyncio
    async def test_backend_error_recovery(self):
        """Test recovery from backend errors."""
        # Backend fails on first call, succeeds on second
        call_count = 0

        async def failing_handle_input(user_input):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False  # First call fails
            return True  # Second call succeeds

        backend = Mock()
        backend.handle_input = failing_handle_input

        stdin_input = "Content 1\n/send\nContent 2\n/send\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(backend)

        assert repl.send_count == 2
        assert repl.total_success is False  # One failure makes overall false

    @pytest.mark.asyncio
    async def test_command_error_recovery(self):
        """Test recovery from command execution errors."""

        def failing_command_handler(command, **kwargs):
            if "fail" in command:
                raise Exception("Command failed")

        repl = HeadlessREPL()
        repl.action_registry.handle_command = failing_command_handler

        stdin_input = "Content 1\n/fail\nContent 2\n/send\n"

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        # Should continue processing despite command error
        assert repl.send_count == 1
        assert self.backend.inputs_received == ["Content 1\nContent 2"]

    @pytest.mark.asyncio
    async def test_multiple_backend_failures(self):
        """Test handling multiple backend failures."""
        self.backend.should_succeed = False

        stdin_input = "Content 1\n/send\nContent 2\n/send\nContent 3\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 3  # All sends attempted
        assert repl.total_success is False
        assert len(self.backend.inputs_received) == 3


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockAsyncBackend()

    @pytest.mark.asyncio
    async def test_mixed_content_and_commands(self):
        """Test mixed content and commands scenario."""
        stdin_input = """First line
/help
Second line
/status
Third line
/send
Fourth line
Fifth line
"""

        executed_commands = []

        def mock_handle_command(command, **kwargs):
            executed_commands.append(command)

        repl = HeadlessREPL()
        repl.action_registry.handle_command = mock_handle_command

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        # Should have two sends: one explicit, one EOF
        assert repl.send_count == 2
        assert self.backend.inputs_received == [
            "First line\nSecond line\nThird line",
            "Fourth line\nFifth line",
        ]
        assert executed_commands == ["/help", "/status"]

    @pytest.mark.asyncio
    async def test_empty_sends_and_content(self):
        """Test scenario with empty sends and content."""
        stdin_input = "/send\nContent\n/send\n/send\nMore content\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        # Only 2 actual sends (empty buffer sends are skipped)
        assert repl.send_count == 2
        assert self.backend.inputs_received == ["Content", "More content"]

    @pytest.mark.asyncio
    async def test_large_content_blocks(self):
        """Test handling of large content blocks."""
        # Create large content block
        large_content = "\n".join([f"Line {i}" for i in range(1000)])
        stdin_input = f"{large_content}\n/send\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 1
        assert len(self.backend.inputs_received) == 1
        assert len(self.backend.inputs_received[0].split("\n")) == 1000

    @pytest.mark.asyncio
    async def test_rapid_send_cycles(self):
        """Test rapid send cycles."""
        # Multiple quick send cycles
        stdin_input = ""
        for i in range(10):
            stdin_input += f"Content {i}\n/send\n"

        repl = HeadlessREPL()

        with patch("sys.stdin", StringIO(stdin_input)):
            await repl._stdin_loop(self.backend)

        assert repl.send_count == 10
        assert len(self.backend.inputs_received) == 10
        for i in range(10):
            assert self.backend.inputs_received[i] == f"Content {i}"

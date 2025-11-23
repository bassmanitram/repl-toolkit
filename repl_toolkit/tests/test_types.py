"""
Tests for protocol compliance and type checking.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from repl_toolkit.actions import ActionRegistry
from repl_toolkit.ptypes import ActionHandler, AsyncBackend, Completer


class TestProtocolCompliance:
    """Test protocol compliance for various interfaces."""

    def test_async_backend_protocol(self):
        """Test AsyncBackend protocol compliance."""

        class TestAsyncBackend:
            async def handle_input(self, user_input: str) -> bool:
                return True

        backend = TestAsyncBackend()
        assert isinstance(backend, AsyncBackend)
        assert hasattr(backend, "handle_input")

    def test_action_handler_protocol(self):
        """Test ActionHandler protocol compliance."""

        class TestActionHandler:
            def execute_action(self, action_name: str, context) -> None:
                pass

            def handle_command(self, command: str) -> None:
                pass

            def validate_action(self, action_name: str) -> bool:
                return True

            def list_actions(self) -> list:
                return []

        handler = TestActionHandler()
        assert isinstance(handler, ActionHandler)
        assert hasattr(handler, "execute_action")
        assert hasattr(handler, "handle_command")
        assert hasattr(handler, "validate_action")
        assert hasattr(handler, "list_actions")

    def test_completer_protocol(self):
        """Test Completer protocol compliance."""

        class TestCompleter:
            def get_completions(self, document, complete_event):
                return []

        completer = TestCompleter()
        assert isinstance(completer, Completer)
        assert hasattr(completer, "get_completions")


class TestMockBackendCompliance:
    """Test mock backend implementations for protocol compliance."""

    def test_mock_backend_async_protocol(self):
        """Test mock backend implements AsyncBackend protocol."""
        mock_backend = Mock(spec=AsyncBackend)
        mock_backend.handle_input = AsyncMock(return_value=True)

        # Should have required method
        assert hasattr(mock_backend, "handle_input")
        assert callable(mock_backend.handle_input)

    @pytest.mark.asyncio
    async def test_mock_backend_functionality(self):
        """Test mock backend functionality."""
        mock_backend = Mock(spec=AsyncBackend)
        mock_backend.handle_input = AsyncMock(return_value=True)

        result = await mock_backend.handle_input("test input")
        assert result is True
        mock_backend.handle_input.assert_called_once_with("test input")


class TestRegistryProtocolCompliance:
    """Test ActionRegistry protocol compliance."""

    def setup_method(self):
        """Set up test registry."""
        self.registry = ActionRegistry()

    def test_implements_action_handler(self):
        """Test registry implements ActionHandler protocol."""
        assert isinstance(self.registry, ActionHandler)

    def test_execute_action_method(self):
        """Test execute_action method signature."""
        from repl_toolkit.actions import ActionContext

        context = ActionContext(registry=self.registry)

        # Should not raise error for built-in action
        self.registry.execute_action("show_help", context)

    def test_handle_command_method(self):
        """Test handle_command method signature."""
        # Should not raise error for unknown command (now synchronous)
        self.registry.handle_command("/unknown")

    def test_validate_action_method(self):
        """Test validate_action method signature."""
        assert self.registry.validate_action("show_help") is True
        assert self.registry.validate_action("nonexistent") is False

    def test_list_actions_method(self):
        """Test list_actions method signature."""
        actions = self.registry.list_actions()
        assert isinstance(actions, list)
        assert len(actions) > 0


class TestBackendUsagePatterns:
    """Test common backend usage patterns for both interactive and headless modes."""

    def test_backend_for_interactive_mode(self):
        """Test backend suitable for interactive mode."""

        class InteractiveBackend:
            async def handle_input(self, user_input: str) -> bool:
                # Interactive backends might do complex processing
                print(f"Processing: {user_input}")
                return True

        backend = InteractiveBackend()
        assert isinstance(backend, AsyncBackend)

    def test_backend_for_headless_mode(self):
        """Test backend suitable for headless mode."""

        class HeadlessBackend:
            def __init__(self):
                self.results = []

            async def handle_input(self, user_input: str) -> bool:
                # Headless backends might accumulate results
                self.results.append(f"Processed: {user_input}")
                return True

        backend = HeadlessBackend()
        assert isinstance(backend, AsyncBackend)
        assert hasattr(backend, "results")

    def test_unified_backend_for_both_modes(self):
        """Test backend that works for both interactive and headless modes."""

        class UnifiedBackend:
            def __init__(self, mode="interactive"):
                self.mode = mode
                self.results = []

            async def handle_input(self, user_input: str) -> bool:
                if self.mode == "interactive":
                    print(f"Interactive: {user_input}")
                else:
                    self.results.append(user_input)
                return True

        # Same backend class works for both modes
        interactive_backend = UnifiedBackend("interactive")
        headless_backend = UnifiedBackend("headless")

        assert isinstance(interactive_backend, AsyncBackend)
        assert isinstance(headless_backend, AsyncBackend)

"""
Tests for AsyncREPL with action support and late backend binding.
"""

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from prompt_toolkit.key_binding import KeyBindings

from repl_toolkit import AsyncREPL, run_async_repl
from repl_toolkit.actions import Action, ActionContext, ActionRegistry, SendToBackend


class MockBackend:
    """Mock backend for testing."""

    def __init__(self):
        self.inputs_received = []
        self.should_succeed = True

    async def handle_input(self, user_input: str) -> bool:
        self.inputs_received.append(user_input)
        await asyncio.sleep(0.01)  # Simulate processing
        return self.should_succeed


class TestAsyncREPL:
    """Test AsyncREPL functionality with late backend binding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockBackend()
        self.action_registry = ActionRegistry()

    def test_repl_initialization(self, mock_terminal_for_repl):
        """Test REPL initialization without backend."""
        repl = AsyncREPL()

        # REPL should initialize without backend
        assert repl.action_registry is not None
        assert hasattr(repl.action_registry, "backend")
        # Backend not set until run() is called
        assert repl.action_registry.backend is None

    def test_repl_with_custom_registry(self, mock_terminal_for_repl):
        """Test REPL with custom action registry."""
        custom_registry = ActionRegistry()
        repl = AsyncREPL(action_registry=custom_registry)

        assert repl.action_registry is custom_registry

    def test_repl_with_history(self, mock_terminal_for_repl):
        """Test REPL with history file."""
        history_path = Path("/tmp/test_history.txt")
        repl = AsyncREPL(history_path=history_path)

        # Should not raise error during initialization
        assert repl.session.history is not None

    def test_key_parsing(self, mock_terminal_for_repl):
        """Test key combination parsing."""
        repl = AsyncREPL()

        # Test function keys
        assert repl._parse_key_combination("F1") == ("f1",)
        assert repl._parse_key_combination("F12") == ("f12",)

        # Test modifier combinations
        assert repl._parse_key_combination("ctrl-s") == ("c-s",)
        assert repl._parse_key_combination("alt-h") == ("escape", "h")

        # Test single keys
        assert repl._parse_key_combination("enter") == ("enter",)

    def test_is_exit_command(self, mock_terminal_for_repl):
        """Test exit condition detection."""
        repl = AsyncREPL()

        assert repl._is_exit_command("/exit")
        assert repl._is_exit_command("/quit")
        assert repl._is_exit_command("  /EXIT  ")
        assert not repl._is_exit_command("/help")
        assert not repl._is_exit_command("regular input")

    def test_backend_injection_during_run(self, mock_terminal_for_repl):
        """Test backend injection into action registry during run."""
        repl = AsyncREPL()

        # Initially no backend
        assert repl.action_registry.backend is None

        # Backend should be injected when run() is called
        # We can't easily test the full run() method, but we can test the injection logic
        repl.action_registry.backend = self.backend
        assert repl.action_registry.backend is self.backend

    @patch("repl_toolkit.async_repl.PromptSession")
    def test_key_bindings_registration(self, mock_session):
        """Test that key bindings are properly registered."""
        # Add a test action with shortcut
        test_action = Action(
            name="test_shortcut",
            description="Test shortcut",
            category="Test",
            handler=lambda ctx: None,
            keys="F5",
        )
        self.action_registry.register_action(test_action)

        repl = AsyncREPL(action_registry=self.action_registry)

        # Verify PromptSession was called with key_bindings
        mock_session.assert_called_once()
        call_kwargs = mock_session.call_args[1]
        assert "key_bindings" in call_kwargs

        key_bindings = call_kwargs["key_bindings"]
        assert key_bindings is not None


class TestRunAsyncREPL:
    """Test run_async_repl convenience function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockBackend()

    @pytest.mark.asyncio
    async def test_run_async_repl_basic(self):
        """Test basic run_async_repl functionality."""
        with patch("repl_toolkit.async_repl.AsyncREPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock()
            mock_repl_class.return_value = mock_repl

            await run_async_repl(backend=self.backend, initial_message="test message")

            # Verify REPL was created and run with correct parameters
            mock_repl_class.assert_called_once()
            mock_repl.run.assert_called_once_with(self.backend, "test message")

    @pytest.mark.asyncio
    async def test_run_async_repl_with_registry(self):
        """Test run_async_repl with custom action registry."""
        custom_registry = ActionRegistry()

        with patch("repl_toolkit.async_repl.AsyncREPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock()
            mock_repl_class.return_value = mock_repl

            await run_async_repl(
                backend=self.backend,
                action_registry=custom_registry,
                prompt_string="Custom: ",
                history_path=Path("/tmp/custom_history.txt"),
            )

            # Verify parameters were passed correctly to AsyncREPL constructor
            call_args = mock_repl_class.call_args[0]
            call_kwargs = mock_repl_class.call_args[1] if mock_repl_class.call_args[1] else {}

            # Check that action_registry was passed (could be positional or keyword)
            assert (len(call_args) > 0 and call_args[0] is custom_registry) or call_kwargs.get(
                "action_registry"
            ) is custom_registry

            # Verify run was called with backend and initial_message
            mock_repl.run.assert_called_once_with(self.backend, None)


class TestREPLActionIntegration:
    """Test integration between REPL and action system with late backend binding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockBackend()
        # Create action registry (backend will be injected later)
        self.action_registry = ActionRegistry()
        self.executed_actions = []

        # Add test action
        def test_handler(context):
            self.executed_actions.append((context.triggered_by, context.args))

        test_action = Action(
            name="test_action",
            description="Test action",
            category="Test",
            handler=test_handler,
            command="/test",
            keys="F9",
        )
        self.action_registry.register_action(test_action)

    def test_action_registry_integration(self, mock_terminal_for_repl):
        """Test that REPL properly integrates with action registry."""
        repl = AsyncREPL(action_registry=self.action_registry)

        # Registry should be the one we provided
        assert repl.action_registry is self.action_registry

        # Test action should be available
        assert repl.action_registry.validate_action("test_action")
        assert "/test" in repl.action_registry.command_map
        assert "F9" in repl.action_registry.key_map

        # Backend not set until run() is called
        assert repl.action_registry.backend is None

    def test_action_registry_without_backend(self, mock_terminal_for_repl):
        """Test REPL with action registry that has no backend initially."""
        registry_without_backend = ActionRegistry()  # No backend
        repl = AsyncREPL(action_registry=registry_without_backend)

        # Registry should not have backend initially (as designed)
        assert repl.action_registry.backend is None
        assert repl.action_registry is registry_without_backend

    def test_backend_injection_during_execution(self, mock_terminal_for_repl):
        """Test that backend gets injected when needed."""
        repl = AsyncREPL(action_registry=self.action_registry)

        # Simulate what happens during run() - backend gets injected
        repl.action_registry.backend = self.backend

        # Now test command execution
        repl.action_registry.handle_command("/test arg1 arg2")

        # Verify action was executed
        assert len(self.executed_actions) == 1
        triggered_by, args = self.executed_actions[0]
        assert triggered_by == "command"
        assert args == ["arg1", "arg2"]

    def test_shortcut_execution_integration(self, mock_terminal_for_repl):
        """Test shortcut execution through REPL."""
        repl = AsyncREPL(action_registry=self.action_registry)

        # Inject backend (simulating what run() does)
        repl.action_registry.backend = self.backend

        # Simulate shortcut execution
        mock_event = Mock()
        repl.action_registry.handle_shortcut("F9", mock_event)

        # Verify action was executed
        assert len(self.executed_actions) == 1
        triggered_by, _ = self.executed_actions[0]
        assert triggered_by == "shortcut"


class TestErrorHandling:
    """Test error handling in AsyncREPL with late backend binding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockBackend()

    def test_backend_error_handling(self, mock_terminal_for_repl):
        """Test handling of backend errors."""
        self.backend.should_succeed = False
        repl = AsyncREPL()

        # Should not raise error during initialization (no backend yet)
        assert repl.action_registry is not None

    def test_invalid_key_combination(self, mock_terminal_for_repl):
        """Test handling of invalid key combinations."""
        repl = AsyncREPL()

        # Should handle invalid key combinations gracefully
        result = repl._parse_key_combination("invalid-key-combo")
        assert isinstance(result, tuple)

    @patch("repl_toolkit.async_repl.logger")
    def test_shortcut_registration_error(self, mock_logger):
        """Test handling of shortcut registration errors."""
        action_registry = ActionRegistry()

        # Add action with potentially problematic key combo
        action_registry.register_action(
            Action(
                name="problematic",
                description="Problematic action",
                category="Test",
                handler=lambda ctx: None,
                keys="invalid-combo",
            )
        )

        # Should not raise error during REPL creation
        repl = AsyncREPL(action_registry=action_registry)
        assert repl is not None


class TestLateBackendBinding:
    """Test late backend binding specific functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockBackend()

    def test_repl_creation_without_backend(self, mock_terminal_for_repl):
        """Test that REPL can be created without backend."""
        repl = AsyncREPL()

        # Should create successfully
        assert repl is not None
        assert repl.action_registry is not None
        assert repl.action_registry.backend is None

    def test_backend_injection_pattern(self, mock_terminal_for_repl):
        """Test the backend injection pattern."""
        # Create REPL without backend
        action_registry = ActionRegistry()
        repl = AsyncREPL(action_registry=action_registry)

        # Initially no backend
        assert action_registry.backend is None

        # Simulate backend becoming available (like in resource context)
        action_registry.backend = self.backend

        # Now backend is available
        assert action_registry.backend is self.backend

    def test_action_execution_with_late_backend(self, mock_terminal_for_repl):
        """Test that actions work with late backend binding."""
        executed = []

        def test_handler(context):
            # Handler can access backend through context
            backend = context.backend
            executed.append(backend is not None)

        action_registry = ActionRegistry()
        action_registry.register_action(
            Action(
                name="test",
                description="Test",
                category="Test",
                handler=test_handler,
                command="/test",
            )
        )

        # Execute without backend
        context = ActionContext(registry=action_registry, triggered_by="test")
        action_registry.execute_action("test", context)
        assert executed == [False]  # No backend available

        # Inject backend and execute again
        executed.clear()
        action_registry.backend = self.backend
        context = ActionContext(registry=action_registry, backend=self.backend, triggered_by="test")
        action_registry.execute_action("test", context)
        assert executed == [True]  # Backend available


class TestAsyncREPLEdgeCases:
    """Test edge cases in AsyncREPL."""

    def test_register_shortcuts_without_key_map(self, mock_terminal_for_repl):
        """Test registering shortcuts when action_registry has no key_map."""

        # Create a mock registry without key_map attribute
        class MockRegistry:
            pass

        mock_registry = MockRegistry()
        repl = AsyncREPL(action_registry=mock_registry)

        # This should not raise - it should handle missing key_map gracefully
        bindings = KeyBindings()
        repl._register_action_shortcuts(bindings)

        # Should have no bindings registered
        assert len(bindings.bindings) == 0


class FakeCancelApp:
    """Stand-in for the cancellation listener application (no terminal access)."""

    is_done = False

    async def run_async(self) -> None:
        await asyncio.Event().wait()

    def exit(self) -> None:
        self.is_done = True


class KwargsBackend:
    """Backend recording the input and keyword arguments passed to handle_input."""

    def __init__(self):
        self.inputs_received = []
        self.kwargs_received = []
        self.image_ids_received = []

    async def handle_input(self, user_input: str, **kwargs) -> bool:
        self.inputs_received.append(user_input)
        self.kwargs_received.append(kwargs)
        # The REPL clears its image buffer after the turn, so snapshot it now
        self.image_ids_received.append(dict(kwargs.get("images", {})))
        return True


class CancellingBackend:
    """Backend that triggers cancellation via cancel_callback and then blocks."""

    def __init__(self):
        self.inputs_received = []
        self.cancel_messages = []

    async def handle_input(self, user_input: str, **kwargs) -> bool:
        self.inputs_received.append(user_input)
        kwargs["cancel_callback"]()
        await asyncio.sleep(10)
        return True

    def cancel(self, message=None) -> None:
        self.cancel_messages.append(message)


class RecordingRegistry:
    """Minimal ActionHandler whose handle_command returns a canned value."""

    def __init__(self, result):
        self.result = result
        self.commands = []
        self.backend = None
        self.key_map = {}

    def handle_command(self, command_string: str, **kwargs):
        self.commands.append(command_string)
        return self.result

    def is_registered_command(self, text: str) -> bool:
        return False


class TestSendToBackendAsyncREPL:
    """Test action handlers that return SendToBackend in the real run() loop (send_to_backend)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = KwargsBackend()
        self.registry = ActionRegistry(printer=Mock())
        self.contexts = []

    def _register(self, handler, name="skill", command="/skill", keys=None):
        """Register a command action with the given handler."""
        self.registry.register_action(
            Action(
                name=name,
                description="Skill",
                category="Test",
                handler=handler,
                command=command,
                keys=keys,
            )
        )

    def _returning(self, result):
        """Register /skill returning the given result and recording its context."""

        def handler(context):
            self.contexts.append(context)
            return result

        self._register(handler)

    def _make_repl(self, monkeypatch, inputs, registry=None, **kwargs) -> AsyncREPL:
        """Create a REPL whose session yields the given inputs and then EOF."""
        repl = AsyncREPL(action_registry=registry or self.registry, **kwargs)
        repl.session = Mock()
        repl.session.prompt_async = AsyncMock(side_effect=list(inputs) + [EOFError()])
        monkeypatch.setattr(repl, "_create_cancel_app", lambda cancel_future: FakeCancelApp())
        return repl

    @pytest.mark.asyncio
    async def test_send_to_backend_reaches_backend(self, mock_terminal_for_repl, monkeypatch):
        """The returned text is sent once and THINKING is printed."""
        from repl_toolkit.async_repl import THINKING_MESSAGE

        self._returning(SendToBackend("hello"))
        repl = self._make_repl(monkeypatch, ["/skill x"])

        with patch("repl_toolkit.async_repl.print") as mock_print:
            await repl.run(self.backend)

        assert self.backend.inputs_received == ["hello"]
        mock_print.assert_any_call(THINKING_MESSAGE)

    @pytest.mark.asyncio
    async def test_send_to_backend_text_not_stripped(self, mock_terminal_for_repl, monkeypatch):
        """The text is passed exactly as returned."""
        self._returning(SendToBackend("  hello\n"))
        repl = self._make_repl(monkeypatch, ["/skill x"])

        await repl.run(self.backend)

        assert self.backend.inputs_received == ["  hello\n"]

    @pytest.mark.asyncio
    async def test_send_to_backend_kwargs_forwarded(self, mock_terminal_for_repl, monkeypatch):
        """backend_kwargs reach handle_input alongside the REPL's own cancel_callback."""
        self._returning(SendToBackend("hello", backend_kwargs={"skill": "s"}))
        repl = self._make_repl(monkeypatch, ["/skill x"])

        await repl.run(self.backend)

        assert self.backend.kwargs_received[0]["skill"] == "s"
        assert callable(self.backend.kwargs_received[0]["cancel_callback"])

    @pytest.mark.asyncio
    async def test_send_to_backend_cancel_callback_dropped(
        self, mock_terminal_for_repl, monkeypatch, caplog
    ):
        """A cancel_callback in backend_kwargs is dropped with a warning."""
        sentinel = object()
        self._returning(SendToBackend("hello", backend_kwargs={"cancel_callback": sentinel}))
        repl = self._make_repl(monkeypatch, ["/skill x"])

        with caplog.at_level(logging.WARNING):
            await repl.run(self.backend)

        received = self.backend.kwargs_received[0]["cancel_callback"]
        assert received is not sentinel
        assert callable(received)
        assert any("cancel_callback" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_send_to_backend_images_dropped_without_paste(
        self, mock_terminal_for_repl, monkeypatch, caplog
    ):
        """With no pasted image, a reserved images key is dropped entirely."""
        self._returning(SendToBackend("hello", backend_kwargs={"images": {"fake": 1}}))
        repl = self._make_repl(monkeypatch, ["/skill x"])

        with caplog.at_level(logging.WARNING):
            await repl.run(self.backend)

        assert self.backend.inputs_received == ["hello"]
        assert "images" not in self.backend.kwargs_received[0]
        assert any("images" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_send_to_backend_images_dropped_with_paste(
        self, mock_terminal_for_repl, monkeypatch, caplog
    ):
        """With a pasted image, the backend gets the REPL buffer, not the action's value."""
        self._returning(SendToBackend("hello", backend_kwargs={"images": {"fake": 1}}))
        repl = self._make_repl(monkeypatch, ["/skill x"])
        image_id = repl.add_image(b"data", "image/png")

        with caplog.at_level(logging.WARNING):
            await repl.run(self.backend)

        assert list(self.backend.image_ids_received[0]) == [image_id]
        assert any("images" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_send_to_backend_pasted_image_reaches_backend(
        self, mock_terminal_for_repl, monkeypatch
    ):
        """A pasted image reaches handle_input on a SendToBackend turn (R1)."""
        self._returning(SendToBackend("look {{image:img_001}}"))
        repl = self._make_repl(monkeypatch, ["/skill x"])
        image_id = repl.add_image(b"data", "image/png")
        assert image_id == "img_001"

        await repl.run(self.backend)

        assert self.backend.inputs_received == ["look {{image:img_001}}"]
        assert "img_001" in self.backend.image_ids_received[0]
        assert repl.get_images() == {}

    @pytest.mark.asyncio
    async def test_send_to_backend_cancellation(self, mock_terminal_for_repl, monkeypatch):
        """Cancellation behaves as for typed input."""
        backend = CancellingBackend()
        self._returning(SendToBackend("hello"))
        repl = self._make_repl(monkeypatch, ["/skill x"])

        with patch("repl_toolkit.async_repl.print") as mock_print:
            await repl.run(backend)

        assert backend.inputs_received == ["hello"]
        assert backend.cancel_messages == ["Operation cancelled by user"]
        mock_print.assert_any_call("\nOperation cancelled by user.")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("text", ["", "   ", "\n"])
    async def test_send_to_backend_empty_text_sends_nothing(
        self, mock_terminal_for_repl, monkeypatch, text
    ):
        """Empty or whitespace-only text does not reach the backend."""
        self._returning(SendToBackend(text, backend_kwargs={"skill": "s"}))
        repl = self._make_repl(monkeypatch, ["/skill x", "typed"])

        await repl.run(self.backend)

        assert self.backend.inputs_received == ["typed"]

    @pytest.mark.asyncio
    async def test_send_to_backend_none_result_sends_nothing(
        self, mock_terminal_for_repl, monkeypatch
    ):
        """A handler returning None does not reach the backend."""
        self._returning(None)
        repl = self._make_repl(monkeypatch, ["/skill x"])

        await repl.run(self.backend)

        assert self.backend.inputs_received == []
        assert len(self.contexts) == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("result", [None, "text", True, {"text": "x"}])
    async def test_send_to_backend_custom_registry_other_results(
        self, mock_terminal_for_repl, monkeypatch, result
    ):
        """Custom registries returning non-SendToBackend values send nothing and the loop continues."""
        registry = RecordingRegistry(result)
        repl = self._make_repl(
            monkeypatch, ["/skill x", "typed"], registry=registry, enable_image_paste=False
        )

        await repl.run(self.backend)

        assert registry.commands == ["/skill x"]
        assert self.backend.inputs_received == ["typed"]

    @pytest.mark.asyncio
    async def test_send_to_backend_multiline_command_input_preserved(
        self, mock_terminal_for_repl, monkeypatch
    ):
        """The handler sees the submitted input with its newline preserved (R2)."""
        self._returning(None)
        repl = self._make_repl(monkeypatch, ["/skill x a\nb"])

        await repl.run(self.backend)

        assert self.contexts[0].user_input == "/skill x a\nb"

    @pytest.mark.asyncio
    async def test_send_to_backend_typed_input_has_no_extra_kwargs(
        self, mock_terminal_for_repl, monkeypatch
    ):
        """Typed input still receives only the REPL's own kwargs."""
        repl = self._make_repl(monkeypatch, ["typed"])

        await repl.run(self.backend)

        assert set(self.backend.kwargs_received[0]) == {"cancel_callback"}

    def test_send_to_backend_shortcut_result_ignored(self, mock_terminal_for_repl, caplog):
        """A shortcut handler returning SendToBackend does not reach the backend."""
        handler = Mock(return_value=SendToBackend("hello"))
        self._register(handler, name="quick", command="/quick", keys="f5")
        self.registry.backend = self.backend
        repl = AsyncREPL(action_registry=self.registry)
        binding = next(b for b in repl._create_key_bindings().bindings if b.keys == ("f5",))

        with caplog.at_level(logging.DEBUG, logger="repl_toolkit.async_repl"):
            binding.handler(Mock())

        handler.assert_called_once()
        assert self.backend.inputs_received == []
        assert any("Ignoring SendToBackend" in record.message for record in caplog.records)

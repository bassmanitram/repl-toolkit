"""
Tests for AsyncREPL with action support and late backend binding.
"""

import pytest
from prompt_toolkit.key_binding import KeyBindings
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from repl_toolkit import AsyncREPL, run_async_repl
from repl_toolkit.actions import ActionRegistry, Action, ActionContext


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
    
    def test_repl_initialization(self):
        """Test REPL initialization without backend."""
        repl = AsyncREPL()
        
        # REPL should initialize without backend
        assert repl.action_registry is not None
        assert hasattr(repl.action_registry, 'backend')
        # Backend not set until run() is called
        assert repl.action_registry.backend is None
    
    def test_repl_with_custom_registry(self):
        """Test REPL with custom action registry."""
        custom_registry = ActionRegistry()
        repl = AsyncREPL(action_registry=custom_registry)
        
        assert repl.action_registry is custom_registry
    
    def test_repl_with_history(self):
        """Test REPL with history file."""
        history_path = Path("/tmp/test_history.txt")
        repl = AsyncREPL(history_path=history_path)
        
        # Should not raise error during initialization
        assert repl.session.history is not None
    
    def test_key_parsing(self):
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
    
    def test_should_exit(self):
        """Test exit condition detection."""
        repl = AsyncREPL()
        
        assert repl._should_exit("/exit")
        assert repl._should_exit("/quit")
        assert repl._should_exit("  /EXIT  ")
        assert not repl._should_exit("/help")
        assert not repl._should_exit("regular input")
    
    def test_backend_injection_during_run(self):
        """Test backend injection into action registry during run."""
        repl = AsyncREPL()
        
        # Initially no backend
        assert repl.action_registry.backend is None
        
        # Backend should be injected when run() is called
        # We can't easily test the full run() method, but we can test the injection logic
        repl.action_registry.backend = self.backend
        assert repl.action_registry.backend is self.backend
    
    @patch('repl_toolkit.async_repl.PromptSession')
    def test_key_bindings_registration(self, mock_session):
        """Test that key bindings are properly registered."""
        # Add a test action with shortcut
        test_action = Action(
            name="test_shortcut",
            description="Test shortcut",
            category="Test",
            handler=lambda ctx: None,
            keys="F5"
        )
        self.action_registry.register_action(test_action)
        
        repl = AsyncREPL(action_registry=self.action_registry)
        
        # Verify PromptSession was called with key_bindings
        mock_session.assert_called_once()
        call_kwargs = mock_session.call_args[1]
        assert 'key_bindings' in call_kwargs
        
        key_bindings = call_kwargs['key_bindings']
        assert key_bindings is not None


class TestRunAsyncREPL:
    """Test run_async_repl convenience function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockBackend()
    
    @pytest.mark.asyncio
    async def test_run_async_repl_basic(self):
        """Test basic run_async_repl functionality."""
        with patch('repl_toolkit.async_repl.AsyncREPL') as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock()
            mock_repl_class.return_value = mock_repl
            
            await run_async_repl(
                backend=self.backend,
                initial_message="test message"
            )
            
            # Verify REPL was created and run with correct parameters
            mock_repl_class.assert_called_once()
            mock_repl.run.assert_called_once_with(self.backend, "test message")
    
    @pytest.mark.asyncio
    async def test_run_async_repl_with_registry(self):
        """Test run_async_repl with custom action registry."""
        custom_registry = ActionRegistry()
        
        with patch('repl_toolkit.async_repl.AsyncREPL') as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock()
            mock_repl_class.return_value = mock_repl
            
            await run_async_repl(
                backend=self.backend,
                action_registry=custom_registry,
                prompt_string="Custom: ",
                history_path=Path("/tmp/custom_history.txt")
            )
            
            # Verify parameters were passed correctly to AsyncREPL constructor
            call_args = mock_repl_class.call_args[0]
            call_kwargs = mock_repl_class.call_args[1] if mock_repl_class.call_args[1] else {}
            
            # Check that action_registry was passed (could be positional or keyword)
            assert (len(call_args) > 0 and call_args[0] is custom_registry) or \
                   call_kwargs.get('action_registry') is custom_registry
            
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
            keys="F9"
        )
        self.action_registry.register_action(test_action)
    
    def test_action_registry_integration(self):
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
    
    def test_action_registry_without_backend(self):
        """Test REPL with action registry that has no backend initially."""
        registry_without_backend = ActionRegistry()  # No backend
        repl = AsyncREPL(action_registry=registry_without_backend)
        
        # Registry should not have backend initially (as designed)
        assert repl.action_registry.backend is None
        assert repl.action_registry is registry_without_backend
    
    def test_backend_injection_during_execution(self):
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
    
    def test_shortcut_execution_integration(self):
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
    
    def test_backend_error_handling(self):
        """Test handling of backend errors."""
        self.backend.should_succeed = False
        repl = AsyncREPL()
        
        # Should not raise error during initialization (no backend yet)
        assert repl.action_registry is not None
    
    def test_invalid_key_combination(self):
        """Test handling of invalid key combinations."""
        repl = AsyncREPL()
        
        # Should handle invalid key combinations gracefully
        result = repl._parse_key_combination("invalid-key-combo")
        assert isinstance(result, tuple)
    
    @patch('repl_toolkit.async_repl.logger')
    def test_shortcut_registration_error(self, mock_logger):
        """Test handling of shortcut registration errors."""
        action_registry = ActionRegistry()
        
        # Add action with potentially problematic key combo
        action_registry.register_action(Action(
            name="problematic",
            description="Problematic action",
            category="Test",
            handler=lambda ctx: None,
            keys="invalid-combo"
        ))
        
        # Should not raise error during REPL creation
        repl = AsyncREPL(action_registry=action_registry)
        assert repl is not None


class TestLateBackendBinding:
    """Test late backend binding specific functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = MockBackend()
    
    def test_repl_creation_without_backend(self):
        """Test that REPL can be created without backend."""
        repl = AsyncREPL()
        
        # Should create successfully
        assert repl is not None
        assert repl.action_registry is not None
        assert repl.action_registry.backend is None
    
    def test_backend_injection_pattern(self):
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
    
    def test_action_execution_with_late_backend(self):
        """Test that actions work with late backend binding."""
        executed = []
        
        def test_handler(context):
            # Handler can access backend through context
            backend = context.backend
            executed.append(backend is not None)
        
        action_registry = ActionRegistry()
        action_registry.register_action(Action(
            name="test",
            description="Test",
            category="Test",
            handler=test_handler,
            command="/test"
        ))
        
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
    
    def test_register_shortcuts_without_key_map(self):
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

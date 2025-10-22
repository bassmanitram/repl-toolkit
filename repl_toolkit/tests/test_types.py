"""
Tests for protocol compliance and type checking.
"""

import pytest
from typing import Protocol, runtime_checkable
from unittest.mock import Mock, AsyncMock

from repl_toolkit.ptypes import AsyncBackend, HeadlessBackend, ActionHandler, Completer
from repl_toolkit.actions import ActionRegistry


class TestProtocolCompliance:
    """Test protocol compliance for various interfaces."""
    
    def test_async_backend_protocol(self):
        """Test AsyncBackend protocol compliance."""
        
        class TestAsyncBackend:
            async def handle_input(self, user_input: str) -> bool:
                return True
        
        backend = TestAsyncBackend()
        assert isinstance(backend, AsyncBackend)
        assert hasattr(backend, 'handle_input')
    
    def test_headless_backend_protocol(self):
        """Test HeadlessBackend protocol compliance."""
        
        class TestHeadlessBackend:
            async def handle_input(self, user_input: str) -> bool:
                return True
            
            def process_message(self, message: str) -> str:
                return f"Processed: {message}"
        
        backend = TestHeadlessBackend()
        assert isinstance(backend, HeadlessBackend)
        assert hasattr(backend, 'handle_input')
        assert hasattr(backend, 'process_message')
    
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
        assert hasattr(handler, 'execute_action')
        assert hasattr(handler, 'handle_command')
        assert hasattr(handler, 'validate_action')
        assert hasattr(handler, 'list_actions')
    
    def test_completer_protocol(self):
        """Test Completer protocol compliance."""
        
        class TestCompleter:
            def get_completions(self, document, complete_event):
                return []
        
        completer = TestCompleter()
        assert isinstance(completer, Completer)
        assert hasattr(completer, 'get_completions')


class TestMockBackendCompliance:
    """Test mock backend implementations for protocol compliance."""
    
    def test_mock_backend_async_protocol(self):
        """Test mock backend implements AsyncBackend protocol."""
        mock_backend = Mock(spec=AsyncBackend)
        mock_backend.handle_input = AsyncMock(return_value=True)
        
        # Should have required method
        assert hasattr(mock_backend, 'handle_input')
        assert callable(mock_backend.handle_input)
    
    def test_mock_backend_headless_protocol(self):
        """Test mock backend implements HeadlessBackend protocol."""
        mock_backend = Mock(spec=HeadlessBackend)
        mock_backend.handle_input = AsyncMock(return_value=True)
        mock_backend.process_message = Mock(return_value="processed")
        
        # Should have required methods
        assert hasattr(mock_backend, 'handle_input')
        assert hasattr(mock_backend, 'process_message')
        assert callable(mock_backend.handle_input)
        assert callable(mock_backend.process_message)
    
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
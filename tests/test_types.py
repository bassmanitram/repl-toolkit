"""
Tests for repl_toolkit type protocols.
"""

import pytest
from repl_toolkit.ptypes import AsyncBackend, HeadlessBackend, CommandHandler


class TestAsyncBackend:
    """Test AsyncBackend protocol."""
    
    def test_protocol_implementation(self):
        """Test that a class can implement AsyncBackend protocol."""
        
        class MockBackend:
            async def handle_input(self, user_input: str) -> bool:
                return True
        
        backend = MockBackend()
        assert isinstance(backend, AsyncBackend)
    
    def test_protocol_structural_typing(self):
        """Test that protocol works with structural typing."""
        
        class MockBackend:
            async def handle_input(self, user_input: str) -> bool:
                return True
        
        backend = MockBackend()
        
        # Test that we can call the expected method
        assert hasattr(backend, 'handle_input')
        assert callable(getattr(backend, 'handle_input'))


class TestHeadlessBackend:
    """Test HeadlessBackend protocol."""
    
    def test_protocol_implementation(self):
        """Test that a class can implement HeadlessBackend protocol."""
        
        class MockBackend:
            async def handle_input(self, user_input: str) -> bool:
                return True
        
        backend = MockBackend()
        assert isinstance(backend, HeadlessBackend)


class TestCommandHandler:
    """Test CommandHandler protocol."""
    
    def test_protocol_implementation(self):
        """Test that a class can implement CommandHandler protocol."""
        
        class MockHandler:
            async def handle_command(self, command: str) -> None:
                pass
        
        handler = MockHandler()
        assert isinstance(handler, CommandHandler)


class TestProtocolUsage:
    """Test how protocols work in practice."""
    
    @pytest.mark.asyncio
    async def test_async_backend_usage(self):
        """Test using AsyncBackend in practice."""
        
        class EchoBackend:
            async def handle_input(self, user_input: str) -> bool:
                return True
        
        backend = EchoBackend()
        
        # This should work as expected
        result = await backend.handle_input("test")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_command_handler_usage(self):
        """Test using CommandHandler in practice."""
        
        class TestHandler:
            def __init__(self):
                self.last_command = None
            
            async def handle_command(self, command: str) -> None:
                self.last_command = command
        
        handler = TestHandler()
        
        # This should work as expected
        await handler.handle_command("/test")
        assert handler.last_command == "/test"
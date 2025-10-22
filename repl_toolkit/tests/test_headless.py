"""
Tests for headless mode functionality.
"""

import pytest
from unittest.mock import AsyncMock

from repl_toolkit import run_headless_mode


class MockHeadlessBackend:
    """Mock backend for headless testing."""
    
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.inputs_received = []
    
    async def handle_input(self, user_input: str) -> bool:
        self.inputs_received.append(user_input)
        return self.should_succeed


class TestHeadlessMode:
    """Test headless mode functionality."""
    
    @pytest.mark.asyncio
    async def test_headless_success(self):
        """Test successful headless execution."""
        backend = MockHeadlessBackend(should_succeed=True)
        
        result = await run_headless_mode(
            backend=backend,
            initial_message="Test message"
        )
        
        assert result is True
        assert backend.inputs_received == ["Test message"]
    
    @pytest.mark.asyncio
    async def test_headless_failure(self):
        """Test headless execution with backend failure."""
        backend = MockHeadlessBackend(should_succeed=False)
        
        result = await run_headless_mode(
            backend=backend,
            initial_message="Test message"
        )
        
        assert result is False
        assert backend.inputs_received == ["Test message"]
    
    @pytest.mark.asyncio
    async def test_headless_no_message(self):
        """Test headless mode with no initial message."""
        backend = MockHeadlessBackend()
        
        result = await run_headless_mode(
            backend=backend,
            initial_message=None
        )
        
        assert result is False
        assert backend.inputs_received == []
    
    @pytest.mark.asyncio
    async def test_headless_empty_message(self):
        """Test headless mode with empty message."""
        backend = MockHeadlessBackend()
        
        result = await run_headless_mode(
            backend=backend,
            initial_message=""
        )
        
        assert result is False
        assert backend.inputs_received == []
    
    @pytest.mark.asyncio
    async def test_headless_backend_exception(self):
        """Test headless mode with backend exception."""
        backend = AsyncMock()
        backend.handle_input.side_effect = Exception("Backend error")
        
        result = await run_headless_mode(
            backend=backend,
            initial_message="Test message"
        )
        
        assert result is False
        backend.handle_input.assert_called_once_with("Test message")
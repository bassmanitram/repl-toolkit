"""
Tests for repl_toolkit headless functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import io

from repl_toolkit.headless import run_headless_mode


class TestHeadlessMode:
    """Test headless mode functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.handle_input = AsyncMock(return_value=True)

    @pytest.mark.asyncio
    async def test_initial_message_processing(self):
        """Test that initial message is processed."""
        input_stream = io.StringIO("")
        
        success = await run_headless_mode(
            self.mock_backend,
            initial_message="Hello",
            input_stream=input_stream
        )
        
        assert success is True
        self.mock_backend.handle_input.assert_called_with("Hello")

    @pytest.mark.asyncio
    async def test_single_line_input(self):
        """Test processing single line input."""
        input_stream = io.StringIO("Test message\n")
        
        success = await run_headless_mode(
            self.mock_backend,
            input_stream=input_stream
        )
        
        assert success is True
        self.mock_backend.handle_input.assert_called_with("Test message")

    @pytest.mark.asyncio
    async def test_multiline_input_with_send(self):
        """Test multiline input with explicit send command."""
        input_stream = io.StringIO("Line 1\nLine 2\n{{send}}\nLine 3\n")
        
        success = await run_headless_mode(
            self.mock_backend,
            input_stream=input_stream
        )
        
        assert success is True
        assert self.mock_backend.handle_input.call_count == 2
        self.mock_backend.handle_input.assert_any_call("Line 1\nLine 2")
        self.mock_backend.handle_input.assert_any_call("Line 3")

    @pytest.mark.asyncio
    async def test_empty_input_skipped(self):
        """Test that empty input is skipped."""
        input_stream = io.StringIO("{{send}}\n\n  \n{{send}}\n")
        
        success = await run_headless_mode(
            self.mock_backend,
            input_stream=input_stream
        )
        
        assert success is True
        # Should not call backend for empty messages
        self.mock_backend.handle_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_backend_failure_handling(self):
        """Test handling of backend failures."""
        self.mock_backend.handle_input.return_value = False
        input_stream = io.StringIO("Test message\n")
        
        success = await run_headless_mode(
            self.mock_backend,
            input_stream=input_stream
        )
        
        assert success is False

    @pytest.mark.asyncio
    async def test_backend_exception_handling(self):
        """Test handling of backend exceptions."""
        self.mock_backend.handle_input.side_effect = Exception("Backend error")
        input_stream = io.StringIO("Test message\n")
        
        success = await run_headless_mode(
            self.mock_backend,
            input_stream=input_stream
        )
        
        assert success is False
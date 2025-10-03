"""
Tests for repl_toolkit AsyncREPL functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from repl_toolkit.async_repl import AsyncREPL, run_async_repl


class TestAsyncREPL:
    """Test AsyncREPL functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.handle_input = AsyncMock(return_value=True)

    def test_async_repl_initialization(self):
        """Test AsyncREPL initialization."""
        with patch('repl_toolkit.async_repl.PromptSession'):
            repl = AsyncREPL(self.mock_backend)
            assert repl.backend is self.mock_backend
            assert repl.command_handler is not None

    def test_async_repl_with_custom_parameters(self):
        """Test AsyncREPL with custom parameters."""
        mock_command_handler = Mock()
        mock_completer = Mock()
        
        with patch('repl_toolkit.async_repl.PromptSession') as mock_session:
            mock_session.return_value.app = Mock()
            
            repl = AsyncREPL(
                backend=self.mock_backend,
                command_handler=mock_command_handler,
                completer=mock_completer,
                prompt_string="Custom: ",
                history_path=Path("/tmp/test_history")
            )
            
            assert repl.backend is self.mock_backend
            assert repl.command_handler is mock_command_handler

    def test_create_history_with_path(self):
        """Test history file creation."""
        with patch('repl_toolkit.async_repl.PromptSession'):
            repl = AsyncREPL(self.mock_backend)
            
            test_path = Path("/tmp/test_history")
            with patch('repl_toolkit.async_repl.FileHistory') as mock_file_history:
                result = repl._create_history(test_path)
                mock_file_history.assert_called_once_with(str(test_path))

    def test_create_history_none_path(self):
        """Test history creation with None path."""
        with patch('repl_toolkit.async_repl.PromptSession'):
            repl = AsyncREPL(self.mock_backend)
            result = repl._create_history(None)
            assert result is None

    def test_should_exit_commands(self):
        """Test exit command detection."""
        with patch('repl_toolkit.async_repl.PromptSession'):
            repl = AsyncREPL(self.mock_backend)
            
            assert repl._should_exit("/exit") is True
            assert repl._should_exit("/quit") is True
            assert repl._should_exit("/EXIT") is True
            assert repl._should_exit("  /exit  ") is True
            assert repl._should_exit("/help") is False
            assert repl._should_exit("regular input") is False

    def test_key_bindings_creation(self):
        """Test key bindings are created."""
        with patch('repl_toolkit.async_repl.PromptSession'):
            repl = AsyncREPL(self.mock_backend)
            bindings = repl._create_key_bindings()
            assert bindings is not None


class TestAsyncREPLIntegration:
    """Integration tests for AsyncREPL."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.handle_input = AsyncMock(return_value=True)

    @pytest.mark.asyncio
    async def test_run_with_initial_message(self):
        """Test run with initial message."""
        with patch('repl_toolkit.async_repl.PromptSession') as mock_session_class:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_session.prompt_async = AsyncMock(side_effect=["/exit"])
            mock_session_class.return_value = mock_session
            
            repl = AsyncREPL(self.mock_backend)
            
            with patch.object(repl, '_process_input') as mock_process:
                await repl.run(initial_message="Hello")
                mock_process.assert_called_with("Hello")

    @pytest.mark.asyncio
    async def test_run_with_normal_input(self):
        """Test run with normal user input."""
        with patch('repl_toolkit.async_repl.PromptSession') as mock_session_class:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_session.prompt_async = AsyncMock(side_effect=["Hello world", "/exit"])
            mock_session_class.return_value = mock_session
            
            repl = AsyncREPL(self.mock_backend)
            
            with patch.object(repl, '_process_input') as mock_process:
                await repl.run()
                mock_process.assert_called_once_with("Hello world")

    @pytest.mark.asyncio
    async def test_run_with_command_input(self):
        """Test run with command input."""
        with patch('repl_toolkit.async_repl.PromptSession') as mock_session_class:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_session.prompt_async = AsyncMock(side_effect=["/help", "/exit"])
            mock_session_class.return_value = mock_session
            
            repl = AsyncREPL(self.mock_backend)
            
            with patch.object(repl.command_handler, 'handle_command') as mock_cmd:
                await repl.run()
                mock_cmd.assert_called_once_with("/help")


class TestRunAsyncREPLFunction:
    """Test the run_async_repl convenience function."""

    @pytest.mark.asyncio
    async def test_run_async_repl_basic(self):
        """Test run_async_repl function."""
        mock_backend = Mock()
        
        with patch('repl_toolkit.async_repl.AsyncREPL') as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock()
            mock_repl_class.return_value = mock_repl
            
            await run_async_repl(mock_backend)
            
            mock_repl_class.assert_called_once()
            mock_repl.run.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_run_async_repl_with_parameters(self):
        """Test run_async_repl with all parameters."""
        mock_backend = Mock()
        mock_command_handler = Mock()
        mock_completer = Mock()
        
        with patch('repl_toolkit.async_repl.AsyncREPL') as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run = AsyncMock()
            mock_repl_class.return_value = mock_repl
            
            await run_async_repl(
                backend=mock_backend,
                command_handler=mock_command_handler,
                completer=mock_completer,
                initial_message="Hello",
                prompt_string="Test: ",
                history_path=Path("/tmp/history")
            )
            
            mock_repl_class.assert_called_once_with(
                mock_backend,
                mock_command_handler,
                mock_completer,
                "Test: ",
                Path("/tmp/history")
            )
            mock_repl.run.assert_called_once_with("Hello")
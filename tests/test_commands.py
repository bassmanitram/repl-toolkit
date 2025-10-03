"""
Tests for repl_toolkit command system.
"""

import pytest
from unittest.mock import Mock, patch

from repl_toolkit.commands import CommandRegistry, BaseCommand, HelpCommand


class TestCommandRegistry:
    """Test CommandRegistry functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()

    def test_registry_initialization(self):
        """Test that registry initializes with basic commands."""
        commands = self.registry.list_commands()
        assert "help" in commands
        assert "exit" in commands
        assert "quit" in commands

    def test_validate_command(self):
        """Test command validation."""
        assert self.registry.validate_command("/help") is True
        assert self.registry.validate_command("help") is True
        assert self.registry.validate_command("/unknown") is False

    def test_add_command(self):
        """Test adding new commands."""
        class TestCommand(BaseCommand):
            async def handle_command(self, command: str, args: list) -> None:
                pass

        self.registry.add_command(
            command="/test",
            handler_class=TestCommand,
            category="Test",
            description="Test command",
            usage="/test - Run test"
        )

        assert self.registry.validate_command("/test") is True
        assert "test" in self.registry.list_commands()

    def test_add_duplicate_command_raises_error(self):
        """Test that adding duplicate commands raises an error."""
        class TestCommand(BaseCommand):
            async def handle_command(self, command: str, args: list) -> None:
                pass

        with pytest.raises(ValueError, match="already exists"):
            self.registry.add_command(
                command="/help",  # Already exists
                handler_class=TestCommand,
                category="Test",
                description="Test command",
                usage="/test"
            )

    def test_get_command_help(self):
        """Test getting command help."""
        help_info = self.registry.get_command_help("help")
        assert help_info is not None
        assert "description" in help_info
        assert "usage" in help_info
        assert "category" in help_info

    def test_get_command_help_unknown_command(self):
        """Test getting help for unknown command."""
        help_info = self.registry.get_command_help("unknown")
        assert help_info is None

    def test_get_command_handler(self):
        """Test getting command handlers."""
        handler = self.registry.get_command_handler("/help")
        assert isinstance(handler, HelpCommand)

    def test_get_command_handler_main_loop_command(self):
        """Test that main loop commands return None."""
        handler = self.registry.get_command_handler("/exit")
        assert handler is None

    @pytest.mark.asyncio
    async def test_handle_command(self):
        """Test command handling."""
        with patch('builtins.print') as mock_print:
            await self.registry.handle_command("/help")
            # Should call print to display help
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self):
        """Test handling unknown commands."""
        with patch('builtins.print') as mock_print:
            await self.registry.handle_command("/unknown")
            # Should print error message
            mock_print.assert_called()


class TestHelpCommand:
    """Test HelpCommand functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CommandRegistry()
        self.help_command = HelpCommand(self.registry)

    @pytest.mark.asyncio
    async def test_general_help(self):
        """Test displaying general help."""
        with patch('builtins.print') as mock_print:
            await self.help_command.handle_command("/help", [])
            # Should display available commands
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_specific_help(self):
        """Test displaying help for specific command."""
        with patch('builtins.print') as mock_print:
            await self.help_command.handle_command("/help", ["help"])
            # Should display help for help command
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_help_for_unknown_command(self):
        """Test help for unknown command."""
        with patch('builtins.print') as mock_print:
            await self.help_command.handle_command("/help", ["unknown"])
            # Should display error message
            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_help_with_too_many_args(self):
        """Test help command with too many arguments."""
        with patch('builtins.print') as mock_print:
            await self.help_command.handle_command("/help", ["arg1", "arg2"])
            # Should display error about too many args
            mock_print.assert_called()


class TestBaseCommand:
    """Test BaseCommand base class."""

    def test_command_name_generation(self):
        """Test that command name is generated correctly."""
        class TestCommand(BaseCommand):
            async def handle_command(self, command: str, args: list) -> None:
                pass

        registry = Mock()
        cmd = TestCommand(registry)
        assert cmd.command_name == "test"

    def test_validate_args_min_args(self):
        """Test argument validation with minimum args."""
        class TestCommand(BaseCommand):
            async def handle_command(self, command: str, args: list) -> None:
                pass

        registry = Mock()
        cmd = TestCommand(registry)
        
        with patch('builtins.print'):
            assert cmd.validate_args([], min_args=1) is False
            assert cmd.validate_args(["arg1"], min_args=1) is True

    def test_validate_args_max_args(self):
        """Test argument validation with maximum args."""
        class TestCommand(BaseCommand):
            async def handle_command(self, command: str, args: list) -> None:
                pass

        registry = Mock()
        cmd = TestCommand(registry)
        
        with patch('builtins.print'):
            assert cmd.validate_args(["arg1", "arg2"], max_args=1) is False
            assert cmd.validate_args(["arg1"], max_args=1) is True

    def test_output_methods(self):
        """Test output methods work without error."""
        class TestCommand(BaseCommand):
            async def handle_command(self, command: str, args: list) -> None:
                pass

        registry = Mock()
        cmd = TestCommand(registry)
        
        with patch('builtins.print'):
            cmd.print_info("Info message")
            cmd.print_error("Error message")
            cmd.print_success("Success message")

    def test_format_list(self):
        """Test list formatting."""
        class TestCommand(BaseCommand):
            async def handle_command(self, command: str, args: list) -> None:
                pass

        registry = Mock()
        cmd = TestCommand(registry)
        
        # Empty list
        result = cmd.format_list([])
        assert result == "  (none)"
        
        # Non-empty list
        result = cmd.format_list(["item1", "item2"])
        assert "item1" in result
        assert "item2" in result
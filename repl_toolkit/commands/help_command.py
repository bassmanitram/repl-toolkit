"""
Help command for repl_toolkit.

Provides help functionality for displaying available commands and their usage.
"""

from typing import List, Dict, Any
from .base import BaseCommand


class HelpCommand(BaseCommand):
    """
    Command handler for displaying help information.
    
    Provides general help and specific command help.
    """

    def __init__(self, registry):
        """Initialize help command."""
        super().__init__(registry)
        self._command_name = "help"

    async def handle_command(self, command: str, args: List[str]) -> None:
        """
        Handle help command requests.
        
        Args:
            command: The command string ('/help')
            args: Optional command name to get specific help for
        """
        if not self.validate_args(args, max_args=1):
            return
        
        if args:
            await self._show_specific_help(args[0])
        else:
            await self._show_general_help()

    async def _show_general_help(self) -> None:
        """Display general help with all available commands."""
        commands = self.registry.list_commands()
        
        if not commands:
            self.print_info("No commands available.")
            return
        
        self.print_info("Available commands:")
        self.print_info("")
        
        # Group commands by category if registry supports it
        grouped = self._group_commands_by_category(commands)
        
        for category, cmd_list in grouped.items():
            if category != "General":
                self.print_info(f"{category}:")
            
            for cmd_name in sorted(cmd_list):
                # Get brief description if available
                help_info = self.registry.get_command_help(cmd_name)
                if help_info and 'description' in help_info:
                    desc = help_info['description'].split('\n')[0]  # First line only
                    self.print_info(f"  /{cmd_name:<12} {desc}")
                else:
                    self.print_info(f"  /{cmd_name}")
            
            self.print_info("")
        
        self.print_info("For help on a specific command, use: /help <command>")
        self.print_info("To exit, use: /exit or /quit")

    async def _show_specific_help(self, command_name: str) -> None:
        """
        Display help for a specific command.
        
        Args:
            command_name: Name of command to show help for
        """
        # Remove leading slash if present
        if command_name.startswith('/'):
            command_name = command_name[1:]
        
        help_info = self.registry.get_command_help(command_name)
        
        if not help_info:
            self.print_error(f"Unknown command: {command_name}")
            self.print_info("Use /help to see available commands.")
            return
        
        self.print_info(f"Help for /{command_name}:")
        self.print_info("")
        
        if 'description' in help_info:
            self.print_info(help_info['description'])
            self.print_info("")
        
        if 'usage' in help_info:
            self.print_info(f"Usage: {help_info['usage']}")
        else:
            self.print_info(f"Usage: /{command_name} [args...]")

    def _group_commands_by_category(self, commands: List[str]) -> Dict[str, List[str]]:
        """
        Group commands by category.
        
        Args:
            commands: List of command names
            
        Returns:
            Dictionary mapping category names to command lists
        """
        grouped = {"General": []}
        
        for cmd_name in commands:
            help_info = self.registry.get_command_help(cmd_name)
            
            if help_info and 'category' in help_info:
                category = help_info['category']
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(cmd_name)
            else:
                grouped["General"].append(cmd_name)
        
        # Remove empty categories
        return {k: v for k, v in grouped.items() if v}

    def get_command_usage(self, command: str) -> str:
        """Get usage string for help command."""
        return "/help [command]"
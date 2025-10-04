"""
Command registry for repl_toolkit.

Provides command registration, validation, and handler instantiation
for extensible command systems.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from ..ptypes import CommandHandler
from .base import BaseCommand, CommandError
from .help_command import HelpCommand


class CommandRegistry(CommandHandler):
    """
    Registry for REPL commands with dynamic handler loading.
    
    Manages command registration, validation, and execution with
    support for categorization and help generation.
    """

    def __init__(self):
        """Initialize command registry with basic commands."""
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.command_cache: Dict[str, BaseCommand] = {}
        
        # Register basic commands
        self._register_basic_commands()

    def _instantiate_handler(self, command: str,
                             handler_class: Any) -> BaseCommand:
        """
        Instantiates a command handler.
        This can be overridden in order to instantiate commands that have
        more complex constructor/initialization needs the the default.

        Args:
            command (str): The name of the command to instantiate the handler for.
            handler_class (Any): The class of the handler to instantiate.

        Returns:
            BaseCommand: An instance of the handler class, initialized with the current object.
        """
        return handler_class(self)
    
    def _register_basic_commands(self) -> None:
        """Register essential commands that every REPL needs."""
        # Help command
        self.add_command(
            command="/help",
            handler_class=HelpCommand,
            category="General",
            description="Show help information",
            usage="/help [command] - Show help for all commands or a specific command"
        )
        
        # Exit commands (handled by main loop, not by handlers)
        self.add_command(
            command="/exit",
            handler_class=None,  # Special case - handled by main loop
            category="Control", 
            description="Exit the application",
            usage="/exit - Exit the REPL"
        )
        
        self.add_command(
            command="/quit",
            handler_class=None,  # Special case - handled by main loop
            category="Control",
            description="Exit the application", 
            usage="/quit - Exit the REPL"
        )

    def add_command(
        self, 
        command: str,
        handler_class: Optional[type],
        category: str,
        description: str,
        usage: str
    ) -> None:
        """
        Add a new command to the registry.

        Args:
            command: Command string (e.g., '/mycommand')
            handler_class: Handler class (or None for main-loop handled commands)
            category: Command category (e.g., 'General', 'Session')
            description: Short description of the command
            usage: Usage string for the command
            
        Raises:
            ValueError: If command already exists
        """
        if command in self.commands:
            raise ValueError(f"Command {command} already exists in registry.")

        self.commands[command] = {
            'handler_class': handler_class,
            'category': category,
            'description': description,
            'usage': usage
        }

    def get_command_help(self, command: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get help information for a specific command.

        Args:
            command: Specific command to get help for

        Returns:
            Dictionary with help information or None if not found
        """
        if not command:
            return None
            
        # Ensure command starts with /
        if not command.startswith('/'):
            command = f'/{command}'
            
        if command not in self.commands:
            return None
            
        cmd_info = self.commands[command]
        return {
            'description': cmd_info['description'],
            'usage': cmd_info['usage'],
            'category': cmd_info['category']
        }

    def get_command_handler(self, command: str) -> Optional[BaseCommand]:
        """
        Get the handler instance for a specific command.

        Args:
            command: Command to get handler for (e.g., '/help')

        Returns:
            Handler instance or None for main-loop handled commands

        Raises:
            CommandError: If command is not found
        """
        # Ensure command starts with /
        if not command.startswith('/'):
            command = f'/{command}'

        if not self.validate_command(command):
            raise CommandError(f"Command {command} is not recognized.", command=command)

        cmd_info = self.commands[command]
        handler_class = cmd_info['handler_class']

        # Main loop commands return None
        if handler_class is None:
            return None

        # Check cache first
        handler_key = handler_class.__name__
        if handler_key in self.command_cache:
            return self.command_cache[handler_key]

        # Instantiate handler
        handler_instance = self._instantiate_handler(command, handler_class)
        self.command_cache[handler_key] = handler_instance
        return handler_instance

    def validate_command(self, command: str) -> bool:
        """
        Validate if a command is supported.

        Args:
            command: Command to validate (e.g., '/help')

        Returns:
            True if command is supported, False otherwise
        """
        if not command.startswith('/'):
            command = f'/{command}'
        return command in self.commands

    def list_commands(self) -> List[str]:
        """
        Return a sorted list of all command names (without leading slash).
        
        Returns:
            List of command names
        """
        return sorted([cmd[1:] for cmd in self.commands.keys()])

    async def handle_command(self, command_string: str) -> None:
        """
        Handle a command by invoking its handler.

        Args:
            command_string: Full command string (e.g., '/help arg1 arg2')

        Raises:
            CommandError: If command is not recognized or handling fails
        """
        logger.debug(f"Handling command: {command_string}")
        
        # Parse command and arguments
        parts = command_string.strip().split()
        if not parts:
            return
            
        command = parts[0]
        args = parts[1:]

        # Ensure command starts with /
        if not command.startswith('/'):
            command = f'/{command}'

        logger.debug(f"Command: {command}, Args: {args}")
        
        if not self.validate_command(command):
            logger.debug(f"Unrecognized command: {command}")
            print(f"Unknown command: {command}")
            print("Use /help to see available commands.")
            return

        try:
            handler = self.get_command_handler(command)
            if handler:
                logger.debug(f"Invoking handler for command: {command} with args: {args}")
                await handler.handle_command(command, args)
            else:
                # Main loop commands (like /exit, /quit) are handled elsewhere
                logger.debug(f"Command {command} is handled by main loop")
                
        except Exception as e:
            logger.opt(exception=True).error(f"Error handling command {command_string}: {e}")
            print(f"Error executing command: {e}")
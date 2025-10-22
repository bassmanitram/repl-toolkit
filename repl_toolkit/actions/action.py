"""
Core action definition and context for the action system.

This module defines the Action dataclass and ActionContext that form the
foundation of the command and keyboard shortcut system.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Union, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from .registry import ActionRegistry


@dataclass
class Action:
    """
    Action definition that can be triggered by commands or keyboard shortcuts.
    
    Actions provide a way to define functionality that can be accessed
    through multiple interaction methods (commands, shortcuts) while maintaining
    consistent behavior and documentation.
    
    Example:
        # Action with both command and shortcut
        help_action = Action(
            name="show_help",
            description="Show help information",
            category="General",
            handler=show_help_function,
            command="/help",
            command_usage="/help [command] - Show help for all or specific command",
            keys="F1",
            keys_description="Show help"
        )
        
        # Command-only action
        history_action = Action(
            name="show_history", 
            description="Display conversation history",
            category="Information",
            handler=show_history_function,
            command="/history",
            command_usage="/history - Display message history"
        )
        
        # Shortcut-only action
        save_action = Action(
            name="quick_save",
            description="Quick save current state",
            category="File",
            handler=quick_save_function,
            keys="ctrl-s",
            keys_description="Quick save"
        )
        
        # Main-loop action (handled externally)
        exit_action = Action(
            name="exit_repl",
            description="Exit the application",
            category="Control",
            handler=None,  # Handled by main loop
            command="/exit",
            command_usage="/exit - Exit the application"
        )
    """
    
    # Core action definition
    name: str                                    # Unique action identifier
    description: str                             # Human-readable description
    category: str                               # Category for grouping/organization
    handler: Optional[Union[Callable, str]]     # Handler function, import path, or None for main-loop
    
    # Command binding (optional)
    command: Optional[str] = None               # Command string (e.g., "/help") 
    command_args_description: Optional[str] = None  # Description of command arguments
    command_usage: Optional[str] = None         # Full usage description
    
    # Keyboard shortcut binding (optional)
    keys: Optional[Union[str, List[str]]] = None    # Key combination(s)
    keys_description: Optional[str] = None      # Shortcut description for help
    
    # Metadata and control
    enabled: bool = True                        # Whether action is currently enabled
    context: Optional[str] = None               # Context where action is available
    requires_backend: bool = False              # Whether action needs backend access
    hidden: bool = False                        # Hide from help listings
    
    def __post_init__(self):
        """Validate action definition after initialization."""
        logger.trace("Action.__post_init__() entry")
        
        if not self.name:
            raise ValueError("Action name cannot be empty")
        
        if not self.description:
            raise ValueError("Action description cannot be empty")
            
        if not self.category:
            raise ValueError("Action category cannot be empty")
            
        # Handler can be None for main-loop actions like exit/quit
        # but if provided, it cannot be empty string
        if self.handler == "":
            raise ValueError("Action handler cannot be empty string (use None for main-loop actions)")
            
        if not self.command and not self.keys:
            raise ValueError("Action must have either command or keys binding")
            
        # Validate command format
        if self.command and not self.command.startswith('/'):
            raise ValueError(f"Command '{self.command}' must start with '/'")
            
        # Ensure command usage is provided for commands
        if self.command and not self.command_usage:
            logger.warning(f"Action '{self.name}' has command but no usage description")
            
        # Ensure keys description is provided for shortcuts
        if self.keys and not self.keys_description:
            logger.warning(f"Action '{self.name}' has keys but no keys description")

        logger.trace("Action.__post_init__() exit")

    @property
    def has_command(self) -> bool:
        """Check if action has a command binding."""
        logger.trace("Action.has_command() entry/exit")
        return self.command is not None
        
    @property 
    def has_shortcut(self) -> bool:
        """Check if action has a keyboard shortcut binding."""
        logger.trace("Action.has_shortcut() entry/exit")
        return self.keys is not None
        
    @property
    def is_main_loop_action(self) -> bool:
        """Check if action is handled by the main loop (handler is None)."""
        logger.trace("Action.is_main_loop_action() entry/exit")
        return self.handler is None
        
    def get_keys_list(self) -> List[str]:
        """Get keys as a list, handling both string and list formats."""
        logger.trace("Action.get_keys_list() entry")
        
        if not self.keys:
            logger.trace("Action.get_keys_list() exit - no keys")
            return []
        
        result = [self.keys] if isinstance(self.keys, str) else self.keys
        logger.trace("Action.get_keys_list() exit")
        return result


@dataclass
class ActionContext:
    """
    Context information passed to action handlers.
    
    ActionContext provides handlers with access to the registry, backend,
    and context-specific information needed to execute actions properly.
    
    The context varies depending on how the action was triggered:
    - Command: args contains parsed command arguments
    - Keyboard: event contains the key press event
    - Programmatic: context can be customized
    """
    
    registry: "ActionRegistry"           # Reference to action registry
    backend: Optional[Any] = None               # Backend instance (if available)
    event: Optional[Any] = None                 # KeyPress event for shortcuts
    args: List[str] = field(default_factory=list)  # Command arguments
    triggered_by: str = "unknown"               # How action was triggered
    user_input: Optional[str] = None            # Original user input
    
    def __post_init__(self):
        """Set triggered_by based on available context."""
        logger.trace("ActionContext.__post_init__() entry")
        
        if self.triggered_by == "unknown":
            if self.event is not None:
                self.triggered_by = "shortcut"
            elif self.args or self.user_input:
                self.triggered_by = "command"
            else:
                self.triggered_by = "programmatic"
        
        logger.trace("ActionContext.__post_init__() exit")


class ActionError(Exception):
    """Base exception for action-related errors."""
    
    def __init__(self, message: str, action_name: Optional[str] = None):
        """
        Initialize action error.
        
        Args:
            message: Error description
            action_name: Name of action that caused error (optional)
        """
        logger.trace("ActionError.__init__() entry/exit")
        super().__init__(message)
        self.action_name = action_name


class ActionValidationError(ActionError):
    """Exception raised when action validation fails."""
    pass


class ActionExecutionError(ActionError):
    """Exception raised when action execution fails."""
    pass
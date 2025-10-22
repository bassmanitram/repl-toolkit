"""
Action handler utilities and base classes.

This module provides utilities for creating and managing action handlers
in the action system.
"""

from typing import Callable, Optional
from loguru import logger

from .action import ActionContext


class ActionHandler:
    """
    Base class for creating action handlers with common utilities.
    
    This class provides common functionality that action handlers often need,
    such as validation, error handling, and output formatting.
    """
    
    def __init__(self, name: str = None):
        """
        Initialize action handler.
        
        Args:
            name: Handler name for logging (optional)
        """
        self.name = name or self.__class__.__name__
    
    def validate_args(self, context: ActionContext, min_args: int = 0, max_args: Optional[int] = None) -> bool:
        """
        Validate command arguments in context.
        
        Args:
            context: Action context containing arguments
            min_args: Minimum number of arguments required
            max_args: Maximum number of arguments allowed (None for unlimited)
            
        Returns:
            True if arguments are valid, False otherwise
        """
        args = context.args
        
        if len(args) < min_args:
            self.print_error(f"Action requires at least {min_args} argument(s)")
            return False
        
        if max_args is not None and len(args) > max_args:
            self.print_error(f"Action accepts at most {max_args} argument(s)")
            return False
        
        return True
    
    def print_info(self, message: str) -> None:
        """Print an informational message."""
        print(message)
    
    def print_error(self, message: str) -> None:
        """Print an error message."""
        print(f"Error: {message}")
        logger.warning(f"Action error in {self.name}: {message}")
    
    def print_success(self, message: str) -> None:
        """Print a success message."""
        print(message)
    
    def format_list(self, items: list, prefix: str = "  • ") -> str:
        """
        Format a list of items for display.
        
        Args:
            items: Items to format
            prefix: Prefix for each item
            
        Returns:
            Formatted string
        """
        if not items:
            return "  (none)"
        
        return "\n".join(f"{prefix}{item}" for item in items)


def action_handler(
    name: str,
    description: str,
    category: str,
    command: Optional[str] = None,
    keys: Optional[str] = None,
    **kwargs
):  
    """
    Decorator for creating action handlers.
    
    This decorator simplifies the process of creating action handlers by
    automatically registering them with appropriate metadata.
    
    Args:
        name: Action name
        description: Action description
        category: Action category
        command: Command string (optional)
        keys: Key combination (optional)
        **kwargs: Additional Action parameters
        
    Example:
        @action_handler(
            name="my_action",
            description="Do something useful",
            category="Utilities",
            command="/myaction",
            keys="ctrl-m"
        )
        async def my_action_handler(context: ActionContext):
            print("Action executed!")
    """
    def decorator(func: Callable):
        # Store action metadata on function
        func._action_name = name
        func._action_description = description
        func._action_category = category
        func._action_command = command
        func._action_keys = keys
        func._action_kwargs = kwargs
        func._is_action_handler = True
        
        return func
    
    return decorator


def get_action_metadata(func: Callable) -> Optional[dict]:
    """
    Extract action metadata from a decorated function.
    
    Args:
        func: Function to extract metadata from
        
    Returns:
        Dictionary with action metadata or None if not an action handler
    """
    if not hasattr(func, '_is_action_handler'):
        return None
    
    return {
        'name': getattr(func, '_action_name', None),
        'description': getattr(func, '_action_description', None),
        'category': getattr(func, '_action_category', None),
        'command': getattr(func, '_action_command', None),
        'keys': getattr(func, '_action_keys', None),
        'kwargs': getattr(func, '_action_kwargs', {}),
        'handler': func
    }
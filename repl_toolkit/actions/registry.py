"""
Action registry for managing commands and keyboard shortcuts.

The registry serves as the central hub for registering, organizing, and
executing actions that can be triggered through multiple interaction methods.
"""

import importlib
from typing import Any, Callable, Dict, List, Optional, Union
from loguru import logger

from ..ptypes import ActionHandler, AsyncBackend
from .action import Action, ActionContext, ActionError, ActionValidationError, ActionExecutionError

class ActionRegistry(ActionHandler):
    """
    Registry for managing both command and keyboard shortcut actions.
    
    The registry provides a single point of control for all user-triggered
    actions, whether they originate from typed commands or keyboard shortcuts.
    It handles action registration, validation, execution, and help generation.
    
    Example:
        registry = ActionRegistry()
        
        # Register an action command and shortcut
        registry.register_action(Action(
            name="show_help",
            description="Show help information", 
            category="General",
            handler=help_handler,
            command="/help",
            command_usage="/help [command] - Show help",
            keys="F1",
            keys_description="Show help"
        ))
        
        # OR using convenience method

        registry.register_action(
            name="show_help",
            description="Show help information", 
            category="General",
            handler=help_handler,
            command="/help",
            command_usage="/help [command] - Show help",
            keys="F1",
            keys_description="Show help"
        )

        # Execute by command
        registry.handle_command("/help")
        
        # Execute by shortcut (in key binding)
        registry.handle_shortcut("F1", event)
    """
    
    def __init__(self):
        """Initialize the action registry with built-in actions."""
        self.actions: Dict[str, Action] = {}
        self.command_map: Dict[str, str] = {}  # command -> action_name
        self.key_map: Dict[str, str] = {}      # key_combo -> action_name
        self.handler_cache: Dict[str, Callable] = {}
        self._backend = None
        # Register built-in actions
        self._register_builtin_actions()
    
    @property
    def backend(self):
        """The backend property getter."""
        return self._backend

    @backend.setter
    def backend(self, value):
        """The backend property setter with validation."""
        if not isinstance(value, AsyncBackend):
            raise TypeError("Backend must implement AsyncBackend.")
        self._backend = value # Set the actual private attribute


    def _register_builtin_actions(self) -> None:
        """Register essential built-in actions."""
        
        # Help action - Both command and shortcut
        self.register_action(Action(
            name="show_help",
            description="Show help information for all actions or a specific action",
            category="General", 
            handler=self._show_help,
            command="/help",
            command_usage="/help [action|command] - Show help for all actions or specific one",
            keys="F1",
            keys_description="Show help"
        ))
        
        # List shortcuts action - command only
        self.register_action(Action(
            name="list_shortcuts", 
            description="List all available keyboard shortcuts",
            category="General",
            handler=self._list_shortcuts,
            command="/shortcuts",
            command_usage="/shortcuts - List all keyboard shortcuts"
        ))
        
        # Exit actions - commands only (main loop handles these)
        self.register_action(Action(
            name="exit_repl",
            description="Exit the REPL application",
            category="Control",
            handler=None,  # Handled by main loop
            command="/exit", 
            command_usage="/exit - Exit the application"
        ))
        
        self.register_action(Action(
            name="quit_repl",
            description="Quit the REPL application", 
            category="Control",
            handler=None,  # Handled by main loop
            command="/quit",
            command_usage="/quit - Quit the application"
        ))
    
    def register_action(self, *args, **kwargs) -> None:
        """
        Register an action in the registry.
        
        Args:
            action: Action to register
            
        Raises:
            ActionValidationError: If action is invalid or conflicts exist
        """
        action = None
        if args and isinstance(args[0], Action):
            action = args[0]
            if kwargs:
                for k, v in kwargs.items():
                    setattr(action, k, v)
        else:
            action = Action(**kwargs)

        # Validate action
        if action.name in self.actions:
            raise ActionValidationError(f"Action '{action.name}' already exists")
        
        if action.command and action.command in self.command_map:
            existing_action = self.command_map[action.command]
            raise ActionValidationError(
                f"Command '{action.command}' already bound to action '{existing_action}'"
            )
        
        # Check for key conflicts
        for key_combo in action.get_keys_list():
            if key_combo in self.key_map:
                existing_action = self.key_map[key_combo]
                raise ActionValidationError(
                    f"Key '{key_combo}' already bound to action '{existing_action}'"
                )
        
        # Register action
        self.actions[action.name] = action
        
        # Register command mapping
        if action.command:
            self.command_map[action.command] = action.name
            
        # Register key mappings
        for key_combo in action.get_keys_list():
            self.key_map[key_combo] = action.name
            
        logger.debug(f"Registered action '{action.name}' with command='{action.command}' keys={action.keys}")
    
    def get_action(self, name: str) -> Optional[Action]:
        """Get an action by name."""
        return self.actions.get(name)
        
    def get_action_by_command(self, command: str) -> Optional[Action]:
        """Get an action by its command string."""
        action_name = self.command_map.get(command)
        return self.actions.get(action_name) if action_name else None
    
    def get_action_by_keys(self, keys: str) -> Optional[Action]:
        """Get an action by its key combination."""
        action_name = self.key_map.get(keys)
        return self.actions.get(action_name) if action_name else None
    
    def _resolve_handler(self, action: Action) -> Optional[Callable]:
        """
        Resolve action handler to a callable function.
        
        Args:
            action: Action whose handler to resolve
            
        Returns:
            Callable handler function or None for main-loop actions
        """
        if action.handler is None:
            return None
            
        # Check cache first
        cache_key = f"{action.name}:{action.handler}"
        if cache_key in self.handler_cache:
            return self.handler_cache[cache_key]
        
        # If already callable, use it
        if callable(action.handler):
            self.handler_cache[cache_key] = action.handler
            return action.handler
        
        # If string, try to import
        if isinstance(action.handler, str):
            try:
                module_path, func_name = action.handler.rsplit('.', 1)
                module = importlib.import_module(module_path)
                handler_func = getattr(module, func_name)
                self.handler_cache[cache_key] = handler_func
                return handler_func
            except Exception as e:
                logger.error(f"Failed to import handler '{action.handler}' for action '{action.name}': {e}")
                raise ActionValidationError(f"Cannot resolve handler '{action.handler}'")
        
        raise ActionValidationError(f"Invalid handler type for action '{action.name}': {type(action.handler)}")
    
    def execute_action(self, action_name: str, context: ActionContext) -> None:
        """
        Execute an action by name.
        
        Args:
            action_name: Name of action to execute
            context: Action context
            
        Raises:
            ActionError: If action is not found or execution fails
        """
        action = self.get_action(action_name)
        if not action:
            raise ActionError(f"Action '{action_name}' not found")
        
        if not action.enabled:
            logger.debug(f"Action '{action_name}' is disabled")
            return
        
        # Resolve handler
        handler = self._resolve_handler(action)
        if handler is None:
            # Main loop actions (like exit/quit) return without execution
            logger.debug(f"Action '{action_name}' handled by main loop")
            return
        
        try:
            logger.debug(f"Executing action '{action_name}' via {context.triggered_by}")
            
            # Execute handler synchronously
            # If handler needs async operations, it can handle them internally
            handler(context)
                
        except Exception as e:
            logger.error(f"Error executing action '{action_name}': {e}")
            raise ActionExecutionError(f"Failed to execute action '{action_name}': {e}", action_name)
    
    def handle_command(self, command_string: str) -> None:
        """
        Handle a command string by mapping to appropriate action.
        
        Args:
            command_string: Full command string (e.g., '/help topic')
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
        
        # Look up action
        action = self.get_action_by_command(command)
        if not action:
            print(f"Unknown command: {command}")
            print("Use /help to see available commands.")
            return
        
        # Create context and execute
        context = ActionContext(
            registry=self,
            args=args,
            backend=self.backend,
            triggered_by="command",
            user_input=command_string
        )
        
        try:
            self.execute_action(action.name, context)
        except ActionError as e:
            print(f"Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling command '{command_string}': {e}")
            print(f"An unexpected error occurred: {e}")
    
    def handle_shortcut(self, key_combo: str, event: Any) -> None:
        """
        Handle a keyboard shortcut by mapping to appropriate action.
        
        Args:
            key_combo: Key combination string
            event: Key press event from prompt_toolkit
        """
        logger.debug(f"Handling shortcut: {key_combo}")
        
        # Look up action
        action = self.get_action_by_keys(key_combo)
        if not action:
            logger.debug(f"No action bound to key combination: {key_combo}")
            return
        
        # Create context and execute
        context = ActionContext(
            registry=self,
            backend=self.backend,
            event=event,
            triggered_by="shortcut"
        )
        
        try:
            self.execute_action(action.name, context)
        except ActionError as e:
            print(f"Error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling shortcut '{key_combo}': {e}")
            print(f"An unexpected error occurred: {e}")
    
    # ActionHandler protocol implementation
    def validate_action(self, action_name: str) -> bool:
        """Validate if an action is supported."""
        return action_name in self.actions
    
    def list_actions(self) -> List[str]:
        """Return a list of all available action names."""
        return list(self.actions.keys())
    
    def list_commands(self) -> List[str]:
        """Return a list of all available commands."""
        return list(self.command_map.keys())
    
    def list_shortcuts(self) -> List[str]:
        """Return a list of all available keyboard shortcuts."""
        return list(self.key_map.keys())
    
    def get_actions_by_category(self) -> Dict[str, List[Action]]:
        """Get actions organized by category."""
        categories = {}
        for action in self.actions.values():
            if action.hidden:
                continue
            if action.category not in categories:
                categories[action.category] = []
            categories[action.category].append(action)
        return categories
    
    # Built-in action handlers
    def _show_help(self, context: ActionContext) -> None:
        """Show help information."""
        if context.args and len(context.args) > 0:
            # Show help for specific action or command
            target = context.args[0]
            
            # Try as action name first
            action = self.get_action(target)
            if not action:
                # Try as command (add / if missing)
                if not target.startswith('/'):
                    target = f'/{target}'
                action = self.get_action_by_command(target)
            
            if action:
                self._show_action_help(action)
            else:
                print(f"No help available for: {context.args[0]}")
        else:
            # Show general help
            self._show_general_help()
    
    def _show_action_help(self, action: Action) -> None:
        """Show detailed help for a specific action."""
        print(f"\n{action.description}")
        print(f"Category: {action.category}")
        
        if action.command:
            print(f"Command: {action.command_usage or action.command}")
        
        if action.keys:
            keys_str = ", ".join(action.get_keys_list())
            desc = f" - {action.keys_description}" if action.keys_description else ""
            print(f"Shortcut: {keys_str}{desc}")
        
        if not action.enabled:
            print("Status: Disabled")
        print()
    
    def _show_general_help(self) -> None:
        """Show general help with all actions organized by category."""
        print("\nAvailable Actions:")
        print("=" * 50)
        
        categories = self.get_actions_by_category()
        
        for category, actions in sorted(categories.items()):
            print(f"\n{category}:")
            for action in sorted(actions, key=lambda a: a.name):
                # Format display line
                parts = []
                
                if action.command:
                    parts.append(f"{action.command:<20}")
                else:
                    parts.append(" " * 20)
                
                if action.keys:
                    keys_str = ", ".join(action.get_keys_list())
                    parts.append(f"{keys_str:<15}")
                else:
                    parts.append(" " * 15)
                
                parts.append(action.description)
                
                print("  " + "".join(parts))
        
        print(f"\nUse '/help <command>' for detailed information about a specific action.")
        print(f"Use '/shortcuts' to see only keyboard shortcuts.")
        print()
    
    def _list_shortcuts(self, context: ActionContext) -> None:
        """List all keyboard shortcuts."""
        print("\nKeyboard Shortcuts:")
        print("=" * 50)
        
        categories = self.get_actions_by_category()
        
        for category, actions in sorted(categories.items()):
            shortcuts_in_category = [a for a in actions if a.keys]
            if not shortcuts_in_category:
                continue
                
            print(f"\n{category}:")
            for action in sorted(shortcuts_in_category, key=lambda a: a.name):
                keys_str = ", ".join(action.get_keys_list())
                desc = action.keys_description or action.description
                print(f"  {keys_str:<15} {desc}")
        
        print()
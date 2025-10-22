# REPL Toolkit

A Python toolkit for building interactive REPL and headless interfaces with support for both commands and keyboard shortcuts, featuring late backend binding for resource context scenarios.

## Key Features

### Action System
- **Single Definition**: One action, multiple triggers (command + shortcut)
- **Flexible Binding**: Command-only, shortcut-only, or both
- **Context Aware**: Actions know how they were triggered
- **Dynamic Registration**: Add actions at runtime
- **Category Organization**: Organize actions for better help systems

### Developer Experience
- **Protocol-Based**: Type-safe interfaces with runtime checking
- **Easy Extension**: Simple inheritance and registration patterns
- **Rich Help System**: Automatic help generation with usage examples
- **Error Handling**: Comprehensive error handling and user feedback
- **Async Native**: Built for modern async Python applications
- **Late Backend Binding**: Initialize REPL before backend is available

### Production Ready
- **Comprehensive Tests**: Full test coverage with pytest
- **Documentation**: Complete API documentation and examples
- **Performance**: Efficient action lookup and execution
- **Logging**: Structured logging with loguru integration
- **Headless Support**: Non-interactive mode for automation

## Installation

```bash
pip install repl-toolkit
```

**Dependencies:**
- Python 3.8+
- prompt-toolkit >= 3.0.0
- loguru >= 0.5.0

## Quick Start

### Basic Usage

```python
import asyncio
from repl_toolkit import run_async_repl, ActionRegistry, Action

# Your backend that processes user input
class MyBackend:
    async def handle_input(self, user_input: str) -> bool:
        print(f"You said: {user_input}")
        return True

# Create action registry with custom actions
class MyActions(ActionRegistry):
    def __init__(self):
        super().__init__()
        
        # Add action with both command and shortcut
        self.register_action(
            name="save_data",
            description="Save current data",
            category="File",
            handler=self._save_data,
            command="/save",
            command_usage="/save [filename] - Save data to file",
            keys="ctrl-s",
            keys_description="Quick save"
        )
    
    def _save_data(self, context):
        # Access backend through context
        backend = context.backend
        filename = context.args[0] if context.args else "data.txt"
        print(f"💾 Saving to {filename}")
        if context.triggered_by == "shortcut":
            print("   (Triggered by Ctrl+S)")

# Run the REPL with late backend binding
async def main():
    actions = MyActions()
    backend = MyBackend()
    
    await run_async_repl(
        backend=backend,
        action_registry=actions,
        prompt_string="My App: "
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Resource Context Pattern

The late backend binding pattern is especially useful when your backend requires resources that are only available within a specific context:

```python
import asyncio
from repl_toolkit import AsyncREPL, ActionRegistry

class DatabaseBackend:
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def handle_input(self, user_input: str) -> bool:
        # Use database connection
        result = await self.db.query(user_input)
        print(f"Query result: {result}")
        return True

async def main():
    # Create REPL without backend (backend not available yet)
    actions = ActionRegistry()
    repl = AsyncREPL(action_registry=actions)
    
    # Backend only available within resource context
    async with get_database_connection() as db:
        backend = DatabaseBackend(db)
        # Now run REPL with backend
        await repl.run(backend, "Database connected!")

asyncio.run(main())
```

Users can now:
- Type `/save myfile.txt` OR press `Ctrl+S`
- Type `/help` OR press `F1` for help
- All actions work seamlessly both ways!

## Core Concepts

### Actions

Actions are the heart of the extension system. Each action can be triggered by:
- **Commands**: Typed commands like `/help` or `/save filename`
- **Keyboard Shortcuts**: Key combinations like `F1` or `Ctrl+S`  
- **Programmatic**: Direct execution in code

```python
from repl_toolkit import Action

# Both command and shortcut
action = Action(
    name="my_action",
    description="Does something useful",
    category="Utilities",
    handler=my_handler_function,
    command="/myaction",
    command_usage="/myaction [args] - Does something useful",
    keys="F5",
    keys_description="Quick action trigger"
)

# Command-only action
cmd_action = Action(
    name="command_only",
    description="Command-only functionality",  
    category="Commands",
    handler=cmd_handler,
    command="/cmdonly"
)

# Shortcut-only action
key_action = Action(
    name="shortcut_only",
    description="Keyboard shortcut",
    category="Shortcuts", 
    handler=key_handler,
    keys="ctrl-k",
    keys_description="Special shortcut"
)
```

### Action Registry

The `ActionRegistry` manages all actions and provides the interface between the REPL and your application logic:

```python
from repl_toolkit import ActionRegistry

class MyRegistry(ActionRegistry):
    def __init__(self):
        super().__init__()
        self._register_my_actions()
    
    def _register_my_actions(self):
        # Command + shortcut
        self.register_action(
            name="action_name",
            description="What it does", 
            category="Category",
            handler=self._handler_method,
            command="/cmd",
            keys="F2"
        )
    
    def _handler_method(self, context):
        # Access backend through context
        backend = context.backend
        if backend:
            # Use backend
            pass
```

### Action Context

Action handlers receive rich context about how they were invoked:

```python
def my_handler(context: ActionContext):
    # Access the registry and backend
    registry = context.registry
    backend = context.backend  # Available after run() is called
    
    # Different context based on trigger method
    if context.triggered_by == "command":
        args = context.args  # Command arguments
        print(f"Command args: {args}")
        
    elif context.triggered_by == "shortcut":
        event = context.event  # Keyboard event
        print("Triggered by keyboard shortcut")
        
    # Original user input (for commands)
    if context.user_input:
        print(f"Full input: {context.user_input}")
```

## Built-in Actions

Every registry comes with essential built-in actions:

| Action | Command | Shortcut | Description |
|--------|---------|----------|-------------|
| **Help** | `/help [action]` | `F1` | Show help for all actions or specific action |
| **Shortcuts** | `/shortcuts` | - | List all keyboard shortcuts |  
| **Exit** | `/exit` | - | Exit the application |
| **Quit** | `/quit` | - | Quit the application |

## Keyboard Shortcuts

The system supports rich keyboard shortcut definitions:

```python
# Function keys
keys="F1"          # F1
keys="F12"         # F12

# Modifier combinations  
keys="ctrl-s"      # Ctrl+S
keys="alt-h"       # Alt+H
keys="shift-tab"   # Shift+Tab

# Complex combinations
keys="ctrl-alt-d"  # Ctrl+Alt+D

# Multiple shortcuts for same action
keys=["F5", "ctrl-r"]  # Either F5 OR Ctrl+R
```

## Architecture

### Late Backend Binding

The v2 architecture supports late backend binding, allowing you to initialize the REPL before the backend is available:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AsyncREPL     │───▶│ ActionRegistry   │    │   Your Backend  │
│   (Interface)   │    │ (Action System)  │    │  (Available Later)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  prompt_toolkit │    │     Actions      │    │  Resource Context│
│   (Terminal)    │    │  (Commands+Keys) │    │   (DB, API, etc.)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Protocol-Based Design

The toolkit uses Python protocols for type safety and flexibility:

```python
from repl_toolkit.ptypes import AsyncBackend, ActionHandler

# Your backend must implement AsyncBackend
class MyBackend(AsyncBackend):
    async def handle_input(self, user_input: str) -> bool:
        # Process input, return success/failure
        return True

# Action registries implement ActionHandler  
class MyActions(ActionHandler):
    def execute_action(self, action_name: str, context: ActionContext):
        # Execute action by name
        pass
    
    def handle_command(self, command_string: str):
        # Handle command input
        pass
    
    def validate_action(self, action_name: str) -> bool:
        # Check if action exists
        return action_name in self.actions
    
    def list_actions(self) -> List[str]:
        # Return available actions
        return list(self.actions.keys())
```

## Examples

### Basic Example

```python
# examples/basic_usage.py - Complete working example
import asyncio
from repl_toolkit import run_async_repl, ActionRegistry, Action

class EchoBackend:
    async def handle_input(self, input: str) -> bool:
        print(f"Echo: {input}")
        return True

async def main():
    backend = EchoBackend()
    await run_async_repl(backend=backend)

asyncio.run(main())
```

### Advanced Example

```python
# examples/advanced_usage.py - Full-featured example
import asyncio
from repl_toolkit import AsyncREPL, ActionRegistry, Action, ActionContext

class AdvancedBackend:
    def __init__(self):
        self.data = []
    
    async def handle_input(self, input: str) -> bool:
        self.data.append(input)
        print(f"Stored: {input} (Total: {len(self.data)})")
        return True

class AdvancedActions(ActionRegistry):
    def __init__(self):
        super().__init__()
        
        # Statistics with both command and shortcut
        self.register_action(
            name="show_stats",
            description="Show data statistics",
            category="Info", 
            handler=self._show_stats,
            command="/stats",
            keys="F3"
        )
    
    def _show_stats(self, context):
        backend = context.backend
        count = len(backend.data) if backend else 0
        print(f"📊 Statistics: {count} items stored")

async def main():
    actions = AdvancedActions()
    backend = AdvancedBackend()
    
    repl = AsyncREPL(action_registry=actions, prompt_string="Advanced: ")
    await repl.run(backend)

asyncio.run(main())
```

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=repl_toolkit --cov-report=html

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
```

### Writing Tests

```python
import pytest
from repl_toolkit import ActionRegistry, Action, ActionContext

def test_my_action():
    # Test action execution
    registry = ActionRegistry()
    
    executed = []
    def test_handler(context):
        executed.append(context.triggered_by)
    
    action = Action(
        name="test",
        description="Test action",
        category="Test",
        handler=test_handler,
        command="/test"
    )
    
    registry.register_action(action)
    
    context = ActionContext(registry=registry)
    registry.execute_action("test", context)
    
    assert executed == ["programmatic"]
```

## API Reference

### Core Classes

#### `AsyncREPL`
```python
class AsyncREPL:
    def __init__(
        self,
        action_registry: Optional[ActionHandler] = None,
        completer: Optional[Completer] = None,
        prompt_string: Optional[str] = None,
        history_path: Optional[Path] = None
    )
    
    async def run(self, backend: AsyncBackend, initial_message: Optional[str] = None)
```

#### `ActionRegistry`
```python
class ActionRegistry(ActionHandler):
    def register_action(self, action: Action) -> None
    def register_action(self, name, description, category, handler, command=None, keys=None, **kwargs) -> None
    
    def execute_action(self, action_name: str, context: ActionContext) -> None
    def handle_command(self, command_string: str) -> None
    def handle_shortcut(self, key_combo: str, event: Any) -> None
    
    def validate_action(self, action_name: str) -> bool
    def list_actions(self) -> List[str]
    def get_actions_by_category(self) -> Dict[str, List[Action]]
```

### Convenience Functions

#### `run_async_repl()`
```python
async def run_async_repl(
    backend: AsyncBackend,
    action_registry: Optional[ActionHandler] = None,
    completer: Optional[Completer] = None,
    initial_message: Optional[str] = None,
    prompt_string: Optional[str] = None,
    history_path: Optional[Path] = None,
)
```

#### `run_headless_mode()`
```python
async def run_headless_mode(
    backend: HeadlessBackend,
    initial_message: Optional[str] = None
) -> bool
```

### Protocols

#### `AsyncBackend`
```python
class AsyncBackend(Protocol):
    async def handle_input(self, user_input: str) -> bool: ...
```

#### `HeadlessBackend`  
```python
class HeadlessBackend(Protocol):
    async def handle_input(self, user_input: str) -> bool: ...
```

#### `ActionHandler`
```python
class ActionHandler(Protocol):
    def execute_action(self, action_name: str, context: ActionContext) -> None: ...
    def handle_command(self, command_string: str) -> None: ...
    def validate_action(self, action_name: str) -> bool: ...
    def list_actions(self) -> List[str]: ...
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/bassmanitram/repl-toolkit.git
cd repl-toolkit

# Create development environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev,test]"

# Run tests
pytest

# Run examples
python examples/basic_usage.py
python examples/advanced_usage.py
```

### Code Quality

```bash
# Format code
black repl_toolkit/
isort repl_toolkit/

# Lint
flake8 repl_toolkit/

# Type check
mypy repl_toolkit/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for excellent terminal handling
- Logging by [loguru](https://github.com/Delgan/loguru) for beautiful structured logs
- Inspired by modern CLI tools and REPL interfaces

---
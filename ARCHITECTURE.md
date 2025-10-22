# REPL Toolkit - Architecture Overview

## Design Philosophy

REPL Toolkit is built around the concept of **Actions** - a single system that handles both typed commands (`/help`) and keyboard shortcuts (`F1`) through the same interface.

## Core Architecture

### Component Hierarchy

```
AsyncREPL (User Interface)
    │
    ├── ActionRegistry (Action Management) 
    │   │
    │   ├── Action (Individual Actions)
    │   ├── ActionContext (Execution Context)
    │   └── Built-in Actions (Help, Shortcuts, etc.)
    │
    └── Backend (Business Logic)
        └── Your Application Code
```

### Key Components

#### 1. **Action System** (`repl_toolkit.actions`)

**Core Classes:**
- `Action`: Dataclass defining individual actions with commands/shortcuts
- `ActionContext`: Rich context passed to action handlers  
- `ActionRegistry`: Central registry managing all actions
- `ActionHandler`: Protocol for action registry implementations

**Key Features:**
- Command + keyboard shortcut definitions
- Category-based organization
- Dynamic registration
- Context-aware execution
- Built-in help generation

#### 2. **REPL Interface** (`repl_toolkit.async_repl`)

**Core Classes:**
- `AsyncREPL`: Main interactive interface
- `run_async_repl()`: Convenience function

**Key Features:**
- Async-native operation with cancellation support
- Keyboard binding from action registry
- History support with file persistence
- Multi-line input with Alt+Enter submission
- Robust error handling

#### 3. **Protocol System** (`repl_toolkit.ptypes`)

**Core Protocols:**
- `AsyncBackend`: Interface for business logic backends
- `HeadlessBackend`: Interface for non-interactive backends  
- `ActionHandler`: Interface for action registries
- `Completer`: Interface for tab completion

**Benefits:**
- Type safety with runtime flexibility
- Clear separation of concerns
- Easy testing and mocking
- Plugin architecture support

#### 4. **Headless Mode** (`repl_toolkit.headless`) 

**Features:**
- Non-interactive execution
- Batch processing support
- Integration testing support
- CI/CD friendly

## Action System Deep Dive

### Action Definition

```python
@dataclass
class Action:
    # Core Definition
    name: str                    # Unique identifier
    description: str             # Human description
    category: str               # Organization category
    handler: Optional[Callable]  # Function to execute
    
    # Command Binding (optional)
    command: Optional[str]       # "/command" 
    command_usage: Optional[str] # Usage description
    
    # Keyboard Binding (optional)  
    keys: Optional[str]          # "F1" or "ctrl-s"
    keys_description: Optional[str] # Shortcut description
    
    # Metadata
    enabled: bool = True         # Enable/disable
    hidden: bool = False         # Hide from help
    context: Optional[str] = None # Context restriction
```

### Action Patterns

1. **Actions** (Command + Shortcut)
   ```python
   Action(
       name="help", handler=show_help,
       command="/help", keys="F1"
   )
   ```

2. **Command-Only Actions**
   ```python
   Action(
       name="search", handler=search_data,
       command="/search"  # No keys
   )
   ```

3. **Shortcut-Only Actions**
   ```python
   Action(
       name="quick_save", handler=save_data,
       keys="ctrl-s"  # No command
   )
   ```

4. **Main-Loop Actions** (Handled externally)
   ```python
   Action(
       name="exit", handler=None,  # Handled by main loop
       command="/exit"
   )
   ```

### Action Registry

The `ActionRegistry` provides:

- **Registration**: Add actions with conflict detection
- **Lookup**: Find actions by name, command, or keys
- **Execution**: Execute actions with rich context
- **Help**: Auto-generate help and shortcut listings
- **Organization**: Category-based action grouping

### Action Context

```python
@dataclass
class ActionContext:
    registry: ActionRegistry  # Access to registry
    backend: Optional[Any]          # Your backend instance
    event: Optional[Any]            # Keyboard event (shortcuts)
    args: List[str]                 # Command arguments
    triggered_by: str               # "command"|"shortcut"|"programmatic"
    user_input: Optional[str]       # Original input string
```

## Execution Flow

### Command Execution Flow

```
User types "/help topic"
    ↓
AsyncREPL.session detects command
    ↓
ActionRegistry.handle_command("/help topic")
    ↓
Parse command: "/help" + ["topic"]
    ↓
Lookup action by command: "/help" → "show_help"
    ↓
Create ActionContext(args=["topic"], triggered_by="command")
    ↓
Execute action: show_help(context)
    ↓
Action displays help for "topic"
```

### Keyboard Shortcut Flow

```
User presses F1
    ↓
AsyncREPL keyboard binding triggered
    ↓
ActionRegistry.handle_shortcut("F1", event)
    ↓
Lookup action by keys: "F1" → "show_help"
    ↓
Create ActionContext(event=event, triggered_by="shortcut")
    ↓
Execute action: show_help(context)
    ↓
Action displays general help
```

## Extension Points

### Custom Action Registry

```python
class MyActionRegistry(ActionRegistry):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._register_my_actions()
    
    def _register_my_actions(self):
        self.register_action(
            name="custom_action",
            description="My custom action",
            category="Custom",
            handler=self._custom_handler,
            command="/custom",
            keys="F9"
        )
    
    async def _custom_handler(self, context: ActionContext):
        # Access backend: self.backend
        # Access registry: context.registry
        # Check trigger: context.triggered_by
        pass
```

### Dynamic Action Registration

```python
# Register actions at runtime
registry.register_action(Action(
    name="runtime_action",
    description="Added at runtime",
    category="Dynamic",
    handler=lambda ctx: print("Dynamic action!"),
    command="/runtime"
))
```

### Custom Backend Integration

```python
class MyBackend:
    def __init__(self):
        self.data = {}
    
    async def handle_input(self, user_input: str) -> bool:
        # Process input
        self.data['last_input'] = user_input
        print(f"Processed: {user_input}")
        return True

# Backend available in action context
async def my_action_handler(context: ActionContext):
    backend = context.backend
    print(f"Last input was: {backend.data['last_input']}")
```

## Testing Architecture

### Protocol-Based Testing

```python
# Mock backend for testing
class MockBackend:
    def __init__(self):
        self.inputs = []
    
    async def handle_input(self, input: str) -> bool:
        self.inputs.append(input)
        return True

# Test action execution
async def test_action():
    registry = ActionRegistry()
    backend = MockBackend()
    
    context = ActionContext(registry=registry, backend=backend)
    await registry.execute_action("show_help", context)
```

### Action Testing Patterns

```python
# Test action registration
def test_register_action():
    registry = ActionRegistry()
    action = Action(name="test", ...)
    registry.register_action(action)
    assert registry.validate_action("test")

# Test command handling
async def test_command_handling():
    registry = ActionRegistry()
    await registry.handle_command("/help")
    # Verify expected behavior

# Test shortcut handling  
async def test_shortcut_handling():
    registry = ActionRegistry()
    mock_event = Mock()
    await registry.handle_shortcut("F1", mock_event)
    # Verify expected behavior
```

## Performance Considerations

### Efficient Action Lookup

- **Hash-based lookups**: O(1) action lookup by name/command/keys
- **Cached handlers**: Import resolution cached after first use
- **Lazy loading**: Actions loaded only when needed

### Memory Management

- **Weak references**: Registry doesn't hold strong refs to backends
- **Context cleanup**: ActionContext is short-lived
- **Event loop integration**: Proper async/await patterns

### Scalability

- **Large action sets**: Registry scales to hundreds of actions
- **Fast registration**: Batch registration optimizations
- **Category filtering**: Efficient help generation

## Security Considerations

### Action Isolation

- **Handler validation**: Handlers validated at registration
- **Context isolation**: Actions only access provided context
- **Backend protection**: Backend access controlled through context

### Input Sanitization

- **Command parsing**: Safe parsing of command arguments
- **Key combination validation**: Keyboard shortcut validation
- **Error boundaries**: Exceptions isolated to individual actions

## Future Extensibility

### Plugin Architecture

The protocol-based design enables:

- **Custom action types**: New action patterns
- **Alternative UIs**: Different REPL implementations  
- **Backend adapters**: Integration with external systems
- **Completion providers**: Custom tab completion

### Backward Compatibility

- **Protocol versioning**: Protocol extensions maintain compatibility
- **Deprecation paths**: Smooth migration paths for breaking changes
- **Feature flags**: Optional features with graceful degradation

---

This architecture provides a solid foundation for building rich, interactive CLI applications with modern Python best practices.
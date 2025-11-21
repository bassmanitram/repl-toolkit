# REPL Toolkit - Architecture Overview

## Design Philosophy

REPL Toolkit is built around the concept of **Actions** - a unified system that handles both typed commands (`/help`) and keyboard shortcuts (`F1`) through the same interface, with support for late backend binding to accommodate resource context scenarios.

## Core Architecture

### Component Hierarchy

```
AsyncREPL (User Interface)
    │
    ├── ActionRegistry (Action Management)
    │   │
    │   ├── Action (Individual Actions)
    │   ├── ActionContext (Execution Context)
    │   └── Built-in Actions (Help, Shortcuts, Shell, etc.)
    │
    └── Backend (Business Logic)
        └── Your Application Code

HeadlessREPL (Non-Interactive Interface)
    │
    ├── ActionRegistry (Same Action System)
    │   └── stdin Processing + Buffer Management
    │
    └── Backend (Same Business Logic)
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

#### 2. **Interactive Interface** (`repl_toolkit.async_repl`)

**Core Classes:**
- `AsyncREPL`: Main interactive interface
- `run_async_repl()`: Convenience function

**Key Features:**
- Async-native operation with cancellation support
- Keyboard binding from action registry
- History support with file persistence
- Multi-line input with Alt+Enter submission
- Late backend binding support
- Robust error handling

#### 3. **Headless Interface** (`repl_toolkit.headless_repl`)

**Core Classes:**
- `HeadlessREPL`: Non-interactive stdin processing
- `run_headless_mode()`: Convenience function

**Key Features:**
- stdin line-by-line processing
- Buffer accumulation until `/send` commands
- Multiple send cycles support
- Action system integration
- EOF auto-send functionality

#### 4. **Protocol System** (`repl_toolkit.ptypes`)

**Core Protocols:**
- `AsyncBackend`: Interface for business logic backends
- `ActionHandler`: Interface for action registries
- `Completer`: Interface for tab completion

**Benefits:**
- Type safety with runtime flexibility
- Clear separation of concerns
- Easy testing and mocking
- Plugin architecture support

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

1. **Dual Actions** (Command + Shortcut)
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
- **Backend Integration**: Late binding support

### Action Context

```python
@dataclass
class ActionContext:
    registry: ActionRegistry     # Access to registry
    backend: Optional[Any]       # Your backend instance
    event: Optional[Any]         # Keyboard event (shortcuts)
    args: List[str]              # Command arguments
    triggered_by: str            # "command"|"shortcut"|"programmatic"
    user_input: Optional[str]    # Original input string

    # Headless mode extensions
    buffer: Optional[str] = None      # Current buffer content (headless)
    headless_mode: bool = False       # Headless mode flag
```

## Execution Flow

### Interactive Command Execution

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

### Interactive Keyboard Shortcut Flow

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

### Headless Processing Flow

```
stdin: "Line 1\nLine 2\n/send\nLine 3\n"
    ↓
HeadlessREPL._stdin_loop() processes line by line
    ↓
"Line 1" → Add to buffer
"Line 2" → Add to buffer
"/send" → Execute send: backend.handle_input("Line 1\nLine 2")
"Line 3" → Add to buffer
EOF → Execute send: backend.handle_input("Line 3")
```

## Late Backend Binding

### Pattern Overview

The architecture supports initializing the REPL before the backend is available:

```python
# Create REPL without backend
repl = AsyncREPL(action_registry=my_actions)

# Backend becomes available later (e.g., in resource context)
async with get_database_connection() as db:
    backend = DatabaseBackend(db)
    await repl.run(backend)  # Backend injected at runtime
```

### Implementation Details

1. **ActionRegistry.backend**: Property that can be set after initialization
2. **ActionContext.backend**: Backend passed through context to actions
3. **Validation**: Actions can check for backend availability
4. **Error Handling**: Graceful handling when backend is unavailable

## Extension Points

### Custom Action Registry

```python
class MyActionRegistry(ActionRegistry):
    def __init__(self):
        super().__init__()
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

    def _custom_handler(self, context: ActionContext):
        # Access backend: context.backend
        # Access registry: context.registry
        # Check trigger: context.triggered_by
        # Check headless: context.headless_mode
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
def my_action_handler(context: ActionContext):
    backend = context.backend
    if backend:
        print(f"Last input was: {backend.data['last_input']}")
    else:
        print("Backend not available")
```

### Headless Mode Extensions

```python
def headless_aware_action(context: ActionContext):
    if context.headless_mode:
        # Headless-specific behavior
        if context.buffer:
            print(f"Current buffer: {len(context.buffer)} characters")
    else:
        # Interactive behavior
        print("Interactive mode")
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
def test_action():
    registry = ActionRegistry()
    backend = MockBackend()

    context = ActionContext(registry=registry, backend=backend)
    registry.execute_action("show_help", context)
```

### Action Testing Patterns

```python
# Test action registration
def test_register_action():
    registry = ActionRegistry()
    action = Action(name="test", description="Test", category="Test",
                   handler=lambda ctx: None, command="/test")
    registry.register_action(action)
    assert registry.validate_action("test")

# Test command handling
def test_command_handling():
    registry = ActionRegistry()
    registry.handle_command("/help")
    # Verify expected behavior

# Test shortcut handling
def test_shortcut_handling():
    registry = ActionRegistry()
    mock_event = Mock()
    registry.handle_shortcut("F1", mock_event)
    # Verify expected behavior
```

### Headless Testing

```python
@pytest.mark.asyncio
async def test_headless_processing():
    backend = MockBackend()
    stdin_input = "Line 1\nLine 2\n/send\n"

    repl = HeadlessREPL()

    with patch('sys.stdin', StringIO(stdin_input)):
        await repl._stdin_loop(backend)

    assert backend.inputs == ["Line 1\nLine 2"]
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

### Headless Security

- **stdin Processing**: Safe line-by-line processing
- **Buffer Management**: Controlled buffer size and content
- **Command Validation**: Same validation as interactive mode

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

## Implementation Notes

### Synchronous vs Asynchronous

- **Action Handlers**: Synchronous by default for simplicity
- **Backend Operations**: Asynchronous for I/O operations
- **Mixed Patterns**: Actions can handle async operations internally

### Error Handling Strategy

- **Action Errors**: Isolated to individual actions
- **Backend Errors**: Propagated with context
- **System Errors**: Graceful degradation
- **User Feedback**: Clear error messages

### Logging Integration

repl-toolkit follows Python library best practices for error handling:

**Error Reporting Strategy:**
- **All errors logged** via Python's logging framework
- **No direct output** to stdout/stderr (applications control display)
- **Two error levels:**
  - `WARNING`: Expected failures (ActionError) - validation failures, invalid commands
  - `ERROR`: Unexpected failures (Exception) - bugs, system errors, includes traceback

**Trace Logging:**
- Entry/exit logging at `DEBUG` level for execution flow analysis
- Extensive tracing throughout the codebase for debugging

**Application Control:**

Applications configure logging to control error visibility:
```python
# See all errors
logging.basicConfig(level=logging.WARNING)

# See only critical errors
logging.basicConfig(level=logging.ERROR)

# Suppress errors
logging.getLogger('repl_toolkit').setLevel(logging.CRITICAL)
```

**Example Configuration:**
```python
import logging

# Configure repl_toolkit logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Optionally adjust level for debugging
# logging.getLogger('repl_toolkit').setLevel(logging.DEBUG)
```

This approach allows applications to:
- Control error visibility (show/hide)
- Customize error formatting
- Route errors to different outputs (files, handlers, services)
- Filter by severity or component

This architecture provides a solid foundation for building rich, interactive CLI applications with modern Python best practices, supporting both interactive and automated use cases.

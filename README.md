# REPL Toolkit

[![PyPI version](https://badge.fury.io/py/repl-toolkit.svg)](https://badge.fury.io/py/repl-toolkit)

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
- **Headless Support**: Non-interactive mode for automation and testing

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
        print(f"Saving to {filename}")
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

The late backend binding pattern is useful when your backend requires resources that are only available within a specific context:

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
- All actions work seamlessly both ways

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

Every registry comes with built-in actions:

| Action | Command | Shortcut | Description |
|--------|---------|----------|-------------|
| **Help** | `/help [action]` | `F1` | Show help for all actions or specific action |
| **Shortcuts** | `/shortcuts` | - | List all keyboard shortcuts |
| **Shell** | `/shell [cmd]` | - | Drop to interactive shell or run command |
| **Exit** | `/exit` | - | Exit the application |
| **Quit** | `/quit` | - | Quit the application |

## Image Paste Support

REPL Toolkit includes built-in support for pasting images from the clipboard, allowing backends to receive both text and image data.

### Quick Start

```python
import asyncio
from repl_toolkit import AsyncREPL, ImageData

class ImageBackend:
    async def handle_input(self, user_input: str, images=None) -> bool:
        # Process text with image placeholders
        print(f"Text: {user_input}")

        # Process images if present
        if images:
            for img_id, img_data in images.items():
                print(f"  {img_id}: {img_data.media_type}, {len(img_data.data)} bytes")

        return True

async def main():
    backend = ImageBackend()
    repl = AsyncREPL(enable_image_paste=True)  # Enabled by default
    await repl.run(backend)

asyncio.run(main())
```

### Usage

1. Copy an image to clipboard (screenshot, file, etc.)
2. Type your message in the REPL
3. Press **F6** or **Ctrl+Shift+V** to paste
4. Continue typing if needed
5. Press **Alt+Enter** to send

The image is inserted as a placeholder like `{{image:img_001}}` and the backend receives both the text and the actual image data.

### Smart Paste Behavior

The paste action automatically detects clipboard content:

- **Image data** → Inserts image placeholder `{{image:img_001}}`
- **Text data** → Inserts text directly
- **Empty clipboard** → Shows message "No content in clipboard"

### Backend Integration

Backends receive images through an optional `images` parameter:

```python
class MyBackend:
    async def handle_input(
        self,
        user_input: str,
        images: dict[str, ImageData] | None = None
    ) -> bool:
        # Parse text with placeholders
        if images:
            for img_id, img_data in images.items():
                # img_data.data: bytes - Raw image data
                # img_data.media_type: str - MIME type (e.g., "image/png")
                # img_data.timestamp: float - When captured
                process_image(img_data.data, img_data.media_type)

        return True
```

### Utility Functions

REPL Toolkit provides utilities to parse and process image placeholders:

#### `parse_image_references(text)`

Extract image IDs and message structure:

```python
from repl_toolkit import parse_image_references

result = parse_image_references("Look at {{image:img_001}} and {{image:img_002}}")
# result.image_ids → {'img_001', 'img_002'}
# result.parts → [('Look at ', None), ('', 'img_001'), (' and ', None), ('', 'img_002')]
```

#### `iter_content_parts(text, images)`

Iterate through text and images in order:

```python
from repl_toolkit import iter_content_parts

for content, image in iter_content_parts(user_input, images):
    if image:
        # Process image: image.data, image.media_type
        api_client.send_image(image.data, image.media_type)
    elif content:
        # Process text
        api_client.send_text(content)
```

#### `reconstruct_message(text, images, formatter)`

Transform message to any format:

```python
from repl_toolkit import reconstruct_message
import base64

def to_api_format(content, image):
    if image:
        encoded = base64.b64encode(image.data).decode()
        return {
            'type': 'image',
            'source': {'data': encoded, 'media_type': image.media_type}
        }
    return {'type': 'text', 'text': content}

# Convert to API-specific format
parts = []
for content, image in iter_content_parts(user_input, images):
    parts.append(to_api_format(content, image))
```

### Supported Image Formats

The paste action auto-detects these image formats:

- **PNG** (image/png)
- **JPEG** (image/jpeg)
- **GIF** (image/gif)
- **WebP** (image/webp)
- **BMP** (image/bmp)

### Installation Note

Image paste requires the optional `pyclip` package:

```bash
pip install pyclip
```

If `pyclip` is not installed, the feature will gracefully disable with a message when attempted.

### Configuration

Control image paste support when creating the REPL:

```python
# Enable image paste (default)
repl = AsyncREPL(enable_image_paste=True)

# Disable image paste
repl = AsyncREPL(enable_image_paste=False)
```

### Example

See `examples/image_paste_demo.py` for a complete working example:

```bash
python examples/image_paste_demo.py
```

### Built-in Action

| Action | Command | Shortcuts | Description |
|--------|---------|-----------|-------------|
| **Paste** | `/paste-image` | `F6`, `Ctrl+Shift+V` | Paste image or text from clipboard |


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

## Headless Mode

For automation, testing, and batch processing:

```python
import asyncio
from repl_toolkit import run_headless_mode

class BatchBackend:
    async def handle_input(self, user_input: str) -> bool:
        # Process input without user interaction
        result = await process_batch_input(user_input)
        return result

async def main():
    backend = BatchBackend()

    # Process initial message, then read from stdin
    success = await run_headless_mode(
        backend=backend,
        initial_message="Starting batch processing"
    )

    return 0 if success else 1

# Usage:
# echo -e "Line 1\nLine 2\n/send\nLine 3" | python script.py
```

### Headless Features

- **stdin Processing**: Reads input line by line from stdin
- **Buffer Accumulation**: Content lines accumulate until `/send` command
- **Multiple Send Cycles**: Support for multiple `/send` operations
- **Command Processing**: Full action system support in headless mode
- **EOF Handling**: Automatically sends remaining buffer on EOF

## Architecture

### Late Backend Binding

The architecture supports late backend binding, allowing you to initialize the REPL before the backend is available:

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

## Completion Utilities

REPL Toolkit includes powerful completion utilities for building sophisticated command-line interfaces with autocompletion support.

For detailed documentation on completion features including:
- **PrefixCompleter**: Slash commands, at-mentions, hashtags with intelligent prefix detection
- **ShellExpansionCompleter**: Environment variable and shell command expansion
- Customization patterns and extensibility

See [repl_toolkit/completion/README.md](repl_toolkit/completion/README.md) for complete documentation and examples.

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
        print(f"Statistics: {count} items stored")

async def main():
    actions = AdvancedActions()
    backend = AdvancedBackend()

    repl = AsyncREPL(action_registry=actions, prompt_string="Advanced: ")
    await repl.run(backend)

asyncio.run(main())
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/bassmanitram/repl-toolkit.git
cd repl-toolkit
pip install -e ".[dev,test]"
```

### Run Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=repl_toolkit --cov-report=html
```

### Code Formatting

```bash
black repl_toolkit/
isort repl_toolkit/
```

### Type Checking

```bash
mypy repl_toolkit/
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
pytest repl_toolkit/tests/test_actions.py     # Action system tests
pytest repl_toolkit/tests/test_async_repl.py  # REPL interface tests
pytest repl_toolkit/tests/test_headless.py    # Headless mode tests
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
    def handle_command(self, command_string: str, **kwargs) -> None
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
    backend: AsyncBackend,
    action_registry: Optional[ActionHandler] = None,
    initial_message: Optional[str] = None,
) -> bool
```

### Protocols

#### `AsyncBackend`
```python
class AsyncBackend(Protocol):
    async def handle_input(self, user_input: str) -> bool: ...
```

#### `ActionHandler`
```python
class ActionHandler(Protocol):
    def execute_action(self, action_name: str, context: ActionContext) -> None: ...
    def handle_command(self, command_string: str, **kwargs) -> None: ...
    def validate_action(self, action_name: str) -> bool: ...
    def list_actions(self) -> List[str]: ...
```

## License

MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and submit pull requests to the [main repository](https://github.com/bassmanitram/repl-toolkit).

## Links

- **GitHub Repository**: https://github.com/bassmanitram/repl-toolkit
- **PyPI Package**: https://pypi.org/project/repl-toolkit/
- **Documentation**: https://repl-toolkit.readthedocs.io/
- **Issue Tracker**: https://github.com/bassmanitram/repl-toolkit/issues

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Acknowledgments

- Built on [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for terminal handling
- Logging by [loguru](https://github.com/Delgan/loguru) for structured logs
- Inspired by modern CLI tools and REPL interfaces

## Formatting Utilities

REPL Toolkit includes utilities for automatically detecting and applying formatted text (HTML or ANSI) without needing to explicitly wrap text in format types.

### Auto-Format Detection

The formatting utilities can automatically detect whether text contains HTML tags, ANSI escape codes, or is plain text:

```python
from repl_toolkit import detect_format_type, auto_format, print_auto_formatted

# Detect format type
detect_format_type("<b>Bold</b>")  # Returns: 'html'
detect_format_type("\x1b[1mBold\x1b[0m")  # Returns: 'ansi'
detect_format_type("Plain text")  # Returns: 'plain'

# Auto-format and print
print_auto_formatted("<b>Bold HTML</b>")  # Automatically applies HTML formatting
print_auto_formatted("\x1b[1mBold ANSI\x1b[0m")  # Automatically applies ANSI formatting
print_auto_formatted("Plain text")  # Prints as-is
```

### Creating Auto-Printers

The `create_auto_printer()` function creates a printer that can be used as a drop-in replacement for `print()` with automatic format detection:

```python
from repl_toolkit import create_auto_printer

# Create a printer
printer = create_auto_printer()

# Use it like print()
printer("<b>Bold text</b>")  # HTML formatting applied
printer("\x1b[1mANSI bold\x1b[0m")  # ANSI formatting applied
printer("Plain text")  # No formatting

# Works with all print() parameters
printer("<b>Prefix:</b> ", end="", flush=True)
printer("Hello world\n")
```

### Integration with Callback Handlers

The auto-printer is particularly useful for integrating with callback handlers from other libraries:

```python
from repl_toolkit import create_auto_printer
from some_library import CallbackHandler

# Create handler with auto-formatting printer
handler = CallbackHandler(
    response_prefix="<b><darkcyan>🤖 Assistant:</darkcyan></b> ",
    printer=create_auto_printer()  # Automatically formats HTML tags
)

# The response_prefix will be properly formatted without needing
# to explicitly wrap it in HTML() or ANSI()
```

### Format Detection Rules

The auto-detection uses the following rules:

1. **ANSI Detection**: Looks for ANSI escape codes (`\x1b[...m`)
   - Pattern: `\x1b\[[0-9;]*m`
   - Examples: `\x1b[1m`, `\x1b[31;1m`

2. **HTML Detection**: Looks for HTML-like tags
   - Pattern: `</?[a-zA-Z][a-zA-Z0-9]*\s*/?>`
   - Examples: `<b>`, `</b>`, `<darkcyan>`, `<tag/>`
   - Avoids false positives: `a < b`, `<123>`, `<_tag>`

3. **Plain Text**: Everything else

### API Reference

#### `detect_format_type(text: str) -> str`
Detect the format type of a text string.

**Returns**: `'ansi'`, `'html'`, or `'plain'`

#### `auto_format(text: str)`
Auto-detect format type and return appropriate formatted text object.

**Returns**: `HTML`, `ANSI`, or `str` object

#### `print_auto_formatted(text: str, **kwargs) -> None`
Print text with auto-detected formatting.

**Parameters**: Same as `print_formatted_text()` from prompt_toolkit

#### `create_auto_printer() -> Callable`
Create a printer function with auto-format detection.

**Returns**: Callable with signature `printer(text: str, **kwargs)`

### Example

See `examples/formatting_demo.py` for a complete demonstration of the formatting utilities.

```bash
python examples/formatting_demo.py
```

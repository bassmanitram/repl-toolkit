# REPL Toolkit

[![Tests](https://github.com/bassmanitram/repl-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/test.yml)
[![Lint](https://github.com/bassmanitram/repl-toolkit/actions/workflows/lint.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/lint.yml)
[![Code Quality](https://github.com/bassmanitram/repl-toolkit/actions/workflows/quality.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/quality.yml)
[![Examples](https://github.com/bassmanitram/repl-toolkit/actions/workflows/examples.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/examples.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/repl-toolkit.svg)](https://pypi.org/project/repl-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Build interactive command-line applications with async Python. Create REPLs (Read-Eval-Print Loops) that feel like modern chat interfaces, complete with keyboard shortcuts, command history, and clipboard support.

## What is this for?

You're building a CLI tool that needs to:
- Accept user input interactively (like a chat bot, debugger, or query tool)
- Support both typed commands (`/help`, `/save`) and keyboard shortcuts (`F1`, `Ctrl+S`)
- Run async operations without blocking the interface
- Handle resources that need context managers (database connections, API clients)
- Paste images from clipboard into your application
- Work in both interactive mode and headless/batch mode

REPL Toolkit handles the terminal UI, input management, and action routing so you can focus on your application logic.

## Installation

```bash
pip install repl-toolkit
```

**Requirements**: Python 3.8+

## Your First REPL in 10 Lines

```python
import asyncio
from repl_toolkit import run_async_repl

class EchoBot:
    async def handle_input(self, user_input: str) -> bool:
        print(f"You said: {user_input}")
        return True

asyncio.run(run_async_repl(backend=EchoBot()))
```

Run it:
```bash
$ python my_repl.py
User: hello
You said: hello
User:
```

Press `Ctrl+D` or type `/exit` to quit. Press `F1` for help.

## How It Works

You provide a **backend** class with a `handle_input()` method. REPL Toolkit:
1. Shows a prompt and waits for user input
2. Handles special commands (`/help`, `/exit`) and keyboard shortcuts (`F1`, `Ctrl+C`)
3. Calls your `handle_input()` method with the text
4. Repeats

Your backend can be anything: a chatbot, a database query tool, a game, a debugger, etc.

## Adding Custom Commands and Shortcuts

Let's make a todo list app with commands and keyboard shortcuts:

```python
import asyncio
from repl_toolkit import AsyncREPL, ActionRegistry

class TodoBackend:
    def __init__(self):
        self.todos = []

    async def handle_input(self, user_input: str) -> bool:
        # Add user input as a todo item
        self.todos.append(user_input)
        print(f"✓ Added: {user_input}")
        return True

class TodoActions(ActionRegistry):
    def __init__(self):
        super().__init__()

        # Command + keyboard shortcut
        self.register_action(
            name="show_list",
            description="Show all todos",
            category="Todos",
            handler=self._show_list,
            command="/list",
            keys="F2"
        )

        # Command only
        self.register_action(
            name="clear_all",
            description="Clear all todos",
            category="Todos",
            handler=self._clear_all,
            command="/clear"
        )

    def _show_list(self, context):
        backend = context.backend
        if not backend.todos:
            print("No todos yet!")
        else:
            print(f"\n{len(backend.todos)} todos:")
            for i, todo in enumerate(backend.todos, 1):
                print(f"  {i}. {todo}")

    def _clear_all(self, context):
        backend = context.backend
        count = len(backend.todos)
        backend.todos.clear()
        print(f"Cleared {count} todos")

async def main():
    actions = TodoActions()
    backend = TodoBackend()
    repl = AsyncREPL(
        action_registry=actions,
        prompt_string="Todo: "
    )
    await repl.run(backend)

asyncio.run(main())
```

Now you can:
- Type anything to add a todo
- Type `/list` or press `F2` to see all todos
- Type `/clear` to clear the list
- Type `/help` or press `F1` to see all commands

## Error Handling

REPL Toolkit uses Python's standard logging framework for all error reporting. This gives you full control over whether errors are displayed, how they're formatted, and where they're sent.

**To see errors, configure logging in your application:**

```python
import asyncio
import logging
from repl_toolkit import run_async_repl

# Configure logging to see errors
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

class MyBackend:
    async def handle_input(self, user_input: str) -> bool:
        print(f"You said: {user_input}")
        return True

asyncio.run(run_async_repl(backend=MyBackend()))
```

### Error Visibility Options

**Show all errors (recommended default):**
```python
import logging
logging.basicConfig(level=logging.WARNING)
```

**Show only critical errors:**
```python
import logging
logging.basicConfig(level=logging.ERROR)
```

**Silent mode (suppress library errors):**
```python
import logging
logging.getLogger('repl_toolkit').setLevel(logging.CRITICAL)
```

**Custom formatting:**
```python
import logging

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))

logger = logging.getLogger('repl_toolkit')
logger.addHandler(handler)
logger.setLevel(logging.WARNING)
```

**Route to file:**
```python
import logging
logging.basicConfig(
    level=logging.WARNING,
    filename='app.log',
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

See Python's [logging documentation](https://docs.python.org/3/library/logging.html) for advanced configuration.


## Working with External Resources

Many backends need database connections, API clients, or other resources. REPL Toolkit supports late binding - you create the REPL first, then provide the backend when resources are ready:

```python
import asyncio
from repl_toolkit import AsyncREPL

class DatabaseBackend:
    def __init__(self, db):
        self.db = db

    async def handle_input(self, user_input: str) -> bool:
        result = await self.db.query(user_input)
        print(f"Result: {result}")
        return True

async def main():
    # Create REPL before database is available
    repl = AsyncREPL(prompt_string="SQL> ")

    # Connect to database in context manager
    async with database.connect() as db:
        backend = DatabaseBackend(db)
        # Now run REPL with connected backend
        await repl.run(backend, "Connected to database!")

asyncio.run(main())
```

This pattern works great with context managers, connection pools, and any resource that needs proper setup/teardown.

## Pasting from Clipboard

Your REPL can accept text and images from the clipboard. Users press `F6` to paste:

```python
import asyncio
from repl_toolkit import AsyncREPL

class ImageBot:
    async def handle_input(self, user_input: str, images=None) -> bool:
        print(f"Message: {user_input}")

        if images:
            for img_id, img_data in images.items():
                print(f"  Received {img_data.media_type} image: {len(img_data.data)} bytes")
                # img_data.data contains the raw image bytes
                # Send to your API, save to disk, etc.

        return True

async def main():
    backend = ImageBot()
    repl = AsyncREPL(enable_image_paste=True)  # Enabled by default
    await repl.run(backend)

asyncio.run(main())
```

Text handling is as expected.

With images, users can:
1. Copy an image to clipboard (screenshot, copy from browser, etc.)
2. Type their message in the REPL
3. Press `F6` to insert the image
4. Press `Alt+Enter` to send

The image appears as `{{image:img_001}}` in the text, and your backend receives both the text and the actual image data.

You then need to _process_ the image in whatever way your application needs to:

### Processing Images

The toolkit provides helpers for parsing messages with images:

```python
from repl_toolkit import iter_content_parts

async def handle_input(self, user_input: str, images=None) -> bool:
    # Iterate through text and images in order
    for content, image in iter_content_parts(user_input, images):
        if image:
            # Process image
            await api.upload_image(image.data, image.media_type)
        elif content:
            # Process text
            await api.send_text(content)

    return True
```

Supported formats: PNG, JPEG, GIF, WebP, BMP

### Image Utility Functions

The toolkit provides several utilities to work with image placeholders and data:

#### `parse_image_references(text)`

Parse text to find all image placeholders and extract their structure:

```python
from repl_toolkit.images import parse_image_references

text = "Look at {{image:img_001}} and {{image:img_002}}"
result = parse_image_references(text)

# result.image_ids is a set of image IDs found
print(result.image_ids)  # {'img_001', 'img_002'}

# result.parts is a list of (text, image_id) tuples
# Text parts have image_id=None, image parts have text=""
for text_part, img_id in result.parts:
    if img_id:
        print(f"Image placeholder: {img_id}")
    else:
        print(f"Text: {text_part}")
```

#### `iter_content_parts(text, images)`

Iterate through text and images in the order they appear:

```python
from repl_toolkit.images import iter_content_parts

async def handle_input(self, user_input: str, images=None) -> bool:
    # Process content in order
    for content, image in iter_content_parts(user_input, images):
        if image:
            # This is an image - image is an ImageData object
            print(f"Image: {image.media_type}, {len(image.data)} bytes")
            await upload_to_api(image.data, image.media_type)
        elif content:
            # This is text
            print(f"Text: {content}")
            await send_text(content)

    return True
```

#### `reconstruct_message(text, images, formatter)`

Transform a message with image placeholders into any format:

```python
from repl_toolkit.images import reconstruct_message
import base64

def format_for_api(content, image):
    """Convert text and images to API format."""
    if image:
        # Format image for API
        encoded = base64.b64encode(image.data).decode()
        return {
            'type': 'image',
            'source': {
                'type': 'base64',
                'media_type': image.media_type,
                'data': encoded
            }
        }
    else:
        # Format text for API
        return {
            'type': 'text',
            'text': content
        }

# Reconstruct the entire message
api_message = []
text = "Here's the image: {{image:img_001}}"
for content, image in iter_content_parts(text, images):
    api_message.append(format_for_api(content, image))

# Or use reconstruct_message for string output
def to_markdown(content, image):
    if image:
        return f"![image](data:{image.media_type};base64,...)"
    return content

markdown = reconstruct_message(text, images, to_markdown)
```

#### `detect_media_type(data)`

Detect image format from raw bytes:

```python
from repl_toolkit.images import detect_media_type

# Read image file
with open('image.png', 'rb') as f:
    img_bytes = f.read()

media_type = detect_media_type(img_bytes)
print(media_type)  # "image/png"
```

Detects: PNG, JPEG, GIF, WebP, BMP by examining magic bytes.

#### ImageData Object

When your backend receives images, each is an `ImageData` object:

```python
class ImageData:
    data: bytes           # Raw image bytes
    media_type: str       # MIME type like "image/png"
    timestamp: float      # When the image was captured
```

Access the data:

```python
async def handle_input(self, user_input: str, images=None) -> bool:
    if images:
        for img_id, img_data in images.items():
            # Save to file
            with open(f'{img_id}.png', 'wb') as f:
                f.write(img_data.data)

            # Upload to API
            await api.upload(
                data=img_data.data,
                content_type=img_data.media_type
            )

    return True
```


## Running Without a Terminal (Headless Mode)

Use your REPL in scripts, tests, or automation:

```python
import asyncio
from repl_toolkit import run_headless_mode

class BatchProcessor:
    async def handle_input(self, user_input: str) -> bool:
        result = await process_data(user_input)
        print(f"Processed: {result}")
        return True

asyncio.run(run_headless_mode(backend=BatchProcessor()))
```

Pipe input:
```bash
$ echo -e "Line 1\nLine 2\nLine 3" | python script.py
Processed: Line 1
Processed: Line 2
Processed: Line 3
```

Headless mode reads from stdin line by line and processes each one with your backend.

## Keyboard Shortcuts

Register shortcuts for common actions:

```python
# Function keys
self.register_action(
    name="help",
    handler=show_help,
    keys="F1"  # Press F1
)

# Modifier combinations
self.register_action(
    name="save",
    handler=save_data,
    keys="ctrl-s"  # Ctrl+S
)

# Multiple shortcuts for same action
self.register_action(
    name="refresh",
    handler=refresh_data,
    keys=["F5", "ctrl-r"]  # F5 or Ctrl+R
)
```

Common shortcuts:
- `"F1"` through `"F12"` - Function keys
- `"ctrl-s"` - Ctrl+S
- `"alt-h"` - Alt+H
- `"ctrl-alt-d"` - Ctrl+Alt+D

## Built-in Commands

Every REPL includes these by default:

| Command | Shortcut | What it does |
|---------|----------|--------------|
| `/help [action]` | `F1` | Show help for all actions or a specific one |
| `/shortcuts` | - | List all keyboard shortcuts |
| `/exit` or `/quit` | - | Exit the application |
| `/paste-image` | `F6` | Paste image from clipboard |

## Handling Action Context

Your action handlers receive context about how they were called:

```python
def my_action(context):
    # Access the backend
    backend = context.backend

    # Check how action was triggered
    if context.triggered_by == "command":
        # User typed "/myaction arg1 arg2"
        args = context.args  # ["arg1", "arg2"]
        print(f"Args: {args}")

    elif context.triggered_by == "shortcut":
        # User pressed keyboard shortcut
        print("Triggered by keyboard")

    # Access the full command
    if context.user_input:
        print(f"Full input: {context.user_input}")
```

## Auto-completion

Add tab completion for commands, file paths, or custom values:

```python
from repl_toolkit import AsyncREPL
from repl_toolkit.completion import PrefixCompleter

# Complete slash commands
completer = PrefixCompleter(
    prefix="/",
    words=["help", "save", "load", "quit"]
)

repl = AsyncREPL(completer=completer)
```

Users can press `Tab` to complete `/he` → `/help`.

See [repl_toolkit/completion/README.md](repl_toolkit/completion/README.md) for advanced completion features including shell command expansion and environment variables.

## Full Example: Chat Bot with Commands

```python
import asyncio
from repl_toolkit import AsyncREPL, ActionRegistry

class ChatBot:
    def __init__(self):
        self.history = []
        self.model = "gpt-4"

    async def handle_input(self, user_input: str) -> bool:
        self.history.append(f"User: {user_input}")

        # Simulate API call
        await asyncio.sleep(0.5)
        response = f"[{self.model}] Response to: {user_input}"

        self.history.append(f"Bot: {response}")
        print(response)
        return True

class ChatActions(ActionRegistry):
    def __init__(self):
        super().__init__()

        self.register_action(
            name="history",
            description="Show conversation history",
            category="Chat",
            handler=self._show_history,
            command="/history",
            keys="F2"
        )

        self.register_action(
            name="model",
            description="Change AI model",
            category="Config",
            handler=self._change_model,
            command="/model",
            command_usage="/model <model-name>"
        )

        self.register_action(
            name="clear",
            description="Clear conversation history",
            category="Chat",
            handler=self._clear_history,
            command="/clear",
            keys="F3"
        )

    def _show_history(self, context):
        backend = context.backend
        if not backend.history:
            print("No conversation history")
        else:
            print("\n=== History ===")
            for line in backend.history:
                print(line)

    def _change_model(self, context):
        backend = context.backend
        if context.args:
            backend.model = context.args[0]
            print(f"Switched to model: {backend.model}")
        else:
            print(f"Current model: {backend.model}")

    def _clear_history(self, context):
        backend = context.backend
        count = len(backend.history)
        backend.history.clear()
        print(f"Cleared {count} messages")

async def main():
    actions = ChatActions()
    backend = ChatBot()

    repl = AsyncREPL(
        action_registry=actions,
        prompt_string="You: "
    )

    await repl.run(backend, "Chat bot ready! Type /help for commands.")

if __name__ == "__main__":
    asyncio.run(main())
```


## Important: Blocking Operations

**Alt+C and Ctrl+C can only cancel async operations.** If your backend does synchronous blocking work (like `subprocess.run()`, `time.sleep()`, or blocking I/O), cancellation won't work until that operation completes.

### The Problem

```python
class BlockingBackend:
    async def handle_input(self, user_input: str) -> bool:
        # This BLOCKS the event loop - cancellation won't work
        subprocess.run(["sleep", "60"], check=True)  # User is stuck for 60 seconds
        return True
```

When you press Alt+C, Python can only cancel at `await` points. The synchronous `subprocess.run()` blocks everything.

### The Solution: Use Async APIs

```python
class NonBlockingBackend:
    async def handle_input(self, user_input: str) -> bool:
        # This is async - cancellation works immediately
        proc = await asyncio.create_subprocess_exec(
            "sleep", "60",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()  # Can be cancelled here
        return True
```

### Quick Reference

**Don't do this** (blocks event loop):
```python
time.sleep(10)                          # Use: await asyncio.sleep(10)
subprocess.run(["cmd"])                 # Use: await asyncio.create_subprocess_exec()
requests.get(url)                       # Use: async with aiohttp.ClientSession()
file.read()                             # Use: async with aiofiles.open()
socket.recv()                           # Use: asyncio streams
while True: compute()                   # Use: await asyncio.sleep(0) in loop
```

**Do this instead** (cancellable):
```python
await asyncio.sleep(10)
proc = await asyncio.create_subprocess_exec("cmd")
async with aiohttp.ClientSession() as session:
    await session.get(url)
async with aiofiles.open(path) as f:
    await f.read()
reader, writer = await asyncio.open_connection(host, port)
while True:
    await asyncio.sleep(0)  # Yield to event loop
    compute()
```

### Using Executors for Blocking Code

If you must use blocking code, run it in an executor so it doesn't block cancellation:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class BackendWithBlocking:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)

    def blocking_operation(self, arg):
        """This is a blocking function."""
        import time
        time.sleep(10)
        return f"Result: {arg}"

    async def handle_input(self, user_input: str) -> bool:
        # Run blocking code in executor - cancellable
        try:
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.blocking_operation,
                    user_input
                ),
                timeout=None  # Or set a timeout
            )
            print(result)
        except asyncio.CancelledError:
            print("Operation cancelled!")
            raise  # Re-raise to complete cancellation
        return True
```

**Note**: Running in an executor means the operation will complete in the background even after cancellation. The thread can't be stopped, but your async code can continue.

### Running Shell Commands Properly

```python
async def handle_input(self, user_input: str) -> bool:
    try:
        # Create process
        proc = await asyncio.create_subprocess_shell(
            user_input,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for completion (cancellable)
        stdout, stderr = await proc.communicate()

        print(stdout.decode())
        if stderr:
            print(f"Error: {stderr.decode()}", file=sys.stderr)

        return True

    except asyncio.CancelledError:
        # Kill the process on cancellation
        proc.kill()
        await proc.wait()
        print("Command cancelled")
        raise
```

### Why This Matters

Python's async is **cooperative** - your code must regularly yield control back to the event loop with `await`. If you don't, nothing else can run, including cancellation handlers.

Think of it like this:
- **Async code**: "I'll do this work, but I'll check for cancellation regularly"
- **Blocking code**: "I'm doing this and nothing can stop me until I'm done"

The REPL Toolkit can't make blocking code cancellable - that's a Python limitation. But by using async APIs throughout your backend, you get responsive cancellation for free.
## Testing Your REPL

Use headless mode for tests:

```python
import asyncio
import pytest
from repl_toolkit import HeadlessREPL

@pytest.mark.asyncio
async def test_backend():
    backend = MyBackend()
    repl = HeadlessREPL(backend=backend)

    # Simulate user input
    result = await repl.process_line("test input")
    assert result == True
```

## Configuration Options

### AsyncREPL

```python
repl = AsyncREPL(
    action_registry=actions,          # Your custom actions
    completer=completer,               # Tab completion
    prompt_string=">>> ",              # Custom prompt
    history_path=Path("~/.myapp_history"),  # Command history file
    enable_image_paste=True,           # Image clipboard support
    enable_system_prompt=True,         # Enable Esc+! for shell commands
)
```

### ActionRegistry

```python
registry.register_action(
    name="action_name",               # Unique identifier
    description="What it does",       # Shown in help
    category="Category",               # Group in help display
    handler=handler_function,          # Your function
    command="/cmd",                    # Optional: typed command
    command_usage="/cmd [args]",       # Optional: usage text
    keys="F5",                         # Optional: keyboard shortcut
    keys_description="Quick action",   # Optional: shortcut description
    enabled=True                       # Optional: enable/disable
)
```

## Real-World Use Cases

REPL Toolkit is useful for building:

- **Database Query Tools** - Interactive SQL or NoSQL clients with command history, query shortcuts, and result formatting
- **Chat Bot Interfaces** - Conversational AI frontends with image support, history management, and quick actions
- **API Testing Tools** - Send HTTP requests interactively with shortcuts for authentication, common endpoints, and response inspection
- **Game Consoles** - Debug commands and cheats during development with quick shortcuts for common operations
- **Log Analyzers** - Query and filter logs interactively with custom commands for common patterns
- **Configuration Managers** - Edit settings interactively with validation and shortcuts for common configurations
- **Monitoring Dashboards** - Command-line monitoring tools with refresh shortcuts and alert management
- **Development Tools** - Any tool that needs interactive command input with a good user experience

The toolkit handles the terminal UI, keyboard shortcuts, and command routing so you can focus on your application's logic.

## Examples

Working examples are in the `examples/` directory:

```bash
# Basic echo REPL
python examples/basic_usage.py

# Advanced with custom actions
python examples/advanced_usage.py

# Image paste demo
python examples/image_paste_demo.py

# Completion examples
python examples/completion_demo.py
```

## API Quick Reference

### Core Classes

```python
from repl_toolkit import AsyncREPL, ActionRegistry, Action

# Create a REPL
repl = AsyncREPL(
    action_registry=actions,
    prompt_string=">>> ",
    history_path=Path("~/.history")
)

# Run with backend
await repl.run(backend, initial_message="Ready!")

# Register an action
actions.register_action(
    name="my_action",
    description="Description",
    category="Category",
    handler=handler_func,
    command="/cmd",
    keys="F5"
)
```

### Protocols (Interfaces)

Your backend must implement:

```python
class MyBackend:
    async def handle_input(self, user_input: str, **kwargs) -> bool:
        # Process input, return True for success
        return True
```

For images, accept the `images` kwarg:

```python
async def handle_input(self, user_input: str, images=None, **kwargs) -> bool:
    if images:
        for img_id, img_data in images.items():
            # Process img_data.data (bytes)
            # img_data.media_type (e.g., "image/png")
            pass
    return True
```

### Convenience Functions

```python
from repl_toolkit import run_async_repl, run_headless_mode

# Quick start
await run_async_repl(backend=backend, prompt_string=">>> ")

# Headless/batch mode
await run_headless_mode(backend=backend, initial_message="Starting...")
```

## Advanced Features

### Formatting Utilities

Auto-format HTML or ANSI codes in output:

```python
from repl_toolkit import create_auto_printer

printer = create_auto_printer()
printer("<b>Bold text</b>")  # Automatically rendered as bold
printer("\x1b[31mRed text\x1b[0m")  # Automatically rendered as red
```

See `examples/formatting_demo.py` for details.

### Custom Completion

Build sophisticated auto-completion:

```python
from repl_toolkit.completion import ShellExpansionCompleter

# Expand $VAR and $(command) on tab
completer = ShellExpansionCompleter()
repl = AsyncREPL(completer=completer)
```

See [repl_toolkit/completion/README.md](repl_toolkit/completion/README.md) for details.

## Development

```bash
# Clone and install
git clone https://github.com/bassmanitram/repl-toolkit.git
cd repl-toolkit
pip install -e ".[dev,test]"

# Run tests
pytest

# Check types
mypy repl_toolkit/

# Format code
black repl_toolkit/
isort repl_toolkit/
```

## Troubleshooting

**"No module named 'repl_toolkit'"**
```bash
pip install repl-toolkit
```

**Image paste doesn't work**
```bash
pip install pyclip
```

**Keyboard shortcuts don't work**
- Some terminals don't support all key combinations
- Try function keys (F1-F12) which work everywhere
- Check your terminal's key binding settings

**Tests fail on import**
- Make sure you're using Python 3.8+
- Install test dependencies: `pip install pytest pytest-asyncio`

## Links

- **Documentation**: [repl-toolkit.readthedocs.io](https://repl-toolkit.readthedocs.io/)
- **PyPI**: [pypi.org/project/repl-toolkit](https://pypi.org/project/repl-toolkit/)
- **Source**: [github.com/bassmanitram/repl-toolkit](https://github.com/bassmanitram/repl-toolkit)
- **Issues**: [github.com/bassmanitram/repl-toolkit/issues](https://github.com/bassmanitram/repl-toolkit/issues)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

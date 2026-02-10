# REPL Toolkit

Build interactive command-line applications with async Python. Create REPLs (Read-Eval-Print Loops) that feel like modern chat interfaces, complete with keyboard shortcuts, command history, and clipboard support.

[![Tests](https://github.com/bassmanitram/repl-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/test.yml)
[![Lint](https://github.com/bassmanitram/repl-toolkit/actions/workflows/lint.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/lint.yml)
[![Code Quality](https://github.com/bassmanitram/repl-toolkit/actions/workflows/quality.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/quality.yml)
[![Examples](https://github.com/bassmanitram/repl-toolkit/actions/workflows/examples.yml/badge.svg)](https://github.com/bassmanitram/repl-toolkit/actions/workflows/examples.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/repl-toolkit.svg)](https://pypi.org/project/repl-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is this for?

Build interactive terminal apps where users type messages and get responses - like chat bots, database queries, or system monitoring tools. REPL Toolkit handles the terminal UI, keyboard shortcuts, and command routing so you focus on your application's logic.

- Support both typed commands (`/help`, `/save`) and keyboard shortcuts (`F1`, `Ctrl+S`)
- Works with async backends (API calls, database queries, etc.)
- Handle images from clipboard
- Full customization of commands and shortcuts

## Quick Start

Install with pip:

```bash
pip install repl-toolkit
```

Create a simple echo bot:

```python
import asyncio
from repl_toolkit import AsyncREPL

class EchoBot:
    async def handle_input(self, user_input: str) -> bool:
        print(f"You said: {user_input}")
        return True

async def main():
    backend = EchoBot()
    repl = AsyncREPL()
    await repl.run(backend)

asyncio.run(main())
```

Run it:
```bash
python echo_bot.py
```

Now you have an interactive chat interface with:
1. Multiline input (Enter for new line, Alt+Enter to send)
2. Handles special commands (`/help`, `/exit`) and keyboard shortcuts (`F1`, `Ctrl+C`)
3. Command history (Up/Down arrows)
4. Async support for API calls or other I/O

## Real Example: Todo List

Let's make a todo list app with commands and keyboard shortcuts:

```python
import asyncio
from repl_toolkit import AsyncREPL, ActionRegistry, Action, ActionContext

class TodoBackend:
    def __init__(self):
        self.todos = []

    async def handle_input(self, user_input: str) -> bool:
        self.todos.append(user_input)
        print(f"Added: {user_input}")
        return True

def setup_actions(backend):
    """Create actions for todo management."""
    registry = ActionRegistry()

    # List todos with F2 or /list
    def list_handler(context: ActionContext):
        if not backend.todos:
            print("No todos yet!")
        else:
            print("\nTodos:")
            for i, todo in enumerate(backend.todos, 1):
                print(f"  {i}. {todo}")

    registry.register_action(Action(
        name="list_todos",
        description="Show all todos",
        handler=list_handler,
        keys="F2",
        command="/list",
    ))

    # Clear list
    def clear_handler(context: ActionContext):
        backend.todos.clear()
        print("Cleared all todos!")

    registry.register_action(Action(
        name="clear_todos",
        description="Clear all todos",
        handler=clear_handler,
        command="/clear"
    ))

    return registry

async def main():
    backend = TodoBackend()
    actions = setup_actions(backend)
    repl = AsyncREPL(action_registry=actions)
    await repl.run(backend, "Todo list ready! Type something to add a todo.")

asyncio.run(main())
```

Usage:
- Type anything to add a todo
- Type `/list` or press `F2` to see all todos
- Type `/clear` to clear the list
- Type `/help` or press `F1` to see all commands
- Commands execute immediately when you press Enter
- For normal text, press Alt+Enter to send

## Error Handling

REPL Toolkit uses Python's standard logging framework for all error reporting. This gives you full control over whether errors are displayed, how they're formatted, and where they're sent.

**To see errors, configure logging in your application:**

```python
import logging

# Option 1: Simple setup - show all errors
logging.basicConfig(level=logging.WARNING)

# Option 2: Custom format
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)

# Option 3: File output
logging.basicConfig(
    filename='repl.log',
    level=logging.DEBUG
)

# Option 4: Detailed control
logger = logging.getLogger('repl_toolkit')
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)
```

**What gets logged:**
- `ERROR`: Action execution failures, clipboard errors, critical issues
- `WARNING`: Non-critical issues (missing dependencies, invalid configs)
- `DEBUG`: Detailed execution flow (useful for troubleshooting)

**Production recommendation:**
```python
# Show warnings and errors, hide debug details
logging.basicConfig(level=logging.WARNING)
```

**Development recommendation:**
```python
# See everything for troubleshooting
logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')
```

If you don't configure logging, errors will be silent (Python's default behavior).

## Image Support

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
3. Press `F6` or type `/paste` to insert the image
4. Press `Alt+Enter` to send

The image appears as `{{image:img_001}}` in the text, and your backend receives both the text and the actual image data.

You then need to _process_ the image in whatever way your application needs to:

### Processing Images

```python
from repl_toolkit import parse_image_references, iter_content_parts

class SmartBackend:
    async def handle_input(self, user_input: str, images=None) -> bool:
        # Option 1: Simple check
        if images:
            print(f"Got {len(images)} images")

        # Option 2: Parse placeholders
        parsed = parse_image_references(user_input)
        print(f"Text references these images: {parsed.image_ids}")

        # Option 3: Iterate through message parts
        for content, image in iter_content_parts(user_input, images):
            if image:
                # Process image
                print(f"Image: {len(image.data)} bytes of {image.media_type}")
                # save_image(image.data)
                # upload_to_api(image.data, image.media_type)
            elif content:
                # Process text
                print(f"Text: {content}")

        return True
```

**Real-world examples:**
- **Claude/ChatGPT clients** - Send images to multimodal AI APIs
- **Support tools** - Users paste screenshots with bug reports
- **Documentation** - Generate docs with embedded images
- **Data annotation** - Label images with text descriptions

See [examples/image_paste_demo.py](examples/image_paste_demo.py) for a complete working example.

## Tab Completion

Add tab completion for commands and custom values:

```python
from repl_toolkit import AsyncREPL, PrefixCompleter

# Complete slash commands
completer = PrefixCompleter(["/help", "/save", "/load", "/exit"])

# Or complete custom values
completer = PrefixCompleter(["apple", "banana", "cherry"])

repl = AsyncREPL(completer=completer)
```

**Features:**
- Complete commands at line start or after newline
- Won't complete mid-sentence (e.g., won't complete in "Please type /help")
- Prefix-only matching (no fuzzy search)

See [repl_toolkit/completion/README.md](repl_toolkit/completion/README.md) for advanced completion features including shell command expansion and environment variables.

## Headless Mode

Process input from stdin instead of interactive prompts - perfect for:
- Piping data: `cat input.txt | python my_tool.py`
- Batch processing: `python my_tool.py < batch.txt`
- Automated testing

```python
import asyncio
from repl_toolkit import run_headless_mode

class BatchProcessor:
    async def handle_input(self, text: str) -> bool:
        result = text.upper()  # Your processing logic
        print(f"Processed: {result}")
        return True

async def main():
    backend = BatchProcessor()
    success = await run_headless_mode(backend)
    return 0 if success else 1

exit(asyncio.run(main()))
```

Input format:
```
First line of input
Second line
/send
More content here
Another line
/send
```

- Content accumulates until `/send`
- Each `/send` triggers backend processing
- EOF auto-sends remaining content
- Commands like `/help` work normally

See [examples/headless_usage.py](examples/headless_usage.py) for a complete example with statistics tracking.

## Actions Deep Dive

Actions provide both typed commands and keyboard shortcuts for the same functionality:

```python
from repl_toolkit import Action, ActionContext

def save_handler(context: ActionContext):
    """Save the conversation."""
    # Get arguments if it was a command
    if context.args:
        filename = context.args[0]
    else:
        filename = "default.txt"

    # Your save logic here
    print(f"Saved to {filename}")

    # Know how it was triggered
    if context.triggered_by == "shortcut":
        print("(via Ctrl+S)")

action = Action(
    name="save",
    description="Save conversation",
    category="File",
    handler=save_handler,
    keys="c-s",              # Ctrl+S
    command="/save",
    command_usage="/save [filename]"
)

registry = ActionRegistry()
registry.register_action(action)
```

### Built-in Actions

Every REPL includes these by default:

| Command | Shortcut | Description |
|---------|----------|-------------|
| `/help [action]` | `F1` | Show help for all actions or a specific one |
| `/shortcuts` | - | List all keyboard shortcuts |
| `/exit` or `/quit` | - | Exit the application |
| `/paste` | `F6` | Paste image or text from clipboard |
| - | `F7` or `Escape, Escape` | Clear the input buffer |

Commands execute immediately when you press Enter. For normal text messages, press Alt+Enter to send.

## Handling Action Context

Your action handlers receive context about how they were called:

```python
def my_handler(context: ActionContext):
    # How was it triggered?
    if context.triggered_by == "command":
        print("User typed the command")
    elif context.triggered_by == "shortcut":
        print("User pressed the keyboard shortcut")

    # Command arguments (if triggered by command)
    if context.args:
        print(f"Arguments: {context.args}")

    # Access the full command
    if context.command:
        print(f"Full command: {context.command}")

    # Access other components
    context.registry  # The action registry
    context.repl      # The REPL instance
    context.backend   # Your backend
```

Add tab completion for commands, file paths, or custom values:

```python
from repl_toolkit import PrefixCompleter, ShellExpansionCompleter

# Complete slash commands
completer = PrefixCompleter(["/help", "/history", "/model"])

# Or use shell-style completion with variables and commands
completer = ShellExpansionCompleter(
    commands=["/help", "/history"],
    enable_env_vars=True,        # Complete $VAR
    enable_command_sub=True      # Complete $(command)
)
```

See [repl_toolkit/completion/README.md](repl_toolkit/completion/README.md) for advanced completion features including shell command expansion and environment variables.

## Advanced Example: Chat Bot

A more complete example with commands, shortcuts, and conversation history:

```python
import asyncio
from repl_toolkit import AsyncREPL, ActionRegistry, Action, ActionContext

class ChatBackend:
    def __init__(self):
        self.history = []
        self.model = "gpt-4"

    async def handle_input(self, user_input: str) -> bool:
        self.history.append({"role": "user", "content": user_input})

        # Your AI API call here
        response = f"[{self.model}] Echo: {user_input}"

        self.history.append({"role": "assistant", "content": response})
        print(response)
        return True

def create_actions(backend):
    registry = ActionRegistry()

    # Show conversation history
    registry.register_action(Action(
        name="show_history",
        description="Show conversation history",
        handler=lambda ctx: print("\n".join(
            f"{msg['role']}: {msg['content']}" for msg in backend.history
        )),
        command="/history",
        keys="F3"
    ))

    # Switch model
    def switch_model(ctx: ActionContext):
        if ctx.args:
            backend.model = ctx.args[0]
            print(f"Switched to {backend.model}")
        else:
            print(f"Current model: {backend.model}")

    registry.register_action(Action(
        name="switch_model",
        description="Switch AI model",
        handler=switch_model,
        command="/model",
        command_usage="/model <model-name>"
    ))

    # Clear history
    registry.register_action(Action(
        name="clear",
        description="Clear conversation history",
        handler=lambda ctx: (backend.history.clear(), print("History cleared!")),
        command="/clear",
        keys="F4"
    ))

    return registry

async def main():
    backend = ChatBackend()
    actions = create_actions(backend)

    repl = AsyncREPL(
        action_registry=actions,
        prompt_string="<b>You:</b> ",
        history_path=Path.home() / ".chatbot_history"
    )

    await repl.run(backend, "Chat bot ready! Type /help for commands.")

asyncio.run(main())
```

## API Overview

### Main Classes

```python
from repl_toolkit import (
    AsyncREPL,                     # Interactive REPL with UI
    run_headless_mode,             # Process stdin without UI
    ActionRegistry,                # Manage commands and shortcuts
    Action,                        # Define a command/shortcut
    ActionContext,                 # Context passed to handlers
    PrefixCompleter,               # Tab completion
    ShellExpansionCompleter,       # Advanced tab completion
)
```

### AsyncREPL Options

```python
repl = AsyncREPL(
    action_registry=None,              # Optional action registry
    completer=None,                    # Optional tab completer
    prompt_string="User: ",            # Custom prompt
    history_path=None,                 # Optional history file
    enable_image_paste=True,           # Image clipboard support
)
```

### Action Definition

```python
action = Action(
    name="my_action",                  # Unique identifier
    description="What it does",       # Help text
    category="General",                # Optional: group in help
    handler=my_function,               # Called when triggered
    keys="F2",                         # Optional: keyboard shortcut
    keys_description="...",            # Optional: help for shortcut
    command="/cmd",                    # Optional: typed command
    command_usage="/cmd [args]",       # Optional: usage text
    enabled=True                       # Optional: enable/disable
)
```

**Key formats:**
- Function keys: `"F1"`, `"F2"`, ..., `"F12"`
- Control: `"c-s"` (Ctrl+S), `"c-q"` (Ctrl+Q)
- Alt/Escape: `"escape"` followed by key
- Control+Shift: `"c-s-v"` (Ctrl+Shift+V)

## Use Cases

REPL Toolkit is designed for any interactive terminal application:

- **AI Chat Clients** - Talk to Claude, ChatGPT, or local models with keyboard shortcuts for common operations
- **Database Query Tools** - Interactive SQL or NoSQL clients with command history, query shortcuts, and result formatting
- **System Monitoring** - Watch logs, metrics, or system status with commands to filter, search, or change views
- **Configuration Editors** - Interactive config file editing with validation and shortcuts for common changes
- **Game Consoles** - Debug commands and cheats during development with quick shortcuts for common operations
- **Log Analyzers** - Query and filter logs interactively with custom commands for common patterns
- **Data Processing** - Interactive data transformation with commands for different operations and live preview
- **API Clients** - Test and explore APIs interactively with shortcuts for common requests
- **Development Tools** - Any tool that needs interactive command input with a good user experience

The toolkit handles the terminal UI, keyboard shortcuts, and command routing so you can focus on your application's logic.

## Examples

The [examples/](examples/) directory contains working examples:

```bash
# Basic usage - simple echo bot
python examples/basic_usage.py

# Advanced - chat bot with history and commands
python examples/advanced_usage.py

# Headless - process input from stdin
echo -e "Line 1\nLine 2\n/send" | python examples/headless_usage.py

# Image paste demo
python examples/image_paste_demo.py

# Tab completion
python examples/completion_demo.py
```

## Implementing Cancellable Backends

Backends can optionally implement cooperative cancellation to gracefully handle cancellation of long-running operations, especially those involving blocking I/O like subprocess calls or HTTP requests.

### Basic Implementation

```python
from typing import Optional

class CancellableBackend:
    def __init__(self):
        self._cancel_requested = False
    
    def cancel(self, message: Optional[str] = None) -> None:
        """Optional method to support cooperative cancellation."""
        self._cancel_requested = True
        if message:
            print(f"Cancellation: {message}")
    
    async def handle_input(self, user_input: str, **kwargs) -> bool:
        """Process input with cancellation checkpoints."""
        # Reset flag at start of each operation
        self._cancel_requested = False
        
        # Process in steps with cancellation checkpoints
        for step in self._get_processing_steps(user_input):
            # Check for cancellation at safe points
            if self._cancel_requested:
                print("Operation cancelled.")
                return False
            
            # Do work
            await self._process_step(step)
        
        return True
```

### When cancel() is Called

The REPL automatically calls `backend.cancel()` (if implemented) when:
- User presses **Alt+C** during operation
- User presses **Ctrl+C** during operation  
- Exception occurs during processing

**Note**: The `cancel()` method is optional. Backends without it will fall back to async task cancellation only (via `asyncio.Task.cancel()`), which may not work for blocking operations.

### Example: Cancelling Subprocess

```python
import asyncio
import subprocess
from typing import Optional

class SubprocessBackend:
    def __init__(self):
        self._cancel_requested = False
        self._current_process = None
    
    def cancel(self, message: Optional[str] = None) -> None:
        """Cancel current subprocess."""
        self._cancel_requested = True
        if self._current_process:
            self._current_process.terminate()  # Stop the subprocess
    
    async def handle_input(self, user_input: str, **kwargs) -> bool:
        """Run command with cancellation support."""
        self._cancel_requested = False
        
        try:
            # Run subprocess in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def run_command():
                if self._cancel_requested:
                    return None
                self._current_process = subprocess.Popen(
                    user_input.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = self._current_process.communicate()
                return stdout.decode()
            
            result = await loop.run_in_executor(None, run_command)
            
            if result is None:
                print("Command cancelled.")
                return False
            
            print(result)
            return True
            
        finally:
            self._current_process = None
```

### Guidelines for cancel() Implementation

1. **Non-blocking**: Method must return immediately
2. **Set flag**: Use internal flag that handle_input() checks
3. **Reset flag**: Clear at start of each operation
4. **Safe checkpoints**: Only check flag at safe cancellation points
5. **Cleanup**: Release resources when cancellation detected

## Action Output Best Practices

Actions in **interactive mode** automatically use prompt_toolkit's output functions to maintain clean prompt display. You don't need to do anything special - just use `context.printer`:

```python
def my_action(context: ActionContext):
    # Recommended: Use context.printer
    context.printer("This output maintains clean prompt display")
    context.printer("Multiple lines work correctly")
    
    # Also works: Standard print() is automatically patched
    print("This also works and maintains prompt")
```

**Why this matters**: In interactive mode, standard `print()` can corrupt the prompt display. The toolkit automatically handles this by:
- Using `print_formatted_text()` for action output
- Wrapping the prompt in `patch_stdout()` to catch any print() calls

**Headless mode**: Continues to use standard `print()` (correct for logs/pipes).

### Formatted Output

Interactive mode supports rich formatting:

```python
from prompt_toolkit import HTML, ANSI

def formatted_action(context: ActionContext):
    # HTML-style formatting
    context.printer(HTML('<b>Bold</b> <green>Green</green>'))
    
    # ANSI codes
    context.printer(ANSI('\x1b[1mBold text\x1b[0m'))
    
    # Plain text (always works)
    context.printer('Plain text')
```

## Advanced Features

### Custom Action Context

Pass additional context to your action handlers:

```python
def my_handler(context: ActionContext):
    # Built-in context
    command = context.command
    args = context.args
    triggered_by = context.triggered_by

    # Your custom data via backend
    backend = context.backend
    user_settings = backend.user_settings
```

### Shell Expansion in Completion

```python
from repl_toolkit import ShellExpansionCompleter

completer = ShellExpansionCompleter(
    commands=["/help", "/load"],
    enable_env_vars=True,        # $HOME, $USER, etc.
    enable_command_sub=True,     # $(echo foo)
    enable_tilde=True,           # ~/Documents
)
# Expand $VAR and $(command) on tab
```

### Dynamic Actions

Enable/disable actions at runtime:

```python
# Disable an action
registry.get_action("save").enabled = False

# Re-enable it
registry.get_action("save").enabled = True
```

### Custom Formatters

The toolkit uses [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/) under the hood. You can use HTML-style formatting in prompts and output:

```python
from prompt_toolkit import HTML

# In prompts
repl = AsyncREPL(prompt_string=HTML("<b>You:</b> "))

# In output
print(HTML("<green>Success!</green>"))
print(HTML("<red>Error!</red>"))
```

## Troubleshooting

**Commands don't work**
- Make sure you're using `ActionRegistry` and registering actions
- Check action names are unique
- Commands execute immediately on Enter; press Alt+Enter for normal text

**Keyboard shortcuts don't work**
- Verify key format: `"F1"`, `"c-s"`, etc.
- Some terminals don't support all key combinations
- Try function keys (`F1`-`F12`) - they work everywhere

**Image paste doesn't work**
- Install pyclip: `pip install pyclip`
- Verify clipboard access on your system
- Linux may need `xclip` or `xsel`: `apt-get install xclip`

**History not saving**
- Check `history_path` is writable
- Parent directory must exist
- Example: `Path.home() / ".myapp_history"`

**Tab completion not working**
- Pass `completer` to `AsyncREPL` constructor
- Verify completion items are strings
- Commands only complete at line start or after newlines

## Requirements

- Python 3.8+
- prompt-toolkit 3.0+
- pyclip 0.7+ (optional, for image paste support)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built on [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for terminal handling.

## Changes

See [CHANGELOG.md](CHANGELOG.md) for version history.

# REPL Toolkit

A Python toolkit for building interactive REPL (Read-Eval-Print Loop) and headless command-line interfaces. This package provides reusable components for creating conversational applications, chatbots, and interactive shells.

## Features

- **Async REPL Interface**: Full-featured interactive shell with history, key bindings, and cancellation support
- **Headless Mode**: Non-interactive interface for scripted or piped input
- **Extensible Command System**: Plugin-based command architecture
- **Clean Abstractions**: Protocol-based design for easy integration with any backend
- **Type Safety**: Full type hints for better development experience

## Installation

```bash
pip install repl-toolkit
```

For development:
```bash
pip install repl-toolkit[dev]
```

## Quick Start

### Async REPL

```python
import asyncio
from repl_toolkit import AsyncREPL
from repl_toolkit.types import AsyncBackend

class MyBackend(AsyncBackend):
    async def handle_input(self, user_input: str) -> bool:
        print(f"Processing: {user_input}")
        return True  # Return False to indicate failure

async def main():
    backend = MyBackend()
    repl = AsyncREPL(backend)
    await repl.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Headless Mode

```python
import asyncio
from repl_toolkit import run_headless_mode
from repl_toolkit.types import HeadlessBackend

class MyBackend(HeadlessBackend):
    async def handle_input(self, user_input: str) -> bool:
        print(f"Processing: {user_input}")
        return True

async def main():
    backend = MyBackend()
    await run_headless_mode(backend, initial_message="Hello!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture

The toolkit is built around clean abstractions:

- **Backend Protocols**: Define how your application processes input
- **Command System**: Extensible command handling with `/command` syntax
- **UI Components**: Reusable REPL and headless interfaces
- **Type Safety**: Full typing support for better development experience

## Components

### AsyncREPL
- Interactive shell with prompt_toolkit
- History support
- Key bindings (Alt+Enter to send, Alt+C to cancel)
- Graceful cancellation of long-running operations
- Customizable prompts and completers

### Headless Mode
- Non-interactive input processing
- Supports piped input and scripting
- `{{send}}` command for explicit message boundaries
- Suitable for automation and testing

### Command System
- Extensible `/command` handling
- Built-in help system
- Easy command registration
- Validation and error handling

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.
# REPL Toolkit - Agent Bootstrap Documentation

**Last Updated:** 2025-12-03  
**Version:** 2.0.2  
**Purpose:** Project context for AI development assistants

---

## Project Overview

**REPL Toolkit** is a production-ready Python library for building interactive command-line applications with async support. It provides a modern REPL (Read-Eval-Print Loop) framework that handles terminal UI, keyboard shortcuts, command routing, and both interactive and headless (batch) processing modes.

### What This Library Does

- **Interactive Terminal UIs**: Build chat-like interfaces for CLIs
- **Unified Action System**: Single API for both typed commands (`/help`) and keyboard shortcuts (`F1`)
- **Async-Native**: Full asyncio support for API calls, database queries, etc.
- **Image Clipboard Support**: Handle images from clipboard alongside text
- **Headless Mode**: Process stdin for batch operations and pipelines
- **Tab Completion**: Customizable completion for commands and values

### Target Use Cases

- AI chat clients (Claude, ChatGPT, local models)
- Database query tools (SQL/NoSQL interactive clients)
- System monitoring dashboards
- Configuration editors with validation
- Game development consoles
- Log analysis tools
- API testing clients

---

## Repository Structure

```
repl-toolkit/
├── repl_toolkit/              # Main package
│   ├── __init__.py           # Public API exports
│   ├── async_repl.py         # Interactive REPL implementation
│   ├── headless_repl.py      # Stdin batch processing
│   ├── ptypes.py             # Protocol definitions (AsyncBackend, etc.)
│   ├── formatting.py         # Auto-formatting utilities (JSON, YAML, etc.)
│   ├── images.py             # Image clipboard handling
│   ├── actions/              # Action system
│   │   ├── action.py         # Action and ActionContext dataclasses
│   │   └── registry.py       # ActionRegistry implementation
│   ├── completion/           # Tab completion
│   │   ├── prefix.py         # Simple prefix completion
│   │   ├── shell_expansion.py # Shell-style completion ($VAR, etc.)
│   │   └── README.md         # Completion system docs
│   └── tests/                # Test suite
│       ├── test_async_repl.py
│       ├── test_headless.py
│       ├── test_actions.py
│       ├── test_completion.py
│       ├── test_images.py
│       └── conftest.py       # Pytest fixtures
├── examples/                  # Working examples
│   ├── basic_usage.py
│   ├── advanced_usage.py
│   ├── headless_usage.py
│   ├── image_paste_demo.py
│   └── completion_demo.py
├── docs/
│   ├── ARCHITECTURE.md        # Detailed architecture docs
│   └── GITHUB_ACTIONS_SETUP.md
├── .github/workflows/         # CI/CD pipelines
│   ├── test.yml              # Test suite (3.8-3.12)
│   ├── lint.yml              # Linting (black, flake8, isort)
│   ├── quality.yml           # Type checking (mypy)
│   ├── examples.yml          # Example validation
│   └── dependencies.yml      # Security checks (bandit, safety)
├── local/                     # Development notes (gitignored)
├── pyproject.toml            # Project metadata & config
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Runtime dependencies
├── README.md                 # User documentation
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
└── LICENSE                   # MIT License
```

---

## Core Architecture

### Component Hierarchy

```
AsyncREPL (Interactive UI)
    ├── ActionRegistry (Commands & Shortcuts)
    │   ├── Built-in Actions (/help, /exit, /paste)
    │   └── Custom Actions (user-defined)
    ├── Tab Completion (optional)
    └── Backend (user's business logic)

HeadlessREPL (Batch Processing)
    ├── ActionRegistry (same system)
    └── Backend (same business logic)
```

### Key Design Patterns

1. **Protocol-Based**: Uses Python protocols (`AsyncBackend`, `ActionHandler`, `Completer`) for loose coupling and testability
2. **Late Backend Binding**: REPL can be initialized before backend is available (useful for resource contexts)
3. **Unified Action System**: Commands and shortcuts use the same action definition
4. **Context-Rich Execution**: Actions receive rich context (trigger method, arguments, backend access)

### Action System

The action system is the heart of the library:

```python
@dataclass
class Action:
    name: str                    # Unique identifier
    description: str             # Help text
    category: str               # Grouping for help display
    handler: Optional[Callable]  # Function to execute
    command: Optional[str]       # "/command" format
    keys: Optional[str]          # "F1", "c-s", etc.
    enabled: bool = True
    hidden: bool = False
```

**Action Execution Flow:**
1. User types command or presses key
2. Registry looks up action
3. Creates `ActionContext` with metadata
4. Executes handler with context
5. Handler can access backend, args, trigger method

---

## Technical Stack

### Core Dependencies

- **Python 3.8+** (supports 3.8, 3.9, 3.10, 3.11, 3.12)
- **prompt-toolkit** ≥3.0.0 (terminal UI framework)
- **pyclip** ≥0.7.0 (clipboard access, optional)

### Development Dependencies

- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: black, flake8, isort
- **Type Checking**: mypy
- **Security**: bandit, safety
- **Build**: build, twine

### CI/CD

**GitHub Actions Workflows:**
- Tests run on Python 3.8-3.12 (Ubuntu, Windows, macOS)
- Linting enforces code style
- Type checking with mypy
- Examples validated
- Security scanning weekly

---

## Development Workflow

### Setup

```bash
# Clone repo
git clone https://github.com/bassmanitram/repl-toolkit.git
cd repl-toolkit

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev,test]"
```

### Running Tests

```bash
# All tests with coverage
pytest

# Specific test file
pytest repl_toolkit/tests/test_actions.py

# Watch mode (requires pytest-watch)
ptw

# Coverage report
pytest --cov=repl_toolkit --cov-report=html
```

### Code Quality

```bash
# Format code
black repl_toolkit/

# Sort imports
isort repl_toolkit/

# Lint
flake8 repl_toolkit/

# Type check
mypy repl_toolkit/

# Security scan
bandit -r repl_toolkit/

# All checks (what CI runs)
black --check repl_toolkit/
isort --check repl_toolkit/
flake8 repl_toolkit/
mypy repl_toolkit/
pytest
```

### Running Examples

```bash
# Basic echo bot
python examples/basic_usage.py

# Advanced chat bot
python examples/advanced_usage.py

# Headless mode
echo -e "test input\n/send" | python examples/headless_usage.py

# Image paste demo
python examples/image_paste_demo.py
```

---

## Key Concepts

### 1. AsyncBackend Protocol

User applications implement this protocol:

```python
class AsyncBackend(Protocol):
    async def handle_input(
        self, 
        user_input: str, 
        images: Optional[Dict[str, ImageData]] = None
    ) -> bool:
        """
        Process user input.
        
        Returns:
            bool: True to continue REPL, False to exit
        """
        ...
```

### 2. Action System

**Three Action Types:**

1. **Dual Actions** (command + shortcut)
   ```python
   Action(name="help", handler=show_help, 
          command="/help", keys="F1")
   ```

2. **Command-Only**
   ```python
   Action(name="search", handler=search, 
          command="/search")
   ```

3. **Shortcut-Only**
   ```python
   Action(name="save", handler=save, 
          keys="c-s")  # Ctrl+S
   ```

**Built-in Actions:**
- `/help` or `F1` - Show help
- `/shortcuts` - List shortcuts
- `/exit` or `/quit` - Exit REPL
- `/paste` or `F6` - Paste from clipboard

### 3. Input Modes

**Interactive Mode:**
- Enter: Execute commands immediately
- Alt+Enter: Send normal text to backend
- Multiline input supported

**Headless Mode:**
- Read from stdin line by line
- Accumulate until `/send` command
- EOF auto-sends remaining buffer

### 4. Image Handling

Images appear as placeholders in text:

```python
user_input = "Check this image {{image:img_001}}"
images = {
    "img_001": ImageData(
        data=b"...",  # Raw bytes
        media_type="image/png"
    )
}
```

Utility functions:
- `parse_image_references(text)` - Extract image IDs
- `iter_content_parts(text, images)` - Iterate text and images
- `detect_media_type(data)` - Detect image format

### 5. Error Handling

The library uses Python's logging framework:

```python
import logging
logging.basicConfig(level=logging.WARNING)
```

**Log Levels:**
- `ERROR`: Critical failures (action errors, clipboard issues)
- `WARNING`: Expected failures (validation, missing deps)
- `DEBUG`: Execution flow tracing

**No direct output** - applications control error display.

---

## Common Patterns

### Basic REPL

```python
import asyncio
from repl_toolkit import AsyncREPL

class MyBackend:
    async def handle_input(self, user_input: str) -> bool:
        print(f"You said: {user_input}")
        return True

async def main():
    repl = AsyncREPL()
    await repl.run(MyBackend())

asyncio.run(main())
```

### With Actions

```python
from repl_toolkit import AsyncREPL, ActionRegistry, Action, ActionContext

def setup_actions():
    registry = ActionRegistry()
    
    def list_handler(ctx: ActionContext):
        print("List action triggered!")
        if ctx.triggered_by == "command":
            print(f"Args: {ctx.args}")
    
    registry.register_action(Action(
        name="list",
        description="List items",
        handler=list_handler,
        command="/list",
        keys="F2"
    ))
    
    return registry

async def main():
    backend = MyBackend()
    actions = setup_actions()
    repl = AsyncREPL(action_registry=actions)
    await repl.run(backend)
```

### Headless Processing

```python
from repl_toolkit import run_headless_mode

class BatchProcessor:
    async def handle_input(self, text: str) -> bool:
        # Process accumulated input
        print(f"Processed: {len(text)} chars")
        return True

# Usage: cat input.txt | python script.py
success = await run_headless_mode(BatchProcessor())
```

### Tab Completion

```python
from repl_toolkit import AsyncREPL, PrefixCompleter

completer = PrefixCompleter(["/help", "/list", "/exit"])
repl = AsyncREPL(completer=completer)
```

---

## Testing Patterns

### Mock Backend

```python
class MockBackend:
    def __init__(self):
        self.inputs = []
    
    async def handle_input(self, user_input: str) -> bool:
        self.inputs.append(user_input)
        return True
```

### Testing Actions

```python
def test_action_execution():
    registry = ActionRegistry()
    backend = MockBackend()
    
    # Register action
    action = Action(
        name="test",
        description="Test action",
        category="Test",
        handler=lambda ctx: backend.inputs.append("triggered"),
        command="/test"
    )
    registry.register_action(action)
    
    # Execute
    context = ActionContext(
        registry=registry,
        backend=backend,
        triggered_by="command"
    )
    registry.execute_action("test", context)
    
    assert "triggered" in backend.inputs
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_repl_run():
    backend = MockBackend()
    repl = AsyncREPL()
    
    # Test would use mock input/output
    # See repl_toolkit/tests/test_async_repl.py for examples
```

---

## Configuration Files

### pyproject.toml

- **Project metadata**: version, description, dependencies
- **Build system**: setuptools config
- **Tool configs**: pytest, black, isort, mypy, coverage

### pytest.ini

- Test paths
- Async mode
- Coverage options

### .mypy.ini

- Type checking strictness
- Excluded paths
- Python version targeting

### .flake8

- Line length (100)
- Ignored rules
- Excluded directories

---

## Version History

**2.0.2** (2024-12-01)
- Commands execute immediately on Enter
- Paste action improvements (`/paste`, `F6`)

**2.0.1** (2024-11-21)
- Fixed PrefixCompleter mid-sentence triggering

**2.0.0** (2024-11-21)
- Breaking: Switched to logging framework
- Silent by default (applications configure logging)

**1.3.0** (2024-11-15)
- Image paste support
- Shell expansion completer
- Headless mode

---

## Important Notes for AI Agents

### When Adding Features

1. **Maintain backward compatibility** unless major version bump
2. **Add tests** for new functionality (target 90%+ coverage)
3. **Update documentation**: README, CHANGELOG, docstrings
4. **Follow existing patterns**: Use protocols, dataclasses, async/await
5. **Run all checks**: black, isort, flake8, mypy, pytest

### Code Style

- **Line length**: 100 characters
- **Formatting**: black (auto-format)
- **Imports**: isort (auto-sort)
- **Type hints**: Required for public APIs
- **Docstrings**: Google style, all public functions

### Testing Requirements

- **Coverage**: 90%+ preferred
- **Test organization**: Mirror package structure
- **Async tests**: Use `@pytest.mark.asyncio`
- **Fixtures**: Defined in `conftest.py`
- **Mock backend**: Use `MockBackend` pattern

### Git Workflow

- **Branch naming**: `feature/description` or `fix/description`
- **Commits**: Descriptive messages, logical units
- **PR requirements**: All CI checks must pass
- **Version bumps**: Update `pyproject.toml` and `CHANGELOG.md`

### Documentation Standards

- **README**: User-focused, example-driven
- **ARCHITECTURE.md**: Developer-focused, detailed
- **CHANGELOG.md**: Keep a Changelog format
- **Code comments**: Why, not what
- **Docstrings**: What and how

---

## Local Development Directory

The `local/` directory (gitignored) contains:
- Development notes and research
- Implementation proposals
- Release planning documents
- Text editing UX research

These are working documents and not part of the package.

---

## Contact & Resources

- **GitHub**: https://github.com/bassmanitram/repl-toolkit
- **PyPI**: https://pypi.org/project/repl-toolkit/
- **Issues**: https://github.com/bassmanitram/repl-toolkit/issues
- **License**: MIT

---

## Quick Reference

### Common Commands

```bash
# Run tests
pytest

# Format code
black repl_toolkit/ && isort repl_toolkit/

# Type check
mypy repl_toolkit/

# Run example
python examples/basic_usage.py

# Build package
python -m build

# Install locally
pip install -e ".[dev,test]"
```

### Key Files to Modify

- **Add feature**: Start in `repl_toolkit/`
- **Add test**: Add to `repl_toolkit/tests/`
- **Update docs**: Update `README.md`, `CHANGELOG.md`
- **Add example**: Add to `examples/`
- **Change API**: Update `repl_toolkit/__init__.py` exports

### Important Patterns

```python
# Protocol definition
class MyProtocol(Protocol):
    def method(self) -> None: ...

# Dataclass with defaults
@dataclass
class MyData:
    required: str
    optional: str = "default"

# Async backend
async def handle_input(self, text: str) -> bool:
    return True

# Action handler
def my_handler(context: ActionContext):
    # Access: context.backend, context.args, context.triggered_by
    pass
```

---

**End of Bootstrap Documentation**

This document provides comprehensive context for AI development assistants working on the REPL Toolkit project. Refer to specific files for implementation details.

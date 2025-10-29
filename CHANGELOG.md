# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-29

### Added
- **Formatting Utilities Module**: New `formatting.py` module with auto-detection and formatting capabilities
  - `detect_format_type()`: Automatically detect HTML, ANSI, or plain text format
  - `auto_format()`: Auto-wrap text in appropriate format type (HTML, ANSI, or plain)
  - `print_auto_formatted()`: Print with automatic format detection
  - `create_auto_printer()`: Create a printer function with auto-formatting (useful for callback handlers)
- **Flexible PromptSession Configuration**: `AsyncREPL` and `run_async_repl()` now accept `**kwargs` to pass custom parameters to PromptSession
  - Enables advanced configuration like `enable_system_prompt`, custom key bindings, etc.
  - Maintains backward compatibility with existing code
- **Documentation**: Added `FORMATTING_UTILITIES.md` with comprehensive guide to formatting utilities
- **Examples**: Added `examples/formatting_demo.py` demonstrating formatting features
- **Tests**: Added 25 new tests for formatting utilities (all passing)

### Changed
- `AsyncREPL.__init__()` now accepts `**kwargs` for PromptSession configuration
- `run_async_repl()` now accepts `**kwargs` for PromptSession configuration
- Improved prompt handling in `AsyncREPL` - prompt now set once during initialization

### Fixed
- None

## [1.0.0] - 2025-10-27

### Added
- Initial stable release of repl-toolkit
- **Core Features**:
  - `AsyncREPL`: Interactive REPL interface with async support
  - `HeadlessREPL`: Non-interactive mode for automation and testing
  - `ActionRegistry`: Extensible action system with commands and keyboard shortcuts
  - `Action`: Single definition for both command and shortcut triggers
  - `ActionContext`: Rich context for action handlers
- **Protocol-Based Architecture**:
  - `AsyncBackend`: Protocol for backend implementations
  - `ActionHandler`: Protocol for action handling
  - `Completer`: Protocol for auto-completion
- **Built-in Actions**:
  - Help system (`/help`, `F1`)
  - Shortcuts listing (`/shortcuts`)
  - Shell access (`/shell`)
  - Exit/Quit commands
- **Late Backend Binding**: Support for resource context patterns
- **Comprehensive Testing**: 97 tests with 96% coverage
- **Documentation**:
  - Complete README with examples
  - Architecture documentation
  - Contributing guidelines
  - API reference
- **Examples**:
  - Basic usage example
  - Advanced usage with custom actions
  - Headless mode example

### Changed
- Renamed `types.py` to `ptypes.py` to avoid conflicts with standard library

### Fixed
- Various bug fixes and improvements from pre-release versions

## [0.1.0] - 2025-10-22

### Added
- Pre-release version with core functionality
- Action system implementation
- REPL interface
- Headless mode support
- Initial test suite

---

## Version History Summary

- **1.1.0** (2025-10-29): Feature release - Formatting utilities and flexible configuration
- **1.0.0** (2025-10-27): Initial stable release
- **0.1.0** (2025-10-22): Pre-release version

---

## Upgrade Guide

### Upgrading from 1.0.0 to 1.1.0

This is a backward-compatible feature release. No breaking changes.

**New Features Available**:
```python
# Use formatting utilities
from repl_toolkit import create_auto_printer, print_auto_formatted

printer = create_auto_printer()
printer("<b>Bold HTML</b>")  # Automatically formatted

# Pass custom PromptSession parameters
await run_async_repl(
    backend=backend,
    enable_system_prompt=True,  # New: custom kwargs supported
    complete_while_typing=False
)
```

**No Changes Required**: Existing code continues to work without modification.

---

## Links

- **GitHub Repository**: https://github.com/bassmanitram/repl-toolkit
- **PyPI Package**: https://pypi.org/project/repl-toolkit/
- **Documentation**: https://repl-toolkit.readthedocs.io/
- **Issue Tracker**: https://github.com/bassmanitram/repl-toolkit/issues

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2025-02-10

### Added

- **`CancellableBackend` Protocol**: Explicit protocol for backends supporting cooperative cancellation
  - Extracted from optional `cancel()` method pattern to formal protocol inheritance
  - Backends implement `CancellableBackend` instead of `AsyncBackend` for cancellation support
  - Type-safe checking via `isinstance(backend, CancellableBackend)`
  - Clear contract: `cancel(message: Optional[str] = None) -> None` method required
  - Comprehensive documentation in protocol docstring

- **`cancel_callback` Parameter**: Backends now receive `cancel_callback` kwarg in `handle_input()`
  - Thread-safe callback function for tools to trigger cancellation
  - Enables tools/subprocesses to signal cancellation back to REPL
  - Used by tools that spawn long-running operations
  - Fully backward compatible - ignored if not used

### Changed

- **Major Refactoring of `async_repl.py`**: Improved code organization and maintainability
  - Extracted `_cancellation_context()` as async context manager
  - Separated concerns: `_create_cancel_app()`, `_build_backend_kwargs()`, `_handle_cancellation()`
  - Added clear section headers for code navigation
  - Simplified method signatures and reduced nesting
  - Removed excessive debug logging (200+ lines removed)
  - Better type annotations and mypy compliance

- **Method Renames for Clarity**:
  - `_should_exit()` → `_is_exit_command()` (clearer intent)
  - `THINKING` constant → `THINKING_MESSAGE` (more descriptive)

- **Type Annotations Improved**:
  - `action_registry` parameter now correctly typed as `Optional[ActionRegistry]` instead of `Optional[ActionHandler]`
  - Fixed mypy errors with proper protocol usage
  - Better type safety throughout

### Documentation

- Updated `CancellableBackend` protocol documentation with implementation guidelines
- Clarified distinction between `AsyncBackend` (base) and `CancellableBackend` (with cancellation)
- Added examples showing proper protocol inheritance
- Updated docstrings to reflect new architecture

### Internal

- Removed 386 lines, added 252 lines (net -134 lines)
- Better separation of concerns with dedicated helper methods
- Improved testability with extracted context manager
- Reduced code duplication in cancellation handling

## [2.1.0] - 2025-01-28

### Added

- **Buffer Clear Keybindings**: Added two new shortcuts to clear the input buffer in interactive mode
  - `F7` - Single key, easy and discoverable
  - `Escape, Escape` - Double escape for intuitive clear operation
  - No command form (e.g., `/clear`) to avoid namespace collisions with other packages
  - Works in interactive mode only (not applicable to headless mode buffer management)

- **Cooperative Cancellation Support**: Backends can now optionally implement `cancel()` method for graceful cancellation
  - Enables backends to handle cancellation of blocking operations (subprocess calls, HTTP requests, etc.)
  - Signal sent before `task.cancel()` to allow cleanup and state management
  - Optional - existing backends without `cancel()` continue to work unchanged
  - Called automatically on Alt+C, Ctrl+C, or error conditions
  - Fully backward compatible - checked via `hasattr()` pattern
  - Comprehensive documentation in `AsyncBackend` Protocol docstring
  - 19 new tests covering cancellable and non-cancellable backends

- **Interactive Mode Output Handling**: Actions now use prompt_toolkit output methods for clean prompt redraw
  - ActionRegistry in interactive mode uses `print_formatted_text()` instead of `print()`
  - Prompt wrapped in `patch_stdout()` to catch any stray print() calls
  - Headless mode correctly continues to use standard `print()` for logs/pipes
  - Fixes issue where key binding output would corrupt the prompt display
  - Supports formatted output (ANSI codes, HTML)
  - Fully backward compatible with existing actions
  - 17 new tests covering output handling in both modes

### Fixed

- **Command Timing Race Condition**: Fixed race condition where commands that modify backend state could be followed by input processing before state modifications were fully visible
  - Added `await asyncio.sleep(0)` after command execution to yield to event loop
  - Ensures pending async work completes before processing next input
  - Applies to both interactive (`AsyncREPL`) and headless (`HeadlessREPL`) modes
  - Critical for commands like `/undo` that modify agent state asynchronously
  - Prevents inconsistent behavior in batch processing scenarios

### Documentation

- Added comprehensive documentation for optional `cancel()` method in AsyncBackend
- Updated examples showing cooperative cancellation implementation
- Added guide for implementing cancellable backends

## [2.0.2] - 2025-12-01

### Changed

- **Enter Key Behavior**: Commands (starting with `/`) now execute immediately when Enter is pressed
  - Improves UX by matching user expectations for command execution
  - Normal text still requires Alt+Enter to send
  - Consistent with how terminal commands typically work

- **Paste Action Improvements**:
  - Command renamed from `/paste-image` to `/paste` for brevity
  - Keyboard shortcut changed from `f6` to `F6` for consistency with other shortcuts (e.g., `F1` for `/help`)

### Documentation

- Updated README with clearer explanations of Enter vs Alt+Enter behavior
- Documented command execution workflow
- Updated all references to paste command and shortcut

## [2.0.1] - 2024-11-21

### Fixed

- **PrefixCompleter**: Fixed command completion triggering mid-sentence. Commands now only complete at line start or after newlines, not after spaces within text.
  - Changed pattern from `(?:^|[\s\n])` to `(?:^|(?<=\n)\s*)`
  - Prevents completion in contexts like "Please type /help"
  - Still completes correctly at line start and after newlines


## [2.0.0] - 2024-11-21

### Breaking Changes

**Error Handling**: Library now uses Python logging exclusively. Applications must configure logging to see errors.

**Migration:** Add one line to your application:
```python
import logging
logging.basicConfig(level=logging.WARNING)
```

**Why**:
- Standard Python practice
- Better control over error visibility and formatting
- Easier integration with application logging
- Production-ready error handling

### Added

- **Comprehensive logging** throughout the library with appropriate levels:
  - `ERROR`: Action failures, clipboard errors, critical issues
  - `WARNING`: Non-critical issues, missing dependencies
  - `DEBUG`: Detailed execution flow for troubleshooting

- **Documentation**: Added extensive error handling documentation to README
  - Multiple configuration examples (simple, custom, file-based)
  - Production and development recommendations
  - Clear explanation of logging levels

### Changed

- **All print() statements removed** from library code except intentional output
- **All exceptions now logged** instead of printed to stderr
- **Silent by default** - matches Python's standard behavior

### Fixed

- Error output no longer pollutes stdout/stderr unless configured
- Consistent error handling across all components


## [1.3.0] - 2024-11-15

### Added

- Image paste support with clipboard integration
- Action execution context with trigger information
- Shell expansion completer with environment variables
- Headless mode for batch processing from stdin

### Changed

- Improved action registry with better validation
- Enhanced completion system with multiple strategies
- Better keyboard shortcut handling

### Fixed

- Various stability improvements
- Better error messages for common issues


## [1.2.0] - 2024-10-20

### Added

- Tab completion support
- Command history persistence
- Action categories for organized help

### Changed

- Improved help command formatting
- Better async task cancellation


## [1.1.0] - 2024-09-15

### Added

- Custom prompt strings with HTML formatting
- Alt+Enter for message sending
- Ctrl+C cancellation during processing

### Fixed

- Memory leaks in long-running sessions
- Race conditions in async operations


## [1.0.0] - 2024-08-01

### Added

- Initial release
- AsyncREPL with action support
- Built-in help system
- Command and shortcut registration
- Multiline input support

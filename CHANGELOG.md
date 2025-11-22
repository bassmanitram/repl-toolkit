# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-11-21

### Fixed

- **PrefixCompleter**: Fixed command completion triggering mid-sentence. Commands now only complete at line start or after newlines, not after spaces within text.
  - Changed pattern from `(?:^|[\s\n])` to `(?:^|(?<=\n)\s*)`
  - Prevents completion in contexts like "Please type /help"
  - Still completes correctly at line start and after newlines


## [2.0.0] - 2025-11-21

### Breaking Changes

**Error Handling**: Library now uses Python logging exclusively. Applications must configure logging to see errors.

**Migration:** Add one line to your application:
```python
import logging
logging.basicConfig(level=logging.WARNING)
```

**What changed:**
- Removed direct console output from error handlers
- ActionError → `logger.warning()`, Exception → `logger.exception()`

**Why:** Follows Python library best practices. Applications control error visibility, formatting, and routing via logging configuration.

**Control options:**
```python
logging.basicConfig(level=logging.WARNING)  # Show all
logging.basicConfig(level=logging.ERROR)     # Critical only
logging.getLogger('repl_toolkit').setLevel(logging.CRITICAL)  # Silent
```

See [Python logging docs](https://docs.python.org/3/library/logging.html) for details.

### Changed

- Error logging upgraded: `logger.error()` → `logger.exception()` (automatic tracebacks)

### Improved

- Better debugging with automatic tracebacks
- Clean separation: library logs, application controls display
- Flexible error handling for different use cases


## [1.3.0] - 2025-11-13

### Added
- **Image Paste Support**: New image handling module `repl_toolkit.images`
  - `ImageData`: Dataclass for image metadata and content
  - `detect_media_type()`: Auto-detect image format from magic bytes (PNG, JPEG, GIF, WebP, BMP)
  - `parse_image_references()`: Parse text for {{image:img_xxx}} placeholders
  - `iter_content_parts()`: Iterator over text and image content parts
  - `reconstruct_message()`: Rebuild messages with custom formatters
  - `create_paste_image_action()`: Factory for paste image action
- **AsyncREPL Image Support**: Built-in image buffer management
  - `add_image()`: Add images to buffer for next message
  - `get_images()`: Retrieve current image buffer
  - `clear_images()`: Clear image buffer
  - `enable_image_paste` parameter (default: True) to control image paste action registration
- **Paste Action**: F6 keyboard shortcut and `/paste-image` command
  - Automatically pastes images from clipboard as placeholders
  - Falls back to text paste if clipboard contains text
  - Supports all major image formats
  - Requires `pyclip` package (already in dependencies)
- **Examples**: New `examples/image_paste_demo.py` demonstrating image integration
- **Tests**: Added 67 new tests for image functionality (243 total tests, all passing)

### Fixed
- **Ctrl-C Cancellation**: Fixed cancellation handling during backend processing
  - Cancel listeners now properly clean up when operations complete
  - Improved keyboard interrupt handling during async wait operations
  - Better coordination between backend tasks and cancel futures
  - Prevents hanging cancel applications after normal completion
- **Type Checking Configuration**: Fixed mypy GitHub Actions failures
  - Configured mypy to only check project code, not installed packages
  - Added proper exclusions for build/dist/venv directories
  - Updated python_version to "3.9" (mypy minimum requirement)
  - Fixed type checking errors in ActionHandler protocol usage

### Changed
- **Logging Standardization**: Standardized logging across all modules
  - Consistent trace-level entry/exit logging
  - Debug-level logging for important state changes
  - Error-level logging for failures
  - Improved debugging and troubleshooting capabilities
- `AsyncREPL.__init__()` now accepts `enable_image_paste` parameter for controlling image support

### Notes
- Image paste requires the `pyclip` package which is included in dependencies
- Images are passed to backend via `images` kwarg in `handle_input()` method
- Backends should handle the `images` parameter containing Dict[str, ImageData]
- Image placeholders use format `{{image:img_xxx}}` where xxx is a zero-padded counter

## [1.2.0] - 2025-11-08

### Added
- **Completion Module**: New sub-module `repl_toolkit.completion` with two completers
  - **ShellExpansionCompleter**: Environment variable and shell command expansion
    - Expand environment variables with `${VAR_NAME}` syntax
    - Execute shell commands with `$(command)` syntax on Tab completion
    - Multi-line output: Select individual lines or ALL option
    - Configurable timeout (default: 2.0s) prevents UI blocking
    - Display limits: `max_lines` (default: 50) and `max_display_length` (default: 80)
    - Limits affect display only, content never truncated
    - Extensible design: 11 public methods for customization
    - Security: Commands only execute on Tab press
  - **PrefixCompleter**: Configurable prefix-based string completion
    - Supports any prefix character: `/`, `@`, `#`, or `None`
    - Smart word-boundary detection avoids false positives
    - Auto-prefix addition for words without prefix
    - Case-sensitive or case-insensitive modes
- **Custom Printer Support**: `ActionRegistry` now accepts optional `printer` parameter for custom output handling
  - Enables integration with logging systems, custom streams, and formatters
  - Printer automatically propagated to all action handlers via `ActionContext`
  - Maintains backward compatibility (defaults to `print`)
- **ActionContext.printer**: New field in `ActionContext` for accessing configured printer
- **Examples**: Four new completion examples
  - `examples/completion_demo.py` - Basic completion usage
  - `examples/path_completion_demo.py` - Combined completers
  - `examples/multiline_completion_demo.py` - Multi-line selection
  - `examples/extensibility_demo.py` - Extension examples
- **Tests**: 47 new completion tests (176 total tests, all passing)

### Changed
- Module restructure: `completion.py` → `completion/` sub-module
  - Separated into `shell_expansion.py` and `prefix.py`
  - Better organization and maintainability
- `ActionRegistry.__init__()` now accepts optional `printer: Callable[[str], None] = print` parameter
- All built-in action handlers now use `context.printer` instead of `print`

### Removed
- **`/shell` command**: Removed built-in shell command
  - prompt_toolkit provides native shell access via `Escape !` key binding
  - New ShellExpansionCompleter provides inline command execution

### Notes
- Import update required: Use `ShellExpansionCompleter` and `PrefixCompleter` (renamed from `EnvCommandCompleter` and `CommandCompleter`)
- All other APIs unchanged - backward compatible
- For shell integration, use prompt_toolkit's native `enable_system_prompt` feature

### Added
- **Formatting Utilities Module**: New `formatting.py` module with auto-detection and formatting capabilities
  - `detect_format_type()`: Automatically detect HTML, ANSI, or plain text format
  - `auto_format()`: Auto-wrap text in appropriate format type (HTML, ANSI, or plain)
  - `print_auto_formatted()`: Print with automatic format detection
  - `create_auto_printer()`: Create a printer function with auto-formatting (useful for callback handlers)
- **Flexible PromptSession Configuration**: `AsyncREPL` and `run_async_repl()` now accept `**kwargs` to pass custom parameters to PromptSession
  - Enables advanced configuration like `enable_system_prompt`, custom key bindings, etc.
  - Maintains backward compatibility with existing code
- **Documentation**: Added `FORMATTING_UTILITIES.md` with guide to formatting utilities
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
  - `ActionContext`: context for action handlers
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
- **Testing**: 97 tests with 96% coverage
- **Documentation**:
  - README with examples
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
- None

## [0.1.0] - 2025-10-26

### Added
- Initial development release
- Basic REPL functionality
- Action system foundation
- Headless mode support

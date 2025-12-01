# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Multiline input support## [2.0.2] - 2024-11-21

### Changed

- **Enter Key Behavior**: Registered commands now execute immediately when Enter is pressed
  - Only executes if buffer contains a valid registered command (e.g., `/help`, `/exit`)
  - Text like "Please use /help" won't trigger command execution
  - Added `ActionRegistry.is_registered_command()` utility method for validation
  - Improves UX by matching user expectations for command execution
  - Normal text still requires Alt+Enter to send
  - Consistent with how terminal commands typically work

- **Paste Action Improvements**:
  - Command renamed from `/paste-image` to `/paste` for brevity
  - Keyboard shortcut changed from `f6` to `F6` for consistency with other shortcuts (e.g., `F1` for `/help`)

### Added

- **ActionRegistry.is_registered_command()**: New utility method to check if text starts with a registered command
  - Validates buffer contains '/<command>' followed by space or end-of-buffer
  - Handles whitespace correctly
  - Prevents false positives (e.g., "Please use /help" won't match)
  - Comprehensive test coverage (6 new tests)

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

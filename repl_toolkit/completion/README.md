# Completion Module

Completion utilities for REPL Toolkit that integrate with prompt_toolkit's completion framework.

## Overview

This module provides two main completers:

1. **ShellExpansionCompleter** - Shell-style variable and command expansion
2. **PrefixCompleter** - Configurable prefix-based string completion

Both completers implement prompt_toolkit's `Completer` protocol and can be combined with other completers using `merge_completers()`.

## Table of Contents

- [ShellExpansionCompleter](#shellexpansioncompleter)
 - [Basic Usage](#basic-usage)
 - [Environment Variables](#environment-variables)
 - [Shell Commands](#shell-commands)
 - [Multi-line Output](#multi-line-output)
 - [Display Limits](#display-limits)
 - [Extensibility](#extensibility)
 - [API Reference](#shellexpansioncompleter-api)
- [PrefixCompleter](#prefixcompleter)
 - [Basic Usage](#prefixcompleter-basic-usage)
 - [Use Cases](#use-cases)
 - [API Reference](#prefixcompleter-api)
- [Combining Completers](#combining-completers)
- [Examples](#examples)
- [Security Considerations](#security-considerations)

---

## ShellExpansionCompleter

Enables inline expansion of environment variables and shell command output during tab completion.

### Basic Usage

```python
from repl_toolkit import AsyncREPL, ShellExpansionCompleter

# Create completer with options
completer = ShellExpansionCompleter(
 timeout=2.0, # Command execution timeout (default: 2.0s)
 multiline_all=True, # Show "ALL" option for multi-line output (default: True)
 max_lines=50, # Max lines shown in menu (default: 50)
 max_display_length=80 # Max chars per line in menu (default: 80)
)

repl = AsyncREPL(backend, completer=completer)
```

### Environment Variables

Expand environment variables using `${VAR_NAME}` syntax:

```bash
# Type in REPL:
User: ${USER}

# Press Tab → Expands to:
User: john_doe

# Other examples:
Home: ${HOME} → /home/john_doe
Shell: ${SHELL} → /bin/bash
Path: ${PWD} → /current/directory
```

**Rules:**
- Variable must exist in environment
- Variable name: alphanumeric + underscore, must start with letter/underscore
- Pattern: `${VAR_NAME}` (not `$VAR_NAME`)

### Shell Commands

Execute shell commands using `$(command)` syntax:

```bash
# Type in REPL:
Date: $(date)

# Press Tab → Expands to:
Date: Mon Jan 4 10:30:45 PST 2025

# Other examples:
Directory: $(pwd) → /home/user/project
User: $(whoami) → john_doe
Files: $(ls -1) → (shows multi-line options)
Git Branch: $(git branch --show-current) → main
```

**Rules:**
- Command executes with configurable timeout (default: 2.0s)
- Only executes when Tab is pressed (not automatically)
- Command runs in shell context (`shell=True`)
- Output is trimmed (leading/trailing whitespace removed)

### Multi-line Output

When a command produces multiple lines, you get multiple completion options:

```bash
# Type:
Files: $(ls -1)

# Press Tab, see options:
 $(ls -1) → ALL (5 files) # Selects all lines: "file1.txt\nfile2.py\n..."
 $(ls -1) → Line 1: file1.txt # Selects just: "file1.txt"
 $(ls -1) → Line 2: file2.py # Selects just: "file2.py"
 $(ls -1) → Line 3: file3.md # Selects just: "file3.md"
 $(ls -1) → Line 4: README.md # Selects just: "README.md"
 $(ls -1) → Line 5: setup.py # Selects just: "setup.py"
```

**Features:**
- **ALL option** - Inserts all lines with newlines preserved
- **Individual lines** - Select specific line by number
- Empty lines are filtered out from individual options
- Line order is preserved
- Can disable ALL option with `multiline_all=False`

### Display Limits

Prevent UI flooding from commands with massive output:

#### Line Limit (`max_lines`)

Limits how many individual line options are shown in the completion menu:

```python
completer = ShellExpansionCompleter(max_lines=5)
```

```bash
# Command produces 100 lines:
$(find . -type f)

# Completion menu shows:
 $(find...) → ALL (100 files) # Still includes ALL 100 files
 $(find...) → Line 1: ./file1.txt
 $(find...) → Line 2: ./file2.py
 $(find...) → Line 3: ./file3.md
 $(find...) → Line 4: ./file4.json
 $(find...) → Line 5: ./file5.yaml
 $(find...) → (95 more lines... use ALL)
```

**Important:** ALL option always includes output regardless of limit.

#### Display Length Limit (`max_display_length`)

Truncates long lines in the menu for readability:

```python
completer = ShellExpansionCompleter(max_display_length=40)
```

```bash
# Long filename:
${VERY_LONG_ENVIRONMENT_VARIABLE_WITH_PATH}

# Completion menu shows:
 ${VERY_LONG_...} → /home/user/very...

# But selecting it inserts:
/home/user/very/long/path/to/some/directory/that/continues/for/a/very/long/time
```

**Important:** Completion text is never truncated - content is always inserted.

### Extensibility

`ShellExpansionCompleter` is designed to be extended. All key functionality is exposed as public methods:

#### Core Methods

Override these to customize behavior:

```python
from repl_toolkit.completion import ShellExpansionCompleter

class CustomExpansion(ShellExpansionCompleter):
 """Add custom behavior."""

 def execute_command(self, command):
 """Customize command execution."""
 # Add logging, caching, security checks, etc.
 return super().execute_command(command)

 def process_command_output(self, output, command):
 """Transform command output."""
 # Modify output before display
 return super().process_command_output(output, command)

 def filter_lines(self, lines):
 """Custom line filtering."""
 # Filter output lines
 return super().filter_lines(lines)
```

#### Overridable Methods

**Core Methods:**
- `execute_command(command)` - Command execution logic
- `process_command_output(output, command)` - Output transformation
- `complete_command(command, match, cursor_pos)` - Main completion flow
- `complete_multiline(full_output, lines, pattern, start_pos)` - Multi-line handling

**Formatting Methods:**
- `format_command_completion(output, pattern, start_pos, label)` - Single-line command display
- `format_variable_completion(var_name, value, start_pos, pattern)` - Variable display
- `format_multiline_completion(line, line_num, pattern, start_pos)` - Individual line display
- `format_all_lines_completion(output, line_count, pattern, start_pos)` - ALL option display
- `format_error_completion(error_msg, pattern, start_pos)` - Error display

**Utility Methods:**
- `truncate_display(text)` - Display truncation logic
- `filter_lines(lines)` - Line filtering logic

#### Extension Examples

**Example 1: Caching**
```python
class CachedShellExpansion(ShellExpansionCompleter):
 """Cache command results to avoid re-execution."""

 def __init__(self, *args, **kwargs):
 super().__init__(*args, **kwargs)
 self._cache = {}

 def execute_command(self, command):
 if command in self._cache:
 return self._cache[command]
 result = super().execute_command(command)
 self._cache[command] = result
 return result
```

**Example 2: Security Filtering**
```python
class SecureShellExpansion(ShellExpansionCompleter):
 """Block dangerous commands."""

 BLOCKED_COMMANDS = ['rm', 'dd', 'mkfs', 'format']

 def execute_command(self, command):
 if any(blocked in command.lower() for blocked in self.BLOCKED_COMMANDS):
 # Return fake error result
 class BlockedResult:
 returncode = 1
 stdout = ""
 stderr = "Command blocked for security"
 return BlockedResult()
 return super().execute_command(command)
```

**Example 3: Output Transformation**
```python
class UppercaseExpansion(ShellExpansionCompleter):
 """Convert all output to uppercase."""

 def process_command_output(self, output, command):
 processed = super().process_command_output(output, command)
 return processed.upper()
```

**Example 4: Custom Filtering**
```python
class LongLinesOnly(ShellExpansionCompleter):
 """Only show lines longer than 10 characters."""

 def filter_lines(self, lines):
 filtered = super().filter_lines(lines)
 return [line for line in filtered if len(line) > 10]
```

**Example 5: Custom Display**
```python
class EmojiExpansion(ShellExpansionCompleter):
 """Add emoji to completions."""

 def format_command_completion(self, output, pattern, start_pos, label=None):
 display_text = self.truncate_display(output)

 return Completion(
 text=output,
 start_position=start_pos,
 display=FormattedText([
 ('', '🚀 '),
 ('class:completion.cmd', pattern),
 ('class:completion.arrow', ' → '),
 ('class:completion.value', display_text),
 ])
 )
```

**Example 6: API Integration**
```python
class APIExpansion(ShellExpansionCompleter):
 """Add API call expansion: @{GET /users}"""

 API_PATTERN = re.compile(r'@\{([^}]+)\}')

 def get_completions(self, document, complete_event):
 # Check for API patterns first
 for match in self.API_PATTERN.finditer(document.text):
 if match.start() <= document.cursor_position <= match.end():
 api_call = match.group(1)
 # Custom API completion logic
 yield from self.complete_api_call(api_call, match, document.cursor_position)
 return

 # Fall back to standard shell expansion
 yield from super().get_completions(document, complete_event)

 def complete_api_call(self, api_call, match, cursor_pos):
 # Make HTTP request, format results, etc.
 ...
```

See `examples/extensibility_demo.py` for working examples.

### ShellExpansionCompleter API

```python
class ShellExpansionCompleter(Completer):
 """Shell-style variable and command expansion completer."""

 # Class attributes
 VAR_PATTERN: re.Pattern # Regex for ${VAR_NAME}
 CMD_PATTERN: re.Pattern # Regex for $(command)

 def __init__(
 self,
 timeout: float = 2.0,
 multiline_all: bool = True,
 max_lines: int = 50,
 max_display_length: int = 80
 ):
 """
 Initialize completer.

 Args:
 timeout: Command execution timeout in seconds
 multiline_all: Include "ALL" option for multi-line output
 max_lines: Maximum lines to show in completion menu
 max_display_length: Maximum characters per line in menu
 """

 # Core protocol method
 def get_completions(self, document, complete_event) -> Iterable[Completion]:
 """Get completions for patterns at cursor position."""

 # Public methods for extension
 def execute_command(self, command: str) -> subprocess.CompletedProcess:
 """Execute shell command. Override for custom execution."""

 def process_command_output(self, output: str, command: str) -> str:
 """Process command output. Override for transformation."""

 def filter_lines(self, lines: list[str]) -> list[str]:
 """Filter output lines. Override for custom filtering."""

 def truncate_display(self, text: str) -> str:
 """Truncate text for display. Override for custom truncation."""

 def complete_command(self, command, match, cursor_pos) -> Iterable[Completion]:
 """Main command completion flow. Override for control."""

 def complete_multiline(self, full_output, lines, pattern, start_pos) -> Iterable[Completion]:
 """Multi-line output handling. Override for custom behavior."""

 # Formatting methods
 def format_command_completion(self, output, pattern, start_pos, label=None) -> Completion:
 """Format single-line command completion. Override for custom display."""

 def format_variable_completion(self, var_name, value, start_pos, pattern) -> Completion:
 """Format variable completion. Override for custom display."""

 def format_multiline_completion(self, line, line_num, pattern, start_pos) -> Completion:
 """Format individual line completion. Override for custom display."""

 def format_all_lines_completion(self, output, line_count, pattern, start_pos) -> Completion:
 """Format ALL option. Override for custom display."""

 def format_error_completion(self, error_msg, pattern, start_pos) -> Completion:
 """Format error completion. Override for custom display."""
```

---

## PrefixCompleter

Generic prefix-based string completion with configurable prefix character.

### PrefixCompleter Basic Usage

```python
from repl_toolkit import AsyncREPL, PrefixCompleter

# Slash commands
cmd_completer = PrefixCompleter(
 words=['/help', '/exit', '/save', '/load'],
 prefix='/',
 ignore_case=True # Case-insensitive matching (default: True)
)

repl = AsyncREPL(backend, completer=cmd_completer)
```

### Use Cases

#### Slash Commands

```python
completer = PrefixCompleter(
 words=['/help', '/exit', '/save', '/load', '/quit'],
 prefix='/'
)

# Type: /he
# Press Tab → /help
```

#### At-Mentions

```python
completer = PrefixCompleter(
 words=['alice', 'bob', 'charlie', 'diana'],
 prefix='@'
)

# Type: @al
# Press Tab → @alice
```

#### Hashtags

```python
completer = PrefixCompleter(
 words=['python', 'coding', 'opensource', 'tutorial'],
 prefix='#'
)

# Type: #py
# Press Tab → #python
```

#### SQL Keywords (No Prefix)

```python
completer = PrefixCompleter(
 words=['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY'],
 prefix=None,
 ignore_case=False
)

# Type: SEL
# Press Tab → SELECT
```

#### Custom Prefix

```python
# Emoji triggers
completer = PrefixCompleter(
 words=['smile', 'heart', 'fire', 'rocket'],
 prefix=':'
)

# Type: :smi
# Press Tab → :smile
```

### Features

**Smart Triggering:**
- Only completes after prefix at word boundaries
- Won't trigger in middle of words: `path/to/file` with `/` prefix
- Works after whitespace, newlines, or start of line

**Auto-Prefix Addition:**
```python
# These are equivalent:
PrefixCompleter(['help', 'exit'], prefix='/')
PrefixCompleter(['/help', '/exit'], prefix='/')

# Both complete: /he → /help
```

**Case Sensitivity:**
```python
# Case-insensitive (default)
completer = PrefixCompleter(['/Help', '/Exit'], ignore_case=True)
# Type: /he → Matches /Help

# Case-sensitive
completer = PrefixCompleter(['/Help', '/Exit'], ignore_case=False)
# Type: /he → No match
```

### PrefixCompleter API

```python
class PrefixCompleter(Completer):
 """Prefix-based string completion."""

 def __init__(
 self,
 words: list[str],
 prefix: Optional[str] = None,
 ignore_case: bool = True
 ):
 """
 Initialize completer.

 Args:
 words: List of words to complete
 prefix: Optional prefix character (e.g., '/', '@', '#')
 If None, completes anywhere (standard word completion)
 ignore_case: Case-insensitive matching
 """

 def get_completions(self, document, complete_event) -> Iterable[Completion]:
 """Get completions for words matching the prefix pattern."""
```

---

## Combining Completers

Use prompt_toolkit's `merge_completers()` to combine multiple completers for a completion experience:

```python
from prompt_toolkit.completion import merge_completers, PathCompleter, WordCompleter
from repl_toolkit import ShellExpansionCompleter, PrefixCompleter

# Create individual completers
command_completer = PrefixCompleter(
 ['/help', '/exit', '/quit', '/save', '/load'],
 prefix='/'
)

path_completer = PathCompleter(
 expanduser=True, # Expand ~/
 only_directories=False # Include files
)

shell_completer = ShellExpansionCompleter(
 timeout=2.0,
 max_lines=30 # Conservative limit
)

word_completer = WordCompleter(
 ['yes', 'no', 'maybe'], # Common words
 ignore_case=True
)

# Combine all completers
combined = merge_completers([
 command_completer, # Slash commands: /help
 path_completer, # File paths: ~/Documents/
 shell_completer, # Variables: ${USER}, Commands: $(date)
 word_completer # Words: yes, no, maybe
])

repl = AsyncREPL(backend, completer=combined)
```

**Result:** Users get context-aware completion for:
- Commands: `/he` + Tab → `/help`
- Paths: `~/Doc` + Tab → `~/Documents/`
- Variables: `${HO` + Tab → `${HOME}` → `/home/user`
- Commands: `$(da` + Tab → `$(date)` → current date
- Words: `y` + Tab → `yes`

**Priority:** Completers are tried in order, first match wins.

---

## Examples

Working examples are provided:

### Basic Completion
```bash
python examples/completion_demo.py
```

Demonstrates:
- ShellExpansionCompleter with environment variables
- ShellExpansionCompleter with shell commands
- PrefixCompleter with slash commands
- Combined usage

### Path + Shell + Command Completion
```bash
python examples/path_completion_demo.py
```

Demonstrates:
- Merging PathCompleter with ShellExpansionCompleter and PrefixCompleter
- All three working simultaneously

### Multi-line Selection
```bash
python examples/multiline_completion_demo.py
```

Demonstrates:
- Multi-line command output
- Selecting individual lines vs ALL
- Display limits in action

### Extensibility
```bash
python examples/extensibility_demo.py
```

Demonstrates:
- Caching expensive commands
- Security filtering
- Output transformation
- Custom line filtering
- Custom formatting
- Combined extensions

---

## Security Considerations

### Command Execution

**When Commands Execute:**
- Commands execute ONLY when user presses Tab
- NOT automatically on typing
- NOT on rendering or display

**Timeout Protection:**
```python
completer = ShellExpansionCompleter(timeout=2.0)
```

- Default: 2.0 seconds
- Prevents UI blocking from hanging commands
- User sees "Timeout (2.0s)" message

**Recommendation:** Use only in trusted environments where arbitrary command execution is acceptable.

### Security Best Practices

1. **Set Conservative Timeout:**
 ```python
 completer = ShellExpansionCompleter(timeout=1.0)
 ```

2. **Use Security Wrapper:**
 ```python
 class SecureExpansion(ShellExpansionCompleter):
 BLOCKED = ['rm', 'dd', 'mkfs', 'format', 'del']

 def execute_command(self, command):
 if any(blocked in command.lower() for blocked in self.BLOCKED):
 raise ValueError("Blocked command")
 return super().execute_command(command)
 ```

3. **Validate in Trusted Context:**
 ```python
 # Only enable in development/admin mode
 if config.is_development:
 completer = ShellExpansionCompleter()
 else:
 completer = PrefixCompleter(['/help', '/exit'], prefix='/')
 ```

4. **Use Read-Only Commands:**
 ```python
 # Encourage safe patterns in documentation
 # Good: $(ls), $(date), $(pwd), $(whoami)
 # Avoid: $(rm ...), $(dd ...), $(curl ...)
 ```

---

## Pattern Reference

### Environment Variable Pattern

**Syntax:** `${VAR_NAME}`

**Rules:**
- Variable name must start with letter or underscore
- Followed by letters, numbers, or underscores
- Must exist in environment

**Examples:**
- Valid: `${USER}`, `${HOME}`, `${_PRIVATE}`, `${PATH123}`
- Invalid: `${123VAR}`, `${-VAR}`, `$VAR` (missing braces)

**Regex:** `\$\{([A-Za-z_][A-Za-z0-9_]*)\}`

### Command Pattern

**Syntax:** `$(command)`

**Rules:**
- Any valid shell command
- Cannot contain closing parenthesis `)`
- Executed with `shell=True`

**Examples:**
- Valid: `$(date)`, `$(echo "hello")`, `$(ls | wc -l)`
- Invalid: `$()` (empty), `$(echo ")")` (contains `)`)

**Regex:** `\$\(([^)]+)\)`

---

## Performance Considerations

### Command Execution

- Commands execute synchronously during completion
- Timeout prevents indefinite blocking (default: 2.0s)
- Consider caching for expensive operations

### Display Limits

- `max_lines` reduces completion menu size
- Improves rendering performance for commands with many lines
- Default (50 lines) balances usability and performance

### Caching Strategy

For expensive commands, implement caching:

```python
from functools import lru_cache

class CachedExpansion(ShellExpansionCompleter):
 @lru_cache(maxsize=100)
 def _cached_execute(self, command):
 result = super().execute_command(command)
 # Cache by converting to tuple
 return (result.returncode, result.stdout, result.stderr)

 def execute_command(self, command):
 cached = self._cached_execute(command)

 class CachedResult:
 def __init__(self, returncode, stdout, stderr):
 self.returncode = returncode
 self.stdout = stdout
 self.stderr = stderr

 return CachedResult(*cached)
```

---

## Troubleshooting

### Commands Not Completing

**Problem:** Typed `$(date)` but Tab shows no completion

**Solutions:**
1. Check cursor position - must be within `$()` pattern
2. Check command exists - `$(nonexistent)` won't complete
3. Check timeout - slow commands may time out
4. Check syntax - must be `$(cmd)` not `$cmd`

### Variables Not Expanding

**Problem:** Typed `${HOME}` but Tab shows no completion

**Solutions:**
1. Check variable exists: `echo $HOME` in terminal
2. Check syntax - must be `${VAR}` not `$VAR`
3. Check cursor position - must be within `${}` pattern
4. Check variable name - must start with letter/underscore

### Prefix Not Triggering

**Problem:** Typed `/help` but PrefixCompleter not working

**Solutions:**
1. Check prefix argument: `prefix='/'` must be set
2. Check word list: word must be in list
3. Check position - `/` must be at word boundary
4. Check case sensitivity - `ignore_case` setting

### Too Many Completions

**Problem:** Completion menu is overwhelming

**Solutions:**
```python
# Reduce limits
completer = ShellExpansionCompleter(
 max_lines=10, # Show fewer lines
 max_display_length=50 # Shorter display
)
```

---

## Integration with Prompt Toolkit

Both completers are compatible with prompt_toolkit's completion system:

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import merge_completers

# Can be used directly with PromptSession
session = PromptSession(completer=shell_completer)

# Or with AsyncREPL
repl = AsyncREPL(backend, completer=shell_completer)

# Supports all prompt_toolkit features
completer = merge_completers([
 completer1,
 completer2,
 completer3
])
```

---

## License

Part of REPL Toolkit - MIT License

---

## Contributing

Contributions welcome! To add new completion features:

1. Create new completer in `repl_toolkit/completion/`
2. Implement `Completer` protocol
3. Add tests in `repl_toolkit/tests/test_completion.py`
4. Update this README
5. Add example in `examples/`

---

## Version History

- **1.2.0** - Initial release with ShellExpansionCompleter and PrefixCompleter
 - Shell-style expansion support
 - Configurable prefix completion
 - Display limits
 - extensibility
 - 47 tests

See main [CHANGELOG.md](../../CHANGELOG.md) for version history.

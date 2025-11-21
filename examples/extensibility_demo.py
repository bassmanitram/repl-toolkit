"""
Demonstration of ShellExpansionCompleter extensibility.

This example shows how to extend ShellExpansionCompleter with custom behavior:
- Caching expensive command results
- Adding security filtering
- Custom output formatting
- New expansion patterns
"""

import asyncio
import logging

# Configure logging to see errors from repl_toolkit
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from prompt_toolkit.completion import Completion
from prompt_toolkit.formatted_text import FormattedText

from repl_toolkit import AsyncREPL, ShellExpansionCompleter

# Suppress logging for cleaner demo output
logging.getLogger("repl_toolkit").setLevel(logging.ERROR)


# Example 1: Cached Command Execution
class CachedShellExpansion(ShellExpansionCompleter):
    """Cache command results to avoid re-execution."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}

    def execute_command(self, command):
        """Cache command results."""
        if command in self._cache:
            print(f"  [Cache hit for: {command}]")
            return self._cache[command]

        print(f"  [Executing: {command}]")
        result = super().execute_command(command)
        self._cache[command] = result
        return result


# Example 2: Security Filtered Execution
class SecureShellExpansion(ShellExpansionCompleter):
    """Filter dangerous commands."""

    BLOCKED_COMMANDS = ["rm", "dd", "mkfs", ":(){:|:&};:"]

    def execute_command(self, command):
        """Block dangerous commands."""
        cmd_lower = command.lower()
        if any(blocked in cmd_lower for blocked in self.BLOCKED_COMMANDS):
            # Return fake error result
            class BlockedResult:
                returncode = 1
                stdout = ""
                stderr = "Command blocked for security"

            return BlockedResult()

        return super().execute_command(command)


# Example 3: Custom Output Processing
class UppercaseShellExpansion(ShellExpansionCompleter):
    """Convert all output to uppercase."""

    def process_command_output(self, output, command):
        """Transform output to uppercase."""
        processed = super().process_command_output(output, command)
        return processed.upper()


# Example 4: Custom Line Filtering
class LongLinesOnlyExpansion(ShellExpansionCompleter):
    """Only show lines longer than 10 characters."""

    def filter_lines(self, lines):
        """Filter to only long lines."""
        filtered = super().filter_lines(lines)
        return [line for line in filtered if len(line) > 10]


# Example 5: Custom Formatting
class EmojiShellExpansion(ShellExpansionCompleter):
    """Add emoji to completions."""

    def format_command_completion(self, command_output, pattern_text, start_pos, label=None):
        """Add 🚀 emoji to command completions."""
        display_text = self.truncate_display(command_output)

        return Completion(
            text=command_output,
            start_position=start_pos,
            display=FormattedText(
                [
                    ("class:completion.emoji", "🚀 "),
                    ("class:completion.cmd", pattern_text),
                    ("class:completion.arrow", " → "),
                    ("class:completion.value", display_text),
                ]
            ),
            display_meta=FormattedText([("class:completion.meta", "Shell command")]),
        )

    def format_variable_completion(self, var_name, value, start_pos, pattern_text):
        """Add 💚 emoji to variable completions."""
        display_value = self.truncate_display(value)

        return Completion(
            text=value,
            start_position=start_pos,
            display=FormattedText(
                [
                    ("class:completion.emoji", "💚 "),
                    ("class:completion.var", "${"),
                    ("class:completion.var.name", var_name),
                    ("class:completion.var", "}"),
                    ("class:completion.arrow", " → "),
                    ("class:completion.value", display_value),
                ]
            ),
            display_meta=FormattedText([("class:completion.meta", "Environment variable")]),
        )


# Example 6: Combined Extensions
class AdvancedShellExpansion(ShellExpansionCompleter):
    """Combine multiple extensions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}
        self.stats = {"executions": 0, "cache_hits": 0}

    def execute_command(self, command):
        """Cached + logged execution."""
        if command in self._cache:
            self.stats["cache_hits"] += 1
            return self._cache[command]

        self.stats["executions"] += 1
        result = super().execute_command(command)
        self._cache[command] = result
        return result

    def process_command_output(self, output, command):
        """Add execution stats as comment."""
        processed = super().process_command_output(output, command)
        return f"{processed}  # [exec:{self.stats['executions']} hits:{self.stats['cache_hits']}]"


# Demo backend
class DemoBackend:
    async def handle_input(self, user_input: str) -> bool:
        if user_input.strip():
            print(f"\nYou entered: {user_input}\n")
        return True


async def main():
    print("=" * 60)
    print("ShellExpansionCompleter Extensibility Demo")
    print("=" * 60)
    print()
    print("Try these examples:")
    print("  1. Cached:     $(date) - Type twice to see caching")
    print("  2. Security:   $(rm -rf /) - Will be blocked")
    print("  3. Uppercase:  $(echo hello) - Output in UPPERCASE")
    print("  4. Long lines: $(printf 'short\\nlong line here') - Filters short lines")
    print("  5. Emoji:      ${USER} or $(pwd) - With emoji decoration")
    print("  6. Advanced:   $(ls) - Combined caching + stats")
    print()
    print("Choose a demo (1-6):")

    # For automated demo, use cached version
    backend = DemoBackend()

    # Create completer based on choice (default to cached for demo)
    completer = CachedShellExpansion(timeout=2.0, max_lines=10)

    print()
    print("Using: CachedShellExpansion")
    print("Type commands with $(cmd) or variables with ${VAR}")
    print("Press Ctrl+D to exit")
    print()

    repl = AsyncREPL(backend, completer=completer, prompt_string="Demo> ")

    try:
        await repl.run(backend)
    except (EOFError, KeyboardInterrupt):
        print("\nExiting demo.")


if __name__ == "__main__":
    asyncio.run(main())

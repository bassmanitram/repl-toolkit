"""
Environment variable and shell command expansion completer.
"""

import os
import re
import subprocess
from typing import Iterable, Optional

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText


class ShellExpansionCompleter(Completer):
    """
    Completer that expands environment variables and executes shell commands.

    Supports two patterns:
    - ${VAR_NAME}: Expands to environment variable value
    - $(command): Executes shell command and shows output

    For multi-line command output, offers:
    - ALL: Complete with all lines (always includes full output)
    - Individual lines: Select specific line (always includes full line content)

    Display limits affect only the completion menu appearance, not the inserted content.

    This class is designed to be extensible. Override these public methods to customize:
    - execute_command(): Custom command execution logic
    - process_command_output(): Transform command output before display
    - filter_lines(): Custom line filtering
    - format_command_completion(): Customize command completion display
    - format_variable_completion(): Customize variable completion display
    - truncate_display(): Custom truncation logic

    Security: Commands only execute when user presses Tab (not automatically).

    Args:
        timeout: Command execution timeout in seconds (default: 2.0)
        multiline_all: Include "ALL" option for multi-line output (default: True)
        max_lines: Maximum lines to show in completion menu (default: 50)
                   ALL option always includes full output regardless of this limit
        max_display_length: Maximum line length in completion menu (default: 80)
                            Actual completion text is never truncated

    Example:
        >>> completer = ShellExpansionCompleter()
        >>> # User types: Hello ${USER}
        >>> # Press Tab: Shows username completion
        >>> # User types: Files: $(ls)
        >>> # Press Tab: Shows file list completion options

        >>> # Extend with custom behavior
        >>> class CachedShellExpansion(ShellExpansionCompleter):
        ...     def execute_command(self, command):
        ...         # Add caching logic
        ...         return super().execute_command(command)
    """

    # Pattern to match ${VAR_NAME}
    VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

    # Pattern to match $(command)
    CMD_PATTERN = re.compile(r"\$\(([^)]+)\)")

    def __init__(
        self,
        timeout: float = 2.0,
        multiline_all: bool = True,
        max_lines: int = 50,
        max_display_length: int = 80,
    ):
        """Initialize the completer."""
        self.timeout = timeout
        self.multiline_all = multiline_all
        self.max_lines = max_lines
        self.max_display_length = max_display_length

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Get completions for environment variables and commands.

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects for patterns at cursor position
        """
        text = document.text
        cursor_pos = document.cursor_position

        # Try command pattern first
        for match in self.CMD_PATTERN.finditer(text):
            if match.start() <= cursor_pos <= match.end():
                # Cursor is within this command pattern
                command = match.group(1).strip()
                if command:
                    yield from self.complete_command(command, match, cursor_pos)
                return

        # Try environment variable pattern
        for match in self.VAR_PATTERN.finditer(text):
            if match.start() <= cursor_pos <= match.end():
                # Cursor is within this variable pattern
                var_name = match.group(1)
                if var_name in os.environ:
                    value = os.environ[var_name]
                    start_pos = match.start() - cursor_pos

                    # Use public method for formatting
                    yield self.format_variable_completion(
                        var_name, value, start_pos, match.group(0)
                    )
                return

    def truncate_display(self, text: str) -> str:
        """
        Truncate text for display purposes only.

        Override this method to customize truncation behavior.

        Args:
            text: Text to potentially truncate

        Returns:
            Truncated text with ellipsis if needed, or original text
        """
        if len(text) > self.max_display_length:
            return text[: self.max_display_length - 3] + "..."
        return text

    def execute_command(self, command: str) -> subprocess.CompletedProcess:
        """
        Execute shell command.

        Override this method to customize command execution (e.g., add caching,
        security filtering, or use a different execution mechanism).

        Args:
            command: Shell command to execute

        Returns:
            CompletedProcess with stdout, stderr, and returncode

        Raises:
            subprocess.TimeoutExpired: If command exceeds timeout
            subprocess.SubprocessError: For other execution errors
        """
        return subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=self.timeout
        )

    def process_command_output(self, output: str, command: str) -> str:
        """
        Process command output before creating completions.

        Override this method to transform, filter, or modify command output.

        Args:
            output: Raw command output
            command: The command that was executed

        Returns:
            Processed output string
        """
        return output.strip()

    def filter_lines(self, lines: list[str]) -> list[str]:
        """
        Filter lines from command output.

        Override this method to implement custom line filtering logic.
        Default implementation removes empty lines.

        Args:
            lines: List of output lines

        Returns:
            Filtered list of lines
        """
        return [line for line in lines if line.strip()]

    def format_variable_completion(
        self, var_name: str, value: str, start_pos: int, pattern_text: str
    ) -> Completion:
        """
        Format environment variable completion.

        Override this method to customize how variable completions are displayed.

        Args:
            var_name: Variable name (without ${})
            value: Variable value
            start_pos: Start position for replacement
            pattern_text: Original pattern text like ${VAR}

        Returns:
            Completion object
        """
        display_value = self.truncate_display(value)

        return Completion(
            text=value,
            start_position=start_pos,
            display=FormattedText(
                [
                    ("class:completion.var", "${"),
                    ("class:completion.var.name", var_name),
                    ("class:completion.var", "}"),
                    ("class:completion.arrow", " → "),
                    ("class:completion.value", display_value),
                ]
            ),
            display_meta=FormattedText([("class:completion.meta", "Environment variable")]),
        )

    def format_command_completion(
        self, command_output: str, pattern_text: str, start_pos: int, label: Optional[str] = None
    ) -> Completion:
        """
        Format single-line command completion.

        Override this method to customize how command completions are displayed.

        Args:
            command_output: Command output text
            pattern_text: Original pattern text like $(command)
            start_pos: Start position for replacement
            label: Optional label for the completion

        Returns:
            Completion object
        """
        display_text = self.truncate_display(command_output)

        return Completion(
            text=command_output,
            start_position=start_pos,
            display=FormattedText(
                [
                    ("class:completion.cmd", pattern_text),
                    ("class:completion.arrow", " → "),
                    ("class:completion.value", display_text),
                ]
            ),
            display_meta=FormattedText([("class:completion.meta", "Shell command")]),
        )

    def format_multiline_completion(
        self, line_text: str, line_number: int, pattern_text: str, start_pos: int
    ) -> Completion:
        """
        Format individual line completion for multi-line output.

        Override this method to customize multi-line completion display.

        Args:
            line_text: Text of the line
            line_number: Line number (1-based)
            pattern_text: Original pattern text like $(command)
            start_pos: Start position for replacement

        Returns:
            Completion object
        """
        display_line = self.truncate_display(line_text)

        return Completion(
            text=line_text,
            start_position=start_pos,
            display=FormattedText(
                [
                    ("class:completion.cmd", pattern_text),
                    ("class:completion.arrow", " → "),
                    ("class:completion.line", f"Line {line_number}: "),
                    ("class:completion.value", display_line),
                ]
            ),
            display_meta=FormattedText([("class:completion.meta", "Shell command")]),
        )

    def format_all_lines_completion(
        self, full_output: str, line_count: int, pattern_text: str, start_pos: int
    ) -> Completion:
        """
        Format "ALL" completion for multi-line output.

        Override this method to customize the ALL option display.

        Args:
            full_output: Complete command output with newlines
            line_count: Number of non-empty lines
            pattern_text: Original pattern text like $(command)
            start_pos: Start position for replacement

        Returns:
            Completion object
        """
        return Completion(
            text=full_output,
            start_position=start_pos,
            display=FormattedText(
                [
                    ("class:completion.cmd", pattern_text),
                    ("class:completion.arrow", " → "),
                    ("class:completion.multiline", f"ALL ({line_count} lines)"),
                ]
            ),
            display_meta=FormattedText([("class:completion.meta", "Shell command")]),
        )

    def format_error_completion(
        self, error_message: str, pattern_text: str, start_pos: int
    ) -> Completion:
        """
        Format error completion.

        Override this method to customize error display.

        Args:
            error_message: Error message to display
            pattern_text: Original pattern text like $(command)
            start_pos: Start position for replacement

        Returns:
            Completion object with empty text
        """
        error_display = self.truncate_display(error_message)

        return Completion(
            text="",
            start_position=start_pos,
            display=FormattedText(
                [
                    ("class:completion.cmd", pattern_text),
                    ("class:completion.arrow", " → "),
                    ("class:completion.error", f"Error: {error_display}"),
                ]
            ),
            display_meta=FormattedText([("class:completion.meta", "Shell command")]),
        )

    def complete_command(self, command: str, match, cursor_pos: int) -> Iterable[Completion]:
        """
        Execute command and yield completion(s).

        This is the main public method for command completion. Override to change
        the overall completion flow.

        Args:
            command: Shell command to execute
            match: Regex match object
            cursor_pos: Cursor position

        Yields:
            Completion objects with command output
        """
        start_pos = match.start() - cursor_pos
        pattern_text = match.group(0)

        try:
            result = self.execute_command(command)

            if result.returncode == 0:
                output = self.process_command_output(result.stdout, command)

                if not output:
                    # Command succeeded but no output
                    yield Completion(
                        text="",
                        start_position=start_pos,
                        display=FormattedText(
                            [
                                ("class:completion.cmd", pattern_text),
                                ("class:completion.arrow", " → "),
                                ("class:completion.info", "(no output)"),
                            ]
                        ),
                        display_meta=FormattedText([("class:completion.meta", "Shell command")]),
                    )
                else:
                    # Check if multi-line output
                    lines = output.split("\n")
                    non_empty_lines = self.filter_lines(lines)

                    if len(non_empty_lines) > 1:
                        # Multi-line output
                        yield from self.complete_multiline(
                            output, non_empty_lines, pattern_text, start_pos
                        )
                    else:
                        # Single line output
                        yield self.format_command_completion(output, pattern_text, start_pos)
            else:
                # Command failed
                error_msg = result.stderr.strip() or f"Exit code {result.returncode}"
                yield self.format_error_completion(error_msg, pattern_text, start_pos)

        except subprocess.TimeoutExpired:
            yield self.format_error_completion(
                f"Timeout ({self.timeout}s)", pattern_text, start_pos
            )
        except FileNotFoundError:
            yield self.format_error_completion("Command not found", pattern_text, start_pos)

    def complete_multiline(
        self, full_output: str, lines: list, pattern_text: str, start_pos: int
    ) -> Iterable[Completion]:
        """
        Yield completions for multi-line command output.

        Override this method to change multi-line completion behavior.

        Args:
            full_output: Complete command output (with newlines)
            lines: List of non-empty lines
            pattern_text: Original pattern text like $(command)
            start_pos: Start position for replacement

        Yields:
            Completion for ALL and individual lines (up to max_lines limit)
        """
        total_lines = len(lines)

        # First option: ALL (complete with all lines - never truncated)
        if self.multiline_all:
            yield self.format_all_lines_completion(
                full_output, total_lines, pattern_text, start_pos
            )

        # Individual line options (limited to max_lines)
        lines_to_show = lines[: self.max_lines]
        remaining = total_lines - len(lines_to_show)

        for i, line in enumerate(lines_to_show, 1):
            yield self.format_multiline_completion(line, i, pattern_text, start_pos)

        # If there are more lines, show an indicator
        if remaining > 0:
            yield Completion(
                text="",  # No completion action
                start_position=start_pos,
                display=FormattedText(
                    [
                        ("class:completion.cmd", pattern_text),
                        ("class:completion.arrow", " → "),
                        ("class:completion.info", f"({remaining} more lines... use ALL)"),
                    ]
                ),
                display_meta=FormattedText([("class:completion.meta", "Shell command")]),
            )

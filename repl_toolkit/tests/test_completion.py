"""
Tests for completion utilities.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest
from prompt_toolkit.document import Document

from repl_toolkit.completion import PrefixCompleter, ShellExpansionCompleter


def _get_text(formatted_text):
    """Helper to extract plain text from FormattedText."""
    if hasattr(formatted_text, "__iter__"):
        return "".join(text for style, text in formatted_text)
    return str(formatted_text)


class TestShellExpansionCompleter:
    """Test ShellExpansionCompleter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.completer = ShellExpansionCompleter()
        self.complete_event = Mock()

    def test_completer_initialization(self):
        """Test completer initialization."""
        completer = ShellExpansionCompleter()
        assert completer.timeout == 2.0

        completer = ShellExpansionCompleter(timeout=5.0)
        assert completer.timeout == 5.0

    def test_environment_variable_expansion(self):
        """Test basic environment variable expansion."""
        # Set test environment variable
        os.environ["TEST_VAR"] = "test_value"

        try:
            # Cursor after variable pattern
            document = Document(text="Hello ${TEST_VAR}", cursor_position=17)
            completions = list(self.completer.get_completions(document, self.complete_event))

            assert len(completions) == 1
            assert completions[0].text == "test_value"
            assert completions[0].start_position == -11  # Position to replace ${TEST_VAR}
            assert "${TEST_VAR}" in _get_text(completions[0].display) or "TEST_VAR" in _get_text(
                completions[0].display
            )
            assert "test_value" in str(completions[0].display)
        finally:
            del os.environ["TEST_VAR"]

    def test_environment_variable_cursor_inside(self):
        """Test expansion when cursor is inside the variable pattern."""
        os.environ["USER_VAR"] = "inside_value"

        try:
            # Cursor in the middle of ${USER_VAR}
            document = Document(text="Value: ${USER_VAR}", cursor_position=12)
            completions = list(self.completer.get_completions(document, self.complete_event))

            assert len(completions) == 1
            assert completions[0].text == "inside_value"
        finally:
            del os.environ["USER_VAR"]

    def test_environment_variable_not_found(self):
        """Test behavior when environment variable doesn't exist."""
        document = Document(text="${NONEXISTENT_VAR}", cursor_position=16)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should not offer completion for nonexistent variables
        assert len(completions) == 0

    def test_environment_variable_cursor_outside(self):
        """Test no completion when cursor is outside the pattern."""
        os.environ["OUTSIDE_VAR"] = "value"

        try:
            # Cursor before the pattern
            document = Document(text="Hello ${OUTSIDE_VAR}", cursor_position=0)
            completions = list(self.completer.get_completions(document, self.complete_event))

            # Should not complete when cursor is outside
            assert len(completions) == 0
        finally:
            del os.environ["OUTSIDE_VAR"]

    def test_multiple_environment_variables(self):
        """Test multiple environment variables in same text."""
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"

        try:
            # Cursor on second variable
            document = Document(text="${VAR1} and ${VAR2}", cursor_position=19)
            completions = list(self.completer.get_completions(document, self.complete_event))

            assert len(completions) == 1
            assert completions[0].text == "value2"
        finally:
            del os.environ["VAR1"]
            del os.environ["VAR2"]

    def test_command_execution_simple(self):
        """Test simple command execution."""
        # Use echo command which is available on most systems
        document = Document(text="Result: $(echo test)", cursor_position=20)
        completions = list(self.completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "test"
        assert "$(echo test)" in str(completions[0].display)

    def test_command_execution_cursor_inside(self):
        """Test command execution when cursor is inside pattern."""
        document = Document(text="$(echo hello)", cursor_position=8)
        completions = list(self.completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "hello"

    def test_command_execution_with_output_trimming(self):
        """Test that command output is trimmed."""
        document = Document(text='$(printf "  spaces  ")', cursor_position=22)
        completions = list(self.completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "spaces"

    def test_command_execution_empty_command(self):
        """Test handling of empty command pattern."""
        document = Document(text="Empty: $()", cursor_position=10)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should not complete empty commands
        assert len(completions) == 0

    def test_command_execution_whitespace_only(self):
        """Test handling of whitespace-only command."""
        document = Document(text="$(   )", cursor_position=6)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should not complete whitespace-only commands
        assert len(completions) == 0

    def test_command_execution_not_found(self):
        """Test handling of command not found error."""
        document = Document(text="$(nonexistent_command_xyz)", cursor_position=26)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should offer completion with error message
        assert len(completions) == 1
        assert completions[0].text == ""  # Empty replacement
        assert "Error" in str(completions[0].display)

    def test_command_execution_failure(self):
        """Test handling of command execution failure."""
        # Command that will fail
        document = Document(text="$(ls /nonexistent/path)", cursor_position=23)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should offer completion with error message
        assert len(completions) == 1
        assert completions[0].text == ""
        assert "Error" in str(completions[0].display)

    def test_command_execution_timeout(self):
        """Test command execution timeout."""
        completer = ShellExpansionCompleter(timeout=0.1)

        # Command that will timeout (sleep longer than timeout)
        document = Document(text="$(sleep 5)", cursor_position=10)
        completions = list(completer.get_completions(document, self.complete_event))

        # Should offer completion with timeout message
        assert len(completions) == 1
        assert completions[0].text == ""
        assert "Timeout" in str(completions[0].display)

    def test_mixed_patterns(self):
        """Test combination of environment variables and commands."""
        os.environ["MIX_VAR"] = "envvalue"

        try:
            # Text with both patterns, cursor on command
            document = Document(text="${MIX_VAR} and $(echo cmd)", cursor_position=26)
            completions = list(self.completer.get_completions(document, self.complete_event))

            # Should only complete the pattern at cursor
            assert len(completions) == 1
            assert completions[0].text == "cmd"
        finally:
            del os.environ["MIX_VAR"]

    def test_cursor_outside_all_patterns(self):
        """Test no completion when cursor is outside all patterns."""
        os.environ["OUT_VAR"] = "value"

        try:
            # Cursor in plain text area
            document = Document(text="Plain ${OUT_VAR} text $(echo test)", cursor_position=19)
            completions = list(self.completer.get_completions(document, self.complete_event))

            # Should not complete
            assert len(completions) == 0
        finally:
            del os.environ["OUT_VAR"]

    def test_variable_pattern_validation(self):
        """Test that only valid variable names are matched."""
        os.environ["_VALID_VAR"] = "valid"

        try:
            # Valid variable name
            document = Document(text="${_VALID_VAR}", cursor_position=13)
            completions = list(self.completer.get_completions(document, self.complete_event))
            assert len(completions) == 1

            # Invalid patterns should not be matched by regex
            # (testing the pattern itself, not the completer behavior)
            assert ShellExpansionCompleter.VAR_PATTERN.match("${123INVALID}") is None
            assert ShellExpansionCompleter.VAR_PATTERN.match("${-INVALID}") is None
        finally:
            del os.environ["_VALID_VAR"]

    def test_start_position_calculation(self):
        """Test correct calculation of start_position."""
        os.environ["POS_VAR"] = "replacement"

        try:
            text = "Prefix ${POS_VAR} suffix"
            cursor_position = 17  # End of ${POS_VAR}
            document = Document(text=text, cursor_position=cursor_position)

            completions = list(self.completer.get_completions(document, self.complete_event))

            assert len(completions) == 1
            # start_position should be negative, pointing back to start of pattern
            # Pattern starts at position 7, cursor at 17
            # start_position = 7 - 17 = -10
            assert completions[0].start_position == -10
        finally:
            del os.environ["POS_VAR"]

    def test_completer_with_real_environment_variables(self):
        """Test with actual system environment variables."""
        # USER or USERNAME should exist on most systems
        var_name = (
            "USER" if "USER" in os.environ else "USERNAME" if "USERNAME" in os.environ else None
        )

        if var_name:
            document = Document(text=f"${{{var_name}}}", cursor_position=len(var_name) + 3)
            completions = list(self.completer.get_completions(document, self.complete_event))

            assert len(completions) == 1
            assert completions[0].text == os.environ[var_name]
        else:
            pytest.skip("No USER or USERNAME environment variable available")

    def test_display_meta_fields(self):
        """Test that display_meta fields are set correctly."""
        os.environ["META_VAR"] = "value"

        try:
            # Test environment variable
            document = Document(text="${META_VAR}", cursor_position=11)
            completions = list(self.completer.get_completions(document, self.complete_event))
            assert _get_text(completions[0].display_meta) == "Environment variable"

            # Test command
            document = Document(text="$(echo test)", cursor_position=12)
            completions = list(self.completer.get_completions(document, self.complete_event))
            assert _get_text(completions[0].display_meta) == "Shell command"
        finally:
            del os.environ["META_VAR"]

    def test_patterns_are_non_greedy(self):
        """Test that command pattern is non-greedy."""
        # Multiple command patterns
        document = Document(text="$(echo a) and $(echo b)", cursor_position=9)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should only complete the first command where cursor is
        assert len(completions) == 1
        assert completions[0].text == "a"


class TestShellExpansionCompleterIntegration:
    """Integration tests for ShellExpansionCompleter."""

    def test_import_from_package(self):
        """Test that completer can be imported from main package."""
        from repl_toolkit import ShellExpansionCompleter

        completer = ShellExpansionCompleter()
        assert completer is not None

    def test_use_with_merge_completers(self):
        """Test integration with prompt_toolkit's merge_completers."""
        from prompt_toolkit.completion import WordCompleter, merge_completers

        from repl_toolkit import ShellExpansionCompleter

        env_completer = ShellExpansionCompleter()
        word_completer = WordCompleter(["exit", "help"])

        combined = merge_completers([env_completer, word_completer])

        assert combined is not None

    def test_completer_protocol_compliance(self):
        """Test that ShellExpansionCompleter implements Completer protocol."""
        from prompt_toolkit.completion import Completer

        from repl_toolkit import ShellExpansionCompleter

        completer = ShellExpansionCompleter()

        # Should have get_completions method
        assert hasattr(completer, "get_completions")
        assert callable(completer.get_completions)

        # Should be instance of Completer
        assert isinstance(completer, Completer)


class TestMultilineCommandCompletion:
    """Test multi-line command output completion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.completer = ShellExpansionCompleter(multiline_all=True)
        self.complete_event = Mock()

    def test_single_line_command(self):
        """Test command with single line output."""
        document = Document(text="$(echo single)", cursor_position=14)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should have one completion for single line
        assert len(completions) == 1
        assert completions[0].text == "single"
        assert "single" in str(completions[0].display)

    def test_multiline_command_with_all(self):
        """Test command with multi-line output offers ALL + individual lines."""
        # Command that produces multiple lines
        document = Document(text='$(printf "line1\\nline2\\nline3")', cursor_position=31)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should have ALL + 3 lines = 4 completions
        assert len(completions) == 4

        # First should be ALL
        assert "ALL" in str(completions[0].display)
        assert completions[0].text == "line1\nline2\nline3"

        # Then individual lines
        assert completions[1].text == "line1"
        assert "Line 1" in str(completions[1].display)

        assert completions[2].text == "line2"
        assert "Line 2" in str(completions[2].display)

        assert completions[3].text == "line3"
        assert "Line 3" in str(completions[3].display)

    def test_multiline_command_without_all(self):
        """Test multi-line output without ALL option."""
        completer = ShellExpansionCompleter(multiline_all=False)

        document = Document(text='$(printf "a\\nb\\nc")', cursor_position=19)
        completions = list(completer.get_completions(document, self.complete_event))

        # Should have only 3 lines (no ALL)
        assert len(completions) == 3

        # All should be individual lines
        assert completions[0].text == "a"
        assert completions[1].text == "b"
        assert completions[2].text == "c"

        # None should be ALL
        for comp in completions:
            assert "ALL" not in str(comp.display)

    def test_command_with_empty_lines(self):
        """Test that empty lines are filtered out."""
        document = Document(text='$(printf "a\\n\\nb\\n\\n")', cursor_position=22)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should have ALL + 2 non-empty lines = 3 completions
        assert len(completions) == 3

        # ALL contains original with empty lines
        assert "ALL" in str(completions[0].display)

        # But individual lines skip empty ones
        assert completions[1].text == "a"
        assert completions[2].text == "b"

    def test_command_no_output(self):
        """Test command with no output."""
        # Command that produces no output
        document = Document(text="$(true)", cursor_position=7)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should have one completion indicating no output
        assert len(completions) == 1
        assert completions[0].text == ""
        assert "no output" in str(completions[0].display)

    def test_multiline_preserves_order(self):
        """Test that lines are offered in order."""
        document = Document(text='$(printf "first\\nsecond\\nthird")', cursor_position=32)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Skip ALL, check line order
        assert completions[1].text == "first"
        assert completions[2].text == "second"
        assert completions[3].text == "third"


class TestPrefixCompleter:
    """Test PrefixCompleter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.completer = PrefixCompleter(["/help", "/exit", "/quit"], prefix="/")
        self.complete_event = Mock()

    def test_command_at_start_of_line(self):
        """Test command completion at start of line."""
        document = Document(text="/he", cursor_position=3)
        completions = list(self.completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "/help"
        assert completions[0].start_position == -3

    def test_no_completion_mid_sentence(self):
        """Test that commands don't complete in middle of sentence."""
        document = Document(text="Please type /he for info", cursor_position=19)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should NOT complete when command is mid-sentence
        assert len(completions) == 0

    def test_no_completion_in_middle_of_text(self):
        """Test no completion when / is in middle of word."""
        document = Document(text="path/to/file", cursor_position=12)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should not complete file paths
        assert len(completions) == 0

    def test_multiple_matching_commands(self):
        """Test multiple matching commands."""
        document = Document(text="/e", cursor_position=2)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should match /exit (not /help or /quit)
        assert len(completions) == 1
        assert completions[0].text == "/exit"

    def test_exact_match(self):
        """Test exact command match."""
        document = Document(text="/help", cursor_position=5)
        completions = list(self.completer.get_completions(document, self.complete_event))

        # Should still offer completion even for exact match
        assert len(completions) == 1
        assert completions[0].text == "/help"

    def test_no_match(self):
        """Test no matching commands."""
        document = Document(text="/xyz", cursor_position=4)
        completions = list(self.completer.get_completions(document, self.complete_event))

        assert len(completions) == 0

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        completer = PrefixCompleter(["/Help", "/Exit"], ignore_case=True)

        document = Document(text="/he", cursor_position=3)
        completions = list(completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "/Help"

    def test_case_sensitive(self):
        """Test case-sensitive matching."""
        completer = PrefixCompleter(["/Help", "/Exit"], ignore_case=False)

        document = Document(text="/he", cursor_position=3)
        completions = list(completer.get_completions(document, self.complete_event))

        # Should not match /Help (capital H)
        assert len(completions) == 0

    def test_commands_without_leading_slash(self):
        """Test that commands without / get it added."""
        completer = PrefixCompleter(["help", "exit"], prefix="/")

        document = Document(text="/he", cursor_position=3)
        completions = list(completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "/help"

    def test_command_after_newline(self):
        """Test command completion after newline."""
        document = Document(text="line1\n/he", cursor_position=9)
        completions = list(self.completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "/help"

    def test_command_after_newline_with_spaces(self):
        """Test command completion after newline with leading spaces."""
        document = Document(text="line1\n  /he", cursor_position=11)
        completions = list(self.completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert completions[0].text == "/help"

    def test_import_from_package(self):
        """Test that PrefixCompleter can be imported."""
        from repl_toolkit import PrefixCompleter

        completer = PrefixCompleter(["/test"])
        assert completer is not None


class TestShellExpansionCompleterLimits:
    """Test limit features of ShellExpansionCompleter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.complete_event = Mock()

    def test_default_limits(self):
        """Test default limit values."""
        completer = ShellExpansionCompleter()
        assert completer.max_lines == 50
        assert completer.max_display_length == 80

    def test_line_limit_enforcement(self):
        """Test that max_lines limit is enforced in menu."""
        completer = ShellExpansionCompleter(max_lines=5)

        # Command that produces 10 lines
        cmd = 'printf "1\\n2\\n3\\n4\\n5\\n6\\n7\\n8\\n9\\n10"'
        document = Document(text=f"$({cmd})", cursor_position=len(f"$({cmd})"))

        completions = list(completer.get_completions(document, self.complete_event))

        # Should have: ALL + 5 lines + "more lines" indicator = 7
        assert len(completions) == 7

        # ALL should have full output
        all_comp = completions[0]
        assert "10" in all_comp.text
        assert "ALL (10 lines)" in str(all_comp.display)

        # Check individual lines shown (should be 5)
        line_comps = [c for c in completions[1:] if "Line " in str(c.display) and c.text]
        assert len(line_comps) == 5

        # Check "more lines" indicator
        more_indicator = [c for c in completions if "more lines" in str(c.display)]
        assert len(more_indicator) == 1
        assert "5 more lines" in str(more_indicator[0].display)

    def test_display_length_truncation(self):
        """Test that display is truncated but completion text is full."""
        completer = ShellExpansionCompleter(max_display_length=20)

        # Command with long output
        long_text = "A" * 100
        cmd = f'printf "{long_text}"'
        document = Document(text=f"$({cmd})", cursor_position=len(f"$({cmd})"))

        completions = list(completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        completion = completions[0]

        # Full text in completion
        assert len(completion.text) == 100
        assert completion.text == long_text

        # Truncated display
        assert "..." in str(completion.display)

    def test_env_variable_display_truncation(self):
        """Test display truncation for long environment variables."""
        long_value = "X" * 100
        os.environ["TEST_LONG_VAR"] = long_value

        try:
            completer = ShellExpansionCompleter(max_display_length=25)

            document = Document(text="${TEST_LONG_VAR}", cursor_position=16)
            completions = list(completer.get_completions(document, self.complete_event))

            assert len(completions) == 1
            completion = completions[0]

            # Full value in completion
            assert len(completion.text) == 100
            assert completion.text == long_value

            # Truncated in display
            assert "..." in str(completion.display)
        finally:
            del os.environ["TEST_LONG_VAR"]

    def test_combined_limits(self):
        """Test combination of line limit and display length limit."""
        completer = ShellExpansionCompleter(max_lines=3, max_display_length=30)

        # Command with 5 long lines
        long_line = "B" * 60
        cmd = f'printf "{long_line}\\n{long_line}\\n{long_line}\\n{long_line}\\n{long_line}"'
        document = Document(text=f"$({cmd})", cursor_position=len(f"$({cmd})"))

        completions = list(completer.get_completions(document, self.complete_event))

        # ALL + 3 lines + "more lines" indicator = 5
        assert len(completions) == 5

        # ALL has full content
        all_comp = completions[0]
        assert long_line in all_comp.text

        # Check individual lines
        line_comps = [c for c in completions[1:] if "Line " in str(c.display) and c.text]
        assert len(line_comps) == 3

        # Each line should have full text but truncated display
        for comp in line_comps:
            assert len(comp.text) == 60
            assert "..." in str(comp.display)

    def test_no_truncation_when_under_limits(self):
        """Test that short content is not truncated."""
        completer = ShellExpansionCompleter(max_lines=10, max_display_length=50)

        # Short command output
        document = Document(text='$(printf "short")', cursor_position=16)
        completions = list(completer.get_completions(document, self.complete_event))

        assert len(completions) == 1
        assert "..." not in str(completions[0].display)
        assert completions[0].text == "short"

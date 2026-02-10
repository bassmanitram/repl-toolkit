"""
Tests for interactive mode output handling with prompt_toolkit.

Verifies that actions triggered by key bindings or commands properly use
print_formatted_text() instead of print() to maintain clean prompt display.
"""

from io import StringIO
from unittest.mock import patch

from repl_toolkit import ActionRegistry, AsyncREPL
from repl_toolkit.actions import Action, ActionContext


class TestInteractiveModeOutput:
    """Test that interactive mode uses prompt_toolkit output functions."""

    def test_async_repl_creates_action_registry_with_print_formatted_text(self):
        """Verify AsyncREPL creates ActionRegistry with print_formatted_text printer."""
        repl = AsyncREPL()

        # Verify ActionRegistry was created
        assert repl.action_registry is not None
        assert isinstance(repl.action_registry, ActionRegistry)

        # Verify printer is not the default print function
        assert repl.action_registry.printer != print

    def test_async_repl_accepts_custom_action_registry(self):
        """Verify AsyncREPL accepts custom ActionRegistry."""
        custom_registry = ActionRegistry(printer=lambda msg: None)
        repl = AsyncREPL(action_registry=custom_registry)

        assert repl.action_registry is custom_registry
        assert repl.action_registry.printer != print

    def test_action_output_uses_prompt_toolkit_printer(self):
        """Verify action output uses the configured printer."""
        output_buffer = []

        def capture_printer(msg):
            output_buffer.append(msg)

        registry = ActionRegistry(printer=capture_printer)

        # Create an action that produces output
        def test_handler(context: ActionContext):
            context.printer("Test output from action")

        action = Action(
            name="test_output",
            description="Test action with output",
            category="Test",
            handler=test_handler,
            command="/test",
        )

        registry.register_action(action)

        # Execute the action
        context = ActionContext(registry=registry, triggered_by="test", printer=capture_printer)
        registry.execute_action("test_output", context)

        # Verify output went through custom printer
        assert "Test output from action" in output_buffer

    @patch("repl_toolkit.async_repl.print_formatted_text")
    def test_async_repl_printer_calls_print_formatted_text(self, mock_print_formatted):
        """Verify AsyncREPL's printer calls print_formatted_text."""
        repl = AsyncREPL()

        # Get the printer function
        printer = repl.action_registry.printer

        # Call it with a message
        printer("Test message")

        # Verify print_formatted_text was called
        mock_print_formatted.assert_called_once_with("Test message")

    def test_action_context_has_prompt_toolkit_printer(self):
        """Verify ActionContext receives prompt_toolkit printer."""
        repl = AsyncREPL()

        # Create a context as the registry would
        context = ActionContext(
            registry=repl.action_registry,
            printer=repl.action_registry.printer,
            triggered_by="test",
        )

        # Verify printer is not standard print
        assert context.printer != print

        # Verify printer is callable
        assert callable(context.printer)

    def test_builtin_help_action_uses_configured_printer(self):
        """Verify built-in help action uses the configured printer."""
        output_buffer = []

        def capture_printer(msg):
            output_buffer.append(msg)

        registry = ActionRegistry(printer=capture_printer)

        # Execute help command
        registry.handle_command("/help")

        # Verify help output went through custom printer
        assert len(output_buffer) > 0
        assert any("help" in msg.lower() for msg in output_buffer)

    def test_unknown_command_uses_configured_printer(self):
        """Verify unknown command errors use the configured printer."""
        output_buffer = []

        def capture_printer(msg):
            output_buffer.append(msg)

        registry = ActionRegistry(printer=capture_printer)

        # Execute unknown command
        registry.handle_command("/nonexistent")

        # Verify error message went through custom printer
        assert len(output_buffer) > 0
        assert any("unknown" in msg.lower() for msg in output_buffer)


class TestHeadlessModeOutput:
    """Test that headless mode continues to use standard print()."""

    def test_headless_repl_uses_standard_print(self):
        """Verify HeadlessREPL uses standard print() for output."""
        from repl_toolkit import HeadlessREPL

        headless = HeadlessREPL()

        # Verify HeadlessREPL uses standard print (correct for headless!)
        assert headless.action_registry.printer == print

    def test_headless_repl_accepts_custom_printer(self):
        """Verify HeadlessREPL accepts custom printer if provided."""
        from repl_toolkit import HeadlessREPL

        custom_printer = lambda msg: None
        custom_registry = ActionRegistry(printer=custom_printer)
        headless = HeadlessREPL(action_registry=custom_registry)

        assert headless.action_registry.printer == custom_printer

    def test_headless_output_goes_to_stdout(self):
        """Verify headless mode output goes to standard stdout."""
        from repl_toolkit import HeadlessREPL

        headless = HeadlessREPL()

        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as fake_stdout:
            # Execute a command that produces output
            headless.action_registry.handle_command("/help")

            # Verify output went to stdout (via print)
            output = fake_stdout.getvalue()
            assert len(output) > 0


class TestOutputConsistency:
    """Test output consistency between modes."""

    def test_same_action_different_output_in_different_modes(self):
        """Verify same action uses different output methods in different modes."""
        from repl_toolkit import HeadlessREPL

        # Interactive mode
        interactive_outputs = []
        interactive_repl = AsyncREPL()
        original_printer = interactive_repl.action_registry.printer

        # Wrap to capture
        def capture_interactive(msg):
            interactive_outputs.append(msg)
            original_printer(msg)

        interactive_repl.action_registry.printer = capture_interactive

        # Headless mode
        headless_outputs = []

        def capture_headless(msg):
            headless_outputs.append(msg)

        headless_registry = ActionRegistry(printer=capture_headless)
        headless_repl = HeadlessREPL(action_registry=headless_registry)

        # Execute same command in both modes
        interactive_repl.action_registry.handle_command("/help")
        headless_repl.action_registry.handle_command("/help")

        # Both should produce output
        assert len(interactive_outputs) > 0
        assert len(headless_outputs) > 0

        # Content should be similar (help text)
        assert any("help" in msg.lower() for msg in interactive_outputs)
        assert any("help" in msg.lower() for msg in headless_outputs)


class TestPatchStdout:
    """Test that patch_stdout is applied during prompt."""

    def test_patch_stdout_import_available(self):
        """Verify patch_stdout is imported."""
        from repl_toolkit.async_repl import patch_stdout

        assert patch_stdout is not None
        assert callable(patch_stdout)

    def test_print_formatted_text_import_available(self):
        """Verify print_formatted_text is imported."""
        from repl_toolkit.async_repl import print_formatted_text

        assert print_formatted_text is not None
        assert callable(print_formatted_text)


class TestCustomActionOutput:
    """Test custom actions with output work correctly."""

    def test_custom_action_with_multiple_output_lines(self):
        """Verify custom action with multiple print statements works."""
        output_buffer = []

        def capture_printer(msg):
            output_buffer.append(msg)

        registry = ActionRegistry(printer=capture_printer)

        def multi_line_handler(context: ActionContext):
            context.printer("Line 1")
            context.printer("Line 2")
            context.printer("Line 3")

        action = Action(
            name="multi_line",
            description="Action with multiple lines",
            category="Test",
            handler=multi_line_handler,
            command="/multiline",
        )

        registry.register_action(action)
        registry.handle_command("/multiline")

        # Verify all lines went through printer
        assert len(output_buffer) == 3
        assert "Line 1" in output_buffer
        assert "Line 2" in output_buffer
        assert "Line 3" in output_buffer

    def test_custom_action_with_formatted_output(self):
        """Verify custom action can use formatted text."""
        output_buffer = []

        def capture_printer(msg):
            output_buffer.append(msg)

        registry = ActionRegistry(printer=capture_printer)

        def formatted_handler(context: ActionContext):
            # Actions can pass formatted text
            context.printer("Regular text")
            context.printer("\x1b[1mBold text\x1b[0m")  # ANSI codes

        action = Action(
            name="formatted",
            description="Action with formatted output",
            category="Test",
            handler=formatted_handler,
            command="/formatted",
        )

        registry.register_action(action)
        registry.handle_command("/formatted")

        # Verify both messages captured
        assert len(output_buffer) == 2
        assert "Regular text" in output_buffer
        assert "\x1b[1mBold text\x1b[0m" in output_buffer


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_action_registry_defaults_to_print_when_no_printer_provided(self):
        """Verify ActionRegistry defaults to print() if no printer provided."""
        registry = ActionRegistry()  # No printer specified

        # Should default to print
        assert registry.printer == print

    def test_existing_actions_continue_to_work(self):
        """Verify existing action implementations continue to work."""

        # This simulates an action written before the printer parameter existed
        def legacy_handler(context: ActionContext):
            # Old actions might not use context.printer
            # They might call print() directly (now patched in interactive mode)
            pass  # Just verify it doesn't crash

        action = Action(
            name="legacy",
            description="Legacy action",
            category="Test",
            handler=legacy_handler,
            command="/legacy",
        )

        registry = ActionRegistry()
        registry.register_action(action)
        registry.handle_command("/legacy")

        # Should complete without error
        assert True

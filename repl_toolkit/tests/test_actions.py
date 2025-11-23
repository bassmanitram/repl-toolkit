"""
Tests for the action system.
"""

from unittest.mock import Mock

import pytest

from repl_toolkit.actions import (
    Action,
    ActionContext,
    ActionError,
    ActionRegistry,
    ActionValidationError,
)


class TestAction:
    """Test Action dataclass functionality."""

    def test_action_creation_minimal(self):
        """Test creating action with minimal required parameters."""
        action = Action(
            name="test_action",
            description="Test action",
            category="Test",
            handler=lambda ctx: None,
            command="/test",
        )

        assert action.name == "test_action"
        assert action.description == "Test action"
        assert action.category == "Test"
        assert action.command == "/test"
        assert action.has_command
        assert not action.has_shortcut

    def test_action_creation_full(self):
        """Test creating action with all parameters."""
        handler = lambda ctx: None

        action = Action(
            name="full_action",
            description="Full test action",
            category="Test",
            handler=handler,
            command="/full",
            command_usage="/full [args] - Full test command",
            keys="F2",
            keys_description="Full test shortcut",
            enabled=True,
            context="test_context",
        )

        assert action.name == "full_action"
        assert action.has_command
        assert action.has_shortcut
        assert action.enabled
        assert action.context == "test_context"

    def test_action_validation_errors(self):
        """Test action validation failures."""
        # Empty name
        with pytest.raises(ValueError, match="Action name cannot be empty"):
            Action(
                name="",
                description="Test",
                category="Test",
                handler=lambda ctx: None,
                command="/test",
            )

        # Empty description
        with pytest.raises(ValueError, match="Action description cannot be empty"):
            Action(
                name="test",
                description="",
                category="Test",
                handler=lambda ctx: None,
                command="/test",
            )

        # No command or keys
        with pytest.raises(ValueError, match="Action must have either command or keys binding"):
            Action(name="test", description="Test", category="Test", handler=lambda ctx: None)

        # Invalid command format
        with pytest.raises(ValueError, match="Command 'test' must start with '/'"):
            Action(
                name="test",
                description="Test",
                category="Test",
                handler=lambda ctx: None,
                command="test",
            )

    def test_keys_list_handling(self):
        """Test handling of keys as string vs list."""
        # Single key as string
        action1 = Action(
            name="test1", description="Test", category="Test", handler=lambda ctx: None, keys="F1"
        )
        assert action1.get_keys_list() == ["F1"]

        # Multiple keys as list
        action2 = Action(
            name="test2",
            description="Test",
            category="Test",
            handler=lambda ctx: None,
            keys=["F1", "ctrl-h"],
        )
        assert action2.get_keys_list() == ["F1", "ctrl-h"]

        # No keys
        action3 = Action(
            name="test3",
            description="Test",
            category="Test",
            handler=lambda ctx: None,
            command="/test",
        )
        assert action3.get_keys_list() == []


class TestActionContext:
    """Test ActionContext functionality."""

    def test_context_creation(self):
        """Test action context creation."""
        registry = Mock()
        backend = Mock()

        context = ActionContext(
            registry=registry, backend=backend, args=["arg1", "arg2"], triggered_by="command"
        )

        assert context.registry is registry
        assert context.backend is backend
        assert context.args == ["arg1", "arg2"]
        assert context.triggered_by == "command"

    def test_context_triggered_by_detection(self):
        """Test automatic triggered_by detection."""
        registry = Mock()

        # Should detect shortcut from event
        context1 = ActionContext(registry=registry, event=Mock())
        assert context1.triggered_by == "shortcut"

        # Should detect command from args
        context2 = ActionContext(registry=registry, args=["arg"])
        assert context2.triggered_by == "command"

        # Should detect command from user_input
        context3 = ActionContext(registry=registry, user_input="/test")
        assert context3.triggered_by == "command"

        # Should default to programmatic
        context4 = ActionContext(registry=registry)
        assert context4.triggered_by == "programmatic"

    def test_context_printer_default(self):
        """Test that printer defaults to print."""
        registry = Mock()
        context = ActionContext(registry=registry)
        assert context.printer == print

    def test_context_custom_printer(self):
        """Test that custom printer can be set."""
        registry = Mock()
        custom_printer = Mock()
        context = ActionContext(registry=registry, printer=custom_printer)
        assert context.printer == custom_printer


class TestActionRegistry:
    """Test ActionRegistry functionality."""

    def setup_method(self):
        """Set up test registry."""
        self.registry = ActionRegistry()

    def test_registry_initialization(self):
        """Test registry initializes with built-in actions."""
        assert len(self.registry.actions) > 0
        assert "show_help" in self.registry.actions
        assert "/help" in self.registry.command_map
        assert "F1" in self.registry.key_map

    def test_registry_custom_printer(self):
        """Test registry with custom printer."""
        mock_printer = Mock()
        registry = ActionRegistry(printer=mock_printer)
        assert registry.printer == mock_printer

    def test_registry_default_printer(self):
        """Test registry defaults to print."""
        registry = ActionRegistry()
        assert registry.printer == print

    def test_register_action(self):
        """Test action registration."""
        action = Action(
            name="test_action",
            description="Test action",
            category="Test",
            handler=lambda ctx: None,
            command="/test",
            keys="F10",
        )

        self.registry.register_action(action)

        assert "test_action" in self.registry.actions
        assert "/test" in self.registry.command_map
        assert "F10" in self.registry.key_map
        assert self.registry.command_map["/test"] == "test_action"
        assert self.registry.key_map["F10"] == "test_action"

    def test_register_action_conflicts(self):
        """Test action registration conflict detection."""
        action1 = Action(
            name="action1",
            description="Test",
            category="Test",
            handler=lambda ctx: None,
            command="/test",
        )
        action2 = Action(
            name="action2",
            description="Test",
            category="Test",
            handler=lambda ctx: None,
            command="/test",  # Same command
        )

        self.registry.register_action(action1)

        with pytest.raises(ActionValidationError, match="Command '/test' already bound"):
            self.registry.register_action(action2)

    def test_convenience_registration_methods(self):
        """Test convenience registration methods."""
        # Test action registration with both command and keys
        self.registry.register_action(
            name="both_test",
            description="Both test",
            category="Test",
            handler=lambda ctx: None,
            command="/both",
            keys="F11",
        )

        assert "both_test" in self.registry.actions
        assert "/both" in self.registry.command_map
        assert "F11" in self.registry.key_map

        # Test command-only registration
        self.registry.register_action(
            name="cmd_test",
            command="/cmdonly",
            description="Command only",
            category="Test",
            handler=lambda ctx: None,
        )

        action = self.registry.get_action("cmd_test")
        assert action.has_command
        assert not action.has_shortcut

        # Test shortcut-only registration
        self.registry.register_action(
            name="key_test",
            keys="F12",
            description="Key only",
            category="Test",
            handler=lambda ctx: None,
        )

        action = self.registry.get_action("key_test")
        assert not action.has_command
        assert action.has_shortcut

    def test_action_lookup_methods(self):
        """Test action lookup methods."""
        action = Action(
            name="lookup_test",
            description="Lookup test",
            category="Test",
            handler=lambda ctx: None,
            command="/lookup",
            keys="ctrl-l",
        )

        self.registry.register_action(action)

        # Test lookup by name
        found = self.registry.get_action("lookup_test")
        assert found is action

        # Test lookup by command
        found = self.registry.get_action_by_command("/lookup")
        assert found is action

        # Test lookup by keys
        found = self.registry.get_action_by_keys("ctrl-l")
        assert found is action

        # Test not found cases
        assert self.registry.get_action("nonexistent") is None
        assert self.registry.get_action_by_command("/nonexistent") is None
        assert self.registry.get_action_by_keys("nonexistent") is None

    def test_execute_action(self):
        """Test action execution."""
        executed = []

        def test_handler(context):
            executed.append(context.triggered_by)

        action = Action(
            name="exec_test",
            description="Execution test",
            category="Test",
            handler=test_handler,
            command="/exec",
        )

        self.registry.register_action(action)

        context = ActionContext(registry=self.registry, triggered_by="test")

        self.registry.execute_action("exec_test", context)
        assert executed == ["test"]

    def test_execute_nonexistent_action(self):
        """Test executing nonexistent action."""
        context = ActionContext(registry=self.registry)

        with pytest.raises(ActionError, match="Action 'nonexistent' not found"):
            self.registry.execute_action("nonexistent", context)

    def test_execute_disabled_action(self):
        """Test executing disabled action."""
        action = Action(
            name="disabled_test",
            description="Disabled test",
            category="Test",
            handler=lambda ctx: None,
            command="/disabled",
            enabled=False,
        )

        self.registry.register_action(action)
        context = ActionContext(registry=self.registry)

        # Should not raise error, but should not execute
        self.registry.execute_action("disabled_test", context)

    def test_handle_command(self):
        """Test command handling."""
        executed = []

        def test_handler(context):
            executed.append(context.args)

        action = Action(
            name="cmd_test",
            description="Command test",
            category="Test",
            handler=test_handler,
            command="/cmdtest",
        )

        self.registry.register_action(action)

        self.registry.handle_command("/cmdtest arg1 arg2")
        assert executed == [["arg1", "arg2"]]

    def test_handle_command_with_custom_printer(self):
        """Test command handling with custom printer."""
        mock_printer = Mock()
        registry = ActionRegistry(printer=mock_printer)

        # Test unknown command uses custom printer
        registry.handle_command("/unknown")

        # Should have printed to custom printer
        assert mock_printer.call_count >= 1
        calls = [str(call) for call in mock_printer.call_args_list]
        assert any("Unknown command" in str(call) for call in calls)

    def test_handle_unknown_command(self):
        """Test handling unknown command."""
        # Should not raise error, just print message
        self.registry.handle_command("/unknown")

    def test_handle_shortcut(self):
        """Test shortcut handling."""
        executed = []

        def test_handler(context):
            executed.append(context.event)

        action = Action(
            name="key_test",
            description="Key test",
            category="Test",
            handler=test_handler,
            keys="F5",
        )

        self.registry.register_action(action)

        mock_event = Mock()
        self.registry.handle_shortcut("F5", mock_event)
        assert executed == [mock_event]

    def test_handle_unknown_shortcut(self):
        """Test handling unknown shortcut."""
        # Should not raise error, just log
        self.registry.handle_shortcut("unknown", Mock())

    def test_printer_propagation_to_context(self):
        """Test that printer is propagated to ActionContext."""
        mock_printer = Mock()
        registry = ActionRegistry(printer=mock_printer)

        outputs = []

        def test_handler(context):
            # Verify context has the custom printer
            assert context.printer == mock_printer
            context.printer("Test output")
            outputs.append("executed")

        action = Action(
            name="printer_test",
            description="Printer test",
            category="Test",
            handler=test_handler,
            command="/printertest",
        )

        registry.register_action(action)
        registry.handle_command("/printertest")

        # Verify handler was executed
        assert outputs == ["executed"]

        # Verify printer was called
        mock_printer.assert_called_with("Test output")

    def test_list_methods(self):
        """Test list methods."""
        actions = self.registry.list_actions()
        assert isinstance(actions, list)
        assert "show_help" in actions

        commands = self.registry.list_commands()
        assert isinstance(commands, list)
        assert "/help" in commands

        shortcuts = self.registry.list_shortcuts()
        assert isinstance(shortcuts, list)
        assert "F1" in shortcuts

    def test_categories(self):
        """Test category organization."""
        categories = self.registry.get_actions_by_category()
        assert isinstance(categories, dict)
        assert "General" in categories
        assert len(categories["General"]) > 0

    def test_builtin_help_action(self):
        """Test built-in help action."""
        # Test general help
        context = ActionContext(registry=self.registry, args=[])
        self.registry.execute_action("show_help", context)

        # Test specific help
        context = ActionContext(registry=self.registry, args=["show_help"])
        self.registry.execute_action("show_help", context)

        # Test help for nonexistent action
        context = ActionContext(registry=self.registry, args=["nonexistent"])
        self.registry.execute_action("show_help", context)

    def test_builtin_help_action_custom_printer(self):
        """Test built-in help action with custom printer."""
        mock_printer = Mock()
        registry = ActionRegistry(printer=mock_printer)

        # Execute help command
        registry.handle_command("/help")

        # Verify custom printer was called
        assert mock_printer.call_count > 0

        # Check that help output was sent to custom printer
        calls = [str(call) for call in mock_printer.call_args_list]
        assert any("Available Actions" in str(call) for call in calls)

    def test_builtin_shortcuts_action(self):
        """Test built-in shortcuts listing action."""
        context = ActionContext(registry=self.registry, args=[])
        self.registry.execute_action("list_shortcuts", context)

    def test_builtin_shortcuts_action_custom_printer(self):
        """Test built-in shortcuts action with custom printer."""
        mock_printer = Mock()
        registry = ActionRegistry(printer=mock_printer)

        # Execute shortcuts command
        registry.handle_command("/shortcuts")

        # Verify custom printer was called
        assert mock_printer.call_count > 0

        # Check that shortcuts output was sent to custom printer
        calls = [str(call) for call in mock_printer.call_args_list]
        assert any("Keyboard Shortcuts" in str(call) for call in calls)


class TestActionHandlerProtocol:
    """Test ActionHandler protocol compliance."""

    def test_protocol_compliance(self):
        """Test that ActionRegistry implements ActionHandler protocol."""
        from repl_toolkit.ptypes import ActionHandler

        registry = ActionRegistry()
        assert isinstance(registry, ActionHandler)

        # Test protocol methods
        assert hasattr(registry, "execute_action")
        assert hasattr(registry, "handle_command")
        assert hasattr(registry, "validate_action")
        assert hasattr(registry, "list_actions")

    def test_validate_action(self):
        """Test action validation."""
        registry = ActionRegistry()

        assert registry.validate_action("show_help")  # Built-in action
        assert not registry.validate_action("nonexistent")

    def test_list_actions(self):
        """Test action listing."""
        registry = ActionRegistry()
        actions = registry.list_actions()

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert "show_help" in actions


class TestActionValidationExtended:
    """Additional validation tests for Action."""

    def test_empty_category_validation(self):
        """Test that empty category raises ValueError."""
        with pytest.raises(ValueError, match="category cannot be empty"):
            Action(
                name="test",
                description="Test",
                category="",  # Empty category
                handler=lambda ctx: None,
            )

    def test_empty_string_handler_validation(self):
        """Test that empty string handler raises ValueError."""
        with pytest.raises(ValueError, match="handler cannot be empty string"):
            Action(
                name="test", description="Test", category="Test", handler=""  # Empty string handler
            )

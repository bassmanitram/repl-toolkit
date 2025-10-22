#!/usr/bin/env python3
"""
Basic usage example for repl_toolkit with actions.

This example demonstrates how to create a simple REPL with both commands
and keyboard shortcuts using the action system with late backend binding.
"""

import asyncio
import sys
from pathlib import Path

# Add the repl_toolkit to path for the example
sys.path.insert(0, str(Path(__file__).parent.parent))

from repl_toolkit import AsyncREPL, run_async_repl, ActionRegistry, Action, ActionContext


class ExampleBackend:
    """Example backend that echoes user input with some processing."""
    
    def __init__(self):
        self.message_count = 0
    
    async def handle_input(self, user_input: str) -> bool:
        """Handle user input by echoing it back with a counter."""
        self.message_count += 1
        
        # Simulate some processing time
        await asyncio.sleep(0.5)
        
        print(f"[Message #{self.message_count}] You said: {user_input}")
        return True


class ExampleActionRegistry(ActionRegistry):
    """Extended action registry with custom actions."""
    
    def __init__(self):
        super().__init__()
        self._register_example_actions()
    
    def _register_example_actions(self):
        """Register example-specific actions."""
        
        # Counter action - both command and shortcut
        self.register_action(
            name="show_counter",
            description="Show message counter",
            category="Example",
            handler=self._show_counter,
            command="/counter",
            command_usage="/counter - Show current message count",
            keys="ctrl-k",
            keys_description="Show message counter"
        )
        
        # Reset counter - command only
        self.register_action(
            name="reset_counter",
            command="/reset",
            description="Reset message counter to zero",
            category="Example",
            handler=self._reset_counter,
            command_usage="/reset - Reset message counter"
        )
        
        # Quick status - shortcut only
        self.register_action(
            name="quick_status",
            keys="F2",
            description="Show quick status",
            category="Example",
            handler=self._quick_status,
            keys_description="Quick status info"
        )
        
        # Save conversation - Both command and shortcut
        self.register_action(
            name="save_conversation",
            description="Save conversation to file",
            category="File",
            handler=self._save_conversation,
            command="/save",
            command_usage="/save [filename] - Save conversation to file",
            keys="ctrl-s", 
            keys_description="Save conversation"
        )
    
    def _show_counter(self, context: ActionContext):
        """Show the current message counter."""
        # Access backend through context or registry
        backend = context.backend or self.backend
        if backend:
            count = backend.message_count
            print(f"📊 Message count: {count}")
            
            if context.triggered_by == "shortcut":
                print("   (Triggered by Ctrl+K)")
            elif context.triggered_by == "command":
                print("   (Triggered by /counter command)")
        else:
            print("❌ Backend not available")
    
    def _reset_counter(self, context: ActionContext):
        """Reset the message counter."""
        backend = context.backend or self.backend
        if backend:
            old_count = backend.message_count
            backend.message_count = 0
            print(f"🔄 Counter reset from {old_count} to 0")
        else:
            print("❌ Backend not available")
    
    def _quick_status(self, context: ActionContext):
        """Show quick status information."""
        backend = context.backend or self.backend
        print("⚡ Quick Status:")
        if backend:
            print(f"   Messages: {backend.message_count}")
            print(f"   Backend: {type(backend).__name__}")
        else:
            print("   Backend: Not available")
        print(f"   Actions: {len(self.actions)} registered")
    
    def _save_conversation(self, context: ActionContext):
        """Save conversation to file."""
        filename = "conversation.txt"
        
        # Use filename from command args if provided
        if context.args and len(context.args) > 0:
            filename = context.args[0]
        
        # Simulate saving (synchronously)
        print(f"💾 Saving conversation to '{filename}'...")
        # Note: In real usage, if you need async operations, handle them internally:
        # import asyncio
        # asyncio.run(some_async_save_operation())
        print(f"✅ Conversation saved!")
        
        if context.triggered_by == "shortcut":
            print("   (Triggered by Ctrl+S)")


async def main():
    """Run the example REPL with late backend binding."""
    print("🚀 REPL Toolkit v1.0 - Basic Usage Example")
    print("=" * 50)
    print()
    print("This example demonstrates the action system with late backend binding.")
    print("You can use both commands and keyboard shortcuts:")
    print()
    print("Commands:")
    print("  /help      - Show all available actions")
    print("  /counter   - Show message counter")
    print("  /reset     - Reset message counter")
    print("  /save      - Save conversation")
    print("  /shell     - Drop to interactive shell")
    print("  /shortcuts - List keyboard shortcuts")
    print()
    print("Keyboard Shortcuts:")
    print("  F1         - Help")
    print("  F2         - Quick status")
    print("  Ctrl+K     - Show counter")
    print("  Ctrl+S     - Save conversation")
    print()
    print("REPL Controls:")
    print("  Enter      - New line")
    print("  Alt+Enter  - Send message")
    print("  Alt+C      - Cancel operation (while processing)")
    print()
    print("Type /exit or /quit to exit.")
    print("=" * 50)
    
    # Create action registry (without backend initially)
    action_registry = ExampleActionRegistry()
    
    # Backend is created and passed to run() - supports resource context pattern
    backend = ExampleBackend()
    
    try:
        # Run the REPL with late backend binding
        await run_async_repl(
            backend=backend,
            action_registry=action_registry,
            prompt_string="Example: ",
            initial_message=None
        )
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


async def main_with_resource_context():
    """
    Example showing how late backend binding supports resource contexts.
    
    This pattern is useful when the backend requires resources that are only
    available within a specific context (database connections, API clients, etc.)
    """
    print("🚀 Resource Context Example")
    print("=" * 30)
    
    # Create REPL and action registry without backend
    action_registry = ExampleActionRegistry()
    repl = AsyncREPL(action_registry=action_registry, prompt_string="Context: ")
    
    # Simulate resource context where backend becomes available
    class ResourceContext:
        def __init__(self):
            self.backend = None
        
        async def __aenter__(self):
            print("📡 Acquiring resources...")
            await asyncio.sleep(0.1)  # Simulate resource acquisition
            self.backend = ExampleBackend()
            print("✅ Resources acquired, backend available")
            return self.backend
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            print("🔒 Releasing resources...")
            await asyncio.sleep(0.1)  # Simulate cleanup
            print("✅ Resources released")
    
    try:
        # Backend only available within resource context
        async with ResourceContext() as backend:
            await repl.run(backend, "Welcome! Backend is now available.")
    except KeyboardInterrupt:
        print("\n👋 Context closed!")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run basic example
    sys.exit(asyncio.run(main()))
    
    # Uncomment to run resource context example instead:
    # sys.exit(asyncio.run(main_with_resource_context()))
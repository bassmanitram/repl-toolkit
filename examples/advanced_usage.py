#!/usr/bin/env python3
"""
Advanced usage example for repl_toolkit v1.0.

This example demonstrates advanced features including:
- Custom action handlers with validation
- Context-aware actions
- Dynamic action registration
- Error handling
- Integration with external systems
- Late backend binding for resource contexts
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add the repl_toolkit to path for the example
sys.path.insert(0, str(Path(__file__).parent.parent))

from repl_toolkit import AsyncREPL, run_async_repl, ActionRegistry, Action, ActionContext
from repl_toolkit.actions import ActionError


class AdvancedBackend:
    """Advanced backend with conversation history and state management."""
    
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.session_data = {
            'start_time': datetime.now(),
            'message_count': 0,
            'last_activity': datetime.now()
        }
        self.active_contexts = set()
    
    async def handle_input(self, user_input: str) -> bool:
        """Handle user input with full conversation tracking."""
        self.session_data['message_count'] += 1
        self.session_data['last_activity'] = datetime.now()
        
        # Add to conversation history
        message = {
            'timestamp': datetime.now().isoformat(),
            'type': 'user',
            'content': user_input,
            'message_id': self.session_data['message_count']
        }
        self.conversation_history.append(message)
        
        # Simulate AI processing
        await asyncio.sleep(0.3)
        
        # Generate response
        response_content = f"I received your message: '{user_input}'"
        if len(user_input) > 50:
            response_content += " (That was a long message!)"
        elif user_input.strip().endswith('?'):
            response_content = f"You asked: '{user_input}' - That's a great question!"
        
        response = {
            'timestamp': datetime.now().isoformat(),
            'type': 'assistant',
            'content': response_content,
            'message_id': self.session_data['message_count'] + 0.5
        }
        self.conversation_history.append(response)
        
        print(f"🤖 {response_content}")
        return True
    
    def get_stats(self) -> Dict:
        """Get comprehensive session statistics."""
        now = datetime.now()
        duration = now - self.session_data['start_time']
        
        return {
            'messages': self.session_data['message_count'],
            'duration_seconds': duration.total_seconds(),
            'conversation_length': len(self.conversation_history),
            'last_activity': self.session_data['last_activity'].isoformat(),
            'active_contexts': len(self.active_contexts)
        }
    
    def search_conversation(self, query: str) -> List[Dict]:
        """Search conversation history."""
        results = []
        query_lower = query.lower()
        
        for msg in self.conversation_history:
            if query_lower in msg['content'].lower():
                results.append(msg)
        
        return results


class AdvancedActionRegistry(ActionRegistry):
    """Advanced action registry with dynamic features."""
    
    def __init__(self):
        super().__init__()
        self._register_advanced_actions()
    
    def _register_advanced_actions(self):
        """Register advanced actions with comprehensive features."""
        
        # Session statistics - both command and shortcut
        self.register_action(
            name="session_stats",
            description="Show detailed session statistics",
            category="Session",
            handler=self._show_session_stats,
            command="/stats",
            command_usage="/stats - Show session statistics",
            keys="F3",
            keys_description="Session statistics"
        )
        
        # Conversation history - command with args
        self.register_action(
            name="show_history",
            command="/history",
            description="Show conversation history",
            category="History",
            handler=self._show_history,
            command_usage="/history [count] - Show last N messages (default: 10)"
        )
        
        # Search conversation - command only
        self.register_action(
            name="search_conversation",
            command="/search",
            description="Search conversation history",
            category="History",
            handler=self._search_conversation,
            command_usage="/search <query> - Search for messages containing query"
        )
        
        # Export conversation - Both command and shortcut
        self.register_action(
            name="export_conversation",
            description="Export conversation to JSON file",
            category="File",
            handler=self._export_conversation,
            command="/export",
            command_usage="/export [filename] - Export conversation to JSON",
            keys="ctrl-e",
            keys_description="Export conversation"
        )
        
        # Clear history - command only (destructive)
        self.register_action(
            name="clear_history",
            command="/clear-history",
            description="Clear conversation history (DESTRUCTIVE)",
            category="Session",
            handler=self._clear_history,
            command_usage="/clear-history - Clear all conversation history"
        )
        
        # Toggle context - shortcut only
        self.register_action(
            name="toggle_debug",
            keys="F12",
            description="Toggle debug information",
            category="Debug",
            handler=self._toggle_debug,
            keys_description="Toggle debug mode"
        )
        
        # Dynamic action registration example
        self.register_action(
            name="register_action",
            command="/register",
            description="Register a new action dynamically",
            category="Meta",
            handler=self._register_dynamic_action,
            command_usage="/register <name> <description> - Register new action"
        )
    
    def _get_backend(self, context: ActionContext) -> AdvancedBackend:
        """Get backend from context or registry, with error handling."""
        backend = context.backend or self.backend
        if not backend:
            raise ActionError("Backend not available")
        return backend
    
    def _show_session_stats(self, context: ActionContext):
        """Show detailed session statistics."""
        try:
            backend = self._get_backend(context)
            stats = backend.get_stats()
            
            print("📊 Session Statistics:")
            print(f"   Messages sent: {stats['messages']}")
            print(f"   Conversation entries: {stats['conversation_length']}")
            print(f"   Session duration: {stats['duration_seconds']:.1f} seconds")
            print(f"   Last activity: {stats['last_activity']}")
            print(f"   Active contexts: {stats['active_contexts']}")
            
            if context.triggered_by == "shortcut":
                print("   (Stats via F3 shortcut)")
        except ActionError as e:
            print(f"❌ {e}")
    
    def _show_history(self, context: ActionContext):
        """Show conversation history."""
        try:
            backend = self._get_backend(context)
            
            # Validate arguments
            count = 10  # default
            if context.args:
                try:
                    count = int(context.args[0])
                    if count <= 0:
                        raise ValueError("Count must be positive")
                except ValueError as e:
                    print(f"❌ Invalid count: {e}")
                    return
            
            history = backend.conversation_history[-count:]
            
            if not history:
                print("📜 No conversation history available")
                return
            
            print(f"📜 Last {len(history)} messages:")
            print("-" * 50)
            
            for msg in history:
                timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M:%S")
                role = "👤" if msg['type'] == 'user' else "🤖"
                content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                print(f"{timestamp} {role} {content}")
            
            print("-" * 50)
        except ActionError as e:
            print(f"❌ {e}")
    
    def _search_conversation(self, context: ActionContext):
        """Search conversation history."""
        try:
            backend = self._get_backend(context)
            
            if not context.args:
                print("❌ Please provide a search query")
                print("Usage: /search <query>")
                return
            
            query = " ".join(context.args)
            results = backend.search_conversation(query)
            
            if not results:
                print(f"🔍 No messages found containing '{query}'")
                return
            
            print(f"🔍 Found {len(results)} messages containing '{query}':")
            print("-" * 50)
            
            for msg in results:
                timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M:%S")
                role = "👤" if msg['type'] == 'user' else "🤖"
                print(f"{timestamp} {role} {msg['content']}")
            
            print("-" * 50)
        except ActionError as e:
            print(f"❌ {e}")
    
    def _export_conversation(self, context: ActionContext):
        """Export conversation to JSON file."""
        try:
            backend = self._get_backend(context)
            
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            if context.args:
                filename = context.args[0]
                if not filename.endswith('.json'):
                    filename += '.json'
            
            export_data = {
                'session_stats': backend.get_stats(),
                'conversation': backend.conversation_history,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Conversation exported to '{filename}'")
            print(f"   {len(backend.conversation_history)} messages exported")
            
            if context.triggered_by == "shortcut":
                print("   (Exported via Ctrl+E)")
                
        except ActionError as e:
            print(f"❌ {e}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def _clear_history(self, context: ActionContext):
        """Clear conversation history with confirmation."""
        try:
            backend = self._get_backend(context)
            
            count = len(backend.conversation_history)
            
            if count == 0:
                print("📜 No conversation history to clear")
                return
            
            print(f"⚠️  This will delete {count} conversation messages.")
            print("This action cannot be undone!")
            
            # In a real implementation, you might want to add confirmation
            backend.conversation_history.clear()
            print("🗑️  Conversation history cleared")
        except ActionError as e:
            print(f"❌ {e}")
    
    def _toggle_debug(self, context: ActionContext):
        """Toggle debug information display."""
        try:
            backend = self._get_backend(context)
            
            debug_context = "debug_mode"
            
            if debug_context in backend.active_contexts:
                backend.active_contexts.remove(debug_context)
                print("🐛 Debug mode: OFF")
            else:
                backend.active_contexts.add(debug_context)
                print("🐛 Debug mode: ON")
                print(f"   Action: {context.triggered_by}")
                print(f"   Registry: {len(self.actions)} actions")
                print(f"   Backend: {type(backend).__name__}")
        except ActionError as e:
            print(f"❌ {e}")
    
    def _register_dynamic_action(self, context: ActionContext):
        """Register a new action dynamically."""
        if len(context.args) < 2:
            print("❌ Usage: /register <name> <description>")
            return
        
        name = context.args[0]
        description = " ".join(context.args[1:])
        
        if name in self.actions:
            print(f"❌ Action '{name}' already exists")
            return
        
        # Create a simple handler (synchronous)
        def dynamic_handler(ctx):
            print(f"🎯 Dynamic action '{name}' executed!")
            print(f"   Description: {description}")
            print(f"   Triggered by: {ctx.triggered_by}")
            # Note: If you need async operations in dynamic handlers, 
            # handle them internally with asyncio.run() or similar
        
        try:
            # Register as command-only action
            self.register_action(
                name=name,
                command=f"/{name}",
                description=description,
                category="Dynamic",
                handler=dynamic_handler,
                command_usage=f"/{name} - {description}"
            )
            
            print(f"✅ Dynamic action '{name}' registered!")
            print(f"   Use /{name} to execute it")
            
        except Exception as e:
            print(f"❌ Failed to register action: {e}")


async def main():
    """Run the advanced example REPL with late backend binding."""
    print("🚀 REPL Toolkit v1.0 - Advanced Usage Example")
    print("=" * 60)
    print()
    print("This example demonstrates advanced features with late backend binding:")
    print("- Conversation tracking and history")
    print("- Search functionality")
    print("- Export capabilities")
    print("- Dynamic action registration")
    print("- Context-aware behavior")
    print("- Resource context support")
    print()
    print("Available Commands:")
    print("  /help              - Show all actions")
    print("  /stats             - Session statistics")
    print("  /history [count]   - Show conversation history")
    print("  /search <query>    - Search conversation")
    print("  /export [file]     - Export to JSON")
    print("  /clear-history     - Clear history (destructive)")
    print("  /register <name> <desc> - Register new action")
    print()
    print("Keyboard Shortcuts:")
    print("  F1      - Help")
    print("  F3      - Session statistics")
    print("  F12     - Toggle debug mode")
    print("  Ctrl+E  - Export conversation")
    print()
    print("Try sending some messages, then use /stats or F3!")
    print("=" * 60)
    
    # Create action registry (without backend initially)
    action_registry = AdvancedActionRegistry()
    
    # Backend created and passed to run() - supports resource context pattern
    backend = AdvancedBackend()
    
    try:
        # Run the REPL with late backend binding
        await run_async_repl(
            backend=backend,
            action_registry=action_registry,
            prompt_string="Advanced: ",
            history_path=Path("/tmp/repl_toolkit_advanced_history.txt")
        )
    except KeyboardInterrupt:
        print("\n👋 Session ended!")
        
        # Show final stats
        stats = backend.get_stats()
        print(f"Final stats: {stats['messages']} messages in {stats['duration_seconds']:.1f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
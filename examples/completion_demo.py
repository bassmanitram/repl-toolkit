"""
Demonstration of ShellExpansionCompleter for environment variable and command expansion.

This example shows how to use the ShellExpansionCompleter with AsyncREPL to enable
inline expansion of environment variables (${VAR}) and shell commands ($(cmd)).

Usage:
    python examples/completion_demo.py

Try typing:
    - User is ${USER} <Tab>
    - Date is $(date) <Tab>
    - Path is ${PATH} <Tab>
    - Files: $(ls) <Tab>
    - /help <Tab> (command completion)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for running from examples/
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable debug output
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="ERROR")

from prompt_toolkit.completion import merge_completers

from repl_toolkit import ActionRegistry, AsyncREPL, PrefixCompleter, ShellExpansionCompleter


class DemoBackend:
    """Simple backend that echoes user input."""

    async def handle_input(self, user_input: str) -> bool:
        """Handle user input."""
        print(f"\nYou entered: {user_input}")
        print(f"Length: {len(user_input)} characters\n")
        return True


async def main():
    """Run the completion demo."""
    print("=" * 70)
    print("ShellExpansionCompleter Demo")
    print("=" * 70)
    print()
    print("This demo showcases environment variable and command expansion.")
    print()
    print("Try these patterns:")
    print("  ${VAR_NAME}  - Press Tab to expand environment variable")
    print("  $(command)   - Press Tab to execute command and insert output")
    print("  /command     - Press Tab to complete slash commands")
    print()
    print("Examples to try:")
    print("  1. Type: User is ${USER}")
    print("     Position cursor after ${USER}, press Tab")
    print()
    print("  2. Type: Date is $(date)")
    print("     Position cursor after $(date), press Tab")
    print()
    print("  3. Type: Working dir: $(pwd)")
    print("     Position cursor after $(pwd), press Tab")
    print()
    print("  4. Type: /he")
    print("     Press Tab to complete /help")
    print()
    print("Commands: /help, /exit, /quit")
    print("=" * 70)
    print()

    # Set a demo environment variable
    os.environ["DEMO_VAR"] = "Hello from environment!"
    print(f"Demo variable set: DEMO_VAR='{os.environ['DEMO_VAR']}'")
    print()

    # Create completers
    command_completer = PrefixCompleter(["/help", "/exit", "/quit", "/shortcuts"], ignore_case=True)

    env_command_completer = ShellExpansionCompleter(timeout=2.0)

    # Merge completers
    combined_completer = merge_completers(
        [command_completer, env_command_completer], deduplicate=True
    )

    # Create backend and registry
    backend = DemoBackend()
    registry = ActionRegistry()

    # Create REPL with combined completer
    repl = AsyncREPL(action_registry=registry, completer=combined_completer, prompt_string="demo> ")

    # Run the REPL
    await repl.run(backend)

    print("\nDemo finished!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except EOFError:
        print("\n\nDemo finished (EOF).")

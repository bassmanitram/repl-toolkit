"""
Demo of multi-line command completion with individual line selection.

Usage: python examples/multiline_completion_demo.py

Try:
    - $(ls) <Tab> → Select individual file or ALL files
    - $(git branch) <Tab> → Select one branch or ALL branches
    - $(ps aux | head -5) <Tab> → Select process or ALL
    - /help <Tab> → Command completion
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging to see errors from repl_toolkit
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable debug output
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="ERROR")

from prompt_toolkit.completion import merge_completers

from repl_toolkit import ActionRegistry, AsyncREPL, PrefixCompleter, ShellExpansionCompleter


class EchoBackend:
    async def handle_input(self, text: str) -> bool:
        print(f"\nYou selected: {text}")
        print(f"Lines: {len(text.splitlines())}\n")
        return True


async def main():
    print("=" * 70)
    print("Multi-line Command Completion Demo")
    print("=" * 70)
    print()
    print("Commands with multiple lines offer:")
    print("  1. ALL - Insert all lines")
    print("  2. Line 1, Line 2, etc. - Select individual lines")
    print()
    print("Try these:")
    print("  $(ls)            - Files in current directory")
    print("  $(ls -1 /)       - Root directory listing")
    print("  $(echo -e 'a\\nb\\nc')  - Three lines")
    print("  /help            - Command completion")
    print()
    print("Position cursor after ), press Tab, select option")
    print("=" * 70)
    print()

    completer = merge_completers(
        [
            PrefixCompleter(["/help", "/exit", "/quit", "/shortcuts"]),
            ShellExpansionCompleter(timeout=2.0, multiline_all=True),
        ]
    )

    repl = AsyncREPL(
        action_registry=ActionRegistry(), completer=completer, prompt_string="select> "
    )

    await repl.run(EchoBackend())


if __name__ == "__main__":
    asyncio.run(main())

"""
Quick demo of PathCompleter with repl-toolkit.

Usage: python examples/path_completion_demo.py

Try:
    - Type any path and Tab to see files
    - Type ~/  and Tab (expands home directory)
    - Combine with ${HOME}/ for variable expansion
    - Type /he and Tab for command completion
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging to see errors from repl_toolkit
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# Add parent directory to path for running from examples/
sys.path.insert(0, str(Path(__file__).parent.parent))

# Disable debug output
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="ERROR")

from prompt_toolkit.completion import PathCompleter, merge_completers

from repl_toolkit import ActionRegistry, AsyncREPL, PrefixCompleter, ShellExpansionCompleter


class EchoBackend:
    async def handle_input(self, text: str) -> bool:
        print(f"You entered: {text}")
        return True


async def main():
    print("Path Completion Demo - Type paths and press Tab\n")
    print("Try:")
    print("  - Type paths: /etc/ <Tab>")
    print("  - Expand home: ~/  <Tab>")
    print("  - Variables: ${HOME}/ <Tab>")
    print("  - Commands: /he <Tab>")
    print()

    completer = merge_completers(
        [
            PrefixCompleter(["/help", "/exit", "/quit", "/shortcuts"]),
            PathCompleter(expanduser=True),
            ShellExpansionCompleter(),
        ]
    )

    repl = AsyncREPL(action_registry=ActionRegistry(), completer=completer, prompt_string="path> ")

    await repl.run(EchoBackend())


if __name__ == "__main__":
    asyncio.run(main())

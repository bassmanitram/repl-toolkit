#!/usr/bin/env python3
"""
Basic usage example for repl_toolkit.

Shows how to create a simple interactive REPL with a custom backend.
"""

import asyncio
from repl_toolkit import AsyncREPL, run_headless_mode
from repl_toolkit.types import AsyncBackend, HeadlessBackend


class EchoBackend(AsyncBackend, HeadlessBackend):
    """Simple backend that echoes user input."""
    
    async def handle_input(self, user_input: str) -> bool:
        """Echo the user input back."""
        print(f"Echo: {user_input}")
        return True


async def run_interactive():
    """Run the interactive REPL."""
    print("Starting interactive REPL (use /exit to quit)...")
    backend = EchoBackend()
    repl = AsyncREPL(backend, prompt_string="Echo> ")
    await repl.run()


async def run_headless():
    """Run in headless mode."""
    print("Running in headless mode...")
    backend = EchoBackend()
    
    # Simulate some input
    import io
    input_stream = io.StringIO("Hello world\nHow are you?\n{{send}}\nGoodbye\n")
    
    success = await run_headless_mode(
        backend, 
        initial_message="Welcome!",
        input_stream=input_stream
    )
    
    print(f"Headless mode completed successfully: {success}")


async def main():
    """Main function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "headless":
        await run_headless()
    else:
        await run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
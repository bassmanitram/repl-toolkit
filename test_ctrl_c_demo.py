#!/usr/bin/env python3
"""
Demo script to manually test Ctrl-C cancellation.

Usage:
  python test_ctrl_c_demo.py

Then:
  1. Type a message and press Alt+Enter
  2. While "Thinking..." is displayed, press Ctrl-C
  3. Verify cancellation works and REPL continues
"""

import asyncio

from repl_toolkit import AsyncREPL


class SlowBackend:
    """Backend with a long-running operation."""

    async def handle_input(self, user_input: str) -> bool:
        print(f"\n🔄 Backend processing: '{user_input}'")
        print("   (This will take 30 seconds...)")

        try:
            await asyncio.sleep(30)
            print("✅ Backend completed successfully!")
            return True
        except asyncio.CancelledError:
            print("❌ Backend was cancelled!")
            raise


async def main():
    print("=" * 60)
    print("Ctrl-C Cancellation Test")
    print("=" * 60)
    print()
    print("Instructions:")
    print("  1. Type any message")
    print("  2. Press Alt+Enter to send")
    print("  3. While 'Thinking...' shows, press Ctrl-C")
    print("  4. Verify cancellation message appears")
    print("  5. Try sending another message to verify REPL still works")
    print()
    print("Alternative: Press Alt-C instead of Ctrl-C (also works)")
    print()
    print("=" * 60)
    print()

    backend = SlowBackend()
    repl = AsyncREPL()

    await repl.run(backend)

    print("\n✨ Demo complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Exited via Ctrl-C")

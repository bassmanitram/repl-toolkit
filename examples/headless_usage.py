#!/usr/bin/env python3
"""
Headless usage example for repl_toolkit.

This example demonstrates how to use the headless mode for automation,
batch processing, and testing scenarios.
"""

import asyncio
import sys
from pathlib import Path

# Add the repl_toolkit to path for the example
sys.path.insert(0, str(Path(__file__).parent.parent))

from repl_toolkit import Action, ActionContext, ActionRegistry, run_headless_mode


class BatchBackend:
    """Backend for batch processing with result accumulation."""

    def __init__(self):
        self.processed_items = []
        self.batch_count = 0

    async def handle_input(self, user_input: str) -> bool:
        """Process input in batch mode."""
        self.batch_count += 1

        # Simulate processing
        await asyncio.sleep(0.1)

        # Process each line
        lines = user_input.strip().split("\n")
        batch_results = []

        for line in lines:
            if line.strip():
                # Simple processing: uppercase and add timestamp
                processed = f"PROCESSED: {line.upper()}"
                batch_results.append(processed)
                self.processed_items.append(processed)

        print(f"Batch #{self.batch_count}: Processed {len(batch_results)} items")
        for result in batch_results:
            print(f"  {result}")

        return True


class HeadlessActionRegistry(ActionRegistry):
    """Action registry with headless-specific actions."""

    def __init__(self):
        super().__init__()
        self._register_headless_actions()

    def _register_headless_actions(self):
        """Register headless-specific actions."""

        # Show processing stats
        self.register_action(
            name="show_stats",
            command="/stats",
            description="Show processing statistics",
            category="Stats",
            handler=self._show_stats,
            command_usage="/stats - Show processing statistics",
        )

        # Show current buffer (headless-specific)
        self.register_action(
            name="show_buffer",
            command="/buffer",
            description="Show current buffer content",
            category="Debug",
            handler=self._show_buffer,
            command_usage="/buffer - Show current buffer content",
        )

        # Add timestamp to buffer
        self.register_action(
            name="add_timestamp",
            command="/timestamp",
            description="Add timestamp to buffer",
            category="Utility",
            handler=self._add_timestamp,
            command_usage="/timestamp - Add current timestamp to buffer",
        )

    def _show_stats(self, context: ActionContext):
        """Show processing statistics."""
        backend = context.backend
        if backend:
            print(f"Processing Statistics:")
            print(f"  Batches processed: {backend.batch_count}")
            print(f"  Total items: {len(backend.processed_items)}")

            if context.headless_mode:
                print(f"  Running in headless mode")
                if hasattr(context, "buffer") and context.buffer:
                    print(f"  Current buffer: {len(context.buffer)} characters")
        else:
            print("Backend not available")

    def _show_buffer(self, context: ActionContext):
        """Show current buffer content (headless mode only)."""
        if context.headless_mode and hasattr(context, "buffer"):
            if context.buffer:
                print(f"Current buffer ({len(context.buffer)} characters):")
                print("-" * 40)
                print(context.buffer)
                print("-" * 40)
            else:
                print("Buffer is empty")
        else:
            print("Buffer information only available in headless mode")

    def _add_timestamp(self, context: ActionContext):
        """Add timestamp to buffer (headless mode only)."""
        if context.headless_mode and hasattr(context, "headless_repl"):
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            context.headless_repl._add_to_buffer(f"[{timestamp}]")
            print(f"Added timestamp: {timestamp}")
        else:
            print("Timestamp can only be added in headless mode")


async def main():
    """Run headless mode example."""
    print("REPL Toolkit v1.0 - Headless Usage Example")
    print("=" * 50)
    print()
    print("This example demonstrates headless mode for batch processing.")
    print("Input is read from stdin line by line.")
    print()
    print("Usage patterns:")
    print("  - Content lines are accumulated in a buffer")
    print("  - Commands are processed immediately")
    print("  - /send triggers processing of accumulated content")
    print("  - EOF automatically sends remaining content")
    print()
    print("Available commands in headless mode:")
    print("  /help      - Show all available actions")
    print("  /stats     - Show processing statistics")
    print("  /buffer    - Show current buffer content")
    print("  /timestamp - Add timestamp to buffer")
    print("  /send      - Send buffer to backend for processing")
    print()
    print("Example input:")
    print("  Item 1")
    print("  Item 2")
    print("  /stats")
    print("  Item 3")
    print("  /send")
    print("  Item 4")
    print("  ^D (EOF)")
    print()
    print("Starting headless mode (reading from stdin)...")
    print("=" * 50)

    # Create backend and action registry
    backend = BatchBackend()
    action_registry = HeadlessActionRegistry()

    try:
        # Run headless mode
        success = await run_headless_mode(
            backend=backend,
            action_registry=action_registry,
            initial_message="Headless batch processing started",
        )

        # Show final results
        print("\n" + "=" * 50)
        print("Headless processing completed")
        print(f"Success: {success}")
        print(f"Total batches: {backend.batch_count}")
        print(f"Total items processed: {len(backend.processed_items)}")

        if backend.processed_items:
            print("\nAll processed items:")
            for i, item in enumerate(backend.processed_items, 1):
                print(f"  {i}. {item}")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\nHeadless processing interrupted")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


async def demo_with_sample_input():
    """Demo with predefined sample input."""
    print("REPL Toolkit v1.0 - Headless Demo with Sample Input")
    print("=" * 60)

    # Sample input data
    sample_input = """First item
Second item
/stats
Third item
/buffer
/send
Fourth item
Fifth item
/timestamp
Sixth item
"""

    print("Sample input:")
    print("-" * 30)
    print(sample_input)
    print("-" * 30)
    print()

    # Create backend and action registry
    backend = BatchBackend()
    action_registry = HeadlessActionRegistry()

    # Simulate stdin with sample input
    import io
    from unittest.mock import patch

    with patch("sys.stdin", io.StringIO(sample_input)):
        success = await run_headless_mode(
            backend=backend,
            action_registry=action_registry,
            initial_message="Demo started with sample input",
        )

    print(f"\nDemo completed. Success: {success}")
    return 0 if success else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run demo with sample input
        sys.exit(asyncio.run(demo_with_sample_input()))
    else:
        # Run normal headless mode (reads from stdin)
        sys.exit(asyncio.run(main()))

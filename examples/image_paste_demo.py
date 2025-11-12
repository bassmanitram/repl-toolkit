#!/usr/bin/env python3
"""
Demo of image paste support in repl-toolkit.

This example shows how to use the image paste feature to send images
from clipboard along with text messages to your backend.

Usage:
1. Copy an image to your clipboard (screenshot, file, etc.)
2. Run this script
3. Type a message
4. Press F6 or Ctrl+Shift+V (or type /paste-image) to add the image
5. Press Alt+Enter to send

The backend will receive both the text and image data.
"""

import asyncio
import base64

from repl_toolkit import AsyncREPL, ImageData


class ImageDemoBackend:
    """Demo backend that shows received images."""

    async def handle_input(
        self, user_input: str, images: dict[str, ImageData] | None = None
    ) -> bool:
        """Handle user input with optional images."""
        print("\n" + "=" * 60)
        print("BACKEND RECEIVED:")
        print("=" * 60)

        # Show the text with placeholders
        print(f"Text: {user_input}")

        # Show image details if present
        if images:
            print(f"\nImages: {len(images)}")
            for img_id, img_data in images.items():
                print(f"\n  {img_id}:")
                print(f"    - Format: {img_data.media_type}")
                print(f"    - Size: {len(img_data.data):,} bytes")
                print(f"    - Timestamp: {img_data.timestamp}")

                # Show first 100 bytes as base64 (preview)
                preview = base64.b64encode(img_data.data[:100]).decode()
                print(f"    - Data preview: {preview}...")

            # Example: How backend might parse placeholders
            print("\n  Parsing placeholders:")
            import re

            parts = re.split(r"({{image:\w+}})", user_input)
            for part in parts:
                if match := re.match(r"{{image:(\w+)}}", part):
                    img_id = match.group(1)
                    if img_id in images:
                        print(f"    - Found reference to {img_id}")
                elif part.strip():
                    print(f'    - Text: "{part}"')
        else:
            print("\nNo images")

        print("=" * 60 + "\n")
        return True


async def main():
    """Run the demo."""
    print("Image Paste Demo")
    print("=" * 60)
    print("Instructions:")
    print("  1. Copy an image to your clipboard")
    print("  2. Type your message")
    print("  3. Press F6 or Ctrl+Shift+V to paste the image")
    print("  4. Continue typing if desired")
    print("  5. Press Alt+Enter to send")
    print("\nCommands:")
    print("  /help      - Show available commands")
    print("  /shortcuts - Show keyboard shortcuts")
    print("  /exit      - Exit the demo")
    print("=" * 60 + "\n")

    # Create backend
    backend = ImageDemoBackend()

    # Create REPL with image paste enabled (default)
    repl = AsyncREPL(
        prompt_string="<b>Demo></b> ",
        enable_image_paste=True,  # This is the default
    )

    # Run the REPL
    await repl.run(backend)

    print("\nDemo finished!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

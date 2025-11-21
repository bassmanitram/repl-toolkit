#!/usr/bin/env python3
"""
Demo of image utility functions in repl-toolkit.

Shows how backends can easily parse and process images using
the provided utility functions.
"""

import asyncio
import base64
import logging

# Configure logging to see errors from repl_toolkit
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from repl_toolkit import (
    AsyncREPL,
    ImageData,
    iter_content_parts,
    parse_image_references,
    reconstruct_message,
)


class SimpleParsingBackend:
    """Example 1: Simple parsing approach."""

    async def handle_input(self, user_input: str, images=None) -> bool:
        print("\n" + "=" * 60)
        print("EXAMPLE 1: Simple Parsing")
        print("=" * 60)

        # Parse image references
        parsed = parse_image_references(user_input)

        print(f"Original text: {parsed.text}")
        print(f"Image IDs found: {parsed.image_ids}")

        # Access images by ID
        if images:
            for img_id in parsed.image_ids:
                img_data = images.get(img_id)
                if img_data:
                    print(f"  - {img_id}: {img_data.media_type}, {len(img_data.data)} bytes")

        return True


class IteratorBackend:
    """Example 2: Using content iterator."""

    async def handle_input(self, user_input: str, images=None) -> bool:
        print("\n" + "=" * 60)
        print("EXAMPLE 2: Iterator Approach")
        print("=" * 60)

        # Iterate over parts in order
        for content, image in iter_content_parts(user_input, images):
            if image:
                print(f"  [IMAGE: {image.media_type}, {len(image.data)} bytes]")
            elif content:
                print(f"  TEXT: {content}")

        return True


class MarkdownBackend:
    """Example 3: Convert to Markdown format."""

    async def handle_input(self, user_input: str, images=None) -> bool:
        print("\n" + "=" * 60)
        print("EXAMPLE 3: Convert to Markdown")
        print("=" * 60)

        def to_markdown(content: str, image: ImageData | None) -> str:
            if image:
                # Convert image to data URL
                b64 = base64.b64encode(image.data).decode()[:50]  # truncated for display
                return f"![image](data:{image.media_type};base64,{b64}...)"
            return content

        markdown = reconstruct_message(user_input, images, to_markdown)
        print(f"Markdown:\n{markdown}")

        return True


class APIBackend:
    """Example 4: Convert to API-specific structure."""

    async def handle_input(self, user_input: str, images=None) -> bool:
        print("\n" + "=" * 60)
        print("EXAMPLE 4: API Format Conversion")
        print("=" * 60)

        # Build API message structure
        message_parts = []

        for content, image in iter_content_parts(user_input, images):
            if image:
                # API wants separate image objects
                message_parts.append(
                    {
                        "type": "image",
                        "media_type": image.media_type,
                        "data": base64.b64encode(image.data).decode()[:50] + "...",
                    }
                )
            elif content:
                # Text content
                message_parts.append({"type": "text", "content": content})

        print("API structure:")
        for i, part in enumerate(message_parts, 1):
            print(f"  Part {i}: {part}")

        return True


class MultiImageBackend:
    """Example 5: Handle multiple images."""

    async def handle_input(self, user_input: str, images=None) -> bool:
        print("\n" + "=" * 60)
        print("EXAMPLE 5: Multiple Images")
        print("=" * 60)

        parsed = parse_image_references(user_input)

        print(f"Found {len(parsed.image_ids)} unique images")

        if images:
            for img_id in parsed.image_ids:
                img_data = images[img_id]
                print(f"\n{img_id}:")
                print(f"  Type: {img_data.media_type}")
                print(f"  Size: {len(img_data.data)} bytes")
                print(f"  Timestamp: {img_data.timestamp}")

        # Show structure
        print("\nMessage structure:")
        for i, (content, image_id) in enumerate(parsed.parts, 1):
            if image_id:
                print(f"  Part {i}: IMAGE({image_id})")
            else:
                print(f"  Part {i}: TEXT('{content}')")

        return True


async def demo():
    """Run the demo with simulated images."""
    print("=" * 60)
    print("IMAGE UTILITY FUNCTIONS DEMO")
    print("=" * 60)

    # Create test images
    png_data = b"\x89PNG\r\n\x1a\n" + b"PNG_IMAGE_DATA_HERE" * 10
    jpg_data = b"\xff\xd8\xff" + b"JPEG_IMAGE_DATA_HERE" * 10

    # Simulate what REPL would provide
    images = {
        "img_001": ImageData(png_data, "image/png", 1699876543.0),
        "img_002": ImageData(jpg_data, "image/jpeg", 1699876544.0),
    }

    user_input = "Compare {{image:img_001}} with {{image:img_002}} for analysis"

    # Run each example backend
    backends = [
        SimpleParsingBackend(),
        IteratorBackend(),
        MarkdownBackend(),
        APIBackend(),
        MultiImageBackend(),
    ]

    for backend in backends:
        await backend.handle_input(user_input, images)
        await asyncio.sleep(0.1)  # Small delay for readability

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. parse_image_references() - Extract image IDs and structure")
    print("2. iter_content_parts() - Iterate over text and images in order")
    print("3. reconstruct_message() - Transform to any format with a formatter")
    print("4. All functions handle edge cases (no images, missing images, etc.)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())

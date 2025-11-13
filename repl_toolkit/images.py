"""Image handling support for repl_toolkit."""

import re
import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterator, Optional, Tuple


@dataclass
class ImageData:
    """
    Represents image data from clipboard.

    Attributes:
        data: Raw image bytes
        media_type: MIME type (e.g., "image/png", "image/jpeg")
        timestamp: When the image was captured
    """

    data: bytes
    media_type: str
    timestamp: float


@dataclass
class ParsedContent:
    """
    Result of parsing text with image placeholders.

    Attributes:
        text: Original text with placeholders
        parts: List of (content, image_id) tuples where image_id is None for text
        image_ids: Set of unique image IDs referenced
    """

    text: str
    parts: list[Tuple[str, Optional[str]]]
    image_ids: set[str]


def detect_media_type(data: bytes) -> Optional[str]:
    """
    Detect image MIME type from magic bytes.

    Args:
        data: Image bytes to analyze

    Returns:
        MIME type string or None if not recognized
    """
    if not data or len(data) < 12:
        return None

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    elif data.startswith(b"RIFF") and b"WEBP" in data[8:12]:
        return "image/webp"
    elif data.startswith(b"BM"):
        return "image/bmp"
    else:
        return None


def parse_image_references(text: str) -> ParsedContent:
    """
    Parse text for image placeholder references.

    Splits text into parts, identifying image placeholders and extracting
    their IDs. Useful for backends that need to reconstruct messages with
    actual image content.

    Args:
        text: Text containing {{image:img_xxx}} placeholders

    Returns:
        ParsedContent with text split into parts and extracted image IDs

    Example:
        >>> result = parse_image_references("Look at {{image:img_001}} and {{image:img_002}}")
        >>> result.parts
        [('Look at ', None), ('', 'img_001'), (' and ', None), ('', 'img_002')]
        >>> result.image_ids
        {'img_001', 'img_002'}
    """
    pattern = r"\{\{image:(\w+)\}\}"
    parts: list[Tuple[str, Optional[str]]] = []
    image_ids: set[str] = set()
    last_end = 0

    for match in re.finditer(pattern, text):
        # Add text before this image reference
        if match.start() > last_end:
            parts.append((text[last_end : match.start()], None))

        # Add image reference
        image_id = match.group(1)
        parts.append(("", image_id))
        image_ids.add(image_id)

        last_end = match.end()

    # Add remaining text
    if last_end < len(text):
        parts.append((text[last_end:], None))

    return ParsedContent(text=text, parts=parts, image_ids=image_ids)


def iter_content_parts(
    text: str, images: Optional[Dict[str, ImageData]] = None
) -> Iterator[Tuple[str, Optional[ImageData]]]:
    """
    Iterate over content parts, yielding text and images in order.

    Convenience iterator that handles parsing and image lookup in one step.
    Yields alternating text segments and image data as they appear in the message.

    Args:
        text: Text containing image placeholders
        images: Dictionary mapping image IDs to ImageData

    Yields:
        Tuples of (content, image_data) where image_data is None for text segments

    Example:
        >>> for content, image in iter_content_parts(text, images):
        ...     if image:
        ...         process_image(image.data, image.media_type)
        ...     elif content:
        ...         process_text(content)
    """
    parsed = parse_image_references(text)
    images = images or {}

    for content, image_id in parsed.parts:
        if image_id:
            # This is an image reference
            image_data = images.get(image_id)
            yield ("", image_data)
        else:
            # This is text content
            yield (content, None)


def reconstruct_message(
    text: str,
    images: Optional[Dict[str, ImageData]],
    formatter: Callable[[str, Optional[ImageData]], str],
) -> str:
    """
    Reconstruct message by applying a formatter to each part.

    Useful for backends that need to convert placeholders into their
    application-specific format (e.g., Markdown, HTML, API structures).

    Args:
        text: Text containing image placeholders
        images: Dictionary mapping image IDs to ImageData
        formatter: Function that takes (content, image_data) and returns formatted string

    Returns:
        Reconstructed message string

    Example:
        >>> def to_markdown(content: str, image: Optional[ImageData]) -> str:
        ...     if image:
        ...         return f"![image](data:{image.media_type};base64,...)"
        ...     return content
        >>> result = reconstruct_message(text, images, to_markdown)
    """
    parts = []
    for content, image in iter_content_parts(text, images):
        parts.append(formatter(content, image))
    return "".join(parts)


def create_paste_image_action(enable_by_default: bool = True):
    """
    Create the default paste_image action.

    This is a factory function that creates the action so it can be
    conditionally registered based on pyclip availability.

    Args:
        enable_by_default: Whether the action should be enabled by default

    Returns:
        Action instance for paste_image functionality
    """
    from .actions import Action

    def paste_image_handler(context):
        """Paste image from clipboard into message."""
        try:
            import pyclip

            # Try to get image data first
            img_bytes = pyclip.paste(text=False)

            if img_bytes:
                # Detect media type
                media_type = detect_media_type(img_bytes)

                if media_type is not None:
                    # Valid image - add to buffer and insert placeholder
                    if not hasattr(context, "repl") or context.repl is None:
                        context.printer("Image paste not available in this context")
                        return

                    image_id = context.repl.add_image(img_bytes, media_type)

                    # Insert placeholder into prompt_toolkit buffer with space before
                    if hasattr(context, "buffer") and context.buffer is not None:
                        placeholder = f" {{{{image:{image_id}}}}}"
                        context.buffer.insert_text(placeholder)
                    return

            # Not an image or no binary data - try text paste instead
            text_data = pyclip.paste(text=True)
            if text_data:
                if hasattr(context, "buffer") and context.buffer is not None:
                    context.buffer.insert_text(text_data)
            else:
                context.printer("No content in clipboard")

        except ImportError:
            context.printer("Image paste requires 'pyclip' package: pip install pyclip")
        except Exception as e:
            context.printer(f"Failed to paste: {e}")

    return Action(
        name="paste_image",
        description="Paste image or text from clipboard",
        category="Input",
        handler=paste_image_handler,
        command="/paste-image",
        command_usage="/paste-image - Paste image or text from clipboard",
        keys="f6",
        keys_description="Paste image or text from clipboard",
        enabled=enable_by_default,
    )

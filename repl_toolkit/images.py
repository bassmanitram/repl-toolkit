"""Image handling support for repl_toolkit."""

import time
from dataclasses import dataclass
from typing import Optional


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

            img_bytes = pyclip.paste(text=False)

            if not img_bytes:
                context.printer("No image in clipboard")
                return

            # Detect media type
            media_type = detect_media_type(img_bytes)

            if media_type is None:
                context.printer("Clipboard content is not a valid image format")
                return

            # Add to REPL's image buffer
            if not hasattr(context, "repl") or context.repl is None:
                context.printer("Image paste not available in this context")
                return

            image_id = context.repl.add_image(img_bytes, media_type)

            # Insert placeholder into prompt_toolkit buffer
            if hasattr(context, "buffer") and context.buffer is not None:
                placeholder = f"{{{{image:{image_id}}}}}"
                context.buffer.insert_text(placeholder)

            context.printer(f"✓ Image {image_id} added ({media_type})")

        except ImportError:
            context.printer("Image paste requires 'pyclip' package: pip install pyclip")
        except Exception as e:
            context.printer(f"Failed to paste image: {e}")

    return Action(
        name="paste_image",
        description="Paste image from clipboard into message",
        category="Input",
        handler=paste_image_handler,
        command="/paste-image",
        command_usage="/paste-image - Paste image from clipboard",
        keys="f6",
        keys_description="Paste image from clipboard",
        enabled=enable_by_default,
    )

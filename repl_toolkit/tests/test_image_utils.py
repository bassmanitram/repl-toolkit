"""Tests for image utility functions."""

import time

from repl_toolkit import (
    ImageData,
    ParsedContent,
    iter_content_parts,
    parse_image_references,
    reconstruct_message,
)


class TestParseImageReferences:
    """Test parse_image_references utility."""

    def test_no_images(self):
        """Test parsing text without image references."""
        result = parse_image_references("Just plain text")

        assert result.text == "Just plain text"
        assert result.parts == [("Just plain text", None)]
        assert result.image_ids == set()

    def test_single_image(self):
        """Test parsing text with one image."""
        result = parse_image_references("Look at {{image:img_001}}")

        assert result.text == "Look at {{image:img_001}}"
        assert result.parts == [("Look at ", None), ("", "img_001")]
        assert result.image_ids == {"img_001"}

    def test_multiple_images(self):
        """Test parsing text with multiple images."""
        text = "First {{image:img_001}} and second {{image:img_002}}"
        result = parse_image_references(text)

        assert result.parts == [
            ("First ", None),
            ("", "img_001"),
            (" and second ", None),
            ("", "img_002"),
        ]
        assert result.image_ids == {"img_001", "img_002"}

    def test_image_at_start(self):
        """Test image reference at start of text."""
        result = parse_image_references("{{image:img_001}} at start")

        assert result.parts == [("", "img_001"), (" at start", None)]
        assert result.image_ids == {"img_001"}

    def test_image_at_end(self):
        """Test image reference at end of text."""
        result = parse_image_references("At end {{image:img_001}}")

        assert result.parts == [("At end ", None), ("", "img_001")]
        assert result.image_ids == {"img_001"}

    def test_only_image(self):
        """Test text with only image reference."""
        result = parse_image_references("{{image:img_001}}")

        assert result.parts == [("", "img_001")]
        assert result.image_ids == {"img_001"}

    def test_consecutive_images(self):
        """Test consecutive image references."""
        result = parse_image_references("{{image:img_001}}{{image:img_002}}")

        assert result.parts == [("", "img_001"), ("", "img_002")]
        assert result.image_ids == {"img_001", "img_002"}

    def test_duplicate_image_ids(self):
        """Test same image referenced multiple times."""
        text = "{{image:img_001}} and again {{image:img_001}}"
        result = parse_image_references(text)

        assert len(result.parts) == 3
        assert result.image_ids == {"img_001"}  # Set contains unique IDs

    def test_empty_text(self):
        """Test empty string."""
        result = parse_image_references("")

        assert result.text == ""
        assert result.parts == []
        assert result.image_ids == set()

    def test_malformed_references(self):
        """Test that malformed references are not parsed."""
        result = parse_image_references("{{image:}} and {image:img_001} and {{img_001}}")

        # None should be parsed as valid image references
        assert result.image_ids == set()
        assert len(result.parts) == 1
        assert result.parts[0][1] is None  # All treated as text


class TestIterContentParts:
    """Test iter_content_parts utility."""

    def test_text_only(self):
        """Test iteration over text without images."""
        parts = list(iter_content_parts("Hello world"))

        assert len(parts) == 1
        assert parts[0] == ("Hello world", None)

    def test_with_images(self):
        """Test iteration with image data."""
        img_data = ImageData(b"data", "image/png", time.time())
        images = {"img_001": img_data}

        text = "Before {{image:img_001}} after"
        parts = list(iter_content_parts(text, images))

        assert len(parts) == 3
        assert parts[0] == ("Before ", None)
        assert parts[1] == ("", img_data)
        assert parts[2] == (" after", None)

    def test_missing_image_data(self):
        """Test iteration when referenced image is missing."""
        text = "Image {{image:img_001}} here"
        parts = list(iter_content_parts(text, images=None))

        # Should yield None for missing image
        assert len(parts) == 3
        assert parts[0] == ("Image ", None)
        assert parts[1] == ("", None)  # Image ID not found
        assert parts[2] == (" here", None)

    def test_multiple_images(self):
        """Test iteration with multiple images."""
        img1 = ImageData(b"data1", "image/png", time.time())
        img2 = ImageData(b"data2", "image/jpeg", time.time())
        images = {"img_001": img1, "img_002": img2}

        text = "{{image:img_001}} and {{image:img_002}}"
        parts = list(iter_content_parts(text, images))

        assert len(parts) == 3
        assert parts[0] == ("", img1)
        assert parts[1] == (" and ", None)
        assert parts[2] == ("", img2)

    def test_empty_text(self):
        """Test iteration over empty string."""
        parts = list(iter_content_parts(""))
        assert parts == []

    def test_only_image(self):
        """Test iteration with only image reference."""
        img_data = ImageData(b"data", "image/png", time.time())
        images = {"img_001": img_data}

        parts = list(iter_content_parts("{{image:img_001}}", images))

        assert len(parts) == 1
        assert parts[0] == ("", img_data)


class TestReconstructMessage:
    """Test reconstruct_message utility."""

    def test_text_only(self):
        """Test reconstruction of text without images."""

        def formatter(content, image):
            if image:
                return "[IMAGE]"
            return content

        result = reconstruct_message("Hello world", None, formatter)
        assert result == "Hello world"

    def test_with_image_to_text(self):
        """Test reconstruction replacing images with text."""
        img_data = ImageData(b"data", "image/png", time.time())
        images = {"img_001": img_data}

        def formatter(content, image):
            if image:
                return f"[{image.media_type}]"
            return content

        text = "Look at {{image:img_001}} this"
        result = reconstruct_message(text, images, formatter)

        assert result == "Look at [image/png] this"

    def test_with_image_to_markdown(self):
        """Test reconstruction converting to Markdown."""
        img_data = ImageData(b"data", "image/png", time.time())
        images = {"img_001": img_data}

        def to_markdown(content, image):
            if image:
                return f"![image](data:{image.media_type};base64,<DATA>)"
            return content

        text = "{{image:img_001}}"
        result = reconstruct_message(text, images, to_markdown)

        assert result == "![image](data:image/png;base64,<DATA>)"

    def test_multiple_images(self):
        """Test reconstruction with multiple images."""
        img1 = ImageData(b"data1", "image/png", time.time())
        img2 = ImageData(b"data2", "image/jpeg", time.time())
        images = {"img_001": img1, "img_002": img2}

        def formatter(content, image):
            if image:
                return f"[{image.media_type}]"
            return content

        text = "First {{image:img_001}} second {{image:img_002}}"
        result = reconstruct_message(text, images, formatter)

        assert result == "First [image/png] second [image/jpeg]"

    def test_missing_image(self):
        """Test reconstruction when image is missing."""

        def formatter(content, image):
            if image:
                return "[IMAGE]"
            elif image is None and not content:
                return "[MISSING]"
            return content

        text = "Image {{image:img_001}} here"
        result = reconstruct_message(text, images=None, formatter=formatter)

        assert result == "Image [MISSING] here"

    def test_complex_formatting(self):
        """Test reconstruction with complex formatter."""
        img_data = ImageData(b"PNG_DATA", "image/png", time.time())
        images = {"img_001": img_data}

        def complex_formatter(content, image):
            if image:
                size = len(image.data)
                return f"<img type='{image.media_type}' size={size} />"
            return content.upper()  # Transform text too

        text = "Check {{image:img_001}} out"
        result = reconstruct_message(text, images, complex_formatter)

        assert result == "CHECK <img type='image/png' size=8 /> OUT"


class TestParsedContentDataclass:
    """Test ParsedContent dataclass."""

    def test_dataclass_creation(self):
        """Test creating ParsedContent instance."""
        parts = [("text", None), ("", "img_001")]
        image_ids = {"img_001"}

        parsed = ParsedContent(text="original", parts=parts, image_ids=image_ids)

        assert parsed.text == "original"
        assert parsed.parts == parts
        assert parsed.image_ids == image_ids

    def test_dataclass_immutability(self):
        """Test that ParsedContent fields can be accessed."""
        parsed = ParsedContent(text="test", parts=[], image_ids=set())

        # Should be able to access all fields
        assert hasattr(parsed, "text")
        assert hasattr(parsed, "parts")
        assert hasattr(parsed, "image_ids")


class TestIntegrationScenarios:
    """Test realistic usage scenarios."""

    def test_backend_workflow(self):
        """Test typical backend parsing workflow."""
        # Simulate what backend receives
        user_text = "Analysis of {{image:img_001}} shows interesting patterns"
        img_data = ImageData(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png", time.time())
        images = {"img_001": img_data}

        # Parse references
        parsed = parse_image_references(user_text)
        assert parsed.image_ids == {"img_001"}

        # Process each part
        parts = list(iter_content_parts(user_text, images))
        text_parts = [p[0] for p in parts if p[1] is None]
        image_parts = [p[1] for p in parts if p[1] is not None]

        assert len(text_parts) == 2
        assert len(image_parts) == 1
        assert image_parts[0].media_type == "image/png"

    def test_conversion_to_api_format(self):
        """Test converting to API-specific format."""
        import base64

        img_data = ImageData(b"IMAGE_BYTES", "image/png", time.time())
        images = {"img_001": img_data}

        def to_api_format(content, image):
            if image:
                encoded = base64.b64encode(image.data).decode()
                return f"[API_IMAGE:{image.media_type}:{encoded}]"
            return content

        text = "See {{image:img_001}}"
        result = reconstruct_message(text, images, to_api_format)

        assert "API_IMAGE:image/png:" in result
        assert base64.b64encode(b"IMAGE_BYTES").decode() in result

    def test_multiline_with_images(self):
        """Test multiline text with images."""
        text = """First line
Image: {{image:img_001}}
Third line with {{image:img_002}}
Last line"""

        img1 = ImageData(b"data1", "image/png", time.time())
        img2 = ImageData(b"data2", "image/jpeg", time.time())
        images = {"img_001": img1, "img_002": img2}

        parsed = parse_image_references(text)
        assert parsed.image_ids == {"img_001", "img_002"}

        # Verify structure preserved
        parts = list(iter_content_parts(text, images))
        full_text = "".join(p[0] if p[1] is None else f"[{p[1].media_type}]" for p in parts)

        assert "First line" in full_text
        assert "[image/png]" in full_text
        assert "[image/jpeg]" in full_text
        assert "Last line" in full_text

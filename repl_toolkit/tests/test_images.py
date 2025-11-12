"""Tests for image handling support in repl_toolkit."""

import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from repl_toolkit import AsyncREPL, ImageData, detect_media_type
from repl_toolkit.actions import ActionContext, ActionRegistry
from repl_toolkit.images import create_paste_image_action


class TestDetectMediaType:
    """Test image media type detection."""

    def test_detect_png(self):
        """Test PNG detection."""
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
        assert detect_media_type(png_header) == "image/png"

    def test_detect_jpeg(self):
        """Test JPEG detection."""
        jpeg_header = b"\xff\xd8\xff" + b"\x00" * 10
        assert detect_media_type(jpeg_header) == "image/jpeg"

    def test_detect_gif87(self):
        """Test GIF87a detection."""
        gif_header = b"GIF87a" + b"\x00" * 10
        assert detect_media_type(gif_header) == "image/gif"

    def test_detect_gif89(self):
        """Test GIF89a detection."""
        gif_header = b"GIF89a" + b"\x00" * 10
        assert detect_media_type(gif_header) == "image/gif"

    def test_detect_webp(self):
        """Test WebP detection."""
        webp_header = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 10
        assert detect_media_type(webp_header) == "image/webp"

    def test_detect_bmp(self):
        """Test BMP detection."""
        bmp_header = b"BM" + b"\x00" * 10
        assert detect_media_type(bmp_header) == "image/bmp"

    def test_detect_empty_data(self):
        """Test with empty data."""
        assert detect_media_type(b"") is None

    def test_detect_short_data(self):
        """Test with data too short."""
        assert detect_media_type(b"\x00" * 5) is None

    def test_detect_unknown_format(self):
        """Test with unknown format."""
        unknown_data = b"UNKNOWN" + b"\x00" * 10
        assert detect_media_type(unknown_data) is None


class TestImageData:
    """Test ImageData dataclass."""

    def test_image_data_creation(self):
        """Test creating ImageData instance."""
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        timestamp = time.time()

        img_data = ImageData(data=data, media_type="image/png", timestamp=timestamp)

        assert img_data.data == data
        assert img_data.media_type == "image/png"
        assert img_data.timestamp == timestamp


class TestAsyncREPLImageSupport:
    """Test AsyncREPL image buffer management."""

    def test_repl_with_image_support(self, mock_terminal_for_repl):
        """Test REPL initialization with image support."""
        repl = AsyncREPL(enable_image_paste=True)

        assert hasattr(repl, "_image_buffer")
        assert hasattr(repl, "_image_counter")
        assert repl._image_buffer == {}
        assert repl._image_counter == 0

    def test_repl_without_image_support(self, mock_terminal_for_repl):
        """Test REPL initialization without image support."""
        repl = AsyncREPL(enable_image_paste=False)

        # Should still have the infrastructure
        assert hasattr(repl, "_image_buffer")
        assert hasattr(repl, "_image_counter")

    def test_add_image(self, mock_terminal_for_repl):
        """Test adding image to buffer."""
        repl = AsyncREPL()

        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image_id = repl.add_image(img_bytes, "image/png")

        assert image_id == "img_001"
        assert image_id in repl._image_buffer
        assert repl._image_buffer[image_id].data == img_bytes
        assert repl._image_buffer[image_id].media_type == "image/png"

    def test_add_multiple_images(self, mock_terminal_for_repl):
        """Test adding multiple images."""
        repl = AsyncREPL()

        img1 = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        img2 = b"\xff\xd8\xff" + b"\x00" * 50

        id1 = repl.add_image(img1, "image/png")
        id2 = repl.add_image(img2, "image/jpeg")

        assert id1 == "img_001"
        assert id2 == "img_002"
        assert len(repl._image_buffer) == 2

    def test_clear_images(self, mock_terminal_for_repl):
        """Test clearing image buffer."""
        repl = AsyncREPL()

        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        repl.add_image(img_bytes, "image/png")
        repl.add_image(img_bytes, "image/png")

        assert len(repl._image_buffer) == 2

        repl.clear_images()

        assert len(repl._image_buffer) == 0

    def test_get_images(self, mock_terminal_for_repl):
        """Test getting image buffer copy."""
        repl = AsyncREPL()

        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image_id = repl.add_image(img_bytes, "image/png")

        images = repl.get_images()

        assert image_id in images
        assert images[image_id].data == img_bytes

        # Should be a copy
        images.clear()
        assert len(repl._image_buffer) == 1


class TestPasteImageAction:
    """Test paste_image action."""

    def test_create_paste_image_action(self):
        """Test creating paste_image action."""
        action = create_paste_image_action()

        assert action.name == "paste_image"
        assert action.command == "/paste-image"
        assert action.keys == ["f6", "c-s-v"]
        assert action.handler is not None

    def test_paste_image_action_registered(self, mock_terminal_for_repl):
        """Test that paste_image action is registered by default."""
        repl = AsyncREPL(enable_image_paste=True)

        assert repl.action_registry.validate_action("paste_image")
        assert "/paste-image" in repl.action_registry.command_map
        assert "f6" in repl.action_registry.key_map

    def test_paste_image_action_not_registered(self, mock_terminal_for_repl):
        """Test that paste_image action is not registered when disabled."""
        repl = AsyncREPL(enable_image_paste=False)

        assert not repl.action_registry.validate_action("paste_image")

    @patch("pyclip.paste")
    def test_paste_image_success(self, mock_paste, mock_terminal_for_repl):
        """Test successful image paste."""
        repl = AsyncREPL(enable_image_paste=True)

        # Mock clipboard with PNG data
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mock_paste.return_value = png_data

        # Create mock buffer
        mock_buffer = Mock()
        mock_buffer.insert_text = Mock()

        # Create context
        context = ActionContext(
            registry=repl.action_registry, repl=repl, buffer=mock_buffer, triggered_by="shortcut"
        )

        # Execute action
        repl.action_registry.execute_action("paste_image", context)

        # Verify image was added
        assert len(repl._image_buffer) == 1
        assert "img_001" in repl._image_buffer

        # Verify placeholder was inserted
        mock_buffer.insert_text.assert_called_once_with(" {{image:img_001}}")

    @patch("pyclip.paste")
    def test_paste_text_fallback(self, mock_paste, mock_terminal_for_repl):
        """Test paste falls back to text when clipboard has text."""
        repl = AsyncREPL(enable_image_paste=True)

        # Mock clipboard: no binary image, but has text
        def paste_side_effect(text=True):
            if text:
                return "Hello from clipboard"
            return None  # No binary data

        mock_paste.side_effect = paste_side_effect

        mock_buffer = Mock()
        mock_buffer.insert_text = Mock()

        context = ActionContext(
            registry=repl.action_registry, repl=repl, buffer=mock_buffer, triggered_by="shortcut"
        )

        repl.action_registry.execute_action("paste_image", context)

        # No image should be added
        assert len(repl._image_buffer) == 0
        # Text should be inserted
        mock_buffer.insert_text.assert_called_once_with("Hello from clipboard")

    @patch("pyclip.paste")
    def test_paste_invalid_image_falls_back_to_text(self, mock_paste, mock_terminal_for_repl):
        """Test paste falls back to text when binary data is not a valid image."""
        repl = AsyncREPL(enable_image_paste=True)

        # Mock clipboard: has binary data but not an image, also has text representation
        def paste_side_effect(text=True):
            if text:
                return "some text content"
            return b"not an image"  # Binary data but not valid image

        mock_paste.side_effect = paste_side_effect

        mock_buffer = Mock()
        mock_buffer.insert_text = Mock()

        context = ActionContext(
            registry=repl.action_registry, repl=repl, buffer=mock_buffer, triggered_by="shortcut"
        )

        repl.action_registry.execute_action("paste_image", context)

        # No image should be added
        assert len(repl._image_buffer) == 0
        # Text should be inserted
        mock_buffer.insert_text.assert_called_once_with("some text content")

    @patch("pyclip.paste")
    def test_paste_no_data(self, mock_paste, mock_terminal_for_repl):
        """Test paste when no content in clipboard."""
        repl = AsyncREPL(enable_image_paste=True)

        mock_paste.return_value = None

        mock_buffer = Mock()
        mock_buffer.insert_text = Mock()

        context = ActionContext(
            registry=repl.action_registry, repl=repl, buffer=mock_buffer, triggered_by="shortcut"
        )

        repl.action_registry.execute_action("paste_image", context)

        # Nothing should be added
        assert len(repl._image_buffer) == 0
        mock_buffer.insert_text.assert_not_called()

    def test_paste_image_no_repl_context(self, mock_terminal_for_repl):
        """Test paste without REPL context."""
        action = create_paste_image_action()

        # Context without repl
        context = ActionContext(registry=ActionRegistry(), triggered_by="test")

        # Should handle gracefully
        action.handler(context)
        # No error should be raised

    @patch("pyclip.paste")
    def test_paste_image_no_buffer(self, mock_paste, mock_terminal_for_repl):
        """Test paste without buffer context."""
        repl = AsyncREPL(enable_image_paste=True)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mock_paste.return_value = png_data

        # Context without buffer
        context = ActionContext(registry=repl.action_registry, repl=repl, triggered_by="command")

        repl.action_registry.execute_action("paste_image", context)

        # Image should still be added to buffer
        assert len(repl._image_buffer) == 1


class TestBackendImageSupport:
    """Test backend integration with images."""

    class MockBackendWithImages:
        """Mock backend that accepts images."""

        def __init__(self):
            self.inputs = []
            self.images_received = []

        async def handle_input(self, user_input: str, images=None) -> bool:
            self.inputs.append(user_input)
            self.images_received.append(images)
            return True

    class MockBackendWithoutImages:
        """Legacy mock backend without images parameter."""

        def __init__(self):
            self.inputs = []

        async def handle_input(self, user_input: str) -> bool:
            self.inputs.append(user_input)
            return True

    @pytest.mark.asyncio
    async def test_backend_receives_images_via_kwargs(self, mock_terminal_for_repl):
        """Test that backend receives images when calling handle_input with kwargs."""
        repl = AsyncREPL()
        backend = self.MockBackendWithImages()

        # Add an image
        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        repl.add_image(img_bytes, "image/png")

        # Prepare kwargs as _process_input would
        kwargs = {}
        if repl._image_buffer:
            kwargs["images"] = repl._image_buffer

        # Call backend directly (simulating what _process_input does)
        await backend.handle_input("test with {{image:img_001}}", **kwargs)

        # Backend should receive images
        assert len(backend.images_received) == 1
        assert backend.images_received[0] is not None
        assert "img_001" in backend.images_received[0]

    @pytest.mark.asyncio
    async def test_backend_no_images_kwargs(self, mock_terminal_for_repl):
        """Test that backend works without images kwargs."""
        repl = AsyncREPL()
        backend = self.MockBackendWithImages()

        # No images in buffer
        kwargs = {}
        if repl._image_buffer:
            kwargs["images"] = repl._image_buffer

        # Call backend directly
        await backend.handle_input("test without images", **kwargs)

        # Backend should not receive images kwargs
        assert len(backend.images_received) == 1
        # When no images, kwargs is not passed so default None is used
        assert backend.images_received[0] is None

    @pytest.mark.asyncio
    async def test_legacy_backend_compatibility(self, mock_terminal_for_repl):
        """Test backward compatibility with legacy backends."""
        repl = AsyncREPL()
        backend = self.MockBackendWithoutImages()

        # Call without images kwargs (legacy backends don't accept it)
        await backend.handle_input("test")
        assert len(backend.inputs) == 1

    def test_images_cleared_after_send(self, mock_terminal_for_repl):
        """Test that images buffer can be cleared."""
        repl = AsyncREPL()

        # Add images
        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        repl.add_image(img_bytes, "image/png")
        repl.add_image(img_bytes, "image/png")

        assert len(repl._image_buffer) == 2

        # Clear images (as _process_input does)
        repl._image_buffer.clear()

        # Images should be cleared
        assert len(repl._image_buffer) == 0

    @pytest.mark.asyncio
    async def test_image_workflow_integration(self, mock_terminal_for_repl):
        """Test complete workflow: add image, prepare kwargs, call backend, clear."""
        repl = AsyncREPL()
        backend = self.MockBackendWithImages()

        # Add image
        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image_id = repl.add_image(img_bytes, "image/png")

        assert len(repl._image_buffer) == 1
        assert image_id == "img_001"

        # Prepare kwargs (as _process_input does)
        kwargs = {}
        if repl._image_buffer:
            kwargs["images"] = repl._image_buffer

        # Call backend
        await backend.handle_input(f"test with {{{{image:{image_id}}}}}", **kwargs)

        # Verify backend received images
        assert len(backend.images_received) == 1
        assert "img_001" in backend.images_received[0]

        # Clear images (as _process_input does in finally block)
        repl._image_buffer.clear()

        # Verify cleared
        assert len(repl._image_buffer) == 0


class TestImagePlaceholders:
    """Test image placeholder handling."""

    def test_placeholder_format(self, mock_terminal_for_repl):
        """Test that placeholders use correct format."""
        repl = AsyncREPL()

        img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        image_id = repl.add_image(img_bytes, "image/png")

        # Expected placeholder format
        expected_placeholder = f"{{{{image:{image_id}}}}}"
        assert expected_placeholder == "{{image:img_001}}"

    @patch("pyclip.paste")
    def test_multiple_placeholders(self, mock_paste, mock_terminal_for_repl):
        """Test multiple image placeholders in same message."""
        repl = AsyncREPL(enable_image_paste=True)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mock_paste.return_value = png_data

        mock_buffer = Mock()
        placeholders = []
        mock_buffer.insert_text = lambda text: placeholders.append(text)

        context = ActionContext(
            registry=repl.action_registry, repl=repl, buffer=mock_buffer, triggered_by="shortcut"
        )

        # Paste two images
        repl.action_registry.execute_action("paste_image", context)
        repl.action_registry.execute_action("paste_image", context)

        assert len(placeholders) == 2
        assert placeholders[0] == " {{image:img_001}}"
        assert placeholders[1] == " {{image:img_002}}"
        assert len(repl._image_buffer) == 2

    def test_paste_image_key_bindings(self, mock_terminal_for_repl):
        """Test that paste_image has both F6 and Ctrl+Shift+V bindings."""
        repl = AsyncREPL(enable_image_paste=True)

        # Both keys should be registered
        assert "f6" in repl.action_registry.key_map
        assert "c-s-v" in repl.action_registry.key_map

        # Both should map to paste_image
        assert repl.action_registry.key_map["f6"] == "paste_image"
        assert repl.action_registry.key_map["c-s-v"] == "paste_image"

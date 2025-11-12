# Image Paste Support Implementation Summary

## Overview
Added clipboard image paste support to repl-toolkit, allowing users to paste images from clipboard directly into messages using F6 or `/paste-image` command.

## Design Decisions

### Option A: Placeholder + Lookup Dictionary (Selected)
- User input text contains placeholders: `{{image:img_001}}`
- Separate dictionary maps image IDs to ImageData
- Backend receives both text and images dictionary
- Backend has full control over final message formatting

### Action System Integration
- Image paste implemented as a regular Action (not built-in infrastructure)
- Users can disable, replace, or customize the action
- Follows existing action patterns for consistency
- Action handler accesses REPL via ActionContext

### Backward Compatibility
- AsyncBackend protocol updated with optional `images` parameter
- Only passes `images` kwarg when images are present
- Legacy backends without `images` parameter continue to work
- No breaking changes to existing code

## Files Created

### 1. `repl_toolkit/images.py`
New module containing:
- `ImageData` dataclass: Stores image bytes, media type, and timestamp
- `detect_media_type()`: Detects image format from magic bytes (PNG, JPEG, GIF, WebP, BMP)
- `create_paste_image_action()`: Factory function for the paste_image action

### 2. `repl_toolkit/tests/test_images.py`
Comprehensive test suite with 31 tests covering:
- Media type detection for all supported formats
- Image buffer management (add, clear, get)
- Paste action functionality with various scenarios
- Backend integration with and without images
- Placeholder format validation
- Error handling and edge cases

## Files Modified

### 1. `pyproject.toml`
- Added dependency: `pyclip>=0.7.0`

### 2. `repl_toolkit/ptypes.py`
- Updated `AsyncBackend` protocol to accept optional `images` parameter
- Added type imports for ImageData
- Updated docstrings

### 3. `repl_toolkit/actions/action.py`
- Added `repl` field to `ActionContext` dataclass
- Allows actions to access REPL instance for image buffer operations

### 4. `repl_toolkit/async_repl.py`
- Added image buffer management: `_image_buffer`, `_image_counter`
- Added `enable_image_paste` parameter to `__init__()`
- Added methods: `add_image()`, `clear_images()`, `get_images()`
- Registers paste_image action automatically if enabled
- Modified `_register_shortcut()` to pass `repl` in ActionContext
- Modified `_process_input()` to pass images to backend via kwargs
- Images cleared after send (in finally block)

### 5. `repl_toolkit/__init__.py`
- Exported `ImageData` and `detect_media_type`
- Updated module docstring with image paste example

## Key Features

### Image Paste Workflow
1. User presses F6 or types `/paste-image`
2. Action handler reads binary data from clipboard via pyclip
3. Image format detected from magic bytes
4. Image added to REPL's buffer with unique ID (img_001, img_002, etc.)
5. Placeholder `{{image:img_xxx}}` inserted at cursor position
6. User can continue typing around the placeholder
7. On send, backend receives both text and images dictionary
8. Images cleared after send (backend's responsibility to process)

### Supported Image Formats
- PNG
- JPEG
- GIF (87a and 89a)
- WebP
- BMP

### User Experience
- Raw placeholder visible in editor: `{{image:img_001}}`
- User can edit/delete placeholders freely
- Multiple images supported in single message
- Action can be disabled: `AsyncREPL(enable_image_paste=False)`
- Action can be customized or replaced by users

## Backend Integration Example

```python
class MyBackend:
    async def handle_input(self, user_input: str, images=None) -> bool:
        """Handle input with optional images."""
        if images:
            # Parse placeholders and reconstruct message
            for img_id, img_data in images.items():
                # img_data.data: raw bytes
                # img_data.media_type: MIME type
                # img_data.timestamp: when captured
                print(f"Found {img_id}: {img_data.media_type}")

        # Process message as needed
        return True
```

## Test Results
- All 207 tests pass (176 existing + 31 new)
- 100% backward compatibility maintained
- Coverage includes error handling, edge cases, and integration scenarios

## Usage Example

```python
from repl_toolkit import AsyncREPL, run_async_repl

class ImageAwareBackend:
    async def handle_input(self, user_input: str, images=None) -> bool:
        if images:
            print(f"Received {len(images)} images with message")
            for img_id, img_data in images.items():
                print(f"  - {img_id}: {img_data.media_type}, "
                      f"{len(img_data.data)} bytes")
        print(f"Text: {user_input}")
        return True

# Run with image support enabled (default)
await run_async_repl(backend=ImageAwareBackend())

# Or disable image paste
repl = AsyncREPL(enable_image_paste=False)
await repl.run(backend=ImageAwareBackend())
```

## Dependencies
- `pyclip>=0.7.0`: Cross-platform clipboard access with binary data support
  - Supports X11, Wayland, macOS, Windows
  - No breaking changes to existing functionality

## Future Enhancements (Not Implemented)
- Optional visual placeholder decoration in editor
- Image preview in terminal
- Additional image format support
- Image size/dimension validation
- Drag-and-drop support
- Multiple clipboard format support

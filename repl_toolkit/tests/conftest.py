"""
Pytest configuration and fixtures for repl-toolkit tests.
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
from prompt_toolkit.input import DummyInput
from prompt_toolkit.output import DummyOutput


@pytest.fixture(autouse=True)
def mock_terminal_for_tests(monkeypatch):
    """
    Automatically mock terminal I/O for all tests to enable cross-platform testing.

    This fixture ensures tests work on Windows, Linux, macOS, and in CI environments
    without requiring an actual terminal.
    """

    # Mock prompt_toolkit's create_output to return DummyOutput
    def mock_create_output(*args, **kwargs):
        return DummyOutput()

    # Mock prompt_toolkit's create_input to return DummyInput
    def mock_create_input(*args, **kwargs):
        return DummyInput()

    # Patch the output creation functions
    monkeypatch.setattr("prompt_toolkit.output.defaults.create_output", mock_create_output)

    # Patch the input creation functions
    monkeypatch.setattr("prompt_toolkit.input.defaults.create_input", mock_create_input)

    # Also patch platform-specific output classes to prevent initialization errors
    if sys.platform == "win32":
        # Mock Windows-specific components
        monkeypatch.setattr(
            "prompt_toolkit.output.windows10.Windows10_Output.__init__",
            lambda self, *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "prompt_toolkit.output.win32.Win32Output.__init__", lambda self, *args, **kwargs: None
        )


@pytest.fixture
def dummy_input():
    """Provide a DummyInput for tests that need to simulate input."""
    return DummyInput()


@pytest.fixture
def dummy_output():
    """Provide a DummyOutput for tests that need to capture output."""
    return DummyOutput()


@pytest.fixture
def mock_prompt_session(monkeypatch, dummy_input, dummy_output):
    """
    Mock PromptSession to work without a real terminal.

    This fixture is useful for tests that specifically need to control
    PromptSession behavior.
    """
    original_init = None

    try:
        from prompt_toolkit.shortcuts.prompt import PromptSession

        original_init = PromptSession.__init__
    except ImportError:
        pass

    def mock_init(self, *args, **kwargs):
        # Override input/output to use dummy versions
        kwargs["input"] = dummy_input
        kwargs["output"] = dummy_output
        if original_init:
            original_init(self, *args, **kwargs)

    if original_init:
        monkeypatch.setattr("prompt_toolkit.shortcuts.prompt.PromptSession.__init__", mock_init)

    return Mock()


@pytest.fixture
def mock_asyncio_event_loop():
    """Provide a mock event loop for testing async code."""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    # Cleanup
    try:
        loop.close()
    except Exception:
        pass

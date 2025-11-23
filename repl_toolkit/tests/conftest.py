"""
Pytest configuration and fixtures for repl-toolkit tests.
"""

import sys

import pytest
from prompt_toolkit.input import DummyInput
from prompt_toolkit.output import DummyOutput


@pytest.fixture
def mock_terminal_for_repl(monkeypatch):
    """
    Mock terminal I/O specifically for REPL tests that need it.

    This fixture should be explicitly requested by tests that create AsyncREPL or
    similar objects that require terminal access.

    Usage:
        def test_something(mock_terminal_for_repl):
            # Terminal is now mocked
            repl = AsyncREPL()
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

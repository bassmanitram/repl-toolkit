# Contributing to REPL Toolkit

Thank you for your interest in contributing to REPL Toolkit! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/bassmanitram/repl-toolkit.git
cd repl-toolkit
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev,test]"
```

4. Run tests to ensure everything works:
```bash
pytest
```

## Development Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature-name`
4. **Make** your changes
5. **Add tests** for new functionality
6. **Run tests**: `pytest`
7. **Commit** your changes: `git commit -am 'Add some feature'`
8. **Push** to your fork: `git push origin feature-name`
9. **Submit** a pull request

## Code Style

- Follow PEP 8 for Python code style
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public APIs
- Keep functions focused and small
- Use meaningful variable and function names

### Code Formatting

```bash
# Format code
black repl_toolkit/
isort repl_toolkit/

# Lint
flake8 repl_toolkit/

# Type check
mypy repl_toolkit/
```

## Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Test both success and failure cases
- Use descriptive test names that explain what is being tested
- Group related tests in classes

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest repl_toolkit/tests/test_actions.py

# Run with coverage
pytest --cov=repl_toolkit --cov-report=html

# Run with verbose output
pytest -v

# Run specific test categories
pytest repl_toolkit/tests/test_actions.py     # Action system tests
pytest repl_toolkit/tests/test_async_repl.py  # Interactive REPL tests
pytest repl_toolkit/tests/test_headless.py    # Headless mode tests
pytest repl_toolkit/tests/test_types.py       # Protocol compliance tests
```

### Test Structure

The test suite is organized into several categories:

- **Action System Tests** (`test_actions.py`): Test action registration, execution, and registry functionality
- **Interactive REPL Tests** (`test_async_repl.py`): Test the interactive interface and late backend binding
- **Headless Mode Tests** (`test_headless.py`): Test non-interactive stdin processing and buffer management
- **Protocol Tests** (`test_types.py`): Test protocol compliance and type safety

### Writing Tests

```python
import pytest
from repl_toolkit import ActionRegistry, Action, ActionContext

def test_action_registration():
    """Test that actions can be registered successfully."""
    registry = ActionRegistry()
    
    action = Action(
        name="test_action",
        description="Test action",
        category="Test",
        handler=lambda ctx: None,
        command="/test"
    )
    
    registry.register_action(action)
    assert registry.validate_action("test_action")

@pytest.mark.asyncio
async def test_headless_processing():
    """Test headless mode processing."""
    from repl_toolkit.headless_repl import HeadlessREPL
    from io import StringIO
    from unittest.mock import patch
    
    backend = MockBackend()
    repl = HeadlessREPL()
    
    stdin_input = "Line 1\nLine 2\n/send\n"
    
    with patch('sys.stdin', StringIO(stdin_input)):
        await repl._stdin_loop(backend)
    
    assert backend.inputs == ["Line 1\nLine 2"]
```

## Documentation

- Update README.md if you change public APIs
- Add docstrings to new functions and classes
- Include examples for complex functionality
- Update type hints in `ptypes.py` if adding new protocols
- Update ARCHITECTURE.md for significant architectural changes

### Documentation Standards

- Use clear, concise language
- Provide practical examples
- Document all parameters and return values
- Include usage patterns and common scenarios
- Avoid superlative language or unnecessary emphasis

## Architecture Guidelines

### Action System

When working with the action system:

- Actions should be focused and do one thing well
- Use appropriate categories for organization
- Provide both command and shortcut bindings when useful
- Handle errors gracefully and provide user feedback
- Support both interactive and headless modes when applicable

### Backend Integration

- Backends should implement the `AsyncBackend` protocol
- Support late backend binding patterns
- Handle resource contexts appropriately
- Provide clear error messages and return values

### Protocol Compliance

- New protocols should be runtime checkable
- Maintain backward compatibility when possible
- Document protocol requirements clearly
- Provide reference implementations

## Submitting Changes

### Pull Request Guidelines

- Include a clear description of what your changes do
- Reference any related issues
- Include tests for new functionality
- Ensure all tests pass
- Update documentation as needed
- Follow the existing code style

### Commit Messages

Use clear, descriptive commit messages:

- `feat: add support for custom key bindings`
- `fix: handle empty input correctly in headless mode`
- `docs: update installation instructions`
- `test: add tests for command registry`
- `refactor: simplify action lookup logic`

## Issue Reporting

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages or stack traces
- Minimal code example if applicable

## Feature Requests

Feature requests are welcome! Please:

- Search existing issues first
- Clearly describe the use case
- Explain why this feature would be useful
- Consider the impact on existing functionality
- Consider submitting a pull request

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Maintain a welcoming environment
- Follow the project's coding standards

For code of conduct enforcement, contact: martin.j.bartlett@gmail.com

## Development Tips

### Running Examples

Test your changes with the provided examples:

```bash
# Basic interactive example
python examples/basic_usage.py

# Advanced features example
python examples/advanced_usage.py

# Headless mode example
echo -e "Line 1\nLine 2\n/send" | python examples/headless_usage.py

# Headless demo with sample input
python examples/headless_usage.py --demo
```

### Debugging

- Use the trace logging to understand execution flow
- Test both interactive and headless modes
- Verify late backend binding scenarios
- Test error conditions and edge cases

### Performance Considerations

- Action lookup should be O(1)
- Avoid blocking operations in action handlers
- Use async patterns appropriately
- Consider memory usage for long-running sessions

## Questions?

If you have questions about contributing, feel free to:

- Open an issue for discussion
- Contact the maintainers at martin.j.bartlett@gmail.com
- Check existing documentation and examples

Thank you for contributing to REPL Toolkit!
# Contributing to REPL Toolkit

Thank you for your interest in contributing to REPL Toolkit! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/bassmanitram/repl-toolkit.git
cd repl-toolkit
```

2. Install in development mode:
```bash
pip install -e .[dev]
```

3. Run tests to ensure everything works:
```bash
pytest tests/
```

## Development Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature-name`
4. **Make** your changes
5. **Add tests** for new functionality
6. **Run tests**: `pytest tests/`
7. **Commit** your changes: `git commit -am 'Add some feature'`
8. **Push** to your fork: `git push origin feature-name`
9. **Submit** a pull request

## Code Style

- Follow PEP 8 for Python code style
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public APIs
- Keep functions focused and small
- Use meaningful variable and function names

## Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Test both success and failure cases
- Use descriptive test names that explain what is being tested
- Group related tests in classes

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_async_repl.py

# Run with coverage
pytest tests/ --cov=repl_toolkit

# Run with verbose output
pytest tests/ -v
```

## Documentation

- Update README.md if you change public APIs
- Add docstrings to new functions and classes
- Include examples for complex functionality
- Update type hints in `types.py` if adding new protocols

## Submitting Changes

### Pull Request Guidelines

- Include a clear description of what your changes do
- Reference any related issues
- Include tests for new functionality
- Ensure all tests pass
- Update documentation as needed

### Commit Messages

Use clear, descriptive commit messages:

- `feat: add support for custom key bindings`
- `fix: handle empty input correctly in headless mode`
- `docs: update installation instructions`
- `test: add tests for command registry`

## Issue Reporting

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages or stack traces

## Feature Requests

Feature requests are welcome! Please:

- Search existing issues first
- Clearly describe the use case
- Explain why this feature would be useful
- Consider submitting a pull request

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Maintain a welcoming environment

## Questions?

If you have questions about contributing, feel free to:

- Open an issue for discussion
- Contact the maintainers
- Check existing documentation

Thank you for contributing!
"""
Action system for repl_toolkit.

This module provides the action architecture that combines command
and keyboard shortcut handling into a single, extensible framework.

The action system allows developers to define actions that can be triggered
by either typed commands (e.g., /help) or keyboard shortcuts (e.g., F1),
providing a consistent and discoverable interface for users.
"""

from .action import (
    RESERVED_BACKEND_KWARGS,
    Action,
    ActionContext,
    ActionError,
    ActionExecutionError,
    ActionValidationError,
    SendToBackend,
    filter_reserved_backend_kwargs,
)
from .registry import ActionRegistry

__all__ = [
    # Core action types
    "Action",
    "ActionContext",
    "ActionError",
    "ActionValidationError",
    "ActionExecutionError",
    # Backend submission
    "SendToBackend",
    "RESERVED_BACKEND_KWARGS",
    "filter_reserved_backend_kwargs",
    # Registry
    "ActionRegistry",
]

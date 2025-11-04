"""
Prefix-based string completer.
"""

import re
from typing import Iterable, List, Optional

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class PrefixCompleter(Completer):
    """
    Completer for static string matching with optional prefix character.

    This completer matches strings from a predefined list. If a prefix is specified,
    it only completes after that prefix character at word boundaries, avoiding false
    positives in paths or other contexts.

    Args:
        words: List of words to complete
        prefix: Optional prefix character (e.g., '/', '@', '#')
                If provided, only completes after this prefix at word boundaries.
                If None, completes anywhere (standard word completion).
        ignore_case: Case-insensitive matching (default: True)

    Examples:
        >>> # Slash commands
        >>> completer = PrefixCompleter(['/help', '/exit', '/quit'], prefix='/')
        >>> # Or let it add the prefix
        >>> completer = PrefixCompleter(['help', 'exit', 'quit'], prefix='/')

        >>> # At-mentions
        >>> completer = PrefixCompleter(['alice', 'bob', 'charlie'], prefix='@')

        >>> # Hashtags
        >>> completer = PrefixCompleter(['python', 'coding', 'opensource'], prefix='#')

        >>> # SQL keywords (no prefix)
        >>> completer = PrefixCompleter(['SELECT', 'FROM', 'WHERE'], prefix=None)
    """

    def __init__(self, words: List[str], prefix: Optional[str] = None, ignore_case: bool = True):
        """Initialize the completer."""
        self.prefix = prefix
        self.ignore_case = ignore_case

        # Normalize words: ensure they have the prefix if specified
        if prefix:
            self.words = [word if word.startswith(prefix) else f"{prefix}{word}" for word in words]
        else:
            self.words = words

        # Build pattern for matching
        if prefix:
            # Match prefix at start of line or after whitespace/newline
            # This prevents matching "/" in paths like "path/to/file"
            escaped_prefix = re.escape(prefix)
            self.pattern = re.compile(rf"(?:^|[\s\n])({escaped_prefix}\S*)$")
        else:
            # No prefix - match word at cursor
            self.pattern = re.compile(r"(\S*)$")

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """
        Get completions for words matching the prefix pattern.

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects for matching words
        """
        # Get text before cursor
        text_before_cursor = document.text_before_cursor

        # Try to match the pattern
        match = self.pattern.search(text_before_cursor)

        if not match:
            return

        # Get the partial word being typed
        partial = match.group(1)

        # Find matching words
        for word in self.words:
            if self._matches(word, partial):
                # Calculate start position (negative, relative to cursor)
                start_pos = -len(partial)

                yield Completion(text=word, start_position=start_pos, display=word)

    def _matches(self, word: str, partial: str) -> bool:
        """
        Check if word matches partial string.

        Args:
            word: Complete word from word list
            partial: Partial string typed by user

        Returns:
            True if word matches partial
        """
        if self.ignore_case:
            return word.lower().startswith(partial.lower())
        else:
            return word.startswith(partial)

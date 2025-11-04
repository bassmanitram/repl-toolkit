#!/usr/bin/env python3
"""
Demo of repl_toolkit's auto-formatting utilities.

This example demonstrates the auto-format detection and printing utilities
that can automatically detect and apply HTML or ANSI formatting.
"""

from repl_toolkit import auto_format, create_auto_printer, detect_format_type, print_auto_formatted


def demo_detection():
    """Demonstrate format type detection."""
    print("\n" + "=" * 70)
    print("FORMAT TYPE DETECTION")
    print("=" * 70)

    test_cases = [
        ("<b>Bold HTML</b>", "html"),
        ("\x1b[1mBold ANSI\x1b[0m", "ansi"),
        ("Plain text", "plain"),
        ("a < b and c > d", "plain"),  # Not HTML
        ("<123>invalid</123>", "plain"),  # Invalid HTML
    ]

    for text, expected in test_cases:
        detected = detect_format_type(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} {repr(text[:30])} → {detected}")


def demo_auto_format():
    """Demonstrate auto-formatting."""
    print("\n" + "=" * 70)
    print("AUTO-FORMATTING")
    print("=" * 70)

    texts = [
        "<b>Bold HTML</b>",
        "\x1b[1mBold ANSI\x1b[0m",
        "Plain text",
    ]

    for text in texts:
        formatted = auto_format(text)
        print(f"\nInput: {repr(text)}")
        print(f"Type: {type(formatted).__name__}")
        print(f"Output: ", end="")
        print_auto_formatted(text)


def demo_print_auto_formatted():
    """Demonstrate auto-formatted printing."""
    print("\n" + "=" * 70)
    print("AUTO-FORMATTED PRINTING")
    print("=" * 70)

    print("\nHTML formatting:")
    print_auto_formatted("<b>Bold</b> <i>italic</i> <u>underline</u>")
    print_auto_formatted("<darkcyan>Cyan text</darkcyan>")
    print_auto_formatted("<b><darkcyan>🤖 Assistant:</darkcyan></b> Hello!")

    print("\nANSI formatting:")
    print_auto_formatted("\x1b[1mBold\x1b[0m \x1b[3mitalic\x1b[0m")
    print_auto_formatted("\x1b[36mCyan text\x1b[0m")

    print("\nPlain text:")
    print_auto_formatted("Just plain text, no formatting")


def demo_create_auto_printer():
    """Demonstrate creating a custom printer."""
    print("\n" + "=" * 70)
    print("CUSTOM AUTO-PRINTER")
    print("=" * 70)

    printer = create_auto_printer()

    print("\nUsing custom printer:")
    printer("<b>Prefix:</b> ", end="", flush=True)
    printer("Hello", end="", flush=True)
    printer(" world!\n")

    print("\nSimulating callback handler:")
    response_prefix = "<b><darkcyan>🤖 Bot:</darkcyan></b> "
    printer(response_prefix, end="", flush=True)
    printer("How can I help you today?")


def demo_callback_handler_integration():
    """Demonstrate integration with callback handlers."""
    print("\n" + "=" * 70)
    print("CALLBACK HANDLER INTEGRATION")
    print("=" * 70)

    # Simulate a callback handler that uses the printer
    class MockCallbackHandler:
        def __init__(self, response_prefix, printer):
            self.response_prefix = response_prefix
            self.printer = printer
            self.in_message = False

        def __call__(self, data="", messageStop=False):
            # Print prefix on first data
            if data and not self.in_message:
                self.in_message = True
                self.printer(self.response_prefix, end="", flush=True)

            # Print data
            if data:
                self.printer(data, end="", flush=True)

            # Reset on message stop
            if messageStop:
                self.in_message = False
                self.printer("\n")

    print("\nWith HTML prefix:")
    handler = MockCallbackHandler(
        response_prefix="<b><darkcyan>🤖 Assistant:</darkcyan></b> ", printer=create_auto_printer()
    )
    handler(data="Hello")
    handler(data=" there!")
    handler(messageStop=True)

    print("\nWith ANSI prefix:")
    handler = MockCallbackHandler(
        response_prefix="\x1b[1;36m🤖 Assistant:\x1b[0m ", printer=create_auto_printer()
    )
    handler(data="How")
    handler(data=" are")
    handler(data=" you?")
    handler(messageStop=True)

    print("\nWith plain prefix:")
    handler = MockCallbackHandler(response_prefix="Assistant: ", printer=create_auto_printer())
    handler(data="I'm")
    handler(data=" doing")
    handler(data=" great!")
    handler(messageStop=True)


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("REPL-TOOLKIT AUTO-FORMATTING UTILITIES DEMO")
    print("=" * 70)
    print("\nThis demo shows how to use repl_toolkit's formatting utilities")
    print("to automatically detect and apply HTML or ANSI formatting.")

    demo_detection()
    demo_auto_format()
    demo_print_auto_formatted()
    demo_create_auto_printer()
    demo_callback_handler_integration()

    print("\n" + "=" * 70)
    print("KEY FEATURES")
    print("=" * 70)
    print(
        """
1. Auto-detection: Automatically detects HTML, ANSI, or plain text
2. No false positives: Handles edge cases like 'a < b' correctly
3. Drop-in replacement: create_auto_printer() works like print()
4. Flexible: Works with any text format
5. Efficient: Pre-compiled regex patterns for performance

USAGE IN YOUR CODE:

    from repl_toolkit import create_auto_printer

    # Create a printer
    printer = create_auto_printer()

    # Use it like print()
    printer("<b>Bold text</b>")
    printer("\\x1b[1mANSI bold\\x1b[0m")
    printer("Plain text")

    # Inject into callback handlers
    handler = CallbackHandler(
        response_prefix="<b>Bot:</b> ",
        printer=create_auto_printer()
    )
    """
    )


if __name__ == "__main__":
    main()

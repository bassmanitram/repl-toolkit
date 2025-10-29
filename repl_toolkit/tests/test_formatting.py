"""
Tests for formatting utilities.
"""

import pytest
from prompt_toolkit.formatted_text import HTML, ANSI

from repl_toolkit.formatting import (
    detect_format_type,
    auto_format,
    print_auto_formatted,
    create_auto_printer,
)


class TestDetectFormatType:
    """Tests for detect_format_type function."""
    
    def test_detect_html(self):
        """Test HTML tag detection."""
        assert detect_format_type("<b>Bold</b>") == "html"
        assert detect_format_type("<darkcyan>Colored</darkcyan>") == "html"
        assert detect_format_type("<b><darkcyan>Nested</darkcyan></b>") == "html"
        assert detect_format_type("<i>Italic</i>") == "html"
        assert detect_format_type("<u>Underline</u>") == "html"
    
    def test_detect_html_uppercase(self):
        """Test HTML detection with uppercase tags."""
        assert detect_format_type("<B>Bold</B>") == "html"
        assert detect_format_type("<TAG>content</TAG>") == "html"
    
    def test_detect_html_self_closing(self):
        """Test HTML self-closing tag detection."""
        assert detect_format_type("<br/>") == "html"
        assert detect_format_type("<tag />") == "html"
    
    def test_detect_ansi(self):
        """Test ANSI escape code detection."""
        assert detect_format_type("\x1b[1mBold\x1b[0m") == "ansi"
        assert detect_format_type("\x1b[31mRed\x1b[0m") == "ansi"
        assert detect_format_type("\x1b[1;32mBold Green\x1b[0m") == "ansi"
        assert detect_format_type("\033[1mBold\033[0m") == "ansi"
    
    def test_detect_plain(self):
        """Test plain text detection."""
        assert detect_format_type("Plain text") == "plain"
        assert detect_format_type("No formatting here") == "plain"
        assert detect_format_type("") == "plain"
    
    def test_edge_cases(self):
        """Test edge cases that should not be detected as HTML."""
        # Comparison operators
        assert detect_format_type("a < b and c > d") == "plain"
        
        # Numbers in tag names (invalid HTML)
        assert detect_format_type("<123>content</123>") == "plain"
        
        # Hyphens in tag names (invalid HTML)
        assert detect_format_type("<a-b>content</a-b>") == "plain"
        
        # Underscore start (invalid HTML)
        assert detect_format_type("<_tag>content</_tag>") == "plain"
        
        # Angle brackets but not tags
        assert detect_format_type("Text with <angle brackets> but not tags") == "plain"
    
    def test_mixed_content(self):
        """Test that ANSI takes precedence over HTML."""
        # If text has both ANSI and HTML-like content, ANSI is detected first
        mixed = "\x1b[1m<b>Bold</b>\x1b[0m"
        assert detect_format_type(mixed) == "ansi"


class TestAutoFormat:
    """Tests for auto_format function."""
    
    def test_auto_format_html(self):
        """Test auto-formatting HTML text."""
        result = auto_format("<b>Bold</b>")
        assert isinstance(result, HTML)
        # HTML objects have the text accessible via their value attribute
        assert result.value == "<b>Bold</b>"
    
    def test_auto_format_ansi(self):
        """Test auto-formatting ANSI text."""
        result = auto_format("\x1b[1mBold\x1b[0m")
        assert isinstance(result, ANSI)
        # ANSI objects have the text accessible via their value attribute
        assert result.value == "\x1b[1mBold\x1b[0m"
    
    def test_auto_format_plain(self):
        """Test auto-formatting plain text."""
        result = auto_format("Plain text")
        assert isinstance(result, str)
        assert result == "Plain text"
    
    def test_auto_format_empty(self):
        """Test auto-formatting empty string."""
        result = auto_format("")
        assert isinstance(result, str)
        assert result == ""


class TestPrintAutoFormatted:
    """Tests for print_auto_formatted function."""
    
    def test_print_html(self):
        """Test printing HTML formatted text."""
        # Just verify it doesn't raise an exception
        # We can't easily test the actual output in pytest
        try:
            print_auto_formatted("<b>Bold</b>")
        except Exception as e:
            pytest.fail(f"print_auto_formatted raised {e}")
    
    def test_print_plain(self):
        """Test printing plain text."""
        try:
            print_auto_formatted("Plain text")
        except Exception as e:
            pytest.fail(f"print_auto_formatted raised {e}")
    
    def test_print_with_kwargs(self):
        """Test printing with additional kwargs."""
        try:
            print_auto_formatted("Test", end="", flush=True)
        except Exception as e:
            pytest.fail(f"print_auto_formatted raised {e}")


class TestCreateAutoPrinter:
    """Tests for create_auto_printer function."""
    
    def test_create_printer(self):
        """Test creating an auto printer."""
        printer = create_auto_printer()
        assert callable(printer)
    
    def test_printer_html(self):
        """Test printer with HTML text."""
        printer = create_auto_printer()
        try:
            printer("<b>Bold</b>")
        except Exception as e:
            pytest.fail(f"printer raised {e}")
    
    def test_printer_plain(self):
        """Test printer with plain text."""
        printer = create_auto_printer()
        try:
            printer("Plain text")
        except Exception as e:
            pytest.fail(f"printer raised {e}")
    
    def test_printer_with_kwargs(self):
        """Test printer with kwargs."""
        printer = create_auto_printer()
        try:
            printer("Test", end="", flush=True)
        except Exception as e:
            pytest.fail(f"printer raised {e}")
    
    def test_printer_multiple_calls(self):
        """Test printer with multiple calls."""
        printer = create_auto_printer()
        try:
            printer("<b>Prefix:</b> ", end="", flush=True)
            printer("Hello", end="", flush=True)
            printer(" world\n")
        except Exception as e:
            pytest.fail(f"printer raised {e}")


class TestIntegration:
    """Integration tests for formatting utilities."""
    
    def test_callback_handler_simulation(self):
        """Test simulating a callback handler usage."""
        # Simulate ConfigurableCallbackHandler behavior
        printer = create_auto_printer()
        response_prefix = "<b><darkcyan>🤖 Assistant:</darkcyan></b> "
        
        try:
            # Print prefix
            printer(response_prefix, end="", flush=True)
            
            # Print message parts
            printer("Hello", end="", flush=True)
            printer(" world", end="", flush=True)
            printer("\n")
        except Exception as e:
            pytest.fail(f"callback simulation raised {e}")
    
    def test_different_format_types(self):
        """Test handling different format types in sequence."""
        printer = create_auto_printer()
        
        try:
            # HTML
            printer("<b>HTML</b>")
            
            # ANSI
            printer("\x1b[1mANSI\x1b[0m")
            
            # Plain
            printer("Plain")
        except Exception as e:
            pytest.fail(f"different format types raised {e}")


class TestDocstrings:
    """Test that docstrings are present and informative."""
    
    def test_detect_format_type_docstring(self):
        """Test detect_format_type has docstring."""
        assert detect_format_type.__doc__ is not None
        assert "Detect the format type" in detect_format_type.__doc__
    
    def test_auto_format_docstring(self):
        """Test auto_format has docstring."""
        assert auto_format.__doc__ is not None
        assert "Auto-detect format type" in auto_format.__doc__
    
    def test_print_auto_formatted_docstring(self):
        """Test print_auto_formatted has docstring."""
        assert print_auto_formatted.__doc__ is not None
        assert "Print text with auto-detected formatting" in print_auto_formatted.__doc__
    
    def test_create_auto_printer_docstring(self):
        """Test create_auto_printer has docstring."""
        assert create_auto_printer.__doc__ is not None
        assert "Create a printer function" in create_auto_printer.__doc__

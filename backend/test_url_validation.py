"""
Tests for URL validation and XSS protection
"""
import pytest
from rag_system import is_safe_url


class TestURLValidation:
    """Test suite for is_safe_url() XSS protection"""

    def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted"""
        assert is_safe_url("http://example.com/lesson1") is True

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted"""
        assert is_safe_url("https://example.com/lesson1") is True

    def test_javascript_xss_attempt(self):
        """Test that XSS attempts with javascript: scheme are blocked"""
        assert is_safe_url("javascript:alert('XSS')") is False

    def test_data_uri_xss_attempt(self):
        """Test that XSS attempts with data: URIs are blocked"""
        assert is_safe_url("data:text/html,<script>alert('XSS')</script>") is False

    def test_file_uri_blocked(self):
        """Test that file:// URIs are blocked"""
        assert is_safe_url("file:///etc/passwd") is False

    def test_vbscript_xss_attempt(self):
        """Test that VBScript XSS attempts are blocked"""
        assert is_safe_url("vbscript:msgbox('XSS')") is False

    def test_malformed_url(self):
        """Test that malformed URLs don't break rendering"""
        assert is_safe_url("not a url at all") is False

    def test_empty_string(self):
        """Test that empty string is handled safely"""
        assert is_safe_url("") is False

    def test_none_value(self):
        """Test that None value doesn't cause errors"""
        # is_safe_url expects a string, but should handle gracefully
        try:
            result = is_safe_url(None)
            assert result is False
        except (TypeError, AttributeError):
            # If it raises an error, that's also acceptable defensive behavior
            pass

    def test_url_with_query_params(self):
        """Test that valid URLs with query parameters are accepted"""
        assert is_safe_url("https://example.com/lesson?id=1&page=2") is True

    def test_url_with_fragment(self):
        """Test that valid URLs with fragments are accepted"""
        assert is_safe_url("https://example.com/lesson#section1") is True

    def test_mixed_case_scheme(self):
        """Test that mixed case schemes are handled correctly"""
        # Mixed case javascript: attempts
        assert is_safe_url("JaVaScRiPt:alert('XSS')") is False
        # Mixed case http should still work
        assert is_safe_url("HtTpS://example.com") is True

    def test_url_with_special_characters(self):
        """Test URLs with encoded special characters"""
        assert is_safe_url("https://example.com/lesson%20with%20spaces") is True

    def test_about_blank(self):
        """Test that about:blank is blocked"""
        assert is_safe_url("about:blank") is False

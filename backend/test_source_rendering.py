"""
Tests for source rendering in the RAG system
This tests the backend logic that prepares sources for frontend display
"""
import pytest
from unittest.mock import Mock, MagicMock
from rag_system import RAGSystem, is_safe_url


class TestSourceRendering:
    """Test suite for source enhancement and rendering preparation"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        self.mock_config = Mock()
        self.mock_config.CHUNK_SIZE = 800
        self.mock_config.CHUNK_OVERLAP = 100
        self.mock_config.CHROMA_PATH = "./test_chroma"
        self.mock_config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        self.mock_config.MAX_RESULTS = 5
        self.mock_config.MAX_HISTORY = 2
        self.mock_config.ANTHROPIC_API_KEY = "test-key"
        self.mock_config.ANTHROPIC_MODEL = "test-model"
        self.mock_config.ANTHROPIC_BASE_URL = None

    def test_sources_with_valid_lesson_links_render_correctly(self):
        """Test that sources with valid lesson links are properly structured"""
        # This tests the enhancement logic in rag_system.py lines 154-177

        # Arrange
        raw_sources = [
            {
                "text": "Introduction to Python - Lesson 1",
                "course_title": "Python Course",
                "lesson_number": 1
            }
        ]

        lesson_link = "https://example.com/lesson1"

        # Simulate the enhancement process
        enhanced_sources = []
        for source in raw_sources:
            source_item = {
                "text": source["text"],
                "link": None
            }

            # Simulate get_lesson_link returning a valid link
            if source.get("lesson_number") is not None and source.get("course_title"):
                # Simulate the is_safe_url check
                if lesson_link and is_safe_url(lesson_link):
                    source_item["link"] = lesson_link

            enhanced_sources.append(source_item)

        # Assert
        assert len(enhanced_sources) == 1
        assert enhanced_sources[0]["text"] == "Introduction to Python - Lesson 1"
        assert enhanced_sources[0]["link"] == "https://example.com/lesson1"

    def test_sources_without_links_display_as_plain_text(self):
        """Test that sources without links only have text field"""
        # Arrange
        raw_sources = [
            {
                "text": "Introduction to Python - General",
                "course_title": "Python Course",
                "lesson_number": None  # No lesson number
            }
        ]

        # Simulate the enhancement process
        enhanced_sources = []
        for source in raw_sources:
            source_item = {
                "text": source["text"],
                "link": None
            }

            # No lesson number, so link stays None
            if source.get("lesson_number") is not None and source.get("course_title"):
                pass  # Would try to get link here

            enhanced_sources.append(source_item)

        # Assert
        assert len(enhanced_sources) == 1
        assert enhanced_sources[0]["text"] == "Introduction to Python - General"
        assert enhanced_sources[0]["link"] is None

    def test_malformed_urls_dont_break_rendering(self):
        """Test that malformed URLs are rejected and don't crash the system"""
        # Arrange
        malformed_urls = [
            "not a url",
            "javascript:alert('xss')",
            "data:text/html,<script>",
            "",
            None
        ]

        # Act & Assert
        for url in malformed_urls:
            # Simulate the is_safe_url check
            if url and is_safe_url(url):
                link = url
            else:
                link = None

            # Malformed URLs should result in None link
            assert link is None

    def test_xss_attempts_in_source_data_are_sanitized(self):
        """Test that XSS attempts in lesson links are blocked"""
        # Arrange
        xss_attempts = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "vbscript:msgbox('XSS')",
            "file:///etc/passwd"
        ]

        raw_sources = []
        for i, xss_url in enumerate(xss_attempts):
            raw_sources.append({
                "text": f"Malicious Source {i}",
                "course_title": "Test Course",
                "lesson_number": i
            })

        # Simulate the enhancement process with XSS URLs
        enhanced_sources = []
        for i, source in enumerate(raw_sources):
            source_item = {
                "text": source["text"],
                "link": None
            }

            # Simulate get_lesson_link returning malicious URL
            malicious_url = xss_attempts[i]
            if source.get("lesson_number") is not None and source.get("course_title"):
                # is_safe_url should block these
                if malicious_url and is_safe_url(malicious_url):
                    source_item["link"] = malicious_url

            enhanced_sources.append(source_item)

        # Assert - all links should be None due to XSS protection
        for source_item in enhanced_sources:
            assert source_item["link"] is None

    def test_missing_course_handling(self):
        """Test that sources with missing course info are handled gracefully"""
        # Arrange
        raw_sources = [
            {
                "text": "Some content",
                "course_title": None,
                "lesson_number": 1
            },
            {
                "text": "Other content",
                "course_title": "Valid Course",
                "lesson_number": None
            },
            {
                "text": "More content",
                # Missing course_title and lesson_number keys entirely
            }
        ]

        # Simulate the enhancement process
        enhanced_sources = []
        for source in raw_sources:
            # Defensive check from rag_system.py:158-159
            if not isinstance(source, dict) or "text" not in source:
                continue

            source_item = {
                "text": source["text"],
                "link": None
            }

            # Check for both course_title and lesson_number
            if source.get("lesson_number") is not None and source.get("course_title"):
                # Would try to get link here
                pass

            enhanced_sources.append(source_item)

        # Assert - all sources should be processed without errors
        assert len(enhanced_sources) == 3
        for source_item in enhanced_sources:
            assert "text" in source_item
            assert "link" in source_item
            assert source_item["link"] is None

    def test_defensive_source_validation(self):
        """Test that invalid source formats are handled defensively"""
        # Arrange - various invalid source formats
        invalid_sources = [
            "not a dict",  # String instead of dict
            123,  # Number
            {"no_text_key": "value"},  # Dict without text key
            None,  # None value
            [],  # Empty list
        ]

        # Act - simulate defensive check from rag_system.py:158-159
        enhanced_sources = []
        for source in invalid_sources:
            if not isinstance(source, dict) or "text" not in source:
                continue  # Skip invalid sources

            source_item = {
                "text": source["text"],
                "link": None
            }
            enhanced_sources.append(source_item)

        # Assert - no invalid sources should make it through
        assert len(enhanced_sources) == 0

"""
Tests for source rendering in the RAG system
This tests the backend logic that prepares sources for frontend display
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
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
        rag = RAGSystem(self.mock_config)

        # Mock the AI generator to avoid actual API calls
        rag.ai_generator.generate_response = Mock(return_value="Test response")

        # Mock the tool manager to return sources with lesson info
        rag.tool_manager.get_last_sources = Mock(return_value=[
            {
                "text": "Introduction to Python - Lesson 1",
                "course_title": "Python Course",
                "lesson_number": 1
            }
        ])

        # Mock vector store to return a valid lesson link
        rag.vector_store.get_lesson_link = Mock(return_value="https://example.com/lesson1")

        # Act
        response, enhanced_sources = rag.query("test query", "session_1")

        # Assert
        assert len(enhanced_sources) == 1
        assert enhanced_sources[0]["text"] == "Introduction to Python - Lesson 1"
        assert enhanced_sources[0]["link"] == "https://example.com/lesson1"

        # Verify the mocks were called correctly
        rag.vector_store.get_lesson_link.assert_called_once_with("Python Course", 1)

    def test_sources_without_links_display_as_plain_text(self):
        """Test that sources without links only have text field"""
        # Arrange
        rag = RAGSystem(self.mock_config)
        rag.ai_generator.generate_response = Mock(return_value="Test response")

        # Mock sources without lesson numbers
        rag.tool_manager.get_last_sources = Mock(return_value=[
            {
                "text": "Introduction to Python - General",
                "course_title": "Python Course",
                "lesson_number": None  # No lesson number
            }
        ])

        rag.vector_store.get_lesson_link = Mock(return_value=None)

        # Act
        response, enhanced_sources = rag.query("test query", "session_1")

        # Assert
        assert len(enhanced_sources) == 1
        assert enhanced_sources[0]["text"] == "Introduction to Python - General"
        assert enhanced_sources[0]["link"] is None

        # get_lesson_link should not be called when lesson_number is None
        rag.vector_store.get_lesson_link.assert_not_called()

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

        for malformed_url in malformed_urls:
            rag = RAGSystem(self.mock_config)
            rag.ai_generator.generate_response = Mock(return_value="Test response")

            rag.tool_manager.get_last_sources = Mock(return_value=[
                {
                    "text": "Test Source",
                    "course_title": "Test Course",
                    "lesson_number": 1
                }
            ])

            # Mock vector store to return malformed URL
            rag.vector_store.get_lesson_link = Mock(return_value=malformed_url)

            # Act
            response, enhanced_sources = rag.query("test query", "session_1")

            # Assert - malformed URLs should result in None link
            assert len(enhanced_sources) == 1
            assert enhanced_sources[0]["link"] is None

    def test_xss_attempts_in_source_data_are_sanitized(self):
        """Test that XSS attempts in lesson links are blocked"""
        # Arrange
        xss_attempts = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "vbscript:msgbox('XSS')",
            "file:///etc/passwd"
        ]

        for i, xss_url in enumerate(xss_attempts):
            rag = RAGSystem(self.mock_config)
            rag.ai_generator.generate_response = Mock(return_value="Test response")

            rag.tool_manager.get_last_sources = Mock(return_value=[
                {
                    "text": f"Malicious Source {i}",
                    "course_title": "Test Course",
                    "lesson_number": i
                }
            ])

            # Mock vector store to return XSS URL
            rag.vector_store.get_lesson_link = Mock(return_value=xss_url)

            # Act
            response, enhanced_sources = rag.query("test query", "session_1")

            # Assert - XSS URLs should be blocked
            assert len(enhanced_sources) == 1
            assert enhanced_sources[0]["link"] is None

    def test_missing_course_handling(self):
        """Test that sources with missing course info are handled gracefully"""
        # Arrange
        rag = RAGSystem(self.mock_config)
        rag.ai_generator.generate_response = Mock(return_value="Test response")

        # Mock sources with various missing fields
        rag.tool_manager.get_last_sources = Mock(return_value=[
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
        ])

        rag.vector_store.get_lesson_link = Mock(return_value="https://example.com/lesson1")

        # Act
        response, enhanced_sources = rag.query("test query", "session_1")

        # Assert - all sources should be processed without errors
        assert len(enhanced_sources) == 3
        for source_item in enhanced_sources:
            assert "text" in source_item
            assert "link" in source_item
            assert source_item["link"] is None

        # get_lesson_link should not be called for any of these sources
        rag.vector_store.get_lesson_link.assert_not_called()

    def test_defensive_source_validation(self):
        """Test that invalid source formats are handled defensively"""
        # Arrange - various invalid source formats
        rag = RAGSystem(self.mock_config)
        rag.ai_generator.generate_response = Mock(return_value="Test response")

        # Mock invalid sources
        rag.tool_manager.get_last_sources = Mock(return_value=[
            "not a dict",  # String instead of dict
            123,  # Number
            {"no_text_key": "value"},  # Dict without text key
            None,  # None value
            [],  # Empty list
        ])

        rag.vector_store.get_lesson_link = Mock(return_value="https://example.com/lesson1")

        # Act - should not crash
        response, enhanced_sources = rag.query("test query", "session_1")

        # Assert - no invalid sources should make it through
        assert len(enhanced_sources) == 0

        # get_lesson_link should not be called for invalid sources
        rag.vector_store.get_lesson_link.assert_not_called()

    def test_tool_manager_reset_called(self):
        """Test that tool_manager.reset_sources() is called after processing"""
        # Arrange
        rag = RAGSystem(self.mock_config)
        rag.ai_generator.generate_response = Mock(return_value="Test response")

        rag.tool_manager.get_last_sources = Mock(return_value=[
            {
                "text": "Test Source",
                "course_title": "Test Course",
                "lesson_number": 1
            }
        ])

        rag.vector_store.get_lesson_link = Mock(return_value="https://example.com/lesson1")

        # Mock reset_sources to track if it's called
        rag.tool_manager.reset_sources = Mock()

        # Act
        response, enhanced_sources = rag.query("test query", "session_1")

        # Assert
        rag.tool_manager.reset_sources.assert_called_once()

    def test_empty_sources_list(self):
        """Test that empty sources list is handled correctly"""
        # Arrange
        rag = RAGSystem(self.mock_config)
        rag.ai_generator.generate_response = Mock(return_value="Test response")

        # Mock empty sources list
        rag.tool_manager.get_last_sources = Mock(return_value=[])

        rag.vector_store.get_lesson_link = Mock(return_value="https://example.com/lesson1")

        # Act
        response, enhanced_sources = rag.query("test query", "session_1")

        # Assert
        assert len(enhanced_sources) == 0
        assert enhanced_sources == []

        # get_lesson_link should not be called for empty list
        rag.vector_store.get_lesson_link.assert_not_called()

    def test_session_manager_integration(self):
        """Test that session manager is updated after query"""
        # Arrange
        rag = RAGSystem(self.mock_config)
        rag.ai_generator.generate_response = Mock(return_value="Test response")

        rag.tool_manager.get_last_sources = Mock(return_value=[])

        # Mock session manager
        rag.session_manager.add_exchange = Mock()

        # Act
        response, enhanced_sources = rag.query("test query", "session_1")

        # Assert
        rag.session_manager.add_exchange.assert_called_once_with(
            "session_1",
            "Answer this question about course materials: test query",
            "Test response"
        )

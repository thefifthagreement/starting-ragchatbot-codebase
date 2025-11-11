"""
Tests for VectorStore.get_lesson_link() functionality
"""
import pytest
import json
from unittest.mock import Mock, MagicMock
from vector_store import VectorStore


class TestGetLessonLink:
    """Test suite for get_lesson_link() method"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        # Mock the VectorStore to avoid ChromaDB dependencies
        self.mock_store = Mock(spec=VectorStore)
        self.mock_store.course_catalog = MagicMock()

    def test_get_lesson_link_with_valid_lesson(self):
        """Test that get_lesson_link returns correct link for valid lesson"""
        # Arrange
        course_title = "Introduction to Python"
        lesson_number = 1
        expected_link = "https://example.com/lesson1"

        lessons_data = [
            {"lesson_number": 0, "lesson_title": "Welcome", "lesson_link": "https://example.com/lesson0"},
            {"lesson_number": 1, "lesson_title": "Variables", "lesson_link": expected_link},
            {"lesson_number": 2, "lesson_title": "Functions", "lesson_link": "https://example.com/lesson2"}
        ]

        mock_metadata = {
            "title": course_title,
            "lessons_json": json.dumps(lessons_data)
        }

        self.mock_store.course_catalog.get.return_value = {
            "metadatas": [[mock_metadata]]
        }

        # Act
        result = VectorStore.get_lesson_link(self.mock_store, course_title, lesson_number)

        # Assert
        assert result == expected_link
        self.mock_store.course_catalog.get.assert_called_once_with(ids=[course_title])

    def test_get_lesson_link_without_link(self):
        """Test that sources without links display as plain text (returns None)"""
        # Arrange
        course_title = "Introduction to Python"
        lesson_number = 1

        lessons_data = [
            {"lesson_number": 0, "lesson_title": "Welcome", "lesson_link": "https://example.com/lesson0"},
            {"lesson_number": 1, "lesson_title": "Variables", "lesson_link": None},
            {"lesson_number": 2, "lesson_title": "Functions", "lesson_link": "https://example.com/lesson2"}
        ]

        mock_metadata = {
            "title": course_title,
            "lessons_json": json.dumps(lessons_data)
        }

        self.mock_store.course_catalog.get.return_value = {
            "metadatas": [[mock_metadata]]
        }

        # Act
        result = VectorStore.get_lesson_link(self.mock_store, course_title, lesson_number)

        # Assert
        assert result is None

    def test_get_lesson_link_missing_course(self):
        """Test that get_lesson_link handles missing courses gracefully"""
        # Arrange
        course_title = "Nonexistent Course"
        lesson_number = 1

        # Simulate course not found - empty results
        self.mock_store.course_catalog.get.return_value = {
            "metadatas": []
        }

        # Act
        result = VectorStore.get_lesson_link(self.mock_store, course_title, lesson_number)

        # Assert
        assert result is None
        self.mock_store.course_catalog.get.assert_called_once_with(ids=[course_title])

    def test_get_lesson_link_invalid_json(self):
        """Test that get_lesson_link handles invalid JSON in metadata gracefully"""
        # Arrange
        course_title = "Introduction to Python"
        lesson_number = 1

        mock_metadata = {
            "title": course_title,
            "lessons_json": "invalid json {{{["  # Malformed JSON
        }

        self.mock_store.course_catalog.get.return_value = {
            "metadatas": [[mock_metadata]]
        }

        # Act
        result = VectorStore.get_lesson_link(self.mock_store, course_title, lesson_number)

        # Assert
        assert result is None

    def test_get_lesson_link_missing_lesson_number(self):
        """Test that get_lesson_link returns None when lesson number doesn't exist"""
        # Arrange
        course_title = "Introduction to Python"
        lesson_number = 99  # Non-existent lesson

        lessons_data = [
            {"lesson_number": 0, "lesson_title": "Welcome", "lesson_link": "https://example.com/lesson0"},
            {"lesson_number": 1, "lesson_title": "Variables", "lesson_link": "https://example.com/lesson1"}
        ]

        mock_metadata = {
            "title": course_title,
            "lessons_json": json.dumps(lessons_data)
        }

        self.mock_store.course_catalog.get.return_value = {
            "metadatas": [[mock_metadata]]
        }

        # Act
        result = VectorStore.get_lesson_link(self.mock_store, course_title, lesson_number)

        # Assert
        assert result is None

    def test_get_lesson_link_exception_handling(self):
        """Test that get_lesson_link handles exceptions gracefully"""
        # Arrange
        course_title = "Introduction to Python"
        lesson_number = 1

        # Simulate an exception during retrieval
        self.mock_store.course_catalog.get.side_effect = Exception("Database error")

        # Act
        result = VectorStore.get_lesson_link(self.mock_store, course_title, lesson_number)

        # Assert
        assert result is None

"""Shared fixtures for all test modules."""
import sys
import os
from unittest.mock import MagicMock
import pytest

# Ensure backend/ is on the path so imports like `from vector_store import ...` work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vector_store import SearchResults


@pytest.fixture
def sample_search_results():
    """A valid SearchResults object with 2 documents."""
    return SearchResults(
        documents=["Lesson 1 content about Python basics.", "More detail on variables."],
        metadata=[
            {"course_title": "Intro to Python", "lesson_number": 1, "chunk_index": 0},
            {"course_title": "Intro to Python", "lesson_number": 1, "chunk_index": 1},
        ],
        distances=[0.1, 0.2],
    )


@pytest.fixture
def mock_vector_store(sample_search_results):
    """MagicMock VectorStore with sensible defaults."""
    store = MagicMock()
    store.search.return_value = sample_search_results
    store.get_lesson_link.return_value = "https://example.com/lesson/1"
    store.get_course_outline.return_value = {
        "title": "Intro to Python",
        "course_link": "https://example.com/course",
        "lessons": [
            {"lesson_number": 1, "lesson_title": "Variables", "lesson_link": "https://example.com/lesson/1"},
            {"lesson_number": 2, "lesson_title": "Functions", "lesson_link": "https://example.com/lesson/2"},
        ],
    }
    return store


@pytest.fixture
def tmp_chroma_path(tmp_path):
    """Temporary ChromaDB directory for integration tests."""
    return str(tmp_path / "chroma_db")

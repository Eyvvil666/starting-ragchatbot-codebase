"""Unit tests for CourseSearchTool (VectorStore is mocked)."""
from unittest.mock import MagicMock
import pytest

from vector_store import SearchResults
from search_tools import CourseSearchTool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool(store):
    return CourseSearchTool(store)


def _empty_results():
    return SearchResults(documents=[], metadata=[], distances=[])


def _error_results(msg):
    return SearchResults.empty(msg)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCourseSearchToolExecute:
    def test_execute_returns_formatted_results(self, mock_vector_store, sample_search_results):
        tool = _make_tool(mock_vector_store)
        result = tool.execute(query="Python basics")

        assert "Lesson 1 content about Python basics." in result
        assert "Intro to Python" in result
        assert "Lesson 1" in result

    def test_execute_empty_results_no_filter(self, mock_vector_store):
        mock_vector_store.search.return_value = _empty_results()
        tool = _make_tool(mock_vector_store)

        result = tool.execute(query="something obscure")
        assert "No relevant content found" in result
        # No extra filter info
        assert "in course" not in result

    def test_execute_empty_results_with_course_filter(self, mock_vector_store):
        mock_vector_store.search.return_value = _empty_results()
        tool = _make_tool(mock_vector_store)

        result = tool.execute(query="something", course_name="Intro to Python")
        assert "No relevant content found" in result
        assert "in course 'Intro to Python'" in result

    def test_execute_returns_error_from_store(self, mock_vector_store):
        mock_vector_store.search.return_value = _error_results("Search error: collection is empty")
        tool = _make_tool(mock_vector_store)

        result = tool.execute(query="anything")
        assert "Search error" in result

    def test_execute_passes_course_name_to_store(self, mock_vector_store):
        tool = _make_tool(mock_vector_store)
        tool.execute(query="what is X", course_name="Advanced Python")

        mock_vector_store.search.assert_called_once_with(
            query="what is X",
            course_name="Advanced Python",
            lesson_number=None,
        )

    def test_execute_passes_lesson_number_to_store(self, mock_vector_store):
        tool = _make_tool(mock_vector_store)
        tool.execute(query="lesson content", lesson_number=2)

        mock_vector_store.search.assert_called_once_with(
            query="lesson content",
            course_name=None,
            lesson_number=2,
        )


class TestCourseSearchToolSources:
    def test_last_sources_populated_with_link(self, mock_vector_store, sample_search_results):
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson/1"
        tool = _make_tool(mock_vector_store)
        tool.execute(query="anything")

        assert len(tool.last_sources) > 0
        assert '<a' in tool.last_sources[0]
        assert 'href="https://example.com/lesson/1"' in tool.last_sources[0]

    def test_last_sources_populated_without_link(self, mock_vector_store, sample_search_results):
        mock_vector_store.get_lesson_link.return_value = None
        tool = _make_tool(mock_vector_store)
        tool.execute(query="anything")

        assert len(tool.last_sources) > 0
        assert '<a' not in tool.last_sources[0]
        assert "Intro to Python" in tool.last_sources[0]

    def test_execute_deduplicates_sources(self, mock_vector_store, sample_search_results):
        # Both chunks are from the same lesson → should produce 1 source entry
        mock_vector_store.search.return_value = sample_search_results  # 2 docs, same lesson 1
        tool = _make_tool(mock_vector_store)
        tool.execute(query="anything")

        assert len(tool.last_sources) == 1


class TestCourseSearchToolDefinition:
    def test_get_tool_definition_has_required_fields(self, mock_vector_store):
        tool = _make_tool(mock_vector_store)
        defn = tool.get_tool_definition()

        assert defn["name"] == "search_course_content"
        assert "description" in defn
        assert "input_schema" in defn
        assert "query" in defn["input_schema"]["required"]

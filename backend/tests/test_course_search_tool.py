import pytest
from unittest.mock import Mock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_tools import CourseSearchTool
from vector_store import SearchResults


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing"""
    return Mock()


@pytest.fixture
def search_tool(mock_vector_store):
    """Create a CourseSearchTool instance with mock vector store"""
    return CourseSearchTool(mock_vector_store)


class TestCourseSearchTool:
    """Test cases for CourseSearchTool.execute method"""

    def test_execute_success_with_results(self, search_tool, mock_vector_store):
        """Test successful search that returns results"""
        # Mock successful search results
        mock_results = SearchResults(
            documents=["Course content about Python basics", "Advanced Python concepts"],
            metadata=[
                {"course_title": "Python Course", "lesson_number": 1, "chunk_index": 0},
                {"course_title": "Python Course", "lesson_number": 2, "chunk_index": 1}
            ],
            distances=[0.1, 0.2],
            error=None
        )
        
        # Mock the lesson link method
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"
        mock_vector_store.search.return_value = mock_results
        
        # Execute search
        result = search_tool.execute("Python basics")
        
        # Verify the search was called correctly
        mock_vector_store.search.assert_called_once_with(
            query="Python basics",
            course_name=None,
            lesson_number=None
        )
        
        # Verify formatted output contains course and lesson info
        assert "[Python Course - Lesson 1]" in result
        assert "[Python Course - Lesson 2]" in result
        assert "Course content about Python basics" in result
        assert "Advanced Python concepts" in result
        
        # Verify sources were tracked
        assert len(search_tool.last_sources) == 2
        assert search_tool.last_sources[0]["text"] == "Python Course - Lesson 1"
        assert search_tool.last_sources[0]["url"] == "https://example.com/lesson1"

    def test_execute_with_course_filter(self, search_tool, mock_vector_store):
        """Test search with course name filter"""
        mock_results = SearchResults(
            documents=["MCP specific content"],
            metadata=[{"course_title": "MCP Course", "lesson_number": 1, "chunk_index": 0}],
            distances=[0.1],
            error=None
        )
        
        mock_vector_store.get_lesson_link.return_value = None
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("concepts", course_name="MCP", lesson_number=1)
        
        # Verify search called with filters
        mock_vector_store.search.assert_called_once_with(
            query="concepts",
            course_name="MCP",
            lesson_number=1
        )
        
        assert "[MCP Course - Lesson 1]" in result

    def test_execute_empty_results(self, search_tool, mock_vector_store):
        """Test search that returns no results"""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("nonexistent topic")
        
        assert result == "No relevant content found."

    @pytest.mark.parametrize("course_name,lesson_number,expected", [
        ("Test Course", None, "No relevant content found in course 'Test Course'."),
        (None, 1, "No relevant content found in lesson 1."),
        ("Test Course", 1, "No relevant content found in course 'Test Course' in lesson 1."),
    ])
    def test_execute_empty_results_with_filters(self, search_tool, mock_vector_store, course_name, lesson_number, expected):
        """Test empty results with different filter combinations"""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("topic", course_name=course_name, lesson_number=lesson_number)
        
        assert result == expected

    def test_execute_search_error(self, search_tool, mock_vector_store):
        """Test handling of search errors"""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error="Database connection failed"
        )
        
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("test query")
        
        assert result == "Database connection failed"

    def test_execute_results_without_lesson_number(self, search_tool, mock_vector_store):
        """Test formatting results that don't have lesson numbers"""
        mock_results = SearchResults(
            documents=["General course content"],
            metadata=[{"course_title": "General Course", "chunk_index": 0}],
            distances=[0.1],
            error=None
        )
        
        mock_vector_store.get_lesson_link.return_value = None
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("general topic")
        
        # Should just show course title without lesson number
        assert "[General Course]" in result
        assert "Lesson" not in result.split("]")[0]  # No "Lesson" in the header

    def test_get_tool_definition(self, search_tool):
        """Test that tool definition is properly formatted"""
        definition = search_tool.get_tool_definition()
        
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["required"] == ["query"]
        
        # Check that all expected properties are defined
        properties = definition["input_schema"]["properties"]
        assert "query" in properties
        assert "course_name" in properties
        assert "lesson_number" in properties

    def test_source_tracking_with_multiple_calls(self, search_tool, mock_vector_store):
        """Test that sources are properly reset between calls"""
        mock_results1 = SearchResults(
            documents=["First result"],
            metadata=[{"course_title": "Course 1", "lesson_number": 1, "chunk_index": 0}],
            distances=[0.1],
            error=None
        )
        mock_results2 = SearchResults(
            documents=["Second result"],
            metadata=[{"course_title": "Course 2", "lesson_number": 2, "chunk_index": 0}],
            distances=[0.1],
            error=None
        )
        
        mock_vector_store.get_lesson_link.return_value = None
        
        # First call
        mock_vector_store.search.return_value = mock_results1
        search_tool.execute("first query")
        assert len(search_tool.last_sources) == 1
        assert search_tool.last_sources[0]["text"] == "Course 1 - Lesson 1"
        
        # Second call
        mock_vector_store.search.return_value = mock_results2
        search_tool.execute("second query")
        assert len(search_tool.last_sources) == 1
        assert search_tool.last_sources[0]["text"] == "Course 2 - Lesson 2"
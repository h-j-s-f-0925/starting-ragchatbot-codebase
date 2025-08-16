import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system import RAGSystem
from models import Course, Lesson


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    config = Mock()
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.CHROMA_PATH = "./test_chroma_db"
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.MAX_RESULTS = 5
    config.ANTHROPIC_API_KEY = "test-api-key"
    config.ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    config.MAX_HISTORY = 2
    return config


@pytest.fixture
def mock_components():
    """Create mock components for RAG system"""
    components = {
        'document_processor': Mock(),
        'vector_store': Mock(),
        'ai_generator': Mock(),
        'session_manager': Mock(),
        'search_tool': Mock(),
        'overview_tool': Mock(),
        'tool_manager': Mock()
    }
    return components


@pytest.fixture
def rag_system(mock_config, mock_components):
    """Create a RAG system with mocked components"""
    with patch('rag_system.DocumentProcessor', return_value=mock_components['document_processor']), \
         patch('rag_system.VectorStore', return_value=mock_components['vector_store']), \
         patch('rag_system.AIGenerator', return_value=mock_components['ai_generator']), \
         patch('rag_system.SessionManager', return_value=mock_components['session_manager']), \
         patch('rag_system.CourseSearchTool', return_value=mock_components['search_tool']), \
         patch('rag_system.CourseOverviewTool', return_value=mock_components['overview_tool']), \
         patch('rag_system.ToolManager', return_value=mock_components['tool_manager']):
        
        system = RAGSystem(mock_config)
        
        # Replace the components with our mocks for easier access
        system.document_processor = mock_components['document_processor']
        system.vector_store = mock_components['vector_store']
        system.ai_generator = mock_components['ai_generator']
        system.session_manager = mock_components['session_manager']
        system.search_tool = mock_components['search_tool']
        system.overview_tool = mock_components['overview_tool']
        system.tool_manager = mock_components['tool_manager']
        
        return system


class TestRAGSystem:
    """Test cases for RAG system integration and query processing"""

    def test_query_processing_successful_response(self, rag_system, mock_components):
        """Test successful query processing end-to-end"""
        # Setup mocks
        mock_components['session_manager'].get_conversation_history.return_value = "Previous conversation"
        mock_components['ai_generator'].generate_response.return_value = "AI response about Python"
        mock_components['tool_manager'].get_last_sources.return_value = [
            {"text": "Python Course - Lesson 1", "url": "https://example.com/lesson1"}
        ]
        mock_components['session_manager'].create_session.return_value = "session_123"
        
        # Execute query
        response, sources = rag_system.query("What is Python?", session_id="test_session")
        
        # Verify AI generator was called with correct parameters
        mock_components['ai_generator'].generate_response.assert_called_once()
        call_args = mock_components['ai_generator'].generate_response.call_args
        
        assert call_args[1]['query'] == "Answer this question about course materials: What is Python?"
        assert call_args[1]['conversation_history'] == "Previous conversation"
        assert call_args[1]['tools'] is not None  # Tool definitions should be passed
        assert call_args[1]['tool_manager'] is not None
        
        # Verify session management
        mock_components['session_manager'].add_exchange.assert_called_once_with(
            "test_session", "What is Python?", "AI response about Python"
        )
        
        # Verify sources handling
        mock_components['tool_manager'].get_last_sources.assert_called_once()
        mock_components['tool_manager'].reset_sources.assert_called_once()
        
        assert response == "AI response about Python"
        assert sources == [{"text": "Python Course - Lesson 1", "url": "https://example.com/lesson1"}]

    def test_query_processing_without_session_id(self, rag_system, mock_components):
        """Test query processing when no session ID is provided"""
        mock_components['session_manager'].create_session.return_value = "new_session_456"
        mock_components['ai_generator'].generate_response.return_value = "Response without session"
        mock_components['tool_manager'].get_last_sources.return_value = []
        
        response, sources = rag_system.query("General question")
        
        # Should not try to get conversation history for None session
        mock_components['session_manager'].get_conversation_history.assert_called_once_with(None)
        
        # Should not add exchange since no session was provided
        mock_components['session_manager'].add_exchange.assert_not_called()
        
        assert response == "Response without session"
        assert sources == []

    def test_query_processing_with_new_session_creation(self, rag_system, mock_components):
        """Test query processing with automatic session creation"""
        # Mock session manager to return None for history (no existing session)
        mock_components['session_manager'].get_conversation_history.return_value = None
        mock_components['ai_generator'].generate_response.return_value = "New session response"
        mock_components['tool_manager'].get_last_sources.return_value = []
        
        response, sources = rag_system.query("Question", session_id="new_session")
        
        # Verify conversation history was requested
        mock_components['session_manager'].get_conversation_history.assert_called_once_with("new_session")
        
        # Verify AI generator called with no history
        call_args = mock_components['ai_generator'].generate_response.call_args[1]
        assert call_args['conversation_history'] is None
        
        # Verify session exchange was added
        mock_components['session_manager'].add_exchange.assert_called_once_with(
            "new_session", "Question", "New session response"
        )

    def test_add_course_document_success(self, rag_system, mock_components):
        """Test successful course document addition"""
        # Setup mock course and chunks
        mock_course = Course(
            title="Test Course",
            instructor="Test Instructor",
            lessons=[Lesson(lesson_number=1, title="Introduction")]
        )
        mock_chunks = [Mock(), Mock(), Mock()]  # 3 chunks
        
        mock_components['document_processor'].process_course_document.return_value = (mock_course, mock_chunks)
        
        course, chunk_count = rag_system.add_course_document("/path/to/course.txt")
        
        # Verify document processing
        mock_components['document_processor'].process_course_document.assert_called_once_with("/path/to/course.txt")
        
        # Verify vector store operations
        mock_components['vector_store'].add_course_metadata.assert_called_once_with(mock_course)
        mock_components['vector_store'].add_course_content.assert_called_once_with(mock_chunks)
        
        assert course == mock_course
        assert chunk_count == 3

    def test_add_course_document_error_handling(self, rag_system, mock_components):
        """Test error handling in course document addition"""
        # Mock an exception during processing
        mock_components['document_processor'].process_course_document.side_effect = Exception("Processing failed")
        
        course, chunk_count = rag_system.add_course_document("/invalid/path.txt")
        
        # Should return None and 0 on error
        assert course is None
        assert chunk_count == 0
        
        # Vector store methods should not be called
        mock_components['vector_store'].add_course_metadata.assert_not_called()
        mock_components['vector_store'].add_course_content.assert_not_called()

    def test_get_course_analytics(self, rag_system, mock_components):
        """Test course analytics retrieval"""
        mock_components['vector_store'].get_course_count.return_value = 5
        mock_components['vector_store'].get_existing_course_titles.return_value = [
            "Course 1", "Course 2", "Course 3", "Course 4", "Course 5"
        ]
        
        analytics = rag_system.get_course_analytics()
        
        assert analytics["total_courses"] == 5
        assert len(analytics["course_titles"]) == 5
        assert "Course 1" in analytics["course_titles"]

    @pytest.mark.parametrize("query,expected_prompt", [
        ("What is Python?", "Answer this question about course materials: What is Python?"),
        ("Explain machine learning", "Answer this question about course materials: Explain machine learning"),
        ("", "Answer this question about course materials: "),
    ])
    def test_query_prompt_formatting(self, rag_system, mock_components, query, expected_prompt):
        """Test that queries are properly formatted into prompts"""
        mock_components['ai_generator'].generate_response.return_value = "Response"
        mock_components['tool_manager'].get_last_sources.return_value = []
        
        rag_system.query(query)
        
        call_args = mock_components['ai_generator'].generate_response.call_args[1]
        assert call_args['query'] == expected_prompt

    def test_tool_manager_integration(self, rag_system, mock_components):
        """Test that tool manager is properly configured and used"""
        # Verify tools were registered during initialization
        mock_components['tool_manager'].register_tool.assert_any_call(mock_components['search_tool'])
        mock_components['tool_manager'].register_tool.assert_any_call(mock_components['overview_tool'])
        
        # Test query uses tool manager
        mock_components['tool_manager'].get_tool_definitions.return_value = ["mock_tool_def"]
        mock_components['ai_generator'].generate_response.return_value = "Tool-enhanced response"
        mock_components['tool_manager'].get_last_sources.return_value = []
        
        rag_system.query("Test query")
        
        # Verify tool definitions and manager were passed to AI generator
        call_args = mock_components['ai_generator'].generate_response.call_args[1]
        assert call_args['tools'] == ["mock_tool_def"]
        assert call_args['tool_manager'] == mock_components['tool_manager']

    def test_source_management_workflow(self, rag_system, mock_components):
        """Test the complete source tracking and reset workflow"""
        mock_sources = [
            {"text": "Source 1", "url": "http://example.com/1"},
            {"text": "Source 2", "url": None}
        ]
        
        mock_components['ai_generator'].generate_response.return_value = "Response with sources"
        mock_components['tool_manager'].get_last_sources.return_value = mock_sources
        
        response, sources = rag_system.query("Query with sources")
        
        # Verify source retrieval and reset sequence
        mock_components['tool_manager'].get_last_sources.assert_called_once()
        mock_components['tool_manager'].reset_sources.assert_called_once()
        
        # Verify reset is called after retrieval
        method_calls = mock_components['tool_manager'].method_calls
        get_sources_call = next(call for call in method_calls if call[0] == 'get_last_sources')
        reset_sources_call = next(call for call in method_calls if call[0] == 'reset_sources')
        
        get_sources_index = method_calls.index(get_sources_call)
        reset_sources_index = method_calls.index(reset_sources_call)
        
        assert reset_sources_index > get_sources_index
        assert sources == mock_sources
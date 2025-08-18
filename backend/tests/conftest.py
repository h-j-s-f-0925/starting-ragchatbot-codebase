"""
Shared pytest fixtures for all test modules.

This module provides common fixtures that can be reused across unit,
integration, and e2e tests to avoid duplication and ensure consistency.
"""

import pytest
from unittest.mock import Mock
import sys
import os

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ======================================
# Mock Configuration Fixtures
# ======================================

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
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


# ======================================
# AI Generator Fixtures
# ======================================

@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    client = Mock()
    return client


@pytest.fixture
def mock_ai_generator(mock_anthropic_client):
    """Create a mock AI generator with standard responses."""
    generator = Mock()
    generator.generate_response.return_value = "Mock AI response"
    generator.client = mock_anthropic_client
    return generator


# ======================================
# Vector Store Fixtures
# ======================================

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing."""
    store = Mock()
    store.search.return_value = Mock(
        documents=["Sample document content"],
        metadata=[{"course_title": "Test Course", "lesson_number": 1}],
        distances=[0.1],
        error=None
    )
    store.get_course_count.return_value = 1
    store.get_existing_course_titles.return_value = ["Test Course"]
    store.get_lesson_link.return_value = "https://example.com/lesson1"
    return store


# ======================================
# Tool and Manager Fixtures
# ======================================

@pytest.fixture
def mock_tool_manager():
    """Create a mock tool manager."""
    manager = Mock()
    manager.execute_tool.return_value = "Mock tool result"
    manager.get_tool_definitions.return_value = []
    manager.get_last_sources.return_value = []
    manager.reset_sources = Mock()
    manager.register_tool = Mock()
    return manager


@pytest.fixture
def mock_search_tool():
    """Create a mock search tool."""
    tool = Mock()
    tool.execute.return_value = "Mock search results"
    return tool


@pytest.fixture
def mock_overview_tool():
    """Create a mock overview tool."""
    tool = Mock()
    tool.execute.return_value = "Mock course overview"
    return tool


# ======================================
# Session Management Fixtures
# ======================================

@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = Mock()
    manager.get_conversation_history.return_value = "Previous conversation"
    manager.create_session.return_value = "test_session_123"
    manager.add_exchange = Mock()
    return manager


# ======================================
# Document Processing Fixtures
# ======================================

@pytest.fixture
def mock_document_processor():
    """Create a mock document processor."""
    processor = Mock()
    return processor


# ======================================
# Sample Data Fixtures
# ======================================

@pytest.fixture
def sample_tools():
    """Sample tool definitions for testing."""
    return [
        {
            "name": "search_course_content",
            "description": "Search course materials",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_course_overview",
            "description": "Get course overview information",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_name": {"type": "string", "description": "Name of the course"}
                },
                "required": ["course_name"]
            }
        }
    ]


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    from vector_store import SearchResults
    return SearchResults(
        documents=["Course content about Python", "Advanced Python concepts"],
        metadata=[
            {"course_title": "Python Course", "lesson_number": 1, "chunk_index": 0},
            {"course_title": "Python Course", "lesson_number": 2, "chunk_index": 1}
        ],
        distances=[0.1, 0.2],
        error=None
    )


@pytest.fixture
def sample_sources():
    """Sample source data for testing."""
    return [
        {"text": "Python Course - Lesson 1", "url": "https://example.com/lesson1"},
        {"text": "Python Course - Lesson 2", "url": "https://example.com/lesson2"}
    ]


# ======================================
# Mock Component Bundle Fixtures
# ======================================

@pytest.fixture
def mock_rag_components(
    mock_document_processor,
    mock_vector_store,
    mock_ai_generator,
    mock_session_manager,
    mock_search_tool,
    mock_overview_tool,
    mock_tool_manager
):
    """Bundle of all RAG system components for integration testing."""
    return {
        'document_processor': mock_document_processor,
        'vector_store': mock_vector_store,
        'ai_generator': mock_ai_generator,
        'session_manager': mock_session_manager,
        'search_tool': mock_search_tool,
        'overview_tool': mock_overview_tool,
        'tool_manager': mock_tool_manager
    }


# ======================================
# Test Markers Configuration
# ======================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests across multiple components")
    config.addinivalue_line("markers", "e2e: End-to-end tests with real components")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
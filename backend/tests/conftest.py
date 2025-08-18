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
# API Testing Fixtures
# ======================================

@pytest.fixture
def test_client():
    """Create a FastAPI test client for API endpoint testing."""
    from fastapi.testclient import TestClient
    from unittest.mock import patch
    
    # Import app but patch static file mounting to avoid filesystem dependencies
    with patch('fastapi.staticfiles.StaticFiles'):
        from app import app
        client = TestClient(app)
        yield client


@pytest.fixture
def api_test_data():
    """Provide test data for API endpoint testing."""
    return {
        "valid_query": {
            "query": "What is Python programming?",
            "session_id": None
        },
        "query_with_session": {
            "query": "How do I use variables?",
            "session_id": "test_session_123"
        },
        "empty_query": {
            "query": ""
        },
        "expected_response": {
            "answer": "Python is a high-level programming language.",
            "sources": [
                {"text": "Python basics lesson", "url": "https://example.com/lesson1"},
                {"text": "Programming fundamentals", "url": None}
            ],
            "session_id": "test_session_123"
        },
        "course_analytics": {
            "total_courses": 3,
            "course_titles": ["Python Basics", "Web Development", "Data Science"]
        }
    }


@pytest.fixture
def mock_fastapi_rag_system():
    """Mock RAG system specifically configured for FastAPI testing."""
    with patch('app.rag_system') as mock_rag:
        # Configure realistic mock responses
        mock_rag.query.return_value = (
            "Python is a versatile programming language used for web development, data science, and automation.",
            [
                {"text": "Python Introduction - Lesson 1", "url": "https://example.com/python/lesson1"},
                {"text": "Python Features Overview", "url": "https://example.com/python/features"},
                {"text": "Why Choose Python", "url": None}
            ]
        )
        
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 4,
            "course_titles": [
                "Python for Beginners",
                "Advanced Python Concepts", 
                "Web Development with FastAPI",
                "Data Analysis with Pandas"
            ]
        }
        
        mock_rag.session_manager.create_session.return_value = "mock_session_456"
        mock_rag.add_course_folder.return_value = (4, 200)  # 4 courses, 200 chunks
        
        yield mock_rag


@pytest.fixture
def api_error_scenarios():
    """Provide various error scenarios for API testing."""
    return {
        "rag_system_error": Exception("Vector database connection failed"),
        "ai_generation_error": Exception("Anthropic API rate limit exceeded"), 
        "session_error": Exception("Session storage unavailable"),
        "analytics_error": Exception("Course analytics service down"),
        "invalid_json": '{"query": "incomplete json"',
        "missing_query": {"session_id": "test123"},
        "malformed_request": {"query": None, "extra_field": "unexpected"}
    }


# ======================================
# HTTP Client Fixtures
# ======================================

@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing external API calls."""
    import httpx
    from unittest.mock import AsyncMock
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


# ======================================
# Test Environment Setup
# ======================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    import os
    import tempfile
    import shutil
    
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp(prefix="rag_test_")
    original_cwd = os.getcwd()
    
    # Set test environment variables
    test_env = {
        'ANTHROPIC_API_KEY': 'test-api-key-for-testing',
        'CHROMA_PATH': os.path.join(temp_dir, 'test_chroma_db'),
        'TESTING': '1'
    }
    
    # Backup original environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield {
        'temp_dir': temp_dir,
        'original_cwd': original_cwd,
        'test_env': test_env
    }
    
    # Cleanup
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    
    # Remove temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_course_documents():
    """Provide sample course documents for testing document processing."""
    return [
        {
            "filename": "python_basics.txt",
            "content": """Course Title: Python Programming Basics
Course Link: https://example.com/python-basics
Course Instructor: Dr. Jane Smith

Lesson 0: Introduction to Python
Lesson Link: https://example.com/python-basics/lesson-0
Python is a high-level, interpreted programming language known for its simplicity and readability.

Lesson 1: Variables and Data Types
Lesson Link: https://example.com/python-basics/lesson-1
In Python, variables are used to store data. Common data types include strings, integers, and floats.

Lesson 2: Control Structures
Lesson Link: https://example.com/python-basics/lesson-2
Python provides if statements, loops, and functions to control program flow."""
        },
        {
            "filename": "web_development.txt", 
            "content": """Course Title: Web Development with FastAPI
Course Link: https://example.com/fastapi-course
Course Instructor: Prof. John Doe

Lesson 0: Introduction to FastAPI
Lesson Link: https://example.com/fastapi-course/lesson-0
FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints.

Lesson 1: Creating Your First API
Lesson Link: https://example.com/fastapi-course/lesson-1
Learn how to create a simple API endpoint using FastAPI decorators and request models."""
        }
    ]


# ======================================
# Performance Testing Fixtures
# ======================================

@pytest.fixture
def performance_test_data():
    """Provide data for performance and load testing."""
    return {
        "concurrent_requests": 10,
        "large_query": "What is " + "Python " * 100 + "programming?",
        "multiple_sessions": [f"session_{i}" for i in range(20)],
        "stress_queries": [
            f"Query number {i} about Python programming concepts"
            for i in range(50)
        ]
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
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "performance: Performance and load tests")
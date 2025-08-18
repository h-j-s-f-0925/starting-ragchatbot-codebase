"""
Test application utilities for handling FastAPI app configuration in test environment.

This module provides utilities to create test versions of the FastAPI app
that avoid filesystem dependencies while maintaining the same API interface.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import List, Optional
from unittest.mock import Mock, patch
import warnings

# Suppress warnings for test environment
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")


def create_test_app():
    """
    Create a FastAPI app for testing that excludes static file mounting.
    
    This function creates a test version of the main FastAPI app with:
    - All API endpoints intact
    - Middleware configuration preserved  
    - Static file mounting removed to avoid filesystem dependencies
    - Mocked RAG system components
    
    Returns:
        FastAPI: Test application instance
    """
    # Import models from main app
    from app import QueryRequest, QueryResponse, Source, CourseStats
    
    # Initialize test FastAPI app
    app = FastAPI(title="Course Materials RAG System (Test)", root_path="")
    
    # Add middleware (same as production)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Create mock RAG system for testing
    mock_rag_system = create_mock_rag_system()
    
    # API Endpoints (identical to main app)
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            
            # Process query using mocked RAG system
            answer, sources = mock_rag_system.query(request.query, session_id)
            
            # Convert source dictionaries to Source objects
            source_objects = []
            for source in sources:
                if isinstance(source, dict):
                    text = source.get("text", "")
                    url = source.get("url")
                    source_objects.append(Source(text=text, url=url))
                else:
                    # Fallback for string sources (backward compatibility)
                    source_objects.append(Source(text=str(source), url=None))
            
            return QueryResponse(
                answer=answer,
                sources=source_objects,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Root endpoint handler (instead of static files)
    @app.get("/")
    async def read_root():
        """Root endpoint for testing (replaces static file serving)"""
        return {"message": "RAG System API - Test Mode", "status": "running"}
    
    return app


def create_mock_rag_system():
    """
    Create a comprehensive mock RAG system for testing.
    
    Returns:
        Mock: Configured mock RAG system with realistic responses
    """
    mock_rag = Mock()
    
    # Configure query responses
    mock_rag.query.return_value = (
        "This is a test response about programming concepts.",
        [
            {"text": "Programming fundamentals lesson", "url": "https://example.com/lesson1"},
            {"text": "Advanced concepts overview", "url": "https://example.com/lesson2"},
            {"text": "Practice exercises", "url": None}
        ]
    )
    
    # Configure analytics responses
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 3,
        "course_titles": [
            "Introduction to Programming",
            "Web Development Basics", 
            "Data Science Fundamentals"
        ]
    }
    
    # Configure session management
    mock_session_manager = Mock()
    mock_session_manager.create_session.return_value = "test_session_abc123"
    mock_session_manager.get_conversation_history.return_value = ""
    mock_session_manager.add_exchange = Mock()
    mock_rag.session_manager = mock_session_manager
    
    # Configure document processing
    mock_rag.add_course_folder.return_value = (3, 150)  # 3 courses, 150 chunks
    
    return mock_rag


def setup_test_environment():
    """
    Set up test environment with proper isolation.
    
    Returns:
        dict: Environment configuration for testing
    """
    import os
    import tempfile
    
    # Create isolated test directory
    test_dir = tempfile.mkdtemp(prefix="rag_api_test_")
    
    # Test environment variables
    test_env = {
        'ANTHROPIC_API_KEY': 'test-api-key-for-testing',
        'CHROMA_PATH': os.path.join(test_dir, 'test_chroma'),
        'TESTING': '1'
    }
    
    return {
        'test_dir': test_dir,
        'env_vars': test_env
    }


class TestRAGSystemManager:
    """
    Context manager for test RAG system setup and teardown.
    
    Usage:
        with TestRAGSystemManager() as rag_system:
            # Use rag_system in tests
            response = rag_system.query("test query", "session_id")
    """
    
    def __init__(self):
        self.mock_rag = None
        self.original_rag = None
    
    def __enter__(self):
        self.mock_rag = create_mock_rag_system()
        
        # Patch the global rag_system if needed
        try:
            import app
            self.original_rag = app.rag_system
            app.rag_system = self.mock_rag
        except (ImportError, AttributeError):
            pass
        
        return self.mock_rag
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original rag_system
        if self.original_rag is not None:
            try:
                import app
                app.rag_system = self.original_rag
            except (ImportError, AttributeError):
                pass


# Test data generators
def generate_test_queries():
    """Generate various test queries for API testing."""
    return [
        "What is Python programming?",
        "How do I create a web application?",
        "Explain data science concepts",
        "What are the benefits of using FastAPI?",
        "How do I handle errors in Python?",
        "",  # Empty query test case
        "a" * 1000,  # Long query test case
        "Special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/`~",  # Special characters
    ]


def generate_test_sessions():
    """Generate test session IDs."""
    return [
        "session_123",
        "user_abc_session",
        "test-session-456",
        None,  # No session provided
        "",  # Empty session
        "very_long_session_id_" + "x" * 100,  # Long session ID
    ]


def mock_error_scenarios():
    """Generate various error scenarios for testing."""
    return {
        "connection_error": Exception("Database connection failed"),
        "timeout_error": Exception("Request timeout after 30 seconds"),
        "rate_limit_error": Exception("API rate limit exceeded"),
        "invalid_query_error": ValueError("Query contains invalid characters"),
        "session_not_found": KeyError("Session not found"),
        "insufficient_permissions": PermissionError("Insufficient API permissions"),
        "service_unavailable": Exception("External service temporarily unavailable")
    }


# Validation utilities
def validate_api_response(response_data):
    """
    Validate API response structure and content.
    
    Args:
        response_data (dict): Response data to validate
        
    Returns:
        bool: True if response is valid
        
    Raises:
        AssertionError: If response structure is invalid
    """
    # Check required fields for query response
    if "answer" in response_data:
        assert isinstance(response_data["answer"], str)
        assert "sources" in response_data
        assert isinstance(response_data["sources"], list)
        assert "session_id" in response_data
        assert isinstance(response_data["session_id"], str)
        
        # Validate source structure
        for source in response_data["sources"]:
            assert "text" in source
            assert isinstance(source["text"], str)
            # url can be None or string
            if "url" in source and source["url"] is not None:
                assert isinstance(source["url"], str)
    
    # Check required fields for course stats response
    elif "total_courses" in response_data:
        assert isinstance(response_data["total_courses"], int)
        assert response_data["total_courses"] >= 0
        assert "course_titles" in response_data
        assert isinstance(response_data["course_titles"], list)
        assert len(response_data["course_titles"]) == response_data["total_courses"]
    
    return True


def cleanup_test_resources(test_dir=None):
    """
    Clean up test resources after test execution.
    
    Args:
        test_dir (str, optional): Test directory to clean up
    """
    import shutil
    import os
    
    if test_dir and os.path.exists(test_dir):
        try:
            shutil.rmtree(test_dir, ignore_errors=True)
        except OSError:
            pass  # Best effort cleanup
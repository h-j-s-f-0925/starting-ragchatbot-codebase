"""
API endpoint tests for the FastAPI application.

Tests cover all major endpoints and their behavior under various conditions.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import app, rag_system


@pytest.fixture
def mock_rag_system():
    """Mock RAG system for API testing."""
    with patch('app.rag_system') as mock:
        # Configure the mock RAG system
        mock.query.return_value = (
            "This is a test response about Python programming.", 
            [
                {"text": "Python is a programming language", "url": "https://example.com/lesson1"},
                {"text": "Variables in Python", "url": "https://example.com/lesson2"}
            ]
        )
        mock.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Python Basics", "Advanced Python"]
        }
        mock.session_manager.create_session.return_value = "test_session_123"
        yield mock


@pytest.fixture
def client():
    """Create test client with mocked static file mounting."""
    # Override static file mounting to avoid filesystem dependency
    with patch('app.StaticFiles'):
        test_client = TestClient(app)
        yield test_client


@pytest.mark.api
class TestQueryEndpoint:
    """Tests for /api/query endpoint."""
    
    def test_query_with_new_session(self, client, mock_rag_system):
        """Test query endpoint with new session creation."""
        response = client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["answer"] == "This is a test response about Python programming."
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "Python is a programming language"
        assert data["sources"][0]["url"] == "https://example.com/lesson1"
        assert data["session_id"] == "test_session_123"
    
    def test_query_with_existing_session(self, client, mock_rag_system):
        """Test query endpoint with existing session."""
        response = client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "session_id": "existing_session_456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the session ID was preserved
        mock_rag_system.query.assert_called_once_with("What is Python?", "existing_session_456")
        assert data["session_id"] == "existing_session_456"
    
    def test_query_empty_request(self, client):
        """Test query endpoint with empty query."""
        response = client.post(
            "/api/query",
            json={"query": ""}
        )
        
        # Should still process but with empty query
        assert response.status_code in [200, 422]  # May fail validation or return empty result
    
    def test_query_invalid_json(self, client):
        """Test query endpoint with invalid JSON."""
        response = client.post(
            "/api/query",
            data="invalid json"
        )
        
        assert response.status_code == 422
    
    def test_query_missing_required_field(self, client):
        """Test query endpoint with missing query field."""
        response = client.post(
            "/api/query",
            json={"session_id": "test"}
        )
        
        assert response.status_code == 422
        assert "query" in response.json()["detail"][0]["loc"]
    
    def test_query_rag_system_error(self, client):
        """Test query endpoint when RAG system raises an error."""
        with patch('app.rag_system') as mock_rag:
            mock_rag.query.side_effect = Exception("Database connection failed")
            
            response = client.post(
                "/api/query",
                json={"query": "What is Python?"}
            )
            
            assert response.status_code == 500
            assert "Database connection failed" in response.json()["detail"]
    
    def test_query_source_format_compatibility(self, client):
        """Test query endpoint handles different source formats."""
        with patch('app.rag_system') as mock_rag:
            # Test mixed source formats (dict and string)
            mock_rag.query.return_value = (
                "Mixed source test",
                [
                    {"text": "Dict source", "url": "https://example.com"},
                    "String source",  # Backward compatibility
                    {"text": "Dict without URL"}
                ]
            )
            mock_rag.session_manager.create_session.return_value = "test_session"
            
            response = client.post(
                "/api/query",
                json={"query": "Test mixed sources"}
            )
            
            assert response.status_code == 200
            data = response.json()
            sources = data["sources"]
            
            # Verify proper conversion
            assert len(sources) == 3
            assert sources[0]["text"] == "Dict source"
            assert sources[0]["url"] == "https://example.com"
            assert sources[1]["text"] == "String source"
            assert sources[1]["url"] is None
            assert sources[2]["text"] == "Dict without URL"
            assert sources[2]["url"] is None


@pytest.mark.api 
class TestCoursesEndpoint:
    """Tests for /api/courses endpoint."""
    
    def test_get_course_stats_success(self, client, mock_rag_system):
        """Test successful retrieval of course statistics."""
        response = client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 2
        assert data["course_titles"] == ["Python Basics", "Advanced Python"]
        
        mock_rag_system.get_course_analytics.assert_called_once()
    
    def test_get_course_stats_rag_error(self, client):
        """Test course stats endpoint when RAG system fails."""
        with patch('app.rag_system') as mock_rag:
            mock_rag.get_course_analytics.side_effect = Exception("Analytics service unavailable")
            
            response = client.get("/api/courses")
            
            assert response.status_code == 500
            assert "Analytics service unavailable" in response.json()["detail"]
    
    def test_get_course_stats_empty_result(self, client):
        """Test course stats endpoint with no courses."""
        with patch('app.rag_system') as mock_rag:
            mock_rag.get_course_analytics.return_value = {
                "total_courses": 0,
                "course_titles": []
            }
            
            response = client.get("/api/courses")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_courses"] == 0
            assert data["course_titles"] == []


@pytest.mark.api
class TestRootEndpoint:
    """Tests for the root endpoint (frontend serving)."""
    
    def test_root_endpoint_static_files(self, client):
        """Test that root endpoint is properly configured for static file serving."""
        # Since we're mocking StaticFiles, this tests the mounting configuration
        with patch('app.StaticFiles') as mock_static:
            mock_static_instance = Mock()
            mock_static.return_value = mock_static_instance
            
            # The static files are mounted on app startup, so we just verify
            # the configuration doesn't cause errors
            response = client.get("/")
            
            # Response code depends on mock behavior, but should not be 500
            assert response.status_code != 500


@pytest.mark.api
class TestAppStartup:
    """Tests for application startup behavior."""
    
    def test_startup_event_document_loading(self):
        """Test that startup event loads documents when docs directory exists."""
        with patch('os.path.exists') as mock_exists, \
             patch('app.rag_system.add_course_folder') as mock_add_folder, \
             patch('builtins.print') as mock_print:
            
            mock_exists.return_value = True
            mock_add_folder.return_value = (3, 150)  # 3 courses, 150 chunks
            
            # Import and trigger startup manually for testing
            from app import startup_event
            import asyncio
            
            asyncio.run(startup_event())
            
            mock_exists.assert_called_once_with("../docs")
            mock_add_folder.assert_called_once_with("../docs", clear_existing=False)
            mock_print.assert_any_call("Loading initial documents...")
            mock_print.assert_any_call("Loaded 3 courses with 150 chunks")
    
    def test_startup_event_no_docs_directory(self):
        """Test startup behavior when docs directory doesn't exist."""
        with patch('os.path.exists') as mock_exists, \
             patch('app.rag_system.add_course_folder') as mock_add_folder, \
             patch('builtins.print') as mock_print:
            
            mock_exists.return_value = False
            
            from app import startup_event
            import asyncio
            
            asyncio.run(startup_event())
            
            mock_exists.assert_called_once_with("../docs")
            mock_add_folder.assert_not_called()
            mock_print.assert_not_called()
    
    def test_startup_event_loading_error(self):
        """Test startup behavior when document loading fails."""
        with patch('os.path.exists') as mock_exists, \
             patch('app.rag_system.add_course_folder') as mock_add_folder, \
             patch('builtins.print') as mock_print:
            
            mock_exists.return_value = True
            mock_add_folder.side_effect = Exception("Failed to load documents")
            
            from app import startup_event
            import asyncio
            
            asyncio.run(startup_event())
            
            mock_print.assert_any_call("Loading initial documents...")
            mock_print.assert_any_call("Error loading documents: Failed to load documents")


@pytest.mark.api
class TestRequestModels:
    """Tests for Pydantic request/response models."""
    
    def test_query_request_validation(self):
        """Test QueryRequest model validation."""
        from app import QueryRequest
        
        # Valid request
        request = QueryRequest(query="What is Python?")
        assert request.query == "What is Python?"
        assert request.session_id is None
        
        # Request with session
        request_with_session = QueryRequest(query="Test", session_id="session123")
        assert request_with_session.session_id == "session123"
    
    def test_source_model_validation(self):
        """Test Source model validation."""
        from app import Source
        
        # Source with URL
        source_with_url = Source(text="Sample text", url="https://example.com")
        assert source_with_url.text == "Sample text"
        assert source_with_url.url == "https://example.com"
        
        # Source without URL
        source_no_url = Source(text="Sample text")
        assert source_no_url.text == "Sample text"
        assert source_no_url.url is None
    
    def test_query_response_validation(self):
        """Test QueryResponse model validation."""
        from app import QueryResponse, Source
        
        sources = [
            Source(text="Source 1", url="https://example.com/1"),
            Source(text="Source 2")
        ]
        
        response = QueryResponse(
            answer="Test answer",
            sources=sources,
            session_id="session123"
        )
        
        assert response.answer == "Test answer"
        assert len(response.sources) == 2
        assert response.session_id == "session123"
    
    def test_course_stats_validation(self):
        """Test CourseStats model validation."""
        from app import CourseStats
        
        stats = CourseStats(
            total_courses=5,
            course_titles=["Course 1", "Course 2", "Course 3"]
        )
        
        assert stats.total_courses == 5
        assert len(stats.course_titles) == 3


@pytest.mark.api
@pytest.mark.slow
class TestEndToEndAPI:
    """End-to-end API tests with more realistic scenarios."""
    
    def test_conversation_flow(self, client):
        """Test a realistic conversation flow through the API."""
        with patch('app.rag_system') as mock_rag:
            # Setup mock for conversation
            mock_rag.session_manager.create_session.return_value = "conv_session_123"
            mock_rag.query.side_effect = [
                ("Python is a programming language.", [{"text": "Python intro", "url": None}]),
                ("Variables store data in Python.", [{"text": "Python variables", "url": None}])
            ]
            
            # First query - creates session
            response1 = client.post(
                "/api/query",
                json={"query": "What is Python?"}
            )
            assert response1.status_code == 200
            session_id = response1.json()["session_id"]
            
            # Follow-up query - uses same session
            response2 = client.post(
                "/api/query", 
                json={
                    "query": "How do variables work?",
                    "session_id": session_id
                }
            )
            assert response2.status_code == 200
            assert response2.json()["session_id"] == session_id
            
            # Verify both queries used RAG system
            assert mock_rag.query.call_count == 2
    
    def test_concurrent_sessions(self, client):
        """Test handling of multiple concurrent sessions."""
        with patch('app.rag_system') as mock_rag:
            mock_rag.session_manager.create_session.side_effect = [
                "session_1", "session_2", "session_3"
            ]
            mock_rag.query.return_value = ("Response", [])
            
            # Create multiple sessions concurrently
            responses = []
            for i in range(3):
                response = client.post(
                    "/api/query",
                    json={"query": f"Question {i}"}
                )
                responses.append(response)
            
            # Verify all succeeded with different sessions
            session_ids = [r.json()["session_id"] for r in responses]
            assert len(set(session_ids)) == 3  # All unique sessions
            assert all(r.status_code == 200 for r in responses)
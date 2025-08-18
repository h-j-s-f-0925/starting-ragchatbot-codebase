"""
Level 4: FastAPI API testing basic examples

This file demonstrates basic API endpoint testing using FastAPI's TestClient.
Perfect for beginners learning API testing with pytest.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional
from unittest.mock import Mock, patch


# =======================================================================
# Example 1: Basic FastAPI app for testing
# =======================================================================

# Pydantic models (same as production app)
class QueryRequest(BaseModel):
    """Request model for queries"""
    query: str
    session_id: Optional[str] = None


class Source(BaseModel):
    """Source information model"""
    text: str
    url: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for queries"""
    answer: str
    sources: List[Source]
    session_id: str


class CourseStats(BaseModel):
    """Course statistics model"""
    total_courses: int
    course_titles: List[str]


# Simple test FastAPI app
def create_test_app():
    """Create a minimal FastAPI app for testing"""
    app = FastAPI(title="Test RAG API")
    
    @app.post("/api/query", response_model=QueryResponse)
    async def test_query_endpoint(request: QueryRequest):
        """Test query endpoint with mock responses"""
        # Mock response based on query content
        if "error" in request.query.lower():
            raise HTTPException(status_code=500, detail="Simulated error")
        
        if not request.query.strip():
            raise HTTPException(status_code=422, detail="Query cannot be empty")
        
        # Generate mock response
        return QueryResponse(
            answer=f"Mock answer for: {request.query}",
            sources=[
                Source(text="Mock source 1", url="https://example.com/1"),
                Source(text="Mock source 2", url=None)
            ],
            session_id=request.session_id or "test_session_123"
        )
    
    @app.get("/api/courses", response_model=CourseStats)
    async def test_courses_endpoint():
        """Test courses endpoint with mock data"""
        return CourseStats(
            total_courses=3,
            course_titles=["Python Basics", "Web Development", "Data Science"]
        )
    
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint"""
        return {"status": "healthy", "service": "RAG API"}
    
    return app


# =======================================================================
# Example 2: Basic fixtures for API testing
# =======================================================================

@pytest.fixture
def test_app():
    """FastAPI app fixture for testing"""
    return create_test_app()


@pytest.fixture
def client(test_app):
    """HTTP test client fixture"""
    return TestClient(test_app)


@pytest.fixture
def sample_queries():
    """Sample query data for testing"""
    return {
        "simple": {"query": "What is Python?"},
        "with_session": {"query": "Tell me about variables", "session_id": "user_123"},
        "empty": {"query": ""},
        "error": {"query": "trigger error"},
        "long": {"query": "This is a very long query " + "word " * 50}
    }


# =======================================================================
# Example 3: Basic API endpoint tests
# =======================================================================

class TestBasicAPIEndpoints:
    """Basic API endpoint testing examples"""
    
    def test_health_check(self, client):
        """Test health check endpoint - simplest possible test"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "RAG API"
    
    def test_query_endpoint_basic_success(self, client, sample_queries):
        """Test successful query request"""
        response = client.post("/api/query", json=sample_queries["simple"])
        
        # Check status code
        assert response.status_code == 200
        
        # Check response structure
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        
        # Check data types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)
        
        # Check content
        assert "Python" in data["answer"]  # Query content reflected in answer
        assert len(data["sources"]) == 2
        assert data["session_id"] == "test_session_123"
    
    def test_query_with_session_id(self, client, sample_queries):
        """Test query with existing session ID"""
        response = client.post("/api/query", json=sample_queries["with_session"])
        
        assert response.status_code == 200
        data = response.json()
        
        # Session ID should be preserved
        assert data["session_id"] == "user_123"
        assert "variables" in data["answer"]
    
    def test_courses_endpoint(self, client):
        """Test courses statistics endpoint"""
        response = client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "total_courses" in data
        assert "course_titles" in data
        
        # Check data
        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3
        assert "Python Basics" in data["course_titles"]


# =======================================================================
# Example 4: Error handling tests
# =======================================================================

class TestAPIErrorHandling:
    """API error handling examples"""
    
    def test_query_empty_request_body(self, client):
        """Test empty request body"""
        response = client.post("/api/query")
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_query_invalid_json(self, client):
        """Test invalid JSON in request"""
        response = client.post(
            "/api/query",
            data="invalid json string",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_query_missing_required_field(self, client):
        """Test missing required query field"""
        response = client.post("/api/query", json={"session_id": "test123"})
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
    
    def test_query_empty_string(self, client, sample_queries):
        """Test empty query string"""
        response = client.post("/api/query", json=sample_queries["empty"])
        
        assert response.status_code == 422
        assert "Query cannot be empty" in response.json()["detail"]
    
    def test_simulated_server_error(self, client, sample_queries):
        """Test server error handling"""
        response = client.post("/api/query", json=sample_queries["error"])
        
        assert response.status_code == 500
        assert "Simulated error" in response.json()["detail"]


# =======================================================================
# Example 5: Response validation tests
# =======================================================================

class TestAPIResponseValidation:
    """Response structure validation examples"""
    
    def test_query_response_structure(self, client, sample_queries):
        """Test that response matches expected Pydantic model"""
        response = client.post("/api/query", json=sample_queries["simple"])
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure matches QueryResponse model
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate sources structure
        for source in data["sources"]:
            assert "text" in source
            assert "url" in source  # Can be None
            assert isinstance(source["text"], str)
            assert source["url"] is None or isinstance(source["url"], str)
    
    def test_courses_response_structure(self, client):
        """Test courses response structure"""
        response = client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate CourseStats model structure
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert data["total_courses"] >= 0
        
        # Validate consistency
        assert len(data["course_titles"]) == data["total_courses"]
        
        # Validate course titles are strings
        for title in data["course_titles"]:
            assert isinstance(title, str)
            assert len(title) > 0


# =======================================================================
# Example 6: Parametrized API tests
# =======================================================================

@pytest.mark.parametrize("query, expected_in_answer", [
    ("Python", "Python"),
    ("variables", "variables"),
    ("functions", "functions"),
    ("machine learning", "machine learning"),
])
def test_query_content_reflection(client, query, expected_in_answer):
    """Test that query content is reflected in answers"""
    response = client.post("/api/query", json={"query": query})
    
    assert response.status_code == 200
    data = response.json()
    assert expected_in_answer.lower() in data["answer"].lower()


@pytest.mark.parametrize("invalid_data", [
    {},  # Empty object
    {"wrong_field": "value"},  # Wrong field name
    {"query": None},  # None value
    {"query": 123},  # Wrong type
])
def test_invalid_request_data(client, invalid_data):
    """Test various invalid request formats"""
    response = client.post("/api/query", json=invalid_data)
    assert response.status_code == 422


# =======================================================================
# Example 7: HTTP methods and headers testing
# =======================================================================

class TestHTTPBasics:
    """HTTP fundamentals testing"""
    
    def test_get_method_not_allowed_on_query(self, client):
        """Test that GET is not allowed on POST endpoint"""
        response = client.get("/api/query")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_content_type_headers(self, client, sample_queries):
        """Test response content type"""
        response = client.post("/api/query", json=sample_queries["simple"])
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_custom_headers_accepted(self, client, sample_queries):
        """Test that custom headers are accepted"""
        headers = {
            "User-Agent": "TestClient/1.0",
            "X-Custom-Header": "test-value"
        }
        
        response = client.post(
            "/api/query", 
            json=sample_queries["simple"],
            headers=headers
        )
        
        assert response.status_code == 200


# =======================================================================
# Running the tests
# =======================================================================

if __name__ == "__main__":
    # You can run this file directly for quick testing
    # But normally you'd run: pytest test_fastapi_basic.py
    
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
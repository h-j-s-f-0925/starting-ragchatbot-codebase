"""
Level 4: Advanced FastAPI testing patterns

This file demonstrates advanced API testing techniques including:
- Complex mocking strategies
- Real app integration with static file handling
- Performance testing
- Session management testing
- Concurrent request testing
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import time
import json


# =======================================================================
# Example 1: Realistic RAG system mocking
# =======================================================================

class MockRAGSystem:
    """Realistic RAG system mock with stateful behavior"""
    
    def __init__(self):
        self.sessions = {}
        self.course_data = {
            "total_courses": 4,
            "course_titles": [
                "Python Programming Fundamentals",
                "Web Development with FastAPI", 
                "Data Science Essentials",
                "Machine Learning Basics"
            ]
        }
        self.call_count = 0
    
    def query(self, query, session_id=None):
        """Mock query with realistic responses"""
        self.call_count += 1
        
        # Create session if not exists
        if session_id and session_id not in self.sessions:
            self.sessions[session_id] = {"history": []}
        
        # Generate response based on query content
        if "python" in query.lower():
            answer = "Python is a high-level, interpreted programming language known for its simplicity and readability."
            sources = [
                {"text": "Python Official Documentation", "url": "https://docs.python.org"},
                {"text": "Python Tutorial - Lesson 1", "url": "https://example.com/python/lesson1"}
            ]
        elif "fastapi" in query.lower():
            answer = "FastAPI is a modern, fast web framework for building APIs with Python 3.6+."
            sources = [
                {"text": "FastAPI Documentation", "url": "https://fastapi.tiangolo.com"},
                {"text": "Web Development Course - Chapter 3", "url": None}
            ]
        elif "error" in query.lower():
            raise Exception("Database connection failed")
        else:
            answer = f"I can help you with information about: {query}"
            sources = [{"text": "General Knowledge Base", "url": None}]
        
        # Store in session history
        if session_id:
            self.sessions[session_id]["history"].append({
                "query": query,
                "answer": answer
            })
        
        return answer, sources
    
    def get_course_analytics(self):
        """Mock course analytics"""
        return self.course_data
    
    def add_course_folder(self, path, clear_existing=False):
        """Mock course loading"""
        return self.course_data["total_courses"], 150  # courses, chunks

    @property
    def session_manager(self):
        """Mock session manager"""
        manager = Mock()
        manager.create_session.return_value = f"session_{len(self.sessions) + 1}"
        return manager


@pytest.fixture
def advanced_mock_rag():
    """Advanced RAG system mock with realistic behavior"""
    return MockRAGSystem()


@pytest.fixture
def app_with_mock_rag(advanced_mock_rag):
    """FastAPI app with advanced RAG system mock"""
    with patch('app.rag_system', advanced_mock_rag):
        # Also patch StaticFiles to avoid filesystem dependencies
        with patch('app.StaticFiles'):
            from app import app
            yield app


@pytest.fixture
def advanced_client(app_with_mock_rag):
    """TestClient with advanced mocking"""
    return TestClient(app_with_mock_rag)


# =======================================================================
# Example 2: Session management testing
# =======================================================================

class TestAdvancedSessionManagement:
    """Advanced session management tests"""
    
    def test_session_creation_and_reuse(self, advanced_client):
        """Test session lifecycle management"""
        # First request creates session
        response1 = advanced_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        session_id = data1["session_id"]
        
        # Second request reuses session
        response2 = advanced_client.post(
            "/api/query", 
            json={
                "query": "Tell me more about functions",
                "session_id": session_id
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["session_id"] == session_id
    
    def test_multiple_concurrent_sessions(self, advanced_client):
        """Test handling multiple concurrent sessions"""
        queries = [
            {"query": "Python basics", "expected_session_id": None},
            {"query": "FastAPI introduction", "expected_session_id": None},
            {"query": "Data science overview", "expected_session_id": None}
        ]
        
        responses = []
        for query_data in queries:
            response = advanced_client.post("/api/query", json=query_data)
            assert response.status_code == 200
            responses.append(response.json())
        
        # All sessions should be different
        session_ids = [r["session_id"] for r in responses]
        assert len(set(session_ids)) == 3, "All sessions should be unique"
    
    def test_session_context_persistence(self, advanced_client, advanced_mock_rag):
        """Test that session context is maintained"""
        # Create session with initial query
        response1 = advanced_client.post(
            "/api/query",
            json={"query": "Tell me about Python"}
        )
        session_id = response1.json()["session_id"]
        
        # Follow-up query using same session
        response2 = advanced_client.post(
            "/api/query",
            json={
                "query": "More details about variables",
                "session_id": session_id
            }
        )
        
        assert response2.status_code == 200
        
        # Verify session was used in mock
        assert session_id in advanced_mock_rag.sessions
        assert len(advanced_mock_rag.sessions[session_id]["history"]) == 2


# =======================================================================
# Example 3: Error scenarios and edge cases
# =======================================================================

class TestAdvancedErrorHandling:
    """Advanced error handling and edge cases"""
    
    def test_rag_system_connection_error(self, advanced_client):
        """Test handling of RAG system connection errors"""
        response = advanced_client.post(
            "/api/query",
            json={"query": "trigger error in system"}
        )
        
        assert response.status_code == 500
        error_data = response.json()
        assert "Database connection failed" in error_data["detail"]
    
    def test_malformed_session_id(self, advanced_client):
        """Test handling of malformed session IDs"""
        malformed_sessions = [
            "",  # Empty string
            " " * 10,  # Whitespace only
            "invalid-session-format",  # Invalid format
            "session_" + "x" * 1000,  # Very long session ID
        ]
        
        for session_id in malformed_sessions:
            response = advanced_client.post(
                "/api/query",
                json={
                    "query": "Test with malformed session",
                    "session_id": session_id
                }
            )
            # Should either accept it or return validation error
            assert response.status_code in [200, 422]
    
    def test_very_long_query(self, advanced_client):
        """Test handling of extremely long queries"""
        long_query = "This is a very long query. " * 1000  # ~25,000 characters
        
        response = advanced_client.post(
            "/api/query",
            json={"query": long_query}
        )
        
        # Should handle gracefully (accept or return validation error)
        assert response.status_code in [200, 422, 413]  # 413 = Payload Too Large
    
    def test_special_characters_in_query(self, advanced_client):
        """Test queries with special characters and unicode"""
        special_queries = [
            "日本語での質問です",  # Japanese
            "Español: ¿Cómo funciona Python?",  # Spanish with accents
            "Query with emojis: 🐍 Python 🚀",  # Emojis
            "SQL injection attempt: '; DROP TABLE users; --",  # Potential injection
            "XSS attempt: <script>alert('test')</script>",  # XSS attempt
        ]
        
        for query in special_queries:
            response = advanced_client.post(
                "/api/query",
                json={"query": query}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response is properly escaped/handled
            assert isinstance(data["answer"], str)
            assert len(data["answer"]) > 0


# =======================================================================
# Example 4: Performance and load testing
# =======================================================================

class TestAPIPerformance:
    """API performance and load testing"""
    
    def test_response_time_under_load(self, advanced_client):
        """Test response times remain reasonable under load"""
        query = {"query": "Performance test query"}
        response_times = []
        
        # Make 10 sequential requests
        for _ in range(10):
            start_time = time.time()
            response = advanced_client.post("/api/query", json=query)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Verify reasonable response times
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        assert avg_time < 1.0, f"Average response time too high: {avg_time:.3f}s"
        assert max_time < 2.0, f"Max response time too high: {max_time:.3f}s"
    
    @pytest.mark.slow
    def test_concurrent_requests(self, advanced_client):
        """Test handling of concurrent requests"""
        def make_request(query_id):
            """Make a single request with unique query"""
            response = advanced_client.post(
                "/api/query", 
                json={"query": f"Concurrent query {query_id}"}
            )
            return response.status_code, response.json()
        
        # Run 5 concurrent requests using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        for status_code, data in results:
            assert status_code == 200
            assert "answer" in data
            assert "session_id" in data
        
        # All session IDs should be different
        session_ids = [data["session_id"] for _, data in results]
        assert len(set(session_ids)) == 5, "All sessions should be unique"
    
    def test_memory_efficiency(self, advanced_client, advanced_mock_rag):
        """Test memory usage doesn't grow excessively"""
        initial_sessions = len(advanced_mock_rag.sessions)
        
        # Make many requests to potentially cause memory issues
        for i in range(50):
            response = advanced_client.post(
                "/api/query",
                json={"query": f"Memory test query {i}"}
            )
            assert response.status_code == 200
        
        # Verify reasonable session growth
        final_sessions = len(advanced_mock_rag.sessions)
        session_growth = final_sessions - initial_sessions
        
        # Should not create excessive sessions
        assert session_growth <= 50, f"Too many sessions created: {session_growth}"


# =======================================================================
# Example 5: Complex workflow testing
# =======================================================================

class TestComplexWorkflows:
    """Complex user workflow simulation"""
    
    def test_complete_learning_session(self, advanced_client):
        """Simulate a complete user learning session"""
        # 1. Get course overview
        courses_response = advanced_client.get("/api/courses")
        assert courses_response.status_code == 200
        courses_data = courses_response.json()
        
        # 2. Ask initial question about first course
        first_course = courses_data["course_titles"][0]
        initial_query = f"Tell me about {first_course}"
        
        response1 = advanced_client.post(
            "/api/query",
            json={"query": initial_query}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # 3. Follow up with related questions
        followup_queries = [
            "Can you give me more details?",
            "What are the prerequisites?", 
            "How long does it take to complete?",
            "Are there any practical exercises?"
        ]
        
        for query in followup_queries:
            response = advanced_client.post(
                "/api/query",
                json={"query": query, "session_id": session_id}
            )
            assert response.status_code == 200
            assert response.json()["session_id"] == session_id
        
        # 4. Switch to another course topic
        second_course = courses_data["course_titles"][1]
        response_final = advanced_client.post(
            "/api/query",
            json={
                "query": f"Now tell me about {second_course}",
                "session_id": session_id
            }
        )
        assert response_final.status_code == 200
        assert "FastAPI" in response_final.json()["answer"]
    
    def test_error_recovery_workflow(self, advanced_client):
        """Test user workflow with error recovery"""
        # 1. Normal request
        response1 = advanced_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # 2. Request that causes error
        error_response = advanced_client.post(
            "/api/query",
            json={"query": "trigger error", "session_id": session_id}
        )
        assert error_response.status_code == 500
        
        # 3. Recovery with new request
        recovery_response = advanced_client.post(
            "/api/query",
            json={"query": "Tell me about variables", "session_id": session_id}
        )
        assert recovery_response.status_code == 200
        assert recovery_response.json()["session_id"] == session_id


# =======================================================================
# Example 6: Advanced mocking patterns
# =======================================================================

class TestAdvancedMocking:
    """Advanced mocking and test isolation patterns"""
    
    @pytest.fixture
    def isolated_rag_mock(self):
        """Completely isolated RAG mock for specific tests"""
        mock = Mock()
        mock.query.side_effect = lambda q, s: (
            f"Isolated response to: {q}",
            [{"text": "Isolated source", "url": None}]
        )
        mock.session_manager.create_session.return_value = "isolated_session"
        mock.get_course_analytics.return_value = {
            "total_courses": 1,
            "course_titles": ["Isolated Test Course"]
        }
        return mock
    
    def test_with_isolated_mock(self, isolated_rag_mock):
        """Test using completely isolated mock"""
        with patch('app.rag_system', isolated_rag_mock):
            with patch('app.StaticFiles'):
                from app import app
                client = TestClient(app)
                
                response = client.post(
                    "/api/query",
                    json={"query": "Isolated test"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "Isolated response" in data["answer"]
                assert data["session_id"] == "isolated_session"
    
    def test_mock_behavior_verification(self, advanced_client, advanced_mock_rag):
        """Test that verifies mock interactions"""
        # Make several requests
        queries = ["Query 1", "Query 2", "Query 3"]
        
        for query in queries:
            response = advanced_client.post(
                "/api/query",
                json={"query": query}
            )
            assert response.status_code == 200
        
        # Verify mock was called correct number of times
        assert advanced_mock_rag.call_count == 3
        
        # Verify course analytics was called when needed
        courses_response = advanced_client.get("/api/courses")
        assert courses_response.status_code == 200
        
        # Mock should track all interactions
        assert len(advanced_mock_rag.sessions) >= 3


# =======================================================================
# Running the tests
# =======================================================================

if __name__ == "__main__":
    # Run with verbose output and show durations
    import sys
    sys.exit(pytest.main([__file__, "-v", "--durations=10"]))
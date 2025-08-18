import pytest

from config import config
from rag_system import RAGSystem


@pytest.mark.e2e
@pytest.mark.slow
class TestLiveSystem:
    """Test the actual live system to identify 'query failed' issues"""

    def test_real_query_with_api_key_check(self):
        """Test a real query to identify where 'query failed' comes from"""
        
        # First check if we have a real API key
        api_key = config.ANTHROPIC_API_KEY
        if not api_key or api_key == "" or api_key.startswith("your_key"):
            pytest.skip("No valid ANTHROPIC_API_KEY found - this would cause query failures")
        
        print(f"Using API key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
        
        # Create RAG system
        rag_system = RAGSystem(config)
        
        try:
            # Test a simple query
            response, sources = rag_system.query("What is Python programming?")
            
            print(f"Response: {response}")
            print(f"Sources count: {len(sources)}")
            print(f"Sources: {sources}")
            
            # Check for failure indicators
            if response.lower().strip() == "query failed":
                pytest.fail("Response is exactly 'query failed' - this is the bug we're looking for!")
            
            if "query failed" in response.lower():
                pytest.fail(f"Response contains 'query failed': {response}")
            
            if "error" in response.lower() and "search error" in response.lower():
                pytest.fail(f"Response indicates search error: {response}")
                
            # Should have a meaningful response
            assert len(response) > 10, f"Response too short: {response}"
            
        except Exception as e:
            pytest.fail(f"Query execution failed with exception: {e}")

    def test_anthropic_api_connectivity(self):
        """Test direct Anthropic API connectivity"""
        from ai_generator import AIGenerator
        
        api_key = config.ANTHROPIC_API_KEY
        if not api_key or api_key == "" or api_key.startswith("your_key"):
            pytest.skip("No valid ANTHROPIC_API_KEY found")
        
        try:
            ai_gen = AIGenerator(api_key, config.ANTHROPIC_MODEL)
            
            # Test a simple request without tools
            response = ai_gen.generate_response("What is 2+2?")
            
            print(f"Simple API response: {response}")
            
            assert "4" in response or "four" in response.lower(), f"Unexpected API response: {response}"
            
        except Exception as e:
            pytest.fail(f"Direct Anthropic API call failed: {e}")

    def test_tool_execution_in_live_system(self):
        """Test tool execution in the live system"""
        
        api_key = config.ANTHROPIC_API_KEY
        if not api_key or api_key == "" or api_key.startswith("your_key"):
            pytest.skip("No valid ANTHROPIC_API_KEY found")
        
        rag_system = RAGSystem(config)
        
        try:
            # Test a query that should trigger tool use
            response, sources = rag_system.query("Tell me about MCP in the course materials")
            
            print(f"Tool-triggered response: {response}")
            print(f"Tool-triggered sources: {sources}")
            
            # Check if tools were actually used (sources should be populated)
            if len(sources) == 0:
                print("WARNING: No sources returned - tools may not have been used")
            
            # Response should mention MCP content
            if "MCP" not in response and len(sources) == 0:
                pytest.fail("Query about MCP didn't return MCP-related content or sources")
                
        except Exception as e:
            pytest.fail(f"Tool execution test failed: {e}")

    def test_error_handling_with_invalid_query(self):
        """Test how the system handles errors"""
        
        api_key = config.ANTHROPIC_API_KEY
        if not api_key or api_key == "" or api_key.startswith("your_key"):
            pytest.skip("No valid ANTHROPIC_API_KEY found")
        
        rag_system = RAGSystem(config)
        
        try:
            # Test with an empty query
            response, sources = rag_system.query("")
            
            print(f"Empty query response: {response}")
            
            # Should not be "query failed"
            assert response.lower().strip() != "query failed", "Empty query returned 'query failed'"
            
        except Exception as e:
            print(f"Empty query caused exception: {e}")
            # This might be expected, but shouldn't result in "query failed"
            assert "query failed" not in str(e).lower()

    def test_session_handling(self):
        """Test session-based queries"""
        
        api_key = config.ANTHROPIC_API_KEY
        if not api_key or api_key == "" or api_key.startswith("your_key"):
            pytest.skip("No valid ANTHROPIC_API_KEY found")
        
        rag_system = RAGSystem(config)
        
        try:
            # Create a session and test multiple queries
            session_id = rag_system.session_manager.create_session()
            
            # First query
            response1, sources1 = rag_system.query("What is Python?", session_id=session_id)
            print(f"First query response: {response1}")
            
            # Second query with context
            response2, sources2 = rag_system.query("Tell me more about it", session_id=session_id)
            print(f"Second query response: {response2}")
            
            # Neither should be "query failed"
            assert response1.lower().strip() != "query failed"
            assert response2.lower().strip() != "query failed"
            
        except Exception as e:
            pytest.fail(f"Session handling test failed: {e}")
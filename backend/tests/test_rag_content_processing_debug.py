import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system import RAGSystem
from config import config


class TestRAGContentProcessingDebug:
    """Debug tests for RAG system content question processing to identify 'query failed' issues"""

    @pytest.fixture
    def real_rag_system(self):
        """Create RAG system with real components (except AI to avoid API calls)"""
        return RAGSystem(config)

    @pytest.fixture
    def mock_ai_rag_system(self, real_rag_system):
        """RAG system with mocked AI generator to avoid API costs"""
        # Mock just the AI generator while keeping other components real
        with patch.object(real_rag_system, 'ai_generator') as mock_ai:
            mock_ai.generate_response.return_value = "Mocked AI response with search results"
            yield real_rag_system, mock_ai

    def test_rag_system_initialization_components(self, real_rag_system):
        """Debug test: Verify all RAG system components are properly initialized"""
        print(f"\n[DEBUG] RAG system components:")
        print(f"  - Vector store: {real_rag_system.vector_store}")
        print(f"  - AI generator: {real_rag_system.ai_generator}")
        print(f"  - Session manager: {real_rag_system.session_manager}")
        print(f"  - Tool manager: {real_rag_system.tool_manager}")
        print(f"  - Search tool: {real_rag_system.search_tool}")
        print(f"  - Overview tool: {real_rag_system.overview_tool}")
        
        # Verify all components exist
        assert real_rag_system.vector_store is not None, "Vector store not initialized"
        assert real_rag_system.ai_generator is not None, "AI generator not initialized"
        assert real_rag_system.session_manager is not None, "Session manager not initialized"
        assert real_rag_system.tool_manager is not None, "Tool manager not initialized"
        assert real_rag_system.search_tool is not None, "Search tool not initialized"
        assert real_rag_system.overview_tool is not None, "Overview tool not initialized"
        
        # Verify tool manager has tools registered
        tool_names = list(real_rag_system.tool_manager.tools.keys())
        print(f"  - Registered tools: {tool_names}")
        assert len(tool_names) >= 1, f"Expected at least 1 tool, got {len(tool_names)}"
        assert "search_course_content" in tool_names, "search_course_content tool not registered"

    def test_rag_system_data_availability(self, real_rag_system):
        """Debug test: Check if RAG system has course data available for querying"""
        # Check course count
        analytics = real_rag_system.get_course_analytics()
        course_count = analytics["total_courses"]
        course_titles = analytics["course_titles"]
        
        print(f"\n[DEBUG] Course analytics:")
        print(f"  - Total courses: {course_count}")
        print(f"  - Course titles: {course_titles}")
        
        if course_count == 0:
            pytest.fail("RAG system has no course data - this will cause 'No relevant content found' for all queries")
        
        assert course_count > 0, f"Expected > 0 courses, got {course_count}"
        assert len(course_titles) > 0, f"Expected course titles, got empty list"

    def test_content_query_processing_workflow(self, mock_ai_rag_system):
        """Debug test: Test complete content query processing workflow"""
        rag_system, mock_ai = mock_ai_rag_system
        
        # Test various content-related queries
        content_queries = [
            "What is Python programming?",
            "Explain machine learning concepts",
            "How do I start with programming?",
            "Tell me about the course content",
            "What topics are covered in lesson 1?"
        ]
        
        for query in content_queries:
            print(f"\n[DEBUG] Testing content query: '{query}'")
            
            try:
                response, sources = rag_system.query(query)
                
                print(f"[DEBUG] Response type: {type(response)}")
                print(f"[DEBUG] Response length: {len(response) if response else 0}")
                print(f"[DEBUG] Response preview: {response[:100] if response else 'None'}...")
                print(f"[DEBUG] Sources count: {len(sources) if sources else 0}")
                print(f"[DEBUG] Sources: {sources}")
                
                # Check for failure indicators
                assert response is not None, f"Query returned None response for: {query}"
                assert response != "", f"Query returned empty response for: {query}"
                assert "query failed" not in response.lower(), f"Query failed for: {query} - Response: {response}"
                
                # Verify AI generator was called correctly
                mock_ai.generate_response.assert_called()
                last_call = mock_ai.generate_response.call_args
                
                print(f"[DEBUG] AI generator called with:")
                print(f"  - Query: {last_call[1]['query']}")
                print(f"  - Tools provided: {last_call[1].get('tools') is not None}")
                print(f"  - Tool manager provided: {last_call[1].get('tool_manager') is not None}")
                
                # Verify proper parameters were passed
                assert 'query' in last_call[1], "Query not passed to AI generator"
                assert 'tools' in last_call[1], "Tools not passed to AI generator"
                assert 'tool_manager' in last_call[1], "Tool manager not passed to AI generator"
                assert last_call[1]['tools'] is not None, "Tools list is None"
                assert last_call[1]['tool_manager'] is not None, "Tool manager is None"
                
                # Reset mock for next iteration
                mock_ai.reset_mock()
                
            except Exception as e:
                pytest.fail(f"Content query processing failed for '{query}': {str(e)}")

    def test_content_query_with_session_management(self, mock_ai_rag_system):
        """Debug test: Test content query processing with session management"""
        rag_system, mock_ai = mock_ai_rag_system
        
        session_id = "test_session_123"
        
        # First query to establish session
        response1, sources1 = rag_system.query("What is programming?", session_id=session_id)
        
        print(f"\n[DEBUG] First query response: {response1[:100]}...")
        print(f"[DEBUG] First query sources: {len(sources1) if sources1 else 0}")
        
        # Second query in same session (should have conversation history)
        response2, sources2 = rag_system.query("Can you explain it in more detail?", session_id=session_id)
        
        print(f"\n[DEBUG] Second query response: {response2[:100]}...")
        print(f"[DEBUG] Second query sources: {len(sources2) if sources2 else 0}")
        
        # Verify both responses are valid
        assert "query failed" not in response1.lower(), f"First query failed: {response1}"
        assert "query failed" not in response2.lower(), f"Second query failed: {response2}"
        
        # Verify AI generator was called with conversation history for second query
        assert mock_ai.generate_response.call_count >= 2, "AI generator should be called for both queries"
        
        # Check second call had conversation history
        second_call = mock_ai.generate_response.call_args
        conversation_history = second_call[1].get('conversation_history')
        
        print(f"[DEBUG] Conversation history passed: {conversation_history is not None}")
        if conversation_history:
            print(f"[DEBUG] History preview: {conversation_history[:200]}...")

    def test_edge_case_queries(self, mock_ai_rag_system):
        """Debug test: Test edge case queries that might trigger failures"""
        rag_system, mock_ai = mock_ai_rag_system
        
        edge_cases = [
            "",  # Empty query
            "   ",  # Whitespace only
            "?",  # Single character
            "a" * 1000,  # Very long query
            "nonexistent_topic_xyz_123_abcdef",  # Definitely nonexistent topic
            "What is the meaning of life?",  # Non-course question
            "How do I delete all files?",  # Potentially harmful query
        ]
        
        for query in edge_cases:
            print(f"\n[DEBUG] Testing edge case: '{query[:50]}{'...' if len(query) > 50 else ''}'")
            
            try:
                response, sources = rag_system.query(query)
                
                print(f"[DEBUG] Edge case response: {response[:100] if response else 'None'}...")
                
                # Should not crash or return "query failed"
                assert response is not None, f"Edge case returned None: {query}"
                assert "query failed" not in response.lower(), f"Edge case returned 'query failed': {query}"
                
            except Exception as e:
                pytest.fail(f"Edge case query failed with exception '{query}': {str(e)}")

    def test_tool_execution_in_real_context(self, real_rag_system):
        """Debug test: Test tool execution without AI calls (direct tool testing)"""
        # Test direct tool execution through tool manager
        tool_manager = real_rag_system.tool_manager
        
        test_queries = [
            "Python programming",
            "machine learning",
            "introduction course"
        ]
        
        for query in test_queries:
            print(f"\n[DEBUG] Direct tool test for: '{query}'")
            
            try:
                result = tool_manager.execute_tool("search_course_content", query=query)
                
                print(f"[DEBUG] Tool result type: {type(result)}")
                print(f"[DEBUG] Tool result length: {len(result) if result else 0}")
                print(f"[DEBUG] Tool result preview: {result[:200] if result else 'None'}...")
                
                assert result is not None, f"Tool returned None for query: {query}"
                assert isinstance(result, str), f"Tool should return string, got {type(result)}"
                assert "query failed" not in result.lower(), f"Tool returned 'query failed' for: {query}"
                
                # Check if sources were tracked
                sources = tool_manager.get_last_sources()
                print(f"[DEBUG] Sources tracked: {len(sources) if sources else 0}")
                
            except Exception as e:
                pytest.fail(f"Direct tool execution failed for '{query}': {str(e)}")

    def test_configuration_values(self):
        """Debug test: Verify configuration values that might cause failures"""
        print(f"\n[DEBUG] Configuration values:")
        print(f"  - ANTHROPIC_API_KEY length: {len(config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else 0}")
        print(f"  - ANTHROPIC_MODEL: {config.ANTHROPIC_MODEL}")
        print(f"  - CHROMA_PATH: {config.CHROMA_PATH}")
        print(f"  - EMBEDDING_MODEL: {config.EMBEDDING_MODEL}")
        print(f"  - MAX_RESULTS: {config.MAX_RESULTS}")
        print(f"  - CHUNK_SIZE: {config.CHUNK_SIZE}")
        print(f"  - CHUNK_OVERLAP: {config.CHUNK_OVERLAP}")
        
        # Check critical configuration
        assert config.ANTHROPIC_API_KEY != "", "ANTHROPIC_API_KEY is empty"
        assert config.ANTHROPIC_API_KEY is not None, "ANTHROPIC_API_KEY is None"
        assert not config.ANTHROPIC_API_KEY.startswith("your_key_here"), "ANTHROPIC_API_KEY is placeholder"
        assert config.ANTHROPIC_MODEL != "", "ANTHROPIC_MODEL is empty"
        assert config.MAX_RESULTS > 0, f"MAX_RESULTS should be > 0, got {config.MAX_RESULTS}"

    def test_error_propagation_through_system(self, real_rag_system):
        """Debug test: Test how errors propagate through the system"""
        # Mock various error conditions and see how they're handled
        
        # Test with corrupted tool manager
        original_tool_manager = real_rag_system.tool_manager
        
        try:
            # Replace with mock that simulates tool failure
            mock_tool_manager = Mock()
            mock_tool_manager.get_tool_definitions.return_value = []
            mock_tool_manager.get_last_sources.return_value = []
            mock_tool_manager.reset_sources.return_value = None
            mock_tool_manager.execute_tool.return_value = "Tool execution error: mock failure"
            
            real_rag_system.tool_manager = mock_tool_manager
            
            # Mock AI to actually use tools
            with patch.object(real_rag_system.ai_generator, 'generate_response') as mock_ai:
                # Simulate AI trying to use tools but getting error
                mock_ai.return_value = "I encountered an error while searching."
                
                response, sources = real_rag_system.query("Test query with tool error")
                
                print(f"\n[DEBUG] Response with tool error: {response}")
                print(f"[DEBUG] Sources with tool error: {sources}")
                
                # Should not crash or return "query failed"
                assert response is not None, "System returned None with tool error"
                assert "query failed" not in response.lower(), f"System returned 'query failed' with tool error: {response}"
                
        finally:
            # Restore original tool manager
            real_rag_system.tool_manager = original_tool_manager
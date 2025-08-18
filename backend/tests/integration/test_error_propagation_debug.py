import pytest
import sys
import os
import traceback
import json
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system import RAGSystem
from ai_generator import AIGenerator
from search_tools import ToolManager
from vector_store import VectorStore
from config import config
import anthropic


class TestErrorPropagationDebug:
    """Test error propagation through the entire system stack"""

    @pytest.fixture
    def rag_system(self):
        """Create a real RAG system for testing"""
        return RAGSystem(config)

    def test_end_to_end_failing_query(self, rag_system):
        """Test the exact failing query end-to-end through RAG system"""
        query = "MCPコースのレッスン5と同じトピックを扱っている他のコースはありますか？"

        print(f"\n=== Testing end-to-end failing query ===")
        print(f"Query: {query}")

        try:
            response, sources = rag_system.query(query)

            print(f"SUCCESS - Response received:")
            print(f"  Response length: {len(response)}")
            print(f"  Response preview: {response[:200]}...")
            print(f"  Sources count: {len(sources)}")
            print(f"  Sources: {sources}")

            assert response is not None
            assert len(response) > 0

        except Exception as e:
            print(f"FAILED - Exception in RAG system:")
            print(f"  Exception type: {type(e).__name__}")
            print(f"  Exception message: {str(e)}")
            print(f"  Full traceback:")
            traceback.print_exc()
            raise

    def test_anthropic_api_connectivity(self):
        """Test if Anthropic API is accessible"""
        print(f"\n=== Testing Anthropic API connectivity ===")

        if not config.ANTHROPIC_API_KEY:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        try:
            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

            # Test simple API call
            response = client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=50,
                temperature=0,
                messages=[
                    {"role": "user", "content": "Hello, respond with 'API working'"}
                ],
            )

            print(f"API Response: {response.content[0].text}")
            assert (
                "API working" in response.content[0].text
                or "working" in response.content[0].text.lower()
            )

        except Exception as e:
            print(f"Anthropic API error: {type(e).__name__}: {str(e)}")
            if "401" in str(e) or "authentication" in str(e).lower():
                print("Authentication error - check API key")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                print("Rate limit error - API usage quota")
            elif "timeout" in str(e).lower():
                print("Timeout error - network connectivity")
            raise

    def test_tool_execution_error_handling(self, rag_system):
        """Test how tool execution errors are handled"""
        print(f"\n=== Testing tool execution error handling ===")

        # Mock the tool manager to simulate errors
        original_tool_manager = rag_system.tool_manager

        try:
            # Create mock tool manager that fails
            mock_tool_manager = Mock()
            mock_tool_manager.get_tool_definitions.return_value = [
                {
                    "name": "get_course_overview",
                    "description": "Get course overview",
                    "input_schema": {
                        "type": "object",
                        "properties": {"course_title": {"type": "string"}},
                        "required": ["course_title"],
                    },
                }
            ]

            # Simulate tool execution failure
            mock_tool_manager.execute_tool.side_effect = Exception(
                "Tool execution failed"
            )
            mock_tool_manager.get_last_sources.return_value = []
            mock_tool_manager.reset_sources.return_value = None

            # Replace the tool manager
            rag_system.tool_manager = mock_tool_manager

            query = (
                "MCPコースのレッスン5と同じトピックを扱っている他のコースはありますか？"
            )

            response, sources = rag_system.query(query)

            print(f"Response with tool error: {response[:200]}...")
            print(f"Sources: {sources}")

            # The system should handle the error gracefully
            assert response is not None
            assert len(response) > 0

        except Exception as e:
            print(f"Tool error handling failed: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise
        finally:
            # Restore original tool manager
            rag_system.tool_manager = original_tool_manager

    def test_vector_store_error_handling(self):
        """Test vector store error scenarios"""
        print(f"\n=== Testing vector store error handling ===")

        # Test with invalid path
        try:
            invalid_vector_store = VectorStore(
                "/invalid/path", config.EMBEDDING_MODEL, config.MAX_RESULTS
            )
            print("Vector store created with invalid path")
        except Exception as e:
            print(f"Vector store creation error: {type(e).__name__}: {str(e)}")

        # Test search on empty/invalid database
        try:
            vector_store = VectorStore(
                config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS
            )

            # Test search that should not fail catastrophically
            results = vector_store.search(
                "nonexistent content", course_name="nonexistent course"
            )
            print(
                f"Search on nonexistent content: Error={results.error}, Documents={len(results.documents)}"
            )

            # Test course name resolution that should fail gracefully
            resolved = vector_store._resolve_course_name(
                "completely_nonexistent_course_name"
            )
            print(f"Nonexistent course resolution: {resolved}")

        except Exception as e:
            print(f"Vector store operation error: {type(e).__name__}: {str(e)}")
            traceback.print_exc()

    def test_ai_generator_error_scenarios(self):
        """Test AI generator with various error scenarios"""
        print(f"\n=== Testing AI generator error scenarios ===")

        if not config.ANTHROPIC_API_KEY:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)

        # Test 1: Invalid tool manager
        print("Test 1: Invalid tool manager")
        try:
            invalid_tool_manager = Mock()
            invalid_tool_manager.get_tool_definitions.return_value = [
                {"invalid": "tool_def"}
            ]
            invalid_tool_manager.execute_tool.side_effect = Exception("Tool failed")

            response = ai_generator.generate_response(
                "test query",
                tools=invalid_tool_manager.get_tool_definitions(),
                tool_manager=invalid_tool_manager,
            )
            print(f"Response with invalid tool manager: {response[:100]}...")
        except Exception as e:
            print(f"Invalid tool manager error: {type(e).__name__}: {str(e)}")

        # Test 2: Very long query
        print("Test 2: Very long query")
        try:
            long_query = "長い質問 " * 1000  # Very long Japanese query
            response = ai_generator.generate_response(long_query)
            print(f"Long query response length: {len(response)}")
        except Exception as e:
            print(f"Long query error: {type(e).__name__}: {str(e)}")

        # Test 3: Empty/None inputs
        print("Test 3: Empty/None inputs")
        try:
            response = ai_generator.generate_response("")
            print(f"Empty query response: {response[:100]}...")
        except Exception as e:
            print(f"Empty query error: {type(e).__name__}: {str(e)}")

    def test_session_management_errors(self, rag_system):
        """Test session management error scenarios"""
        print(f"\n=== Testing session management errors ===")

        # Test with invalid session ID
        try:
            response, sources = rag_system.query(
                "test query", session_id="invalid_session_id_that_does_not_exist"
            )
            print(f"Invalid session ID handled: {response[:100]}...")
        except Exception as e:
            print(f"Invalid session error: {type(e).__name__}: {str(e)}")

        # Test with extremely long conversation history
        try:
            session_id = rag_system.session_manager.create_session()

            # Add many exchanges to create long history
            for i in range(20):
                rag_system.session_manager.add_exchange(
                    session_id,
                    f"Question {i}: " + "long question " * 50,
                    f"Answer {i}: " + "long answer " * 50,
                )

            response, sources = rag_system.query(
                "Final question", session_id=session_id
            )
            print(f"Long history session handled: {response[:100]}...")

        except Exception as e:
            print(f"Long history error: {type(e).__name__}: {str(e)}")

    def test_http_error_simulation(self):
        """Simulate HTTP errors that would cause 'Query failed' in frontend"""
        print(f"\n=== Testing HTTP error simulation ===")

        # Test various exception types that could cause HTTP 500
        error_scenarios = [
            ("ValueError", ValueError("Invalid input parameter")),
            ("KeyError", KeyError("Missing required key")),
            ("AttributeError", AttributeError("Object has no attribute")),
            ("TypeError", TypeError("Invalid type")),
            ("RuntimeError", RuntimeError("Runtime failure")),
            ("Exception", Exception("Generic exception")),
        ]

        for error_name, error_obj in error_scenarios:
            print(f"\nTesting {error_name} scenario:")

            # Create a RAG system that will fail
            with patch("rag_system.RAGSystem.query") as mock_query:
                mock_query.side_effect = error_obj

                try:
                    rag_system = RAGSystem(config)
                    response, sources = rag_system.query("test")
                    print(f"Unexpected success: {response}")
                except Exception as e:
                    print(f"  Exception caught: {type(e).__name__}: {str(e)}")
                    print(f"  This would cause HTTP 500 -> 'Query failed' in frontend")

    def test_anthropic_specific_errors(self):
        """Test Anthropic-specific error scenarios"""
        print(f"\n=== Testing Anthropic-specific errors ===")

        if not config.ANTHROPIC_API_KEY:
            pytest.skip("ANTHROPIC_API_KEY not configured")

        ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)

        # Test with malformed tool definitions
        print("Testing malformed tool definitions:")
        try:
            malformed_tools = [
                {
                    "name": "invalid_tool",
                    "description": "Test tool",
                    # Missing input_schema
                }
            ]

            mock_tool_manager = Mock()
            mock_tool_manager.execute_tool.return_value = "result"

            response = ai_generator.generate_response(
                "test query", tools=malformed_tools, tool_manager=mock_tool_manager
            )
            print(f"Malformed tools response: {response[:100]}...")

        except Exception as e:
            print(f"Malformed tools error: {type(e).__name__}: {str(e)}")
            if "tool" in str(e).lower():
                print(
                    "  This is likely a tool-related error that could cause Query failed"
                )

    def test_full_stack_error_trace(self, rag_system):
        """Test full stack trace for the failing query"""
        print(f"\n=== Testing full stack error trace ===")

        query = "MCPコースのレッスン5と同じトピックを扱っている他のコースはありますか？"

        # Enable detailed error tracking
        import logging

        logging.basicConfig(level=logging.DEBUG)

        try:
            print("Step 1: Starting RAG query...")
            response, sources = rag_system.query(query)
            print("Step 2: RAG query completed successfully")
            print(f"Response: {response[:200]}...")

        except Exception as e:
            print(f"ERROR at step: RAG query execution")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print(f"Exception args: {e.args}")

            # Get the full traceback
            tb_lines = traceback.format_exc().split("\n")
            print("Full traceback:")
            for i, line in enumerate(tb_lines):
                print(f"  {i:2d}: {line}")

            # Identify which component failed
            if "ai_generator" in str(e) or "anthropic" in str(e).lower():
                print("IDENTIFIED: AI Generator / Anthropic API issue")
            elif "vector_store" in str(e) or "chroma" in str(e).lower():
                print("IDENTIFIED: Vector Store / ChromaDB issue")
            elif "search_tools" in str(e) or "tool" in str(e).lower():
                print("IDENTIFIED: Search Tools issue")
            elif "rag_system" in str(e):
                print("IDENTIFIED: RAG System orchestration issue")
            else:
                print("IDENTIFIED: Unknown component issue")

            raise


if __name__ == "__main__":
    # Allow running individual tests for debugging
    pytest.main([__file__, "-v", "-s"])

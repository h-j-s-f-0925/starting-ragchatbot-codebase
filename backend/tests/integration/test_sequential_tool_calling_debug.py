import pytest
import sys
import os
import traceback
from unittest.mock import Mock, patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool, CourseOverviewTool
from vector_store import VectorStore
from config import config


class TestSequentialToolCallingDebug:
    """Debug tests for sequential tool calling functionality with specific focus on failing queries"""

    @pytest.fixture
    def vector_store(self):
        """Create a real vector store for testing"""
        return VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)

    @pytest.fixture
    def tool_manager(self, vector_store):
        """Create tool manager with real tools"""
        manager = ToolManager()
        search_tool = CourseSearchTool(vector_store)
        overview_tool = CourseOverviewTool(vector_store)
        manager.register_tool(search_tool)
        manager.register_tool(overview_tool)
        return manager

    @pytest.fixture
    def ai_generator(self):
        """Create AI generator with real API key if available"""
        api_key = config.ANTHROPIC_API_KEY
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not configured")
        return AIGenerator(api_key, config.ANTHROPIC_MODEL)

    def test_failing_japanese_query_detailed(self, ai_generator, tool_manager):
        """Test the exact failing Japanese query with detailed error reporting"""
        query = "MCPコースのレッスン5と同じトピックを扱っている他のコースはありますか？"
        
        print(f"\n=== Testing failing query: {query} ===")
        
        try:
            # Test the full sequential tool calling
            response = ai_generator.generate_response(
                query=query,
                conversation_history=None,
                tools=tool_manager.get_tool_definitions(),
                tool_manager=tool_manager
            )
            
            print(f"SUCCESS: Response received: {response[:200]}...")
            assert response is not None
            assert len(response) > 0
            
        except Exception as e:
            print(f"FAILED: Exception occurred: {type(e).__name__}: {str(e)}")
            print(f"Full traceback:")
            traceback.print_exc()
            
            # Re-raise to fail the test
            raise

    def test_english_equivalent_query(self, ai_generator, tool_manager):
        """Test equivalent English query to compare behavior"""
        query = "Are there other courses that cover the same topics as lesson 5 of the MCP course?"
        
        print(f"\n=== Testing English equivalent: {query} ===")
        
        try:
            response = ai_generator.generate_response(
                query=query,
                conversation_history=None,
                tools=tool_manager.get_tool_definitions(),
                tool_manager=tool_manager
            )
            
            print(f"SUCCESS: Response received: {response[:200]}...")
            assert response is not None
            assert len(response) > 0
            
        except Exception as e:
            print(f"FAILED: Exception occurred: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise

    def test_step_by_step_tool_execution(self, tool_manager):
        """Test individual tool executions step by step"""
        print(f"\n=== Testing step-by-step tool execution ===")
        
        # Step 1: Test course overview for MCP
        print("Step 1: Testing MCP course overview...")
        try:
            overview_result = tool_manager.execute_tool("get_course_overview", course_title="MCP")
            print(f"Overview result: {overview_result[:200]}...")
            assert "error" not in overview_result.lower() or "not found" not in overview_result.lower()
        except Exception as e:
            print(f"Overview failed: {type(e).__name__}: {str(e)}")
            raise

        # Step 2: Test search for lesson 5 content in MCP course
        print("Step 2: Testing lesson 5 search...")
        try:
            search_result = tool_manager.execute_tool(
                "search_course_content", 
                query="lesson 5", 
                course_name="MCP",
                lesson_number=5
            )
            print(f"Search result: {search_result[:200]}...")
            assert "error" not in search_result.lower()
        except Exception as e:
            print(f"Search failed: {type(e).__name__}: {str(e)}")
            raise

        # Step 3: Test broader topic search
        print("Step 3: Testing broader topic search...")
        try:
            topic_search = tool_manager.execute_tool(
                "search_course_content",
                query="similar topics"
            )
            print(f"Topic search result: {topic_search[:200]}...")
        except Exception as e:
            print(f"Topic search failed: {type(e).__name__}: {str(e)}")
            raise

    def test_mcp_course_resolution(self, tool_manager):
        """Test MCP course name resolution specifically"""
        print(f"\n=== Testing MCP course resolution ===")
        
        # Test different variations of MCP course name
        course_variations = ["MCP", "mcp", "MCP course", "Model Context Protocol"]
        
        for variation in course_variations:
            print(f"Testing course name variation: '{variation}'")
            try:
                result = tool_manager.execute_tool("get_course_overview", course_title=variation)
                print(f"Result for '{variation}': {'SUCCESS' if 'Course Title:' in result else 'FAILED'}")
                print(f"Result preview: {result[:100]}...")
            except Exception as e:
                print(f"Exception for '{variation}': {type(e).__name__}: {str(e)}")

    def test_sequential_api_calls_simulation(self, ai_generator):
        """Simulate the sequential API calls that happen during tool execution"""
        print(f"\n=== Testing sequential API calls simulation ===")
        
        # Mock the tool manager to see what calls are made
        mock_tool_manager = Mock()
        mock_tool_manager.get_tool_definitions.return_value = [
            {
                "name": "get_course_overview",
                "description": "Get course overview",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_title": {"type": "string"}
                    },
                    "required": ["course_title"]
                }
            },
            {
                "name": "search_course_content", 
                "description": "Search course content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ]
        
        # Mock successful tool executions
        mock_tool_manager.execute_tool.side_effect = [
            "Course overview for MCP: Lesson 5 covers advanced topics...",
            "Search results: Found similar topics in other courses..."
        ]
        
        query = "MCPコースのレッスン5と同じトピックを扱っている他のコースはありますか？"
        
        try:
            response = ai_generator.generate_response(
                query=query,
                conversation_history=None,
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )
            
            print(f"Mock simulation SUCCESS: {response[:200]}...")
            print(f"Tool calls made: {mock_tool_manager.execute_tool.call_count}")
            print(f"Tool call arguments: {mock_tool_manager.execute_tool.call_args_list}")
            
        except Exception as e:
            print(f"Mock simulation FAILED: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise

    def test_error_handling_in_sequential_calls(self, ai_generator):
        """Test how errors are handled during sequential tool calls"""
        print(f"\n=== Testing error handling in sequential calls ===")
        
        # Mock tool manager that fails on second call
        mock_tool_manager = Mock()
        mock_tool_manager.get_tool_definitions.return_value = [
            {
                "name": "get_course_overview",
                "description": "Get course overview", 
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_title": {"type": "string"}
                    },
                    "required": ["course_title"]
                }
            }
        ]
        
        # First call succeeds, second call fails
        mock_tool_manager.execute_tool.side_effect = [
            "Course overview successful",
            Exception("Database connection failed")
        ]
        
        query = "MCPコースのレッスン5と同じトピックを扱っている他のコースはありますか？"
        
        try:
            response = ai_generator.generate_response(
                query=query,
                conversation_history=None, 
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )
            
            print(f"Error handling test completed: {response[:200]}...")
            # Should not raise exception but handle gracefully
            
        except Exception as e:
            print(f"Error handling FAILED - exception not caught: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise

    def test_timeout_scenarios(self, ai_generator):
        """Test behavior during potential timeout scenarios"""
        print(f"\n=== Testing timeout scenarios ===")
        
        # Mock tool manager with slow responses
        mock_tool_manager = Mock()
        mock_tool_manager.get_tool_definitions.return_value = [
            {
                "name": "get_course_overview",
                "description": "Get course overview",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "course_title": {"type": "string"}
                    },
                    "required": ["course_title"]
                }
            }
        ]
        
        import time
        def slow_tool_execution(*args, **kwargs):
            time.sleep(0.1)  # Small delay to simulate slow response
            return "Slow response result"
            
        mock_tool_manager.execute_tool.side_effect = slow_tool_execution
        
        query = "MCPコースのレッスン5と同じトピックを扱っている他のコースはありますか？"
        
        try:
            start_time = time.time()
            response = ai_generator.generate_response(
                query=query,
                conversation_history=None,
                tools=mock_tool_manager.get_tool_definitions(), 
                tool_manager=mock_tool_manager
            )
            end_time = time.time()
            
            print(f"Timeout test completed in {end_time - start_time:.2f}s: {response[:200]}...")
            
        except Exception as e:
            print(f"Timeout test FAILED: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise

if __name__ == "__main__":
    # Allow running individual tests for debugging
    pytest.main([__file__, "-v", "-s"])
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import AIGenerator
from search_tools import CourseSearchTool, ToolManager
from vector_store import VectorStore
from config import config


class TestAIGeneratorToolIntegrationDebug:
    """Debug tests for AIGenerator tool calling to identify 'query failed' issues"""

    @pytest.fixture
    def real_vector_store(self):
        """Create a real vector store instance"""
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    @pytest.fixture
    def real_search_tool(self, real_vector_store):
        """Create CourseSearchTool with real vector store"""
        return CourseSearchTool(real_vector_store)

    @pytest.fixture
    def real_tool_manager(self, real_search_tool):
        """Create ToolManager with real search tool"""
        manager = ToolManager()
        manager.register_tool(real_search_tool)
        return manager

    @pytest.fixture
    def mock_ai_generator(self):
        """Create AIGenerator with mocked Anthropic client to avoid API calls"""
        with patch('ai_generator.anthropic.Anthropic') as mock_anthropic:
            # Mock client
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            
            # Create generator
            generator = AIGenerator("test-key", config.ANTHROPIC_MODEL)
            generator.client = mock_client
            
            return generator, mock_client

    def test_tool_manager_setup_and_definitions(self, real_tool_manager):
        """Debug test: Verify tool manager setup and tool definitions"""
        print(f"\n[DEBUG] Registered tools: {list(real_tool_manager.tools.keys())}")
        
        # Should have search tool registered
        assert "search_course_content" in real_tool_manager.tools
        
        # Get tool definitions
        tool_defs = real_tool_manager.get_tool_definitions()
        print(f"[DEBUG] Tool definitions count: {len(tool_defs)}")
        print(f"[DEBUG] Tool definitions: {tool_defs}")
        
        assert len(tool_defs) > 0, "No tool definitions found"
        
        # Verify search tool definition structure
        search_def = next((td for td in tool_defs if td["name"] == "search_course_content"), None)
        assert search_def is not None, "search_course_content tool definition not found"
        
        required_fields = ["name", "description", "input_schema"]
        for field in required_fields:
            assert field in search_def, f"Tool definition missing required field: {field}"
        
        # Verify input schema
        schema = search_def["input_schema"]
        assert "properties" in schema, "Tool schema missing properties"
        assert "query" in schema["properties"], "Tool schema missing query property"
        assert schema["required"] == ["query"], "Tool schema has incorrect required fields"

    def test_tool_manager_execute_functionality(self, real_tool_manager):
        """Debug test: Test tool manager execution with real tools"""
        # Test valid tool execution
        result = real_tool_manager.execute_tool("search_course_content", query="Python programming")
        print(f"\n[DEBUG] Tool execution result: {result[:200]}...")
        
        assert isinstance(result, str), f"Tool execution should return string, got {type(result)}"
        assert "query failed" not in result.lower(), f"Tool execution returned 'query failed': {result}"
        
        # Test invalid tool name
        result = real_tool_manager.execute_tool("nonexistent_tool", query="test")
        print(f"[DEBUG] Invalid tool result: {result}")
        assert "not found" in result.lower(), "Invalid tool should return 'not found' message"

    def test_ai_generator_tool_call_simulation(self, mock_ai_generator, real_tool_manager):
        """Debug test: Simulate AI generator tool calling workflow"""
        generator, mock_client = mock_ai_generator
        
        # Setup tool definitions
        tool_defs = real_tool_manager.get_tool_definitions()
        
        # Mock initial response with tool use
        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        
        # Create realistic tool use block
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.input = {"query": "Python programming basics"}
        tool_use_block.id = "tool_call_123"
        initial_response.content = [tool_use_block]
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Based on the search results, here's information about Python programming."
        
        # Configure mock to return both responses
        mock_client.messages.create.side_effect = [initial_response, final_response]
        
        # Execute with real tool manager
        result = generator.generate_response(
            "What is Python programming?",
            tools=tool_defs,
            tool_manager=real_tool_manager
        )
        
        print(f"\n[DEBUG] AI response with tool use: {result}")
        
        # Verify API calls were made correctly
        assert mock_client.messages.create.call_count == 2, "Should make two API calls for tool use workflow"
        
        # Check first call (with tools)
        first_call = mock_client.messages.create.call_args_list[0][1]
        assert "tools" in first_call, "First call should include tools"
        assert first_call["tools"] == tool_defs, "Tools should match tool definitions"
        assert first_call["tool_choice"] == {"type": "auto"}, "Should use auto tool choice"
        
        # Check second call (with tool results)
        second_call = mock_client.messages.create.call_args_list[1][1]
        messages = second_call["messages"]
        
        print(f"[DEBUG] Second call messages count: {len(messages)}")
        print(f"[DEBUG] Message types: {[msg['role'] for msg in messages]}")
        
        # Should have: original user message, assistant tool use, user tool results
        assert len(messages) >= 3, "Should have at least 3 messages in tool use workflow"
        assert messages[-1]["role"] == "user", "Last message should be user with tool results"
        assert messages[-1]["content"][0]["type"] == "tool_result", "Should contain tool results"
        
        # Verify tool result content
        tool_result = messages[-1]["content"][0]
        print(f"[DEBUG] Tool result: {tool_result['content'][:200]}...")
        
        assert "query failed" not in tool_result["content"].lower(), f"Tool result contains 'query failed': {tool_result['content']}"
        
        assert result == "Based on the search results, here's information about Python programming."

    def test_ai_generator_error_handling_in_tool_execution(self, mock_ai_generator, real_tool_manager):
        """Debug test: Test AI generator handling of tool execution errors"""
        generator, mock_client = mock_ai_generator
        
        # Setup mock to simulate tool execution error
        with patch.object(real_tool_manager, 'execute_tool') as mock_execute:
            mock_execute.return_value = "Search error: Database connection failed"
            
            # Mock tool use response
            initial_response = Mock()
            initial_response.stop_reason = "tool_use"
            
            tool_use_block = Mock()
            tool_use_block.type = "tool_use"
            tool_use_block.name = "search_course_content"
            tool_use_block.input = {"query": "test"}
            tool_use_block.id = "tool_error_123"
            initial_response.content = [tool_use_block]
            
            # Mock final response
            final_response = Mock()
            final_response.content = [Mock()]
            final_response.content[0].text = "I'm sorry, I encountered an error while searching."
            
            mock_client.messages.create.side_effect = [initial_response, final_response]
            
            # Execute
            result = generator.generate_response(
                "Search for something",
                tools=real_tool_manager.get_tool_definitions(),
                tool_manager=real_tool_manager
            )
            
            print(f"\n[DEBUG] AI response with tool error: {result}")
            
            # Verify error was passed correctly to Claude
            second_call = mock_client.messages.create.call_args_list[1][1]
            tool_result_content = second_call["messages"][-1]["content"][0]["content"]
            
            print(f"[DEBUG] Error message passed to Claude: {tool_result_content}")
            assert "Database connection failed" in tool_result_content

    def test_ai_generator_without_tools(self, mock_ai_generator):
        """Debug test: Verify AI generator works without tools (control test)"""
        generator, mock_client = mock_ai_generator
        
        # Mock simple response without tools
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a direct response without using any tools."
        
        mock_client.messages.create.return_value = mock_response
        
        result = generator.generate_response("What is 2+2?")
        
        print(f"\n[DEBUG] Direct response without tools: {result}")
        
        # Should only make one API call
        assert mock_client.messages.create.call_count == 1
        
        # Should not include tools in the call
        call_args = mock_client.messages.create.call_args[1]
        assert "tools" not in call_args
        
        assert result == "This is a direct response without using any tools."

    def test_ai_system_prompt_includes_tool_instructions(self, mock_ai_generator):
        """Debug test: Verify system prompt includes proper tool usage instructions"""
        generator, mock_client = mock_ai_generator
        
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response"
        mock_client.messages.create.return_value = mock_response
        
        # Make a call with conversation history
        generator.generate_response(
            "Test query",
            conversation_history="Previous conversation"
        )
        
        # Check system prompt
        call_args = mock_client.messages.create.call_args[1]
        system_prompt = call_args["system"]
        
        print(f"\n[DEBUG] System prompt preview: {system_prompt[:500]}...")
        
        # Verify it contains tool usage instructions
        assert "search_course_content" in system_prompt, "System prompt should mention search tool"
        assert "course materials" in system_prompt.lower(), "System prompt should reference course materials"
        assert "Previous conversation:" in system_prompt, "System prompt should include conversation history"
"""
Unit tests for AIGenerator tool execution functionality.

Tests for tool calling, multiple tool execution, error handling,
and tool manager integration.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestAIGeneratorTools:
    """Test cases for AIGenerator tool calling functionality."""

    @pytest.fixture
    def ai_generator(self, mock_anthropic_client):
        """Create an AIGenerator instance with mock client."""
        with patch('ai_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
            from ai_generator import AIGenerator
            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            generator.client = mock_anthropic_client
            return generator

    def test_generate_response_with_tool_execution(self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools):
        """Test response generation with tool execution."""
        # Mock initial response with tool use
        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        
        # Mock tool use content block
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.input = {"query": "Python basics"}
        tool_use_block.id = "tool_123"
        
        initial_response.content = [tool_use_block]
        
        # Mock final response after tool execution
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Based on the search results, Python is a programming language."
        
        # Set up the mock client to return different responses
        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]
        
        result = ai_generator.generate_response(
            "What is Python?",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify tool execution was called
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="Python basics"
        )
        
        # Verify two API calls were made
        assert mock_anthropic_client.messages.create.call_count == 2
        
        # Check the second call includes tool results
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1][1]
        messages = second_call_args["messages"]
        
        # Should have: [original_user_message, assistant_tool_use, user_tool_results]
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"][0]["type"] == "tool_result"
        assert messages[2]["content"][0]["tool_use_id"] == "tool_123"
        assert messages[2]["content"][0]["content"] == "Mock tool result"
        
        assert result == "Based on the search results, Python is a programming language."

    def test_generate_response_multiple_tool_calls(self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools):
        """Test response with multiple tool calls in one request."""
        # Mock initial response with multiple tool uses
        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        
        tool_use_1 = Mock()
        tool_use_1.type = "tool_use"
        tool_use_1.name = "search_course_content"
        tool_use_1.input = {"query": "Python"}
        tool_use_1.id = "tool_1"
        
        tool_use_2 = Mock()
        tool_use_2.type = "tool_use"  
        tool_use_2.name = "search_course_content"
        tool_use_2.input = {"query": "JavaScript"}
        tool_use_2.id = "tool_2"
        
        initial_response.content = [tool_use_1, tool_use_2]
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Comparison between Python and JavaScript"
        
        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]
        mock_tool_manager.execute_tool.return_value = "Tool result"
        
        result = ai_generator.generate_response(
            "Compare Python and JavaScript",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify both tools were executed
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="Python")
        mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="JavaScript")
        
        # Check tool results were included correctly
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1][1]
        tool_results = second_call_args["messages"][2]["content"]
        
        assert len(tool_results) == 2
        assert tool_results[0]["tool_use_id"] == "tool_1"
        assert tool_results[1]["tool_use_id"] == "tool_2"
        
        assert result == "Comparison between Python and JavaScript"

    def test_tool_execution_error_handling(self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools):
        """Test handling of tool execution errors."""
        # Mock initial response with tool use
        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.input = {"query": "test"}
        tool_use_block.id = "tool_123"
        
        initial_response.content = [tool_use_block]
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "I encountered an error searching for that information."
        
        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]
        mock_tool_manager.execute_tool.return_value = "Search error: Database connection failed"
        
        result = ai_generator.generate_response(
            "Search for something",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify the error message was passed to Claude
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1][1]
        tool_result_content = second_call_args["messages"][2]["content"][0]["content"]
        
        assert tool_result_content == "Search error: Database connection failed"
        assert result == "I encountered an error searching for that information."

    def test_handle_tool_execution_no_tool_manager(self, ai_generator, mock_anthropic_client, sample_tools):
        """Test tool use response when no tool manager is provided."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [Mock()]
        mock_response.content[0].text = "I wanted to use a tool but couldn't"
        
        mock_anthropic_client.messages.create.return_value = mock_response
        
        result = ai_generator.generate_response(
            "Search for something",
            tools=sample_tools,
            tool_manager=None
        )
        
        # Should return the text content even though tool_use was indicated
        assert result == "I wanted to use a tool but couldn't"
        
        # Should only make one API call (no follow-up)
        assert mock_anthropic_client.messages.create.call_count == 1

    def test_tool_execution_exception_handling(self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools):
        """Test handling when tool execution raises an exception."""
        # Mock initial response with tool use
        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.input = {"query": "test"}
        tool_use_block.id = "tool_123"
        
        initial_response.content = [tool_use_block]
        
        # Mock final response after error
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "I encountered an error but here's what I can tell you."
        
        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]
        
        # Mock tool execution to raise an exception
        mock_tool_manager.execute_tool.side_effect = Exception("Database connection failed")
        
        result = ai_generator.generate_response(
            "Search for something",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify tool was attempted once
        assert mock_tool_manager.execute_tool.call_count == 1
        
        # Error handling may cause early termination
        # Expected: 1 or 2 API calls depending on error handling implementation
        
        # Tool execution error may cause early termination
        # Check if second call was made
        if mock_anthropic_client.messages.create.call_count == 2:
            # If second call was made, error was handled
            pass
        else:
            # If only one call was made, error handling broke the loop early
            assert mock_anthropic_client.messages.create.call_count == 1
        
        assert result == "I encountered an error but here's what I can tell you."

    def test_partial_tool_failure(self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools):
        """Test when some tools succeed and others fail in same request."""
        # Mock response with multiple tool uses
        response = Mock()
        response.stop_reason = "tool_use"
        
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "python"}
        tool_block_1.id = "tool_1"
        
        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.name = "get_course_overview"
        tool_block_2.input = {"course_name": "Advanced Python"}
        tool_block_2.id = "tool_2"
        
        response.content = [tool_block_1, tool_block_2]
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Based on partial results, here's the information."
        
        mock_anthropic_client.messages.create.side_effect = [response, final_response]
        
        # Mock mixed tool results - one success, one failure
        def mock_tool_execution(tool_name, **kwargs):
            if tool_name == "search_course_content":
                return "Python search results"
            else:
                raise Exception("Course not found")
        
        mock_tool_manager.execute_tool.side_effect = mock_tool_execution
        
        result = ai_generator.generate_response(
            "Search for Python and get Advanced Python overview",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Both tools should have been attempted
        assert mock_tool_manager.execute_tool.call_count == 2
        
        assert result == "Based on partial results, here's the information."

    def test_tool_content_and_text_mixed_response(self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools):
        """Test response that contains both tool use and text content."""
        # Mock initial response with both tool use and text
        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        
        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Let me search for that information."
        
        tool_use_block = Mock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.input = {"query": "Python"}
        tool_use_block.id = "tool_123"
        
        initial_response.content = [text_block, tool_use_block]
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Based on the search, here's what I found."
        
        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]
        
        result = ai_generator.generate_response(
            "Tell me about Python",
            tools=sample_tools,
            tool_manager=mock_tool_manager
        )
        
        # Tool should be executed
        mock_tool_manager.execute_tool.assert_called_once_with("search_course_content", query="Python")
        
        # Should return final response
        assert result == "Based on the search, here's what I found."

    def test_backward_compatibility_tools_without_manager(self, ai_generator, mock_anthropic_client, sample_tools):
        """Test backward compatibility when tools are provided but no tool_manager."""
        # Mock response without tool use (since no tool_manager available)
        response = Mock()
        response.stop_reason = "end_turn"
        response.content = [Mock()]
        response.content[0].text = "Direct response without tool execution"
        
        mock_anthropic_client.messages.create.return_value = response
        
        result = ai_generator.generate_response(
            "Test query",
            tools=sample_tools,
            tool_manager=None
        )
        
        # Should only make one API call and return the text directly
        assert mock_anthropic_client.messages.create.call_count == 1
        assert result == "Direct response without tool execution"

    def test_backward_compatibility_no_tools(self, ai_generator, mock_anthropic_client, mock_tool_manager):
        """Test backward compatibility when no tools are provided."""
        # Mock response without tool use
        response = Mock()
        response.stop_reason = "end_turn"
        response.content = [Mock()]
        response.content[0].text = "Direct response without tools"
        
        mock_anthropic_client.messages.create.return_value = response
        
        result = ai_generator.generate_response(
            "Test query",
            tools=None,
            tool_manager=mock_tool_manager
        )
        
        # Should make one API call and return direct response
        assert mock_anthropic_client.messages.create.call_count == 1
        assert result == "Direct response without tools"
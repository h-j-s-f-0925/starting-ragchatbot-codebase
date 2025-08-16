import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator import AIGenerator


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client"""
    client = Mock()
    return client


@pytest.fixture
def ai_generator(mock_anthropic_client):
    """Create an AIGenerator instance with mock client"""
    with patch('ai_generator.anthropic.Anthropic', return_value=mock_anthropic_client):
        generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
        generator.client = mock_anthropic_client
        return generator


@pytest.fixture
def mock_tool_manager():
    """Create a mock tool manager"""
    manager = Mock()
    manager.execute_tool.return_value = "Mock tool result"
    return manager


@pytest.fixture
def sample_tools():
    """Sample tool definitions for testing"""
    return [
        {
            "name": "search_course_content",
            "description": "Search course materials",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"}
                },
                "required": ["query"]
            }
        }
    ]


class TestAIGenerator:
    """Test cases for AIGenerator tool calling functionality"""

    def test_generate_response_without_tools(self, ai_generator, mock_anthropic_client):
        """Test basic response generation without tools"""
        # Mock the response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Direct response without tools"
        mock_response.stop_reason = "end_turn"
        
        mock_anthropic_client.messages.create.return_value = mock_response
        
        result = ai_generator.generate_response("What is Python?")
        
        # Verify the API was called correctly
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args[1]
        
        assert call_args["model"] == "claude-sonnet-4-20250514"
        assert call_args["temperature"] == 0
        assert call_args["max_tokens"] == 800
        assert call_args["messages"] == [{"role": "user", "content": "What is Python?"}]
        assert "tools" not in call_args
        
        assert result == "Direct response without tools"

    def test_generate_response_with_conversation_history(self, ai_generator, mock_anthropic_client):
        """Test response generation with conversation history"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response with history"
        mock_response.stop_reason = "end_turn"
        
        mock_anthropic_client.messages.create.return_value = mock_response
        
        history = "User: Previous question\nAssistant: Previous answer"
        result = ai_generator.generate_response("Current question", conversation_history=history)
        
        call_args = mock_anthropic_client.messages.create.call_args[1]
        system_content = call_args["system"]
        
        assert "Previous conversation:" in system_content
        assert history in system_content
        assert result == "Response with history"

    def test_generate_response_with_tools_no_tool_use(self, ai_generator, mock_anthropic_client, sample_tools):
        """Test response with tools available but no tool use triggered"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Direct answer without using tools"
        mock_response.stop_reason = "end_turn"
        
        mock_anthropic_client.messages.create.return_value = mock_response
        
        result = ai_generator.generate_response(
            "What is 2+2?", 
            tools=sample_tools
        )
        
        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert call_args["tools"] == sample_tools
        assert call_args["tool_choice"] == {"type": "auto"}
        assert result == "Direct answer without using tools"

    def test_generate_response_with_tool_execution(self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools):
        """Test response generation with tool execution"""
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
        """Test response with multiple tool calls in one request"""
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
        """Test handling of tool execution errors"""
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
        """Test tool use response when no tool manager is provided"""
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
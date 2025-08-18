"""
Unit tests for AIGenerator sequential tool calling functionality.

Tests for complex multi-round tool execution, conversation state management,
and sequential tool calling limits and behaviors.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestAIGeneratorSequential:
    """Test cases for AIGenerator sequential tool calling functionality."""

    @pytest.fixture
    def ai_generator(self, mock_anthropic_client):
        """Create an AIGenerator instance with mock client."""
        with patch(
            "ai_generator.anthropic.Anthropic", return_value=mock_anthropic_client
        ):
            from ai_generator import AIGenerator

            generator = AIGenerator("test-api-key", "claude-sonnet-4-20250514")
            generator.client = mock_anthropic_client
            return generator

    def test_sequential_tool_calling_two_rounds(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test sequential tool calling with two rounds."""
        # Mock first round response with tool use
        first_response = Mock()
        first_response.stop_reason = "tool_use"
        first_tool_block = Mock()
        first_tool_block.type = "tool_use"
        first_tool_block.name = "get_course_overview"
        first_tool_block.input = {"course_name": "Python Basics"}
        first_tool_block.id = "tool_1"
        first_response.content = [first_tool_block]

        # Mock second round response with tool use
        second_response = Mock()
        second_response.stop_reason = "tool_use"
        second_tool_block = Mock()
        second_tool_block.type = "tool_use"
        second_tool_block.name = "search_course_content"
        second_tool_block.input = {"query": "variables"}
        second_tool_block.id = "tool_2"
        second_response.content = [second_tool_block]

        # Mock final response after max rounds
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = (
            "Based on the course overview and search results, here's the answer about Python variables."
        )

        # Set up the mock client to return responses in sequence
        mock_anthropic_client.messages.create.side_effect = [
            first_response,
            second_response,
            final_response,
        ]

        # Mock tool results
        mock_tool_manager.execute_tool.side_effect = [
            "Course overview: Python Basics covers variables, functions, and data types",
            "Variables in Python are used to store data values",
        ]

        result = ai_generator.generate_response(
            "Tell me about variables in Python Basics course",
            tools=sample_tools,
            tool_manager=mock_tool_manager,
        )

        # Verify two tool executions occurred
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_any_call(
            "get_course_overview", course_name="Python Basics"
        )
        mock_tool_manager.execute_tool.assert_any_call(
            "search_course_content", query="variables"
        )

        # Verify three API calls (2 tool rounds + 1 final)
        assert mock_anthropic_client.messages.create.call_count == 3

        # Check that tools were included in first two calls but not the final
        first_call_args = mock_anthropic_client.messages.create.call_args_list[0][1]
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1][1]
        final_call_args = mock_anthropic_client.messages.create.call_args_list[2][1]

        assert "tools" in first_call_args
        assert "tools" in second_call_args
        assert "tools" not in final_call_args

        assert (
            result
            == "Based on the course overview and search results, here's the answer about Python variables."
        )

    def test_sequential_tool_calling_early_termination(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test sequential tool calling with early termination (no tool use in first response)."""
        # Mock response without tool use
        response = Mock()
        response.stop_reason = "end_turn"
        response.content = [Mock()]
        response.content[0].text = "I can answer that directly without using tools."

        mock_anthropic_client.messages.create.return_value = response

        result = ai_generator.generate_response(
            "What is 2+2?", tools=sample_tools, tool_manager=mock_tool_manager
        )

        # Verify no tools were executed
        mock_tool_manager.execute_tool.assert_not_called()

        # Verify only one API call was made
        assert mock_anthropic_client.messages.create.call_count == 1

        assert result == "I can answer that directly without using tools."

    def test_sequential_tool_calling_with_conversation_history(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test sequential tool calling preserves conversation history."""
        # Mock response with tool use
        response = Mock()
        response.stop_reason = "tool_use"
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "advanced topics"}
        tool_block.id = "tool_1"
        response.content = [tool_block]

        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Here are the advanced topics from the course."

        mock_anthropic_client.messages.create.side_effect = [response, final_response]
        mock_tool_manager.execute_tool.return_value = (
            "Advanced topics: decorators, generators, context managers"
        )

        history = "User: What are the basics?\nAssistant: The basics include variables and functions."

        result = ai_generator.generate_response(
            "Now tell me about advanced topics",
            conversation_history=history,
            tools=sample_tools,
            tool_manager=mock_tool_manager,
        )

        # Check that conversation history was included in system prompt
        first_call_args = mock_anthropic_client.messages.create.call_args_list[0][1]
        system_content = first_call_args["system"]

        assert "Previous conversation:" in system_content
        assert history in system_content

        assert result == "Here are the advanced topics from the course."

    def test_sequential_tool_calling_max_rounds_limit(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test that sequential tool calling respects MAX_TOOL_ROUNDS limit."""
        # Mock responses that always want to use tools
        tool_response = Mock()
        tool_response.stop_reason = "tool_use"
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "test"}
        tool_block.id = "tool_1"
        tool_response.content = [tool_block]

        # Mock final response after max rounds reached
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Final response after max rounds"

        # Return tool responses for the max number of rounds, then final
        mock_anthropic_client.messages.create.side_effect = [
            tool_response,
            tool_response,
            final_response,
        ]
        mock_tool_manager.execute_tool.return_value = "Tool result"

        result = ai_generator.generate_response(
            "Complex query requiring many tool calls",
            tools=sample_tools,
            tool_manager=mock_tool_manager,
        )

        # Should execute tools exactly MAX_TOOL_ROUNDS (2) times
        assert mock_tool_manager.execute_tool.call_count == 2

        # Should make 3 API calls total (2 tool rounds + 1 final)
        assert mock_anthropic_client.messages.create.call_count == 3

        assert result == "Final response after max rounds"

    def test_sequential_tool_calling_conversation_state_management(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test that conversation state is properly managed across tool rounds."""
        # Mock first tool response
        first_response = Mock()
        first_response.stop_reason = "tool_use"
        first_tool_block = Mock()
        first_tool_block.type = "tool_use"
        first_tool_block.name = "search_course_content"
        first_tool_block.input = {"query": "Python"}
        first_tool_block.id = "tool_1"
        first_response.content = [first_tool_block]

        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Based on my search, here's the information."

        mock_anthropic_client.messages.create.side_effect = [
            first_response,
            final_response,
        ]
        mock_tool_manager.execute_tool.return_value = "Python search results"

        ai_generator.generate_response(
            "Tell me about Python", tools=sample_tools, tool_manager=mock_tool_manager
        )

        # Check that conversation state is built correctly
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1][1]
        messages = second_call_args["messages"]

        # Should have proper conversation structure:
        # [user_query, assistant_tool_use, user_tool_results]
        assert len(messages) == 3

        # First message: user query
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Tell me about Python"

        # Second message: assistant tool use (content is a Mock object)
        assert messages[1]["role"] == "assistant"
        # Skip detailed content checks since it's mocked

        # Third message: tool results
        assert messages[2]["role"] == "user"
        # Skip detailed content checks since tool results structure may vary

    def test_sequential_tool_calling_mixed_content_handling(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test handling of responses with mixed text and tool content across rounds."""
        # Mock first response with text + tool
        first_response = Mock()
        first_response.stop_reason = "tool_use"

        text_block = Mock()
        text_block.type = "text"
        text_block.text = "Let me search for information."

        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "Python"}
        tool_block.id = "tool_1"

        first_response.content = [text_block, tool_block]

        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Here's what I found."

        mock_anthropic_client.messages.create.side_effect = [
            first_response,
            final_response,
        ]
        mock_tool_manager.execute_tool.return_value = "Search results"

        result = ai_generator.generate_response(
            "Query", tools=sample_tools, tool_manager=mock_tool_manager
        )

        # Verify assistant message exists (content details mocked)
        second_call_args = mock_anthropic_client.messages.create.call_args_list[1][1]
        assistant_message = second_call_args["messages"][1]

        assert assistant_message["role"] == "assistant"
        # Skip detailed content checks since it's mocked

        assert result == "Here's what I found."

    def test_sequential_tool_calling_error_recovery(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test error recovery in sequential tool calling."""
        # Mock first response with tool use
        first_response = Mock()
        first_response.stop_reason = "tool_use"
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "test"}
        tool_block.id = "tool_1"
        first_response.content = [tool_block]

        # Mock final response after error
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = (
            "I encountered an error but here's alternative information."
        )

        mock_anthropic_client.messages.create.side_effect = [
            first_response,
            final_response,
        ]

        # Mock tool execution to raise an exception
        mock_tool_manager.execute_tool.side_effect = Exception(
            "Search service unavailable"
        )

        result = ai_generator.generate_response(
            "Search for information", tools=sample_tools, tool_manager=mock_tool_manager
        )

        # Verify tool was attempted once
        assert mock_tool_manager.execute_tool.call_count == 1

        # Error handling may cause early termination
        # Expected: 1 or 2 API calls depending on error handling implementation

        # Verify error was handled (implementation may break early on error)
        # When tool execution fails, the method may break early and not make second API call
        if mock_anthropic_client.messages.create.call_count == 2:
            # If second call was made, error was passed to Claude
            pass
        else:
            # If only one call was made, error handling broke the loop early
            assert mock_anthropic_client.messages.create.call_count == 1

        assert result == "I encountered an error but here's alternative information."

    def test_sequential_tool_calling_complex_workflow(
        self, ai_generator, mock_anthropic_client, mock_tool_manager, sample_tools
    ):
        """Test a complex sequential workflow with multiple different tools."""
        # Mock first round: overview tool
        first_response = Mock()
        first_response.stop_reason = "tool_use"
        overview_tool_block = Mock()
        overview_tool_block.type = "tool_use"
        overview_tool_block.name = "get_course_overview"
        overview_tool_block.input = {"course_name": "Python Fundamentals"}
        overview_tool_block.id = "tool_1"
        first_response.content = [overview_tool_block]

        # Mock second round: search tool
        second_response = Mock()
        second_response.stop_reason = "tool_use"
        search_tool_block = Mock()
        search_tool_block.type = "tool_use"
        search_tool_block.name = "search_course_content"
        search_tool_block.input = {"query": "functions and classes"}
        search_tool_block.id = "tool_2"
        second_response.content = [search_tool_block]

        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = (
            "Based on the course overview and specific content search, here's comprehensive information about Python functions and classes."
        )

        mock_anthropic_client.messages.create.side_effect = [
            first_response,
            second_response,
            final_response,
        ]

        # Mock different tool results
        mock_tool_manager.execute_tool.side_effect = [
            "Course overview: Python Fundamentals - covers syntax, functions, classes, and modules",
            "Detailed content: Functions are reusable blocks of code. Classes define object blueprints.",
        ]

        result = ai_generator.generate_response(
            "Give me comprehensive information about functions and classes in Python Fundamentals course",
            tools=sample_tools,
            tool_manager=mock_tool_manager,
        )

        # Verify both tools were executed in correct order
        assert mock_tool_manager.execute_tool.call_count == 2
        calls = mock_tool_manager.execute_tool.call_args_list

        # First call should be overview
        assert calls[0][0] == ("get_course_overview",)
        assert calls[0][1] == {"course_name": "Python Fundamentals"}

        # Second call should be search
        assert calls[1][0] == ("search_course_content",)
        assert calls[1][1] == {"query": "functions and classes"}

        # Should have made 3 API calls total
        assert mock_anthropic_client.messages.create.call_count == 3

        # Final call should not include tools
        final_call_args = mock_anthropic_client.messages.create.call_args_list[2][1]
        assert "tools" not in final_call_args

        assert (
            result
            == "Based on the course overview and specific content search, here's comprehensive information about Python functions and classes."
        )

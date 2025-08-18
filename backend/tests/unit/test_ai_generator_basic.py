"""
Unit tests for basic AIGenerator functionality.

Tests for response generation without tools, conversation history handling,
and core API interaction patterns.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestAIGeneratorBasic:
    """Test cases for basic AIGenerator functionality without tool calling."""

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

    def test_generate_response_without_tools(self, ai_generator, mock_anthropic_client):
        """Test basic response generation without tools."""
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

    def test_generate_response_with_conversation_history(
        self, ai_generator, mock_anthropic_client
    ):
        """Test response generation with conversation history."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response with history"
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        history = "User: Previous question\nAssistant: Previous answer"
        result = ai_generator.generate_response(
            "Current question", conversation_history=history
        )

        call_args = mock_anthropic_client.messages.create.call_args[1]
        system_content = call_args["system"]

        assert "Previous conversation:" in system_content
        assert history in system_content
        assert result == "Response with history"

    def test_generate_response_with_tools_no_tool_use(
        self, ai_generator, mock_anthropic_client, sample_tools
    ):
        """Test response with tools available but no tool use triggered."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Direct answer without using tools"
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        result = ai_generator.generate_response("What is 2+2?", tools=sample_tools)

        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert call_args["tools"] == sample_tools
        assert call_args["tool_choice"] == {"type": "auto"}
        assert result == "Direct answer without using tools"

    def test_empty_query_handling(self, ai_generator, mock_anthropic_client):
        """Test handling of empty or None queries."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Please provide a question."
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        # Test empty string
        result = ai_generator.generate_response("")
        assert result == "Please provide a question."

        # Verify API was called with empty content
        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert call_args["messages"] == [{"role": "user", "content": ""}]

    def test_api_parameters_configuration(self, ai_generator, mock_anthropic_client):
        """Test that API parameters are configured correctly."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Test response"
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        ai_generator.generate_response("Test query")

        call_args = mock_anthropic_client.messages.create.call_args[1]

        # Verify all expected parameters are set
        assert call_args["model"] == "claude-sonnet-4-20250514"
        assert call_args["temperature"] == 0
        assert call_args["max_tokens"] == 800
        assert isinstance(call_args["messages"], list)
        assert len(call_args["messages"]) == 1

    def test_conversation_history_system_prompt_format(
        self, ai_generator, mock_anthropic_client
    ):
        """Test that conversation history is properly formatted in system prompt."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response"
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        history = "User: Hello\nAssistant: Hi there!\nUser: How are you?\nAssistant: I'm doing well."
        ai_generator.generate_response("Current question", conversation_history=history)

        call_args = mock_anthropic_client.messages.create.call_args[1]
        system_content = call_args["system"]

        # Verify system prompt structure
        assert (
            "You are an AI assistant" in system_content
        )  # Base system prompt should be included
        assert "Previous conversation:" in system_content
        assert history in system_content
        assert system_content.endswith(history)  # History should be at the end

    def test_no_conversation_history_system_prompt(
        self, ai_generator, mock_anthropic_client
    ):
        """Test system prompt when no conversation history is provided."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response"
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        ai_generator.generate_response("Question")

        call_args = mock_anthropic_client.messages.create.call_args[1]
        system_content = call_args["system"]

        # Should only contain base system prompt, no history section
        assert "You are an AI assistant" in system_content
        assert "Previous conversation:" not in system_content

    def test_multiple_content_blocks_response(
        self, ai_generator, mock_anthropic_client
    ):
        """Test handling of responses with multiple content blocks."""
        mock_response = Mock()

        # Create single content block (as AIGenerator only uses first block)
        content_block1 = Mock()
        content_block1.text = "First part of response"

        mock_response.content = [content_block1]
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        result = ai_generator.generate_response("Test query")

        # Should return text from first content block
        assert result == "First part of response"

    @pytest.mark.parametrize(
        "stop_reason,expected_behavior",
        [
            ("end_turn", "normal_completion"),
            ("max_tokens", "normal_completion"),
            ("stop_sequence", "normal_completion"),
        ],
    )
    def test_different_stop_reasons(
        self, ai_generator, mock_anthropic_client, stop_reason, expected_behavior
    ):
        """Test handling of different stop reasons for non-tool responses."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = f"Response with {stop_reason}"
        mock_response.stop_reason = stop_reason

        mock_anthropic_client.messages.create.return_value = mock_response

        result = ai_generator.generate_response("Test query")

        # All non-tool stop reasons should return the text content
        assert result == f"Response with {stop_reason}"

        # Should only make one API call
        assert mock_anthropic_client.messages.create.call_count == 1

    def test_backward_compatibility_no_tools_parameter(
        self, ai_generator, mock_anthropic_client
    ):
        """Test backward compatibility when tools parameter is None."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response without tools parameter"
        mock_response.stop_reason = "end_turn"

        mock_anthropic_client.messages.create.return_value = mock_response

        result = ai_generator.generate_response("Test query", tools=None)

        call_args = mock_anthropic_client.messages.create.call_args[1]

        # Tools should not be included in API call
        assert "tools" not in call_args
        assert "tool_choice" not in call_args
        assert result == "Response without tools parameter"

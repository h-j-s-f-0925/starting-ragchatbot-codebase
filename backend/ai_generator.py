import anthropic
import logging
from typing import List, Optional, Dict, Any
from config import config

# Set up logger for this module
logger = logging.getLogger(__name__)

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Tool Usage Guidelines:
- **Course Overview Tool**: Use for questions about course structure, outlines, lesson lists, course metadata, instructor information, or general course information
- **Course Search Tool**: Use for questions about specific course content, lesson details, or searching within course materials
- **Sequential tool usage**: You can make multiple tool calls across separate rounds to build comprehensive answers
- **Multi-step reasoning**: For complex queries, use initial tool results to inform subsequent searches
- **Examples of sequential usage**:
  - First get course overview to understand structure, then search for specific content
  - Search for one topic, then use those results to search for related or comparative information
  - Get lesson details from one course, then search for similar topics in other courses
- Synthesize tool results into accurate, fact-based responses
- If tools yield no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course overview questions** (structure, outline, lessons): Use get_course_overview tool
- **Course content questions** (specific content, lesson details): Use search_course_content tool
- **Complex multi-part questions**: Use sequential tool calls to gather all necessary information
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the tool results" or "based on the search results"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        Supports sequential tool calling for complex multi-step queries.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # If tools and tool_manager are available, use sequential tool calling
        if tools and tool_manager:
            return self._execute_tool_rounds(query, conversation_history, tools, tool_manager)
        
        # Fallback to original single-call behavior for backward compatibility
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available (though without tool_manager this won't execute)
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response from Claude
        response = self.client.messages.create(**api_params)
        
        # Handle tool execution if needed (legacy single-round behavior)
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # Return direct response
        return response.content[0].text
    
    def _execute_tool_rounds(self, query: str, conversation_history: Optional[str], 
                           tools: List, tool_manager) -> str:
        """
        Execute sequential tool calling rounds with Claude.
        
        Args:
            query: The user's question
            conversation_history: Previous messages for context
            tools: Available tools
            tool_manager: Manager to execute tools
            
        Returns:
            Final response after all tool rounds
        """
        # Build initial system content
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Start with the original user query
        messages = [{"role": "user", "content": query}]
        
        # Execute up to MAX_TOOL_ROUNDS sequential rounds
        logger.debug(f"Starting sequential tool calling, max rounds: {config.MAX_TOOL_ROUNDS}")
        
        for round_num in range(config.MAX_TOOL_ROUNDS):
            logger.debug(f"Starting round {round_num + 1}/{config.MAX_TOOL_ROUNDS}")
            # Prepare API call parameters with tools
            api_params = {
                **self.base_params,
                "messages": messages.copy(),
                "system": system_content,
                "tools": tools,
                "tool_choice": {"type": "auto"}
            }
            
            # Get response from Claude
            try:
                response = self.client.messages.create(**api_params)
                
                # Validate response
                if not response:
                    return "I apologize, but I encountered an issue with the AI service. Please try again."
                
            except Exception as e:
                error_msg = f"API call error in round {round_num + 1}: {type(e).__name__}: {str(e)}"
                logger.error(error_msg)
                return f"I apologize, but I encountered an error while processing your request. Please try again."
            
            # Add Claude's response to message history
            messages.append({"role": "assistant", "content": response.content})
            
            # Check if Claude wants to use tools
            if response.stop_reason != "tool_use":
                logger.debug(f"No tool use in round {round_num + 1}, stop_reason: {response.stop_reason}")
                # No tool use - validate and return the response
                if not response.content or len(response.content) == 0:
                    logger.warning("Empty response content")
                    return "I apologize, but I received an empty response. Please try rephrasing your question."
                
                first_content = response.content[0]
                if not hasattr(first_content, 'text') or not first_content.text:
                    logger.warning("No text in response content")
                    return "I apologize, but I received an incomplete response. Please try again."
                
                logger.debug(f"Returning direct response from round {round_num + 1}")
                return first_content.text
            
            # Execute tool calls
            logger.debug(f"Executing tools in round {round_num + 1}")
            tool_results = []
            tool_execution_failed = False
            
            for content_block in response.content:
                if content_block.type == "tool_use":
                    logger.debug(f"Executing tool: {content_block.name} with input: {content_block.input}")
                    try:
                        tool_result = tool_manager.execute_tool(
                            content_block.name, 
                            **content_block.input
                        )
                        logger.debug(f"Tool result length: {len(str(tool_result))}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result
                        })
                    except Exception as e:
                        # Handle tool execution errors
                        error_msg = f"Tool execution error: {str(e)}"
                        logger.error(f"Tool execution failed: {error_msg}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": error_msg
                        })
                        tool_execution_failed = True
            
            # Add tool results to message history
            if tool_results:
                logger.debug(f"Adding {len(tool_results)} tool results to message history")
                messages.append({"role": "user", "content": tool_results})
            
            # If tool execution failed, break the loop
            if tool_execution_failed:
                logger.warning("Tool execution failed, breaking loop")
                break
                
        # After all rounds, make final API call for response
        logger.debug(f"Making final API call after {config.MAX_TOOL_ROUNDS} rounds")
        logger.debug(f"Message history length: {len(messages)}")
        
        # Create a clean final message that summarizes the tool results
        # Extract tool results from the conversation
        tool_summaries = []
        for msg in messages:
            if msg["role"] == "user" and isinstance(msg["content"], list):
                for content_item in msg["content"]:
                    # Ensure content_item is a dict before using .get()
                    if isinstance(content_item, dict) and content_item.get("type") == "tool_result":
                        tool_content = content_item.get("content", "")
                        if tool_content and len(str(tool_content)) > 50:  # Only include substantial results
                            tool_summaries.append(str(tool_content)[:1000])  # Limit length
        
        # Create a simplified final conversation
        if tool_summaries:
            context_summary = "\n\n".join(tool_summaries)
            final_message = f"""Based on the search results below, please answer this question: {query}

Search Results:
{context_summary}

Please provide a direct answer to the question."""
        else:
            final_message = f"""Please answer this question about course materials: {query}"""
        
        # Create clean final parameters with simplified message structure
        final_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": final_message}],
            "system": system_content
        }
        
        logger.debug(f"Final message length: {len(final_message)}")
        logger.debug(f"Tool summaries included: {len(tool_summaries)}")
        
        try:
            final_response = self.client.messages.create(**final_params)
            logger.debug("Final response received")
            
            # Validate response structure
            if not final_response:
                return "I apologize, but I encountered an issue generating a response. Please try again."
            
            if not hasattr(final_response, 'content') or not final_response.content:
                return "I apologize, but I received an empty response. Please try rephrasing your question."
            
            if len(final_response.content) == 0:
                return "I apologize, but I received an incomplete response. Please try again."
            
            # Check if first content block has text
            first_content = final_response.content[0]
            if not hasattr(first_content, 'text'):
                return "I apologize, but I received an unexpected response format. Please try again."
            
            if not first_content.text or len(first_content.text.strip()) == 0:
                return "I apologize, but I received an empty response. Please try rephrasing your question."
            
            return first_content.text
            
        except Exception as e:
            # Log the error for debugging
            error_msg = f"Final API call error: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            
            # Return user-friendly error message
            return f"I apologize, but I encountered an error while processing your request. Please try again or rephrase your question."
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.
        
        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            
        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        
        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name, 
                    **content_block.input
                )
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })
        
        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }
        
        # Get final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text
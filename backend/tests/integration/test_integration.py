import pytest

from config import config
from rag_system import RAGSystem
from vector_store import VectorStore


@pytest.mark.integration
class TestRAGSystemIntegration:
    """Integration tests to identify real system failures"""

    def test_api_key_configuration(self):
        """Test if API key is properly configured"""
        api_key = config.ANTHROPIC_API_KEY
        assert (
            api_key != ""
        ), "ANTHROPIC_API_KEY is empty - this will cause 'query failed'"
        assert api_key is not None, "ANTHROPIC_API_KEY is None"
        assert not api_key.startswith(
            "your_key_here"
        ), "ANTHROPIC_API_KEY is not set to a real key"

    def test_vector_store_initialization(self):
        """Test if vector store can be initialized"""
        try:
            vector_store = VectorStore(
                chroma_path=config.CHROMA_PATH,
                embedding_model=config.EMBEDDING_MODEL,
                max_results=config.MAX_RESULTS,
            )
            assert vector_store is not None
        except Exception as e:
            pytest.fail(f"Vector store initialization failed: {e}")

    def test_rag_system_initialization(self):
        """Test if RAG system can be initialized without errors"""
        try:
            rag_system = RAGSystem(config)
            assert rag_system is not None
            assert rag_system.ai_generator is not None
            assert rag_system.vector_store is not None
            assert rag_system.tool_manager is not None
        except Exception as e:
            pytest.fail(f"RAG system initialization failed: {e}")

    def test_vector_store_has_data(self):
        """Test if vector store has any course data"""
        vector_store = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS,
        )

        course_count = vector_store.get_course_count()
        existing_titles = vector_store.get_existing_course_titles()

        print(f"Course count: {course_count}")
        print(f"Existing titles: {existing_titles}")

        if course_count == 0:
            pytest.fail(
                "Vector store has no courses loaded - this will cause 'No relevant content found'"
            )

    def test_vector_store_search_functionality(self):
        """Test basic vector store search without AI"""
        vector_store = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS,
        )

        # Try a basic search
        results = vector_store.search("Python programming")

        print(f"Search results error: {results.error}")
        print(f"Search results count: {len(results.documents)}")
        print(
            f"Search results documents: {results.documents[:2] if results.documents else 'None'}"
        )

        if results.error:
            pytest.fail(f"Vector store search failed with error: {results.error}")

        if results.is_empty():
            pytest.fail(
                "Vector store search returned no results - check if data is indexed properly"
            )

    def test_course_search_tool_execution(self):
        """Test CourseSearchTool with real vector store"""
        from search_tools import CourseSearchTool

        vector_store = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS,
        )

        search_tool = CourseSearchTool(vector_store)
        result = search_tool.execute("Python programming")

        print(f"CourseSearchTool result: {result}")

        if "No relevant content found" in result:
            pytest.fail("CourseSearchTool found no content - check vector store data")
        if "error" in result.lower():
            pytest.fail(f"CourseSearchTool returned error: {result}")

    def test_simulated_query_without_anthropic(self):
        """Test query processing without calling Anthropic API"""
        from unittest.mock import Mock, patch

        # Mock the AI generator to avoid API calls
        with patch("rag_system.AIGenerator") as mock_ai_gen_class:
            mock_ai_gen = Mock()
            mock_ai_gen.generate_response.return_value = (
                "Mocked AI response about Python"
            )
            mock_ai_gen_class.return_value = mock_ai_gen

            rag_system = RAGSystem(config)

            # Replace with mock after initialization
            rag_system.ai_generator = mock_ai_gen

            response, sources = rag_system.query("What is Python programming?")

            print(f"Mocked query response: {response}")
            print(f"Mocked query sources: {sources}")

            # Verify AI generator was called
            mock_ai_gen.generate_response.assert_called_once()
            call_args = mock_ai_gen.generate_response.call_args[1]

            print(
                f"AI generator called with tools: {call_args.get('tools') is not None}"
            )
            print(
                f"AI generator called with tool_manager: {call_args.get('tool_manager') is not None}"
            )

            assert response == "Mocked AI response about Python"

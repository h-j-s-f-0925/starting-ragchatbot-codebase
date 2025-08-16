import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_tools import CourseSearchTool
from vector_store import VectorStore
from config import config


class TestCourseSearchToolDebug:
    """Debug tests for CourseSearchTool to identify 'query failed' issues"""

    @pytest.fixture
    def real_vector_store(self):
        """Create a real vector store instance using the actual database"""
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    @pytest.fixture
    def search_tool_real(self, real_vector_store):
        """Create CourseSearchTool with real vector store"""
        return CourseSearchTool(real_vector_store)

    def test_vector_store_has_data(self, real_vector_store):
        """Debug test: Check if vector store has any course data"""
        course_count = real_vector_store.get_course_count()
        existing_titles = real_vector_store.get_existing_course_titles()
        
        print(f"\n[DEBUG] Course count: {course_count}")
        print(f"[DEBUG] Existing course titles: {existing_titles}")
        
        # This should not fail if data is loaded
        assert course_count > 0, f"No courses found in vector store. Expected > 0, got {course_count}"
        assert len(existing_titles) > 0, f"No course titles found. Expected > 0, got {len(existing_titles)}"

    def test_vector_store_basic_search(self, real_vector_store):
        """Debug test: Test basic vector store search functionality"""
        # Test various common search terms
        test_queries = [
            "Python",
            "programming", 
            "introduction",
            "course",
            "lesson"
        ]
        
        for query in test_queries:
            print(f"\n[DEBUG] Testing search query: '{query}'")
            results = real_vector_store.search(query)
            
            print(f"[DEBUG] Search error: {results.error}")
            print(f"[DEBUG] Documents found: {len(results.documents)}")
            print(f"[DEBUG] Sample metadata: {results.metadata[:2] if results.metadata else 'None'}")
            
            # Check for search errors
            assert results.error is None, f"Vector store search failed for query '{query}': {results.error}"
            
            # At least one query should return results if data exists
            if not results.is_empty():
                print(f"[DEBUG] ✓ Found results for query: '{query}'")
                break
        else:
            pytest.fail("No search queries returned results - vector store may be empty or misconfigured")

    def test_course_search_tool_execute_detailed(self, search_tool_real):
        """Debug test: Detailed testing of CourseSearchTool.execute method"""
        test_queries = [
            # Basic queries
            "Python",
            "programming", 
            "introduction",
            
            # Course-specific queries (if courses exist)
            "lesson",
            "course content",
            
            # Empty/edge cases  
            "",
            "nonexistent_topic_xyz_123"
        ]
        
        for query in test_queries:
            print(f"\n[DEBUG] Testing CourseSearchTool.execute with query: '{query}'")
            
            try:
                result = search_tool_real.execute(query)
                print(f"[DEBUG] Result type: {type(result)}")
                print(f"[DEBUG] Result length: {len(result)}")
                print(f"[DEBUG] Result preview: {result[:200]}...")
                
                # Check for specific error patterns
                if "query failed" in result.lower():
                    pytest.fail(f"CourseSearchTool.execute returned 'query failed' for query '{query}': {result}")
                
                if result.strip() == "":
                    pytest.fail(f"CourseSearchTool.execute returned empty string for query '{query}'")
                
                # Track successful searches
                if "No relevant content found" not in result and query.strip():
                    print(f"[DEBUG] ✓ Successful search result for: '{query}'")
                    
                    # Verify sources were tracked
                    print(f"[DEBUG] Sources tracked: {len(search_tool_real.last_sources)}")
                    print(f"[DEBUG] Source details: {search_tool_real.last_sources}")
                    
            except Exception as e:
                pytest.fail(f"CourseSearchTool.execute raised exception for query '{query}': {str(e)}")

    def test_course_search_tool_with_filters(self, search_tool_real, real_vector_store):
        """Debug test: Test CourseSearchTool with course name and lesson filters"""
        # Get actual course titles to test with
        existing_titles = real_vector_store.get_existing_course_titles()
        
        if not existing_titles:
            pytest.skip("No courses available to test filters")
        
        course_title = existing_titles[0]
        print(f"\n[DEBUG] Testing with course filter: '{course_title}'")
        
        # Test with course name filter
        result = search_tool_real.execute("introduction", course_name=course_title)
        print(f"[DEBUG] Filtered search result: {result[:200]}...")
        
        assert "query failed" not in result.lower(), f"Filtered search failed: {result}"
        
        # Test with invalid course name
        result = search_tool_real.execute("introduction", course_name="NonexistentCourse123")
        print(f"[DEBUG] Invalid course filter result: {result}")
        
        # Should return appropriate "not found" message, not "query failed"
        assert "query failed" not in result.lower(), f"Invalid course filter caused 'query failed': {result}"

    def test_vector_store_embedding_model(self, real_vector_store):
        """Debug test: Check if embedding model is working correctly"""
        print(f"\n[DEBUG] Embedding model: {real_vector_store.embedding_model}")
        
        # Test if embeddings can be generated
        try:
            # This should work if the embedding model is properly initialized
            test_texts = ["test text for embedding"]
            # Note: We can't directly access the embedding function, but search should work
            results = real_vector_store.search("test")
            print(f"[DEBUG] Embedding test search error: {results.error}")
            
            if results.error and "embedding" in results.error.lower():
                pytest.fail(f"Embedding model error detected: {results.error}")
                
        except Exception as e:
            pytest.fail(f"Embedding model test failed: {str(e)}")

    def test_chroma_database_integrity(self, real_vector_store):
        """Debug test: Check ChromaDB database integrity"""
        print(f"\n[DEBUG] ChromaDB path: {real_vector_store.chroma_path}")
        
        # Check if database files exist
        db_path = real_vector_store.chroma_path
        if not os.path.exists(db_path):
            pytest.fail(f"ChromaDB directory does not exist: {db_path}")
        
        # Check if there are any database files
        db_files = os.listdir(db_path) if os.path.exists(db_path) else []
        print(f"[DEBUG] Database files: {db_files}")
        
        if not db_files:
            pytest.fail(f"ChromaDB directory is empty: {db_path}")
        
        # Test if collections can be accessed
        try:
            # The vector store should have initialized collections
            course_count = real_vector_store.get_course_count()
            print(f"[DEBUG] Successfully accessed database, course count: {course_count}")
        except Exception as e:
            pytest.fail(f"ChromaDB access error: {str(e)}")
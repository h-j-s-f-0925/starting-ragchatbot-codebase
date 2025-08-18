import pytest
import sys
import os
import traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_store import VectorStore
from search_tools import ToolManager, CourseSearchTool, CourseOverviewTool
from config import config


class TestMCPCourseResolution:
    """Specific tests for MCP course resolution and lesson 5 content"""

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

    def test_course_catalog_contents(self, vector_store):
        """Test what courses are actually in the database"""
        print(f"\n=== Testing course catalog contents ===")
        
        try:
            # Get all course titles
            course_titles = vector_store.get_existing_course_titles()
            print(f"Found {len(course_titles)} courses in database:")
            for i, title in enumerate(course_titles, 1):
                print(f"  {i}. {title}")
            
            # Check if MCP-related course exists
            mcp_courses = [title for title in course_titles if "mcp" in title.lower() or "model context protocol" in title.lower()]
            print(f"\nMCP-related courses found: {mcp_courses}")
            
            assert len(course_titles) > 0, "No courses found in database"
            
        except Exception as e:
            print(f"Error getting course catalog: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise

    def test_mcp_course_name_resolution(self, vector_store):
        """Test resolution of MCP course name variations"""
        print(f"\n=== Testing MCP course name resolution ===")
        
        variations = [
            "MCP",
            "mcp", 
            "MCP course",
            "Model Context Protocol",
            "model context protocol",
            "MCPコース"
        ]
        
        for variation in variations:
            print(f"\nTesting variation: '{variation}'")
            try:
                resolved = vector_store._resolve_course_name(variation)
                print(f"  Resolved to: {resolved}")
                
                if resolved:
                    # Get course metadata to verify
                    all_courses = vector_store.get_all_courses_metadata()
                    matching_course = None
                    for course in all_courses:
                        if course.get('title') == resolved:
                            matching_course = course
                            break
                    
                    if matching_course:
                        print(f"  Course metadata found: {matching_course.get('title')}")
                        lessons = matching_course.get('lessons', [])
                        print(f"  Total lessons: {len(lessons)}")
                        
                        # Check for lesson 5 specifically
                        lesson_5 = None
                        for lesson in lessons:
                            if lesson.get('lesson_number') == 5:
                                lesson_5 = lesson
                                break
                        
                        if lesson_5:
                            print(f"  Lesson 5 found: {lesson_5.get('lesson_title')}")
                        else:
                            print(f"  Lesson 5 NOT found in course")
                    else:
                        print(f"  Course metadata NOT found for resolved title")
                else:
                    print(f"  Failed to resolve course name")
                    
            except Exception as e:
                print(f"  Error resolving '{variation}': {type(e).__name__}: {str(e)}")

    def test_lesson_5_content_search(self, vector_store):
        """Test searching for lesson 5 content specifically"""
        print(f"\n=== Testing lesson 5 content search ===")
        
        # First, try to resolve MCP course name
        course_name = vector_store._resolve_course_name("MCP")
        if not course_name:
            pytest.skip("MCP course not found in database")
        
        print(f"Using resolved course name: {course_name}")
        
        # Test various search queries for lesson 5
        search_queries = [
            "lesson 5",
            "レッスン5", 
            "fifth lesson",
            "lesson five",
            "5"
        ]
        
        for query in search_queries:
            print(f"\nTesting search query: '{query}'")
            try:
                results = vector_store.search(
                    query=query,
                    course_name=course_name,
                    lesson_number=5
                )
                
                print(f"  Error: {results.error}")
                print(f"  Documents found: {len(results.documents)}")
                
                if results.documents:
                    print(f"  First result preview: {results.documents[0][:100]}...")
                    print(f"  Metadata: {results.metadata[0] if results.metadata else 'No metadata'}")
                
            except Exception as e:
                print(f"  Search error for '{query}': {type(e).__name__}: {str(e)}")

    def test_lesson_content_by_number(self, vector_store):
        """Test getting content for each lesson number"""
        print(f"\n=== Testing lesson content by number ===")
        
        course_name = vector_store._resolve_course_name("MCP")
        if not course_name:
            pytest.skip("MCP course not found in database")
        
        print(f"Using resolved course name: {course_name}")
        
        # Test lessons 1-10
        for lesson_num in range(1, 11):
            print(f"\nTesting lesson {lesson_num}:")
            try:
                results = vector_store.search(
                    query="content",
                    course_name=course_name,
                    lesson_number=lesson_num
                )
                
                if results.error:
                    print(f"  Error: {results.error}")
                elif results.documents:
                    print(f"  Found {len(results.documents)} documents")
                    print(f"  Preview: {results.documents[0][:100]}...")
                else:
                    print(f"  No content found")
                    
            except Exception as e:
                print(f"  Error for lesson {lesson_num}: {type(e).__name__}: {str(e)}")

    def test_course_overview_tool_mcp(self, tool_manager):
        """Test course overview tool specifically for MCP"""
        print(f"\n=== Testing course overview tool for MCP ===")
        
        try:
            result = tool_manager.execute_tool("get_course_overview", course_title="MCP")
            print(f"Overview result:\n{result}")
            
            # Check if overview contains expected elements
            assert "Course Title:" in result, "Missing course title in overview"
            assert "Instructor:" in result, "Missing instructor in overview"
            assert "Lesson" in result, "Missing lesson information in overview"
            
            # Check for lesson 5 specifically
            if "Lesson 5:" in result:
                print("✓ Lesson 5 found in course overview")
            else:
                print("✗ Lesson 5 NOT found in course overview")
                print("Available lessons in overview:")
                lines = result.split('\n')
                for line in lines:
                    if 'Lesson' in line and ':' in line:
                        print(f"  {line.strip()}")
                        
        except Exception as e:
            print(f"Course overview tool error: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise

    def test_course_search_tool_mcp_lesson5(self, tool_manager):
        """Test course search tool for MCP lesson 5"""
        print(f"\n=== Testing course search tool for MCP lesson 5 ===")
        
        search_scenarios = [
            {"query": "lesson 5", "course_name": "MCP", "lesson_number": None},
            {"query": "content", "course_name": "MCP", "lesson_number": 5},
            {"query": "topics", "course_name": "MCP", "lesson_number": 5},
            {"query": "レッスン5", "course_name": "MCP", "lesson_number": None}
        ]
        
        for scenario in search_scenarios:
            print(f"\nTesting scenario: {scenario}")
            try:
                result = tool_manager.execute_tool("search_course_content", **scenario)
                print(f"Search result length: {len(result)}")
                print(f"Result preview: {result[:200]}...")
                
                # Check for error indicators
                if "No relevant content found" in result:
                    print("⚠ No content found for this search")
                elif "error" in result.lower():
                    print("✗ Error in search result")
                else:
                    print("✓ Content found")
                    
            except Exception as e:
                print(f"Search tool error: {type(e).__name__}: {str(e)}")

    def test_similar_topics_search(self, tool_manager):
        """Test searching for similar topics across courses"""
        print(f"\n=== Testing similar topics search ===")
        
        # First, try to get lesson 5 content from MCP
        try:
            mcp_lesson5_result = tool_manager.execute_tool(
                "search_course_content",
                query="content",
                course_name="MCP", 
                lesson_number=5
            )
            
            print(f"MCP Lesson 5 content: {mcp_lesson5_result[:200]}...")
            
            # If we found content, extract key topics and search for similar
            if "No relevant content found" not in mcp_lesson5_result:
                # Search for similar topics in other courses
                similar_topics_result = tool_manager.execute_tool(
                    "search_course_content",
                    query="similar topics across courses"
                )
                
                print(f"Similar topics search: {similar_topics_result[:200]}...")
            else:
                print("Cannot test similar topics - no lesson 5 content found")
                
        except Exception as e:
            print(f"Similar topics search error: {type(e).__name__}: {str(e)}")
            traceback.print_exc()

    def test_database_integrity(self, vector_store):
        """Test database integrity for MCP course data"""
        print(f"\n=== Testing database integrity ===")
        
        try:
            # Test course catalog collection
            print("Testing course catalog collection...")
            course_count = vector_store.get_course_count()
            print(f"Total courses: {course_count}")
            
            # Test course content collection
            print("Testing course content collection...")
            # Try a general search to see if content exists
            results = vector_store.search("test")
            print(f"General search returned {len(results.documents)} documents")
            
            if results.documents:
                print("Sample content metadata:")
                for i, meta in enumerate(results.metadata[:3]):
                    print(f"  {i+1}. {meta}")
            
            # Check for MCP specifically in content
            mcp_results = vector_store.search("MCP")
            print(f"MCP search returned {len(mcp_results.documents)} documents")
            
        except Exception as e:
            print(f"Database integrity error: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            raise

if __name__ == "__main__":
    # Allow running individual tests for debugging
    pytest.main([__file__, "-v", "-s"])
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Course Materials RAG (Retrieval-Augmented Generation) System built with FastAPI, ChromaDB, and Anthropic's Claude. The application enables users to query course materials through a web interface, providing AI-powered responses with source attribution.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Set up environment variables (required)
# Create .env file with: ANTHROPIC_API_KEY=your_key_here
```

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Accessing the Application
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Architecture Overview

### Core RAG Pipeline
The system follows a modular RAG architecture with these key components:

1. **Document Processing (`document_processor.py`)**: Parses structured course documents, extracts metadata (course title, instructor, lessons), and creates overlapping text chunks
2. **Vector Storage (`vector_store.py`)**: Uses ChromaDB with sentence-transformers embeddings for semantic search over course content
3. **AI Generation (`ai_generator.py`)**: Integrates with Claude API using tool-calling for search-augmented response generation
4. **Session Management (`session_manager.py`)**: Tracks conversation history for context-aware responses
5. **Search Tools (`search_tools.py`)**: Implements tool-based search interface that Claude can call to retrieve relevant content

### Key Data Flow
```
User Query → FastAPI → RAGSystem → Claude (with tools) → Search Tool → Vector Store → Response
```

### Document Structure Expected
Course documents must follow this format:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [instructor]

Lesson 0: Introduction
Lesson Link: [lesson_url]
[lesson content]

Lesson 1: [title]
[lesson content]
```

## Configuration (`config.py`)

Key settings:
- `CHUNK_SIZE: 800` - Text chunk size for vector storage
- `CHUNK_OVERLAP: 100` - Character overlap between chunks
- `MAX_RESULTS: 5` - Maximum search results returned
- `MAX_HISTORY: 2` - Conversation messages remembered
- `ANTHROPIC_MODEL: "claude-sonnet-4-20250514"` - Claude model used
- `EMBEDDING_MODEL: "all-MiniLM-L6-v2"` - Sentence transformer model

## Component Interactions

### RAG System Orchestration
`RAGSystem` in `rag_system.py` coordinates all components:
- Initializes vector store, AI generator, session manager, and search tools
- Processes document additions with metadata extraction and chunking
- Handles queries by managing conversation history and tool execution

### Tool-Based Search
The system uses Anthropic's tool calling feature:
- `CourseSearchTool` defines search capabilities for Claude
- Claude decides when to search based on query content
- Search results are formatted with course/lesson context
- Sources are tracked for UI display

### Vector Search Strategy
ChromaDB collections store:
- Course metadata for high-level information
- Content chunks with rich metadata (course_title, lesson_number, chunk_index)
- Semantic search using sentence-transformers embeddings

## Frontend Integration

Simple HTML/CSS/JavaScript frontend (`frontend/`):
- Communicates via `/api/query` and `/api/courses` endpoints
- Manages session state and conversation history
- Displays responses with collapsible source attribution

## Data Persistence

- ChromaDB database: `./chroma_db/` (created automatically)
- Course documents: `docs/` directory (loaded on startup)
- Session data: In-memory only (resets on restart)

## Important Implementation Notes

- Document processing expects UTF-8 encoding with fallback error handling
- Chunk overlap ensures context continuity across chunk boundaries
- Session history is limited to prevent context window overflow
- Vector store checks for existing courses to avoid duplication
- Tool execution includes source tracking for transparency
- Error handling preserves user experience with graceful degradation
- サーバー実行は必ずUVを使い、pipは直接使わない
- すべての依存関係を管理するためにuv を使ってください。
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) chatbot system for educational course materials. It uses a tool-based AI architecture where Claude autonomously decides when to search course content via semantic vector search.

**Key Architecture Pattern**: Tool-based RAG with agentic AI behavior
- Claude receives tool definitions and decides when to search
- Two-phase AI interaction: tool decision → tool execution → synthesis
- Vector search provides context, AI synthesizes natural responses

**IMPORTANT**: This project uses `uv` as the package manager. Always use `uv` commands, never `pip` directly.

## Running the Application

```bash
# Quick start (from project root)
./run.sh

# Manual start (if run.sh fails)
cd backend
uv run uvicorn app:app --reload --port 8000
```

**Access points:**
- Web UI: http://localhost:8000
- API docs: http://localhost:8000/docs

**Prerequisites:**
- Python 3.13+
- `uv` package manager
- API key in `.env` file (supports both Anthropic and OpenRouter)

## Environment Configuration

The system supports both direct Anthropic API and OpenRouter:

**For Anthropic (direct):**
```bash
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
# ANTHROPIC_BASE_URL=  # Leave empty or omit
```

**For OpenRouter:**
```bash
ANTHROPIC_API_KEY=sk-or-v1-...
ANTHROPIC_MODEL=anthropic/claude-sonnet-4-20250514
ANTHROPIC_BASE_URL=https://openrouter.ai/api/v1
```

**Note**: The `.env` file should be located at `backend/.env` (see `backend/config.py:6`).

## Core Architecture

### Request Flow (Query Processing)

```
Frontend (script.js)
  → POST /api/query
  → app.py:query_documents()
  → rag_system.py:query()
  → ai_generator.py:generate_response()
  → Claude API Call #1 (with tools)
  → [IF tool_use] tool_manager.execute_tool()
  → vector_store.search() → ChromaDB
  → Claude API Call #2 (with results)
  → Response with sources
```

### Component Responsibilities

**app.py** - FastAPI application
- Endpoints: `/api/query` (chat), `/api/courses` (stats)
- Startup event loads documents from `../docs` folder
- Serves frontend static files from `../frontend`

**rag_system.py** - Main orchestrator
- Coordinates all components (document processor, vector store, AI generator, session manager)
- `query()` method: manages full RAG pipeline
- `add_course_folder()`: ingests documents into vector store
- Retrieves sources from tool manager after search

**ai_generator.py** - Claude API integration
- `__init__`: accepts optional `base_url` for OpenRouter support
- `generate_response()`: handles two-phase tool calling
- `_handle_tool_execution()`: executes tools and sends results back to Claude
- System prompt defines tool usage behavior (search only when needed)

**search_tools.py** - Tool system
- `CourseSearchTool`: implements vector search with filtering
- `ToolManager`: registers tools, provides definitions to Claude
- **Important**: `last_sources` tracking - search tool stores sources for UI display
- Sources must be retrieved via `get_last_sources()` then reset with `reset_sources()`

**vector_store.py** - ChromaDB interface
- `search()`: unified search with course/lesson filtering
- Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings
- Stores course metadata separately from content chunks

**document_processor.py** - Document parsing
- Expects structured format: Course Title/Link/Instructor + Lesson sections
- Chunks text with overlap (default: 800 chars, 100 overlap)
- Creates `CourseChunk` objects with metadata for vector storage

**session_manager.py** - Conversation history
- Maintains per-session message history (default: last 2 exchanges)
- Formats history as text for Claude's context
- Session IDs: `session_1`, `session_2`, etc.

### Data Models (models.py)

```python
Course
  - title: str (unique identifier)
  - course_link, instructor: Optional[str]
  - lessons: List[Lesson]

Lesson
  - lesson_number: int
  - title: str
  - lesson_link: Optional[str]

CourseChunk
  - content: str
  - course_title: str
  - lesson_number: Optional[int]
  - chunk_index: int
```

## Key Implementation Details

### Tool Calling Flow

1. **Tool Registration**: `rag_system.py` registers `CourseSearchTool` with `ToolManager`
2. **Tool Definitions**: Sent to Claude via `tool_manager.get_tool_definitions()`
3. **Claude Decision**: Claude returns `stop_reason="tool_use"` if search needed
4. **Execution**: `ai_generator._handle_tool_execution()` calls tools and builds conversation
5. **Second Call**: Claude receives tool results and synthesizes final answer
6. **Source Tracking**: Search tool stores sources in `last_sources` attribute

**Critical**: The two-phase approach means you must:
- Check `response.stop_reason == "tool_use"` after first call
- Add assistant message with tool_use block to conversation
- Execute tools and add tool_result block
- Make second API call without tools parameter

### Vector Store Search

The search supports three modes:
1. Pure semantic search: `search(query="topic")`
2. Course-filtered: `search(query="topic", course_name="partial name")`
3. Lesson-filtered: `search(query="topic", lesson_number=2)`

Course name matching is fuzzy (partial match on title).

### Document Format Expected

```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [title]
Lesson Link: [url]
[content...]

Lesson 1: [title]
[content...]
```

Files should be placed in `docs/` folder. Supported: `.txt`, `.pdf`, `.docx`

## Configuration Parameters

Located in `backend/config.py`:

```python
CHUNK_SIZE = 800          # Text chunk size for vector storage
CHUNK_OVERLAP = 100       # Overlap between chunks
MAX_RESULTS = 5           # Vector search results to return
MAX_HISTORY = 2           # Conversation message pairs to remember
CHROMA_PATH = "./chroma_db"  # Vector database location
```

## Common Modifications

### Adding New Tools

1. Create tool class inheriting from `Tool` (in `search_tools.py`)
2. Implement `get_tool_definition()` - returns Anthropic tool schema
3. Implement `execute(**kwargs)` - performs tool action
4. Register in `rag_system.py:__init__`: `tool_manager.register_tool(tool_instance)`

### Changing AI Behavior

Edit system prompt in `ai_generator.py:SYSTEM_PROMPT`
- Controls when Claude uses tools
- Response style and format
- Search strategy

### Supporting New LLM Providers

The `base_url` parameter in `AIGenerator.__init__` supports any Anthropic-compatible API:
1. Add provider URL to `.env` as `ANTHROPIC_BASE_URL`
2. Use provider's API key format in `ANTHROPIC_API_KEY`
3. Use provider's model naming in `ANTHROPIC_MODEL`

## Development Workflow

**CRITICAL**: Always use `uv` for all Python operations. Never use `pip`, `python`, or `python3` directly.

**Installing dependencies:**
```bash
uv sync  # Install/sync all dependencies from pyproject.toml
```

**Adding new dependencies:**
```bash
uv add package-name  # Add a new package
uv add --dev package-name  # Add a dev dependency
```

**Running Python commands:**
```bash
uv run python script.py  # Run Python scripts
uv run uvicorn app:app --reload  # Run the server
```

**Running with auto-reload:**
```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

**Adding documents:**
Place files in `docs/` folder - they load automatically on server startup.

**Clearing vector database:**
Delete `backend/chroma_db/` directory and restart server.

**Testing changes:**
- Frontend changes: Refresh browser (no-cache headers in dev mode)
- Backend changes: Auto-reload enabled with `--reload` flag
- New documents: Restart server or call `rag_system.add_course_folder()`

## Frontend Integration

**JavaScript (script.js):**
- `sendMessage()`: Main query handler
- Uses `marked.parse()` for markdown rendering
- Displays sources in collapsible `<details>` element
- Session ID managed in `currentSessionId` global variable

**API Contract:**
```javascript
// Request
POST /api/query
{ query: string, session_id?: string }

// Response
{
  answer: string,           // Markdown-formatted
  sources: string[],        // ["Course - Lesson N", ...]
  session_id: string
}
```

## Important Gotchas

1. **Source Tracking**: Must call `tool_manager.reset_sources()` after retrieving sources, or they persist across queries
2. **Base URL**: Empty string `""` is different from `None` - use conditional check `if config.ANTHROPIC_BASE_URL else None`
3. **Conversation History**: Limited to `MAX_HISTORY * 2` messages (pairs of user/assistant)
4. **Tool Results Format**: Must use specific structure with `tool_use_id` matching the request
5. **Session Management**: Sessions are in-memory only - restart clears all sessions
6. **Document Processing**: Files only load on startup; changes require server restart or manual reload

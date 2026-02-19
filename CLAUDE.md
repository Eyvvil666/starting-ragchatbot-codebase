# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Start the server (from repo root)
./run.sh

# Start manually (equivalent to run.sh)
cd backend && uv run uvicorn app:app --reload --port 8000
```

The app runs on `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Environment

Requires a `.env` file in the repo root (not `backend/`):
```
ANTHROPIC_API_KEY=sk-ant-...
```

`config.py` uses `load_dotenv()` which resolves relative to the working directory — `run.sh` sets this correctly by running uvicorn from `backend/` after `cd`.

## Architecture

This is a RAG chatbot that answers questions about course materials. The backend is FastAPI; the frontend is plain HTML/JS served as static files by FastAPI itself.

**Request flow for `POST /api/query`:**

1. `app.py` — receives request, creates session if needed, calls `RAGSystem.query()`
2. `rag_system.py` — fetches conversation history, wraps the query in a prompt, calls `AIGenerator`
3. `ai_generator.py` — makes a first Claude API call with the `search_course_content` tool available
   - If Claude responds directly (`stop_reason=end_turn`): returns the text
   - If Claude calls the tool (`stop_reason=tool_use`): executes tool, makes a second Claude call with results, returns final text
4. `search_tools.py` / `vector_store.py` — tool execution: embeds the query with `all-MiniLM-L6-v2`, searches ChromaDB `course_content` collection, returns top-5 chunks
5. `session_manager.py` — conversation history is saved (capped at `MAX_HISTORY=2` turns)

**Key design decisions:**
- Claude autonomously decides whether to search (tool-use) or answer from general knowledge
- Two ChromaDB collections: `course_catalog` (course-level index for fuzzy name matching) and `course_content` (chunk-level for semantic search)
- Session state is in-memory only; it resets when the server restarts
- Course documents are loaded from `../docs/` at startup; already-indexed courses are skipped (dedup by title)

**Course document format** (`docs/*.txt`):
```
Course Title: ...
Course Link: ...
Course Instructor: ...

Lesson 0: Title
Lesson Link: ...
lesson body text...

Lesson 1: Title
...
```
`DocumentProcessor` parses this format, splits lessons into 800-character chunks with 100-character overlap.

## Key Configuration (`backend/config.py`)

| Setting | Default | Purpose |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Model used for generation |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local embedding model (sentence-transformers) |
| `CHUNK_SIZE` | `800` | Max characters per vector chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between adjacent chunks |
| `MAX_RESULTS` | `5` | ChromaDB results returned per search |
| `MAX_HISTORY` | `2` | Conversation turns retained per session |
| `CHROMA_PATH` | `./chroma_db` | ChromaDB persistence path (relative to `backend/`) |

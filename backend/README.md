# OpenAgentRAG Backend

Self-hostable agentic RAG platform backend built with FastAPI, CrewAI, LangChain, and ChromaDB.

## Features

- **Document Processing**: Extract text from PDF, DOCX, XLSX, TXT, and URLs
- **Semantic Chunking**: Intelligent text chunking based on semantic similarity
- **Hybrid Retrieval**: Vector similarity search with ChromaDB
- **LLM Generation**: Answer generation using Ollama (llama3 default)
- **Quality Evaluation**: Automatic evaluation of answer relevance, groundedness, and hallucination risk
- **Agent Orchestration**: CrewAI agents for ingestion, embedding, retrieval, and evaluation
- **Chat History**: Persistent chat sessions with SQLite
- **REST API**: Complete FastAPI REST endpoints

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Ollama running locally or remotely
- ChromaDB running locally or remotely

### Installation

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# Ensure OLLAMA_BASE_URL and CHROMA_HOST are correct
```

### Run

```bash
# Run with Poetry
poetry run uvicorn main:app --reload

# Or activate virtual environment and run
poetry shell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at http://localhost:8000

- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Documents

- `POST /api/documents/upload` - Upload and process document
- `POST /api/documents/ingest-url` - Ingest from URL
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document and embeddings

### Chat

- `POST /api/chat/query` - Send query to RAG system
- `GET /api/chat/history/{session_id}` - Get chat history
- `DELETE /api/chat/history/{session_id}` - Clear chat history
- `GET /api/chat/sessions` - List all sessions

### Settings

- `GET /api/settings/` - Get all settings
- `PUT /api/settings/` - Update setting
- `GET /api/settings/status` - Health check (Ollama, ChromaDB, Database)
- `GET /api/settings/config` - Get configuration

## Architecture

```
backend/
├── agents/          # CrewAI agents for RAG workflows
├── config/          # Configuration and settings
├── database/        # SQLAlchemy models and ChromaDB client
├── rag/            # RAG components (chunking, embedding, retrieval, generation)
├── routers/        # FastAPI route handlers
├── services/       # Business logic services
└── main.py         # FastAPI application entry point
```

## Configuration

See `.env.example` for all configuration options:

- **OLLAMA_BASE_URL**: Ollama API URL (default: http://ollama:11434)
- **LLM_MODEL**: Model name (default: llama3)
- **CHROMA_HOST**: ChromaDB host (default: chromadb)
- **CHROMA_PORT**: ChromaDB port (default: 8000)
- **EMBEDDING_MODEL**: Sentence transformer model (default: sentence-transformers/all-MiniLM-L6-v2)
- **CHUNK_SIZE**: Maximum chunk size (default: 512)
- **CHUNK_OVERLAP**: Chunk overlap (default: 50)

## Docker

```bash
# Build image
docker build -t openagentrag-backend .

# Run container
docker run -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e CHROMA_HOST=host.docker.internal \
  -v $(pwd)/data:/app/data \
  openagentrag-backend
```

## Development

```bash
# Install dev dependencies
poetry install

# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Run tests
poetry run pytest
```

## License

MIT

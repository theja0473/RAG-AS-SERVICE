# System Folder Structure

Complete directory layout of the OpenAgentRAG repository with descriptions of each file and directory.

---

## Repository Root

```
open-agent-rag/
├── backend/                    # Python FastAPI backend service
│   ├── agents/                 # CrewAI agent definitions
│   │   ├── __init__.py
│   │   ├── crew.py             # Agent crew orchestration (IngestionCrew, QueryCrew)
│   │   ├── data_ingestion_agent.py  # Document extraction tools (PDF, DOCX, XLSX, TXT, URL)
│   │   ├── embedding_agent.py  # Embedding generation and vector storage
│   │   ├── evaluation_agent.py # Response quality evaluation metrics
│   │   └── retrieval_agent.py  # Vector database search and retrieval
│   ├── config/                 # Application configuration
│   │   ├── __init__.py
│   │   └── settings.py         # Pydantic Settings (loads from .env)
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── chromadb_client.py  # ChromaDB vector database client wrapper
│   │   ├── models.py           # SQLAlchemy models (Document, ChatHistory, EvaluationLog, Settings)
│   │   └── session.py          # Async SQLAlchemy engine and session management
│   ├── rag/                    # RAG pipeline implementation
│   │   ├── __init__.py
│   │   ├── chunking.py         # Semantic text chunking with fallback splitter
│   │   ├── embedding.py        # Embedding manager (SentenceTransformers)
│   │   ├── generator.py        # LLM answer generation via Ollama
│   │   └── retriever.py        # Hybrid retrieval with similarity scoring
│   ├── routers/                # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── chat.py             # /api/chat/* endpoints (query, history, sessions)
│   │   ├── documents.py        # /api/documents/* endpoints (upload, list, delete)
│   │   └── settings.py         # /api/settings/* endpoints (config, status, health)
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── chat_service.py     # RAG pipeline orchestration for chat queries
│   │   └── document_service.py # Document ingestion pipeline orchestration
│   ├── data/                   # Runtime data directory (gitignored)
│   │   └── uploads/            # Uploaded document storage
│   ├── .env.example            # Backend environment variable template
│   ├── .gitignore              # Backend-specific git ignores
│   ├── Dockerfile              # Backend container definition
│   ├── main.py                 # FastAPI application entry point
│   ├── pyproject.toml          # Poetry project configuration
│   ├── requirements.txt        # pip dependency list
│   ├── start.sh                # Development startup script
│   └── README.md               # Backend documentation
│
├── frontend/                   # Next.js frontend application
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   │   ├── chat/
│   │   │   │   └── page.tsx    # Chat interface (RAG query UI)
│   │   │   ├── documents/
│   │   │   │   └── page.tsx    # Document management (upload, list, delete)
│   │   │   ├── settings/
│   │   │   │   └── page.tsx    # Settings panel (service config, health status)
│   │   │   ├── globals.css     # Global styles and Tailwind component layers
│   │   │   ├── layout.tsx      # Root layout with Sidebar navigation
│   │   │   └── page.tsx        # Home page (redirects to /chat)
│   │   ├── components/         # Reusable React components
│   │   │   ├── ChatMessage.tsx # Chat message with markdown rendering
│   │   │   ├── FileUpload.tsx  # Drag-and-drop file upload component
│   │   │   ├── Sidebar.tsx     # Navigation sidebar with active link highlighting
│   │   │   ├── SourceCard.tsx  # Expandable source citation card
│   │   │   └── StatusBadge.tsx # Service status indicator (online/offline)
│   │   └── lib/
│   │       └── api.ts          # Centralized API client for backend communication
│   ├── .env.example            # Frontend environment variable template
│   ├── .gitignore              # Frontend-specific git ignores
│   ├── Dockerfile              # Multi-stage production container
│   ├── next.config.js          # Next.js configuration with API rewrites
│   ├── package.json            # Node.js dependencies and scripts
│   ├── postcss.config.js       # PostCSS configuration for Tailwind
│   ├── tailwind.config.ts      # TailwindCSS theme and plugin configuration
│   ├── tsconfig.json           # TypeScript compiler configuration
│   └── README.md               # Frontend documentation
│
├── docs/                       # Project documentation
│   ├── Agent_Workflow.md       # Agent architecture, roles, and pipeline flows
│   ├── Agentic_Code_Generation_Workflow.md  # How agents process and generate responses
│   ├── CLAUDE_CODE_MASTER_PROMPT.md         # System prompts and agent configuration
│   ├── Deployment_Guide.md     # Installation, Docker deployment, production setup
│   ├── Development_Roadmap.md  # Phased development plan with milestones
│   ├── Project_Overview.md     # Problem statement, value proposition, target users
│   ├── software_stack.md       # Consolidated technology and version reference
│   ├── System_Folder_Structure.md  # This file - repository layout documentation
│   └── Technical_Architecture.md   # System layers, data flows, API design
│
├── scripts/                    # Utility scripts
│   └── setup.sh                # Post-deployment setup and verification script
│
├── .dockerignore               # Docker build context exclusions
├── .env.example                # Root environment variable template
├── .gitignore                  # Git ignore rules
├── CONTRIBUTING.md             # Contribution guidelines and code standards
├── docker-compose.yml          # Docker Compose service definitions
├── LICENSE                     # Apache License 2.0
└── README.md                   # Project overview and quick start guide
```

---

## Directory Purposes

### `backend/agents/`
Contains CrewAI agent definitions. Each agent is a self-contained module with tools and task definitions. The `crew.py` file orchestrates agents into workflows (IngestionCrew for document processing, QueryCrew for query answering).

### `backend/config/`
Centralized configuration using Pydantic Settings. All values are loaded from environment variables with sensible defaults. The `get_settings()` function provides a cached singleton.

### `backend/database/`
Database access layer with two backends:
- **SQLAlchemy** (async) for metadata storage (documents, chat history, evaluation logs)
- **ChromaDB** client for vector embedding storage and semantic search

### `backend/rag/`
Core RAG pipeline modules:
1. `chunking.py` - Splits documents into semantic chunks
2. `embedding.py` - Generates vector embeddings from text
3. `retriever.py` - Searches ChromaDB for relevant chunks
4. `generator.py` - Generates answers using Ollama LLM

### `backend/routers/`
FastAPI route handlers organized by domain:
- `chat.py` - Query processing and chat history
- `documents.py` - Document upload and management
- `settings.py` - System configuration and health checks

### `backend/services/`
Business logic layer that orchestrates agents and RAG pipeline modules. Services are called by routers and coordinate between multiple components.

### `frontend/src/app/`
Next.js App Router pages. Each subdirectory represents a route:
- `/chat` - Main RAG query interface
- `/documents` - Document management
- `/settings` - System configuration

### `frontend/src/components/`
Reusable React components shared across pages. All components use TypeScript interfaces for props and TailwindCSS for styling.

### `frontend/src/lib/`
Shared utilities. Currently contains `api.ts` which provides a typed API client for all backend endpoints.

---

## Data Flow Through the Structure

```
User Request → frontend/src/lib/api.ts
             → backend/routers/chat.py
             → backend/services/chat_service.py
             → backend/agents/retrieval_agent.py
             → backend/rag/retriever.py
             → backend/database/chromadb_client.py (vector search)
             → backend/rag/generator.py (LLM answer)
             → backend/agents/evaluation_agent.py (quality check)
             → Response back to frontend
```

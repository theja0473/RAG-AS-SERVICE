# Software Stack

This document provides a consolidated view of the technologies, frameworks, and tools used in the OpenAgentRAG platform.

---

## Core Components

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Backend API | FastAPI | 0.109.0+ | REST API, async processing, WebSocket support |
| Frontend | Next.js (App Router) | 14.2.3 | Modern web UI with React Server Components |
| UI Framework | React | 18.3.1 | Component-based UI rendering |
| Vector Database | ChromaDB | 0.4.22+ | Embedding storage and semantic search |
| LLM Inference | Ollama | latest | Local model serving (Llama 3, Mistral, etc.) |
| Agent Framework | CrewAI | 0.1.0+ | Multi-agent orchestration |
| Containerization | Docker + Compose | 24.0+ / 2.0+ | Service orchestration and deployment |

---

## Backend Stack (Python)

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.109.0+ | Web framework |
| Uvicorn | 0.27.0+ | ASGI server |
| SQLAlchemy | 2.0.25+ | ORM / async database access |
| aiosqlite | 0.19.0+ | Async SQLite driver |
| Pydantic | 2.5.0+ | Data validation and settings |
| LangChain | 0.1.0+ | LLM integration framework |
| LangChain-Community | 0.0.13+ | Community integrations (Ollama) |
| Sentence Transformers | 2.3.0+ | Embedding model inference |
| CrewAI | 0.1.0+ | Agent orchestration |
| ChromaDB Client | 0.4.22+ | Vector database client |
| pdfplumber | 0.10.0+ | PDF text extraction |
| python-docx | 1.1.0+ | DOCX parsing |
| openpyxl | 3.1.0+ | XLSX parsing |
| BeautifulSoup4 | 4.12.0+ | HTML parsing |
| httpx | 0.26.0+ | Async HTTP client |

### Dev Dependencies

| Package | Purpose |
|---------|---------|
| pytest + pytest-asyncio | Testing framework |
| black | Code formatting |
| ruff | Linting |
| mypy | Type checking |

---

## Frontend Stack (TypeScript)

| Package | Version | Purpose |
|---------|---------|---------|
| Node.js | 20+ | Runtime |
| Next.js | 14.2.3 | React framework (App Router) |
| React | 18.3.1 | UI library |
| TypeScript | 5.4.5 | Type-safe JavaScript |
| TailwindCSS | 3.4.3 | Utility-first CSS framework |
| lucide-react | latest | Icon library |
| react-markdown | latest | Markdown rendering in chat |
| react-syntax-highlighter | latest | Code block highlighting |
| uuid | latest | Session ID generation |

---

## Infrastructure

| Component | Image / Tool | Purpose |
|-----------|-------------|---------|
| Frontend Container | node:20-alpine | Production Next.js server |
| Backend Container | python:3.11-slim | FastAPI application server |
| Ollama Container | ollama/ollama:latest | LLM inference engine |
| ChromaDB Container | chromadb/chroma:latest | Vector database server |
| Docker Network | bridge (open-agent-rag-network) | Inter-service communication |
| Volumes | ollama_data, chroma_data, backend_data | Persistent storage |

---

## Supported LLM Models (via Ollama)

| Model | Parameters | Use Case |
|-------|-----------|----------|
| Llama 3 | 8B | Default - good quality/speed balance |
| Llama 3 70B | 70B | Higher quality, requires more resources |
| Mistral | 7B | Faster inference, lighter resource usage |
| Mixtral | 8x7B | MoE model, good quality |

---

## Supported Embedding Models

| Model | Dimensions | Use Case |
|-------|-----------|----------|
| all-MiniLM-L6-v2 | 384 | Default - fast, lightweight |
| all-mpnet-base-v2 | 768 | Higher quality, slower |
| multi-qa-MiniLM-L6-cos-v1 | 384 | Optimized for Q&A retrieval |

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RAM | 16 GB | 32 GB |
| Disk Space | 50 GB | 100 GB |
| CPU | 4 cores | 8+ cores |
| GPU | None (CPU inference) | NVIDIA with CUDA |
| Docker | 24.0+ | Latest |
| Docker Compose | 2.0+ | Latest |

---

## Network Ports

| Port | Service | Protocol |
|------|---------|----------|
| 3000 | Frontend (Next.js) | HTTP |
| 8000 | Backend (FastAPI) | HTTP |
| 8100 | ChromaDB | HTTP |
| 11434 | Ollama | HTTP |

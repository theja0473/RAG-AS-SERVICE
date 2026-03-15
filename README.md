# OpenAgentRAG

**Self-hostable agentic RAG platform powered by Ollama, ChromaDB, Neo4j, and CrewAI**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](backend/requirements.txt)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)](frontend/package.json)

OpenAgentRAG is an enterprise-grade, fully self-hostable Retrieval-Augmented Generation (RAG) platform that combines multi-agent orchestration with advanced retrieval techniques. Built on open-source technologies, it enables organizations to deploy intelligent document query systems without relying on external APIs or cloud services.

---

## Features

- **Multi-Agent Architecture**: CrewAI-powered agents for query understanding, retrieval, synthesis, and evaluation
- **Graph RAG**: Knowledge graph integration with Neo4j — entities and relationships are extracted from documents and used to enrich retrieval with connected context
- **Hybrid Retrieval**: Combines semantic search (ChromaDB) with keyword matching and knowledge graph traversal for optimal relevance
- **Query Expansion**: Automatically generates query variations to improve retrieval coverage
- **Self-Improving Pipeline**: Feedback loop for continuous quality enhancement based on user interactions
- **100% Self-Hosted**: Run entirely on your infrastructure with Ollama for LLM inference
- **Multi-Format Support**: Ingest PDFs, DOCX, TXT, Markdown, CSV, and JSON documents
- **Phase-Based Chunking**: Intelligent document segmentation that preserves semantic boundaries
- **Real-Time Evaluation**: Built-in metrics for retrieval relevance, groundedness, and answer quality
- **Modern Web UI**: Next.js 14 frontend with real-time streaming responses
- **Docker-First Deployment**: One-command setup with docker-compose

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           User Interface                             │
│                    (Next.js 14 Web Application)                      │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────────┐
│                         Backend API Layer                            │
│                      (FastAPI Python Service)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ REST API     │  │ WebSocket    │  │ Document Upload &        │  │
│  │ Endpoints    │  │ Streaming    │  │ Processing               │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                        Agent Orchestration                           │
│                   (CrewAI Multi-Agent System)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Query Agent  │──▶│ Retrieval    │──▶│ Synthesis Agent         │  │
│  │ (Expansion)  │  │ Agent        │  │ (Answer Generation)      │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────────────┘  │
│                           │                      │                   │
│                           │                      ▼                   │
│                           │          ┌──────────────────────────┐   │
│                           │          │ Evaluation Agent         │   │
│                           │          │ (Quality Assessment)     │   │
│                           │          └──────────────────────────┘   │
└───────────────────────────┼──────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼─────────┐ ┌───────▼─────────┐ ┌──────▼──────────┐
│  Vector Store   │ │  LLM Inference  │ │  Document Store │
│  (ChromaDB)     │ │  (Ollama)       │ │  (Local FS)     │
│                 │ │                 │ │                 │
│ - Embeddings    │ │ - Llama 3       │ │ - Raw files     │
│ - Semantic      │ │ - Mistral       │ │ - Metadata      │
│   Search        │ │ - Custom models │ │ - Processed     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        │
        │  Graph-enhanced retrieval
        ▼
┌─────────────────┐
│ Knowledge Graph │
│ (Neo4j)         │
│                 │
│ - Entities      │
│ - Relationships │
│ - Graph RAG     │
└─────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- 16GB RAM minimum (32GB recommended for larger models)
- 50GB free disk space (for models and data)
- Optional: NVIDIA GPU with CUDA support for faster inference

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/theja0473/RAG-AS-SERVICE.git
   cd open-agent-rag
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings (defaults work out of the box)
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Pull the LLM model** (required on first run)
   ```bash
   docker compose exec ollama ollama pull llama3
   ```

5. **Access the application**
   - Web UI: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ChromaDB Admin: http://localhost:8100
   - Neo4j Browser: http://localhost:7474 (credentials: neo4j/openagentrag)

### Post-Setup

Run the setup script to verify all services and initialize the system:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This script will:
- Wait for all services to become healthy
- Pull the default LLM model
- Create the default ChromaDB collection
- Verify the complete pipeline

---

## Configuration

All configuration is managed through the `.env` file. Key parameters:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | `llama3` | Ollama model for generation (llama3, mistral, mixtral) |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Model for vector embeddings |
| `CHUNK_SIZE` | `512` | Document chunk size in tokens |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `5` | Number of chunks to retrieve |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity score for retrieval |
| `ENABLE_QUERY_EXPANSION` | `true` | Generate query variations |
| `NUM_QUERY_VARIATIONS` | `2` | Number of query alternatives |
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j connection URI |
| `NEO4J_USERNAME` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `openagentrag` | Neo4j password |
| `GRAPH_RAG_ENABLED` | `true` | Enable knowledge graph enrichment |

See `.env.example` for the complete list of configuration options.

---

## Supported Data Sources

| Format | Extension | Parsing Strategy |
|--------|-----------|------------------|
| PDF | `.pdf` | PyMuPDF with text/table extraction |
| Word | `.docx` | python-docx with style preservation |
| Text | `.txt` | Plain text with UTF-8 encoding |
| Markdown | `.md` | CommonMark parser with header-based chunking |
| CSV | `.csv` | Pandas with configurable delimiter |
| JSON | `.json` | Recursive extraction with JSONPath support |
| HTML | `.html` | BeautifulSoup with boilerplate removal |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI (Python 3.9+) | REST API and async processing |
| **Frontend** | Next.js 14 (React 18) | Modern web interface with App Router |
| **Vector DB** | ChromaDB 0.4+ | Semantic search and embedding storage |
| **Knowledge Graph** | Neo4j 5 Community | Entity/relationship storage and graph traversal |
| **LLM** | Ollama | Local LLM inference engine |
| **Agents** | CrewAI | Multi-agent orchestration framework |
| **Embeddings** | Sentence Transformers | Text-to-vector conversion |
| **Containerization** | Docker + Docker Compose | Service orchestration |

---

## Development

### Running Without Docker

**Backend**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

**External Dependencies**:
- Install Ollama locally: https://ollama.ai
- Run ChromaDB: `docker run -p 8100:8000 chromadb/chroma:latest`
- Run Neo4j: `docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/openagentrag neo4j:5-community`

### Project Structure

```
open-agent-rag/
├── backend/
│   ├── agents/              # CrewAI agent definitions
│   ├── config/              # Application configuration (Pydantic Settings)
│   ├── database/            # SQLAlchemy models, ChromaDB and Neo4j clients
│   ├── rag/                 # RAG pipeline (chunking, embedding, retrieval, graph retrieval, generation)
│   ├── routers/             # FastAPI route handlers
│   ├── services/            # Business logic layer
│   ├── main.py              # FastAPI application entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js 14 App Router pages
│   │   ├── components/      # React components
│   │   └── lib/             # API client
│   ├── Dockerfile
│   └── package.json
├── docs/                    # Detailed documentation
├── scripts/                 # Utility scripts
├── docker-compose.yml
├── .env.example
└── README.md
```

### Testing

```bash
# Backend tests
cd backend
pytest tests/ --cov=app --cov-report=term-missing

# Frontend tests
cd frontend
npm test

# Integration tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Screenshots

_Coming soon: Web UI screenshots showing document upload, chat interface, and evaluation dashboard_

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick contribution workflow**:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest` (backend) and `npm test` (frontend)
5. Commit with conventional commits: `feat: add XYZ capability`
6. Push and create a Pull Request

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Citation

If you use OpenAgentRAG in your research or project, please cite:

```bibtex
@software{openagentrag2026,
  title = {OpenAgentRAG: Self-Hostable Agentic RAG Platform},
  author = {OpenAgentRAG Contributors},
  year = {2026},
  url = {https://github.com/theja0473/RAG-AS-SERVICE},
  version = {0.1.0}
}
```

---

## Roadmap

- [x] Core RAG pipeline with hybrid retrieval
- [x] Multi-agent orchestration with CrewAI
- [x] Docker-based deployment
- [x] Graph RAG with knowledge graph integration (Neo4j)
- [ ] Multi-modal support (images, audio)
- [ ] Fine-tuning pipeline for domain adaptation
- [ ] Kubernetes deployment manifests
- [ ] RESTful API for programmatic access
- [ ] Multi-tenancy support

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/theja0473/RAG-AS-SERVICE/issues)
- **Discussions**: [GitHub Discussions](https://github.com/theja0473/RAG-AS-SERVICE/discussions)

---

**Built with open-source technologies for the open-source community.**

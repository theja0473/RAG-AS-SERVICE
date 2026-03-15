# Deployment Guide

## Prerequisites

- **Docker** v20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** v2.0+ (included with Docker Desktop)
- **16GB RAM** minimum (Ollama + embeddings require significant memory)
- **20GB disk space** (for Docker images, models, and vector data)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org>/open-agent-rag.git
cd open-agent-rag
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if you need to customize defaults:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `CHROMA_HOST` | `chromadb` | ChromaDB hostname |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model name |
| `LLM_MODEL` | `llama3` | Ollama LLM model |
| `CHUNK_SIZE` | `512` | Document chunk size in tokens |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |

### 3. Launch All Services

```bash
docker compose up -d
```

This starts four containers:
- **frontend** (port 3000) - Next.js web UI
- **backend** (port 8000) - FastAPI server
- **ollama** (port 11434) - Local LLM server
- **chromadb** (port 8100) - Vector database

### 4. Pull the LLM Model

```bash
docker compose exec ollama ollama pull llama3
```

This downloads the llama3 model (~4.7GB). Wait for completion.

### 5. Access the Application

Open your browser to [http://localhost:3000](http://localhost:3000)

## Post-Setup Verification

### Check Service Health

```bash
# All containers running
docker compose ps

# Backend health
curl http://localhost:8000/api/settings/status

# Ollama responding
curl http://localhost:11434/api/tags

# ChromaDB responding
curl http://localhost:8100/api/v1/heartbeat
```

### Run Setup Script (Optional)

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Service Details

### Frontend (Next.js)

- **URL**: http://localhost:3000
- **Build**: `docker compose build frontend`
- **Logs**: `docker compose logs -f frontend`

### Backend (FastAPI)

- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Logs**: `docker compose logs -f backend`

### Ollama (LLM)

- **URL**: http://localhost:11434
- **Models**: `docker compose exec ollama ollama list`
- **Pull model**: `docker compose exec ollama ollama pull <model>`
- **Logs**: `docker compose logs -f ollama`

### ChromaDB (Vector Store)

- **URL**: http://localhost:8100
- **Logs**: `docker compose logs -f chromadb`

## Data Persistence

All data is persisted via Docker volumes:

| Volume | Purpose |
|---|---|
| `ollama_data` | Downloaded LLM models |
| `chroma_data` | Vector embeddings |
| `backend_data` | Uploaded documents, SQLite metadata |

To reset all data:
```bash
docker compose down -v
```

## Troubleshooting

### Container won't start

```bash
docker compose logs <service-name>
```

### Out of memory

Ollama requires significant RAM. If the system is slow or crashes:
- Use a smaller model: `docker compose exec ollama ollama pull phi3`
- Update `LLM_MODEL=phi3` in `.env`
- Restart: `docker compose restart backend`

### ChromaDB connection refused

Ensure ChromaDB is fully started before the backend:
```bash
docker compose restart backend
```

### Ollama model not found

```bash
docker compose exec ollama ollama pull llama3
```

### Frontend can't reach backend

Check that the backend container is running and healthy:
```bash
docker compose ps backend
curl http://localhost:8000/docs
```

## Development Mode (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Start local Ollama and ChromaDB first
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Resource Requirements

| Component | RAM | CPU | Disk |
|---|---|---|---|
| Ollama (llama3) | 8GB | 2 cores | 5GB |
| ChromaDB | 1GB | 1 core | Varies |
| Backend | 2GB | 1 core | 500MB |
| Frontend | 512MB | 0.5 core | 200MB |
| **Total** | **~12GB** | **4.5 cores** | **~6GB** |

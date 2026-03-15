# Technical Architecture: OpenAgentRAG

## Overview

This document provides a comprehensive technical specification of OpenAgentRAG's architecture, including system layers, component interactions, data flows, and technology choices.

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Next.js 19 Frontend (React Server Components)                 │  │
│  │  - Chat Interface        - Document Upload                     │  │
│  │  - Response Streaming    - Evaluation Dashboard                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ HTTP/REST + WebSocket
┌──────────────────────────▼───────────────────────────────────────────┐
│                          API Gateway Layer                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                           │  │
│  │  - REST Endpoints        - WebSocket Handlers                  │  │
│  │  - Request Validation    - Rate Limiting                       │  │
│  │  - Authentication        - Logging & Monitoring                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                        Business Logic Layer                           │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Document Ingestion  │  │ RAG Pipeline                        │   │
│  │ - Format Detection  │  │ - Query Processing                  │   │
│  │ - Parsing           │  │ - Hybrid Retrieval                  │   │
│  │ - Chunking          │  │ - Context Assembly                  │   │
│  │ - Embedding         │  │ - Response Generation               │   │
│  └─────────────────────┘  └─────────────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                         Agent Orchestration                           │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  CrewAI Workflow Engine                                        │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   │  │
│  │  │ Query Agent  │ │ Retrieval    │ │ Synthesis Agent      │   │  │
│  │  │ (Expansion)  │ │ Agent        │ │ (Generation)         │   │  │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘   │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ Evaluation Agent (Quality Assessment)                     │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                           Data Layer                                  │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────┐ │
│  │  ChromaDB        │ │  Ollama          │ │  File System         │ │
│  │  (Vector Store)  │ │  (LLM Engine)    │ │  (Document Store)    │ │
│  │                  │ │                  │ │                      │ │
│  │  - Embeddings    │ │  - Llama 3       │ │  - Raw Files         │ │
│  │  - HNSW Index    │ │  - Mistral       │ │  - Processed Chunks  │ │
│  │  - Metadata      │ │  - Custom Models │ │  - Metadata          │ │
│  └──────────────────┘ └──────────────────┘ └──────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Layer Descriptions

### 1. Presentation Layer

**Technology**: Next.js 19 with React 19

**Responsibilities**:
- Render user interface components
- Handle user interactions
- Stream responses in real-time via WebSocket
- Manage client-side state
- Display evaluation metrics and source citations

**Key Components**:

```typescript
// src/app/page.tsx (Server Component)
import { ChatInterface } from '@/components/ChatInterface';
import { DocumentUpload } from '@/components/DocumentUpload';

export default function Home() {
  return (
    <main>
      <ChatInterface />
      <DocumentUpload />
    </main>
  );
}
```

**Features**:
- **Server Components**: Initial HTML rendered server-side for performance
- **Client Components**: Interactive elements with hooks
- **Streaming UI**: Progressive response rendering using React Suspense
- **Real-time Updates**: WebSocket integration for live answer streaming

---

### 2. API Gateway Layer

**Technology**: FastAPI (Python 3.9+)

**Responsibilities**:
- Expose REST endpoints for document upload and query submission
- Handle WebSocket connections for streaming
- Validate requests and enforce rate limits
- Authenticate users (optional, extensible)
- Log requests and metrics

**API Endpoints**:

```python
# app/api/routes.py
from fastapi import APIRouter, UploadFile, HTTPException
from app.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/v1")

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Process a user query through the RAG pipeline.

    Request:
        {
            "query": "What is the maximum voltage?",
            "top_k": 5,
            "enable_expansion": true
        }

    Response:
        {
            "answer": "The maximum voltage is...",
            "sources": [...],
            "evaluation": {...}
        }
    """
    result = await rag_pipeline.process(request.query)
    return result

@router.post("/documents/upload")
async def upload_document(file: UploadFile):
    """Upload and process a document for indexing."""
    await ingestion_service.ingest(file)
    return {"status": "success", "filename": file.filename}

@router.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """Stream query responses in real-time."""
    await websocket.accept()
    query = await websocket.receive_text()

    async for chunk in rag_pipeline.stream(query):
        await websocket.send_json({"type": "chunk", "data": chunk})
```

**Middleware**:
- CORS handling for cross-origin requests
- Request logging with correlation IDs
- Rate limiting (60 requests/minute default)
- Error handling with structured responses

---

### 3. Business Logic Layer

#### Document Ingestion Pipeline

**Flow**:
```
Upload → Format Detection → Parsing → Chunking → Embedding → Storage
```

**Components**:

```python
# app/ingestion/pipeline.py
from typing import List
from app.ingestion.parsers import PDFParser, DOCXParser
from app.ingestion.chunkers import SemanticChunker
from app.core.embeddings import EmbeddingModel

class IngestionPipeline:
    def __init__(self):
        self.parsers = {
            "pdf": PDFParser(),
            "docx": DOCXParser(),
            # ... more parsers
        }
        self.chunker = SemanticChunker(chunk_size=512, overlap=50)
        self.embedder = EmbeddingModel()

    async def ingest(self, file_path: str) -> dict:
        # 1. Detect format
        file_type = self._detect_format(file_path)

        # 2. Parse document
        parser = self.parsers[file_type]
        text, metadata = await parser.parse(file_path)

        # 3. Chunk text
        chunks = self.chunker.chunk(text, metadata)

        # 4. Generate embeddings
        embeddings = self.embedder.embed_batch(chunks)

        # 5. Store in vector DB
        await vector_store.add(chunks, embeddings, metadata)

        return {
            "chunks_created": len(chunks),
            "metadata": metadata
        }
```

**Chunking Strategies**:

1. **Semantic Chunking** (default):
   - Uses sentence embeddings to group semantically similar sentences
   - Preserves paragraph boundaries
   - Handles variable-length chunks based on content

2. **Phase-Based Chunking**:
   - Detects structural markers (headers, sections, phases)
   - Chunks by document structure
   - Ideal for structured documents (contracts, transcripts)

3. **Fixed-Size Chunking**:
   - Simple token-based splitting
   - Configurable overlap
   - Fallback for unstructured text

#### RAG Pipeline

**Architecture**:

```python
# app/rag/pipeline.py
from app.rag.query_expander import QueryExpander
from app.rag.retriever import HybridRetriever
from app.rag.generator import ResponseGenerator

class RAGPipeline:
    def __init__(self, config):
        self.expander = QueryExpander(
            llm=config.llm,
            num_variations=config.num_query_variations
        )
        self.retriever = HybridRetriever(
            vector_store=config.vector_store,
            semantic_weight=0.7,
            keyword_weight=0.3
        )
        self.generator = ResponseGenerator(llm=config.llm)

    async def process(self, query: str) -> dict:
        # Step 1: Expand query
        queries = await self.expander.expand(query)

        # Step 2: Retrieve for each variation
        all_docs = []
        for q in queries:
            docs = await self.retriever.retrieve(q, top_k=5)
            all_docs.extend(docs)

        # Step 3: Deduplicate and rank
        unique_docs = self._deduplicate(all_docs)
        ranked_docs = self._rerank(unique_docs)

        # Step 4: Generate response
        context = self._assemble_context(ranked_docs)
        response = await self.generator.generate(query, context)

        return {
            "answer": response.text,
            "sources": [doc.metadata for doc in ranked_docs],
            "query_variations": queries
        }
```

**Hybrid Retrieval**:

```python
# app/rag/retriever.py
from app.rag.semantic_search import SemanticSearch
from app.rag.keyword_search import BM25Search

class HybridRetriever:
    def __init__(self, vector_store, semantic_weight=0.7, keyword_weight=0.3):
        self.semantic = SemanticSearch(vector_store)
        self.keyword = BM25Search(vector_store)
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

    async def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        # Parallel retrieval
        semantic_results = await self.semantic.search(query, k=top_k*2)
        keyword_results = await self.keyword.search(query, k=top_k*2)

        # Reciprocal Rank Fusion
        fused_scores = self._fuse_scores(semantic_results, keyword_results)

        # Return top-k
        sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in sorted_docs[:top_k]]

    def _fuse_scores(self, semantic_results, keyword_results):
        """Reciprocal Rank Fusion algorithm."""
        fused = {}
        k = 60  # RRF constant

        for rank, doc in enumerate(semantic_results, 1):
            fused[doc.id] = fused.get(doc.id, 0) + self.semantic_weight / (k + rank)

        for rank, doc in enumerate(keyword_results, 1):
            fused[doc.id] = fused.get(doc.id, 0) + self.keyword_weight / (k + rank)

        return fused
```

---

### 4. Agent Orchestration Layer

**Technology**: CrewAI

**Agent Definitions**:

```python
# app/agents/crew_setup.py
from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama

# Initialize Ollama LLM
llm = Ollama(model="llama3", base_url="http://ollama:11434")

# Query Agent: Expands user query
query_agent = Agent(
    role="Query Analyzer",
    goal="Understand user intent and generate effective query variations",
    backstory="""You are an expert at understanding user questions and
    reformulating them for better retrieval. You consider synonyms,
    related concepts, and different phrasings.""",
    llm=llm,
    verbose=True
)

# Retrieval Agent: Finds relevant documents
retrieval_agent = Agent(
    role="Information Retriever",
    goal="Find the most relevant documents for the query",
    backstory="""You are a librarian with deep expertise in information
    retrieval. You know when to use semantic search vs. keyword search
    and how to combine results effectively.""",
    llm=llm,
    verbose=True
)

# Synthesis Agent: Generates answers
synthesis_agent = Agent(
    role="Answer Synthesizer",
    goal="Create accurate, well-grounded answers from retrieved context",
    backstory="""You are a knowledge worker who excels at synthesizing
    information from multiple sources into clear, accurate answers.
    You always cite your sources.""",
    llm=llm,
    verbose=True
)

# Evaluation Agent: Assesses quality
evaluation_agent = Agent(
    role="Quality Evaluator",
    goal="Assess the quality of generated answers",
    backstory="""You are a quality assurance specialist who evaluates
    answers for relevance, groundedness, and completeness. You provide
    constructive feedback.""",
    llm=llm,
    verbose=True
)

# Define tasks
expand_task = Task(
    description="Analyze the query: {query} and generate 2 alternative phrasings",
    agent=query_agent,
    expected_output="List of query variations"
)

retrieve_task = Task(
    description="Retrieve relevant documents for the query variations",
    agent=retrieval_agent,
    expected_output="List of relevant document chunks with metadata"
)

synthesize_task = Task(
    description="Generate an answer based on retrieved documents",
    agent=synthesis_agent,
    expected_output="Final answer with source citations"
)

evaluate_task = Task(
    description="Evaluate the answer quality and groundedness",
    agent=evaluation_agent,
    expected_output="Quality metrics and feedback"
)

# Create crew
crew = Crew(
    agents=[query_agent, retrieval_agent, synthesis_agent, evaluation_agent],
    tasks=[expand_task, retrieve_task, synthesize_task, evaluate_task],
    process="sequential",
    verbose=True
)
```

**Workflow Execution**:

```python
# app/agents/executor.py
async def execute_agent_workflow(query: str) -> dict:
    """Execute the full agent workflow for a query."""

    result = crew.kickoff(inputs={"query": query})

    return {
        "answer": result.tasks[-2].output,  # Synthesis task output
        "evaluation": result.tasks[-1].output,  # Evaluation task output
        "agent_logs": result.logs
    }
```

---

### 5. Data Layer

#### Vector Store: ChromaDB

**Configuration**:

```python
# app/core/vector_store.py
import chromadb
from chromadb.config import Settings

client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "chromadb"),
    port=int(os.getenv("CHROMA_PORT", 8000)),
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

collection = client.get_or_create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"}
)
```

**Operations**:

```python
# Add documents
collection.add(
    embeddings=embeddings,
    documents=texts,
    metadatas=metadata_list,
    ids=doc_ids
)

# Query
results = collection.query(
    query_embeddings=query_embedding,
    n_results=10,
    where={"source": "manual.pdf"}  # Metadata filter
)
```

**Indexing**: Uses HNSW (Hierarchical Navigable Small World) for fast approximate nearest neighbor search.

#### LLM Engine: Ollama

**Model Management**:

```bash
# Pull models
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull mistral

# List available models
docker compose exec ollama ollama list

# Run inference
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "What is RAG?",
  "stream": false
}'
```

**Integration**:

```python
# app/core/llm.py
from langchain_community.llms import Ollama

llm = Ollama(
    model=os.getenv("LLM_MODEL", "llama3"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
    temperature=0.7,
    top_p=0.9
)

response = llm.invoke("Generate a query variation for: What is RAG?")
```

#### Document Store: File System

**Structure**:
```
/app/data/
├── uploads/          # Original uploaded files
│   ├── manual.pdf
│   └── guide.docx
├── processed/        # Parsed and chunked data
│   ├── manual_chunks.json
│   └── guide_chunks.json
└── metadata/         # Document metadata
    ├── manual_meta.json
    └── guide_meta.json
```

---

## Data Flow Diagrams

### Query Processing Flow

```
┌─────────┐
│  User   │
│  Query  │
└────┬────┘
     │
     ▼
┌────────────────┐
│ API Gateway    │
│ (FastAPI)      │
└────┬───────────┘
     │
     ▼
┌────────────────┐     ┌──────────────────┐
│ Query Agent    │────▶│ Query Expander   │
│ (CrewAI)       │     │ (LLM)            │
└────┬───────────┘     └──────────────────┘
     │ [Original + 2 variations]
     ▼
┌────────────────────────────────────────┐
│ Retrieval Agent                        │
│ ┌──────────────┐    ┌───────────────┐ │
│ │ Semantic     │    │ Keyword       │ │
│ │ Search       │    │ Search (BM25) │ │
│ │ (ChromaDB)   │    │               │ │
│ └──────┬───────┘    └───────┬───────┘ │
│        │                    │         │
│        └────────┬───────────┘         │
│                 ▼                     │
│         ┌──────────────┐              │
│         │ Reciprocal   │              │
│         │ Rank Fusion  │              │
│         └──────┬───────┘              │
└────────────────┼──────────────────────┘
                 │ [Top-5 chunks]
                 ▼
┌────────────────────────────────┐
│ Synthesis Agent                │
│ ┌────────────────────────────┐ │
│ │ Context Assembly           │ │
│ ├────────────────────────────┤ │
│ │ Prompt Construction        │ │
│ ├────────────────────────────┤ │
│ │ LLM Generation (Ollama)    │ │
│ └────────────┬───────────────┘ │
└──────────────┼─────────────────┘
               │ [Generated answer]
               ▼
┌──────────────────────────────────┐
│ Evaluation Agent                 │
│ - Relevance Score                │
│ - Groundedness Check             │
│ - Completeness Assessment        │
└──────────────┬───────────────────┘
               │ [Answer + Metrics]
               ▼
┌──────────────────────────────────┐
│ API Response                     │
│ {                                │
│   "answer": "...",               │
│   "sources": [...],              │
│   "evaluation": {...}            │
│ }                                │
└──────────────────────────────────┘
```

### Document Ingestion Flow

```
┌──────────────┐
│ File Upload  │
│ (HTTP POST)  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Format Detection │
│ (MIME type)      │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Parser Selection & Execution     │
│ ┌─────────┐  ┌──────┐  ┌──────┐ │
│ │ PDF     │  │ DOCX │  │ TXT  │ │
│ │ Parser  │  │Parser│  │Parser│ │
│ └────┬────┘  └───┬──┘  └───┬──┘ │
└──────┼───────────┼─────────┼────┘
       │           │         │
       └───────────┴─────────┘
                   │ [Text + Metadata]
                   ▼
       ┌───────────────────────┐
       │ Semantic Chunker      │
       │ - Sentence splitting  │
       │ - Boundary detection  │
       │ - Overlap handling    │
       └───────────┬───────────┘
                   │ [Chunks]
                   ▼
       ┌───────────────────────┐
       │ Embedding Generation  │
       │ (Sentence Transform.) │
       └───────────┬───────────┘
                   │ [Vectors]
                   ▼
       ┌───────────────────────┐
       │ Vector Store Insert   │
       │ (ChromaDB)            │
       └───────────┬───────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │ Metadata Storage      │
       │ (File system)         │
       └───────────────────────┘
```

---

## Technology Choices & Rationale

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend Framework** | FastAPI | Async support, automatic API docs, high performance, type hints |
| **Frontend Framework** | Next.js 19 | Server components, streaming UI, excellent DX, SEO-friendly |
| **Vector Database** | ChromaDB | Self-hostable, simple API, good performance, Apache 2.0 license |
| **LLM Engine** | Ollama | Easy local deployment, model management, OpenAI-compatible API |
| **Agent Framework** | CrewAI | Built for autonomous agents, workflow orchestration, LLM integration |
| **Embeddings** | Sentence Transformers | State-of-the-art quality, runs locally, MIT license |
| **Containerization** | Docker Compose | Simple orchestration, reproducible environments, cross-platform |
| **Programming Language** | Python 3.9+ | Rich ML/AI ecosystem, type hints, async/await support |

---

## Security Considerations

1. **Input Validation**: All user inputs sanitized and validated
2. **Rate Limiting**: Prevents abuse and DOS attacks
3. **File Upload Restrictions**: Size limits, type validation, malware scanning
4. **Environment Variables**: Secrets managed via `.env`, never in code
5. **Network Isolation**: Services communicate via internal Docker network
6. **HTTPS**: TLS termination at reverse proxy layer (production)

---

## Scalability Considerations

1. **Horizontal Scaling**: Multiple backend instances behind load balancer
2. **Vector DB Sharding**: ChromaDB supports multi-node deployment
3. **Ollama Clustering**: Multiple Ollama instances with model caching
4. **Caching Layer**: Redis for query result caching
5. **Async Processing**: Background workers for document ingestion

---

## Monitoring & Observability

1. **Logging**: Structured JSON logs with correlation IDs
2. **Metrics**: Prometheus metrics for latency, throughput, error rates
3. **Tracing**: OpenTelemetry for distributed tracing
4. **Health Checks**: Liveness and readiness probes for all services
5. **Dashboards**: Grafana dashboards for system overview

---

## Next Steps

- See [Agent Workflow](Agent_Workflow.md) for detailed agent behavior
- See [Development Roadmap](Development_Roadmap.md) for future enhancements
- See [Deployment Guide](Deployment_Guide.md) for production setup

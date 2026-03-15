# Agentic Code Generation Workflow

This document describes how the OpenAgentRAG multi-agent system processes user queries and generates grounded answers through a structured agent pipeline.

---

## Overview

OpenAgentRAG uses a **multi-agent architecture** powered by CrewAI. Instead of a single monolithic pipeline, the system decomposes the RAG workflow into specialized agents that collaborate to produce high-quality, grounded responses.

Each agent has a defined role, goal, and set of tools. Agents are orchestrated into **crews** that execute tasks sequentially, passing results between stages.

---

## Agent Inventory

| Agent | Module | Responsibility |
|-------|--------|---------------|
| Data Source Agent | `agents/data_ingestion_agent.py` | Extract text from uploaded files and URLs |
| Document Processing Agent | `agents/data_ingestion_agent.py` | Parse and normalize extracted content |
| Chunking Agent | `rag/chunking.py` | Split documents into semantic chunks |
| Embedding Agent | `agents/embedding_agent.py` | Generate vector embeddings and store in ChromaDB |
| Vector Storage Agent | `database/chromadb_client.py` | Manage vector database collections |
| Retrieval Agent | `agents/retrieval_agent.py` | Search vectors for relevant chunks |
| Answer Generation Agent | `rag/generator.py` | Generate grounded answers using LLM |
| Evaluation Agent | `agents/evaluation_agent.py` | Assess response quality metrics |

---

## Workflow 1: Document Ingestion Pipeline

When a user uploads a document, the ingestion crew processes it through these stages:

```
┌─────────────────┐
│  User Upload     │  (PDF, DOCX, XLSX, TXT, URL)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Source     │  Extract raw text from file format
│  Agent           │  Tools: extract_pdf, extract_docx, extract_xlsx,
│                  │         extract_txt, extract_url
└────────┬────────┘
         │ Raw text + metadata
         ▼
┌─────────────────┐
│  Chunking        │  Split into semantic chunks
│  Agent           │  - Sentence boundary detection
│                  │  - Cosine similarity grouping
│                  │  - Fallback: RecursiveCharacterTextSplitter
└────────┬────────┘
         │ List of text chunks
         ▼
┌─────────────────┐
│  Embedding       │  Generate vector embeddings
│  Agent           │  Model: sentence-transformers/all-MiniLM-L6-v2
│                  │  Batch processing for efficiency
└────────┬────────┘
         │ Embeddings + metadata
         ▼
┌─────────────────┐
│  Vector Storage  │  Store in ChromaDB collection
│  Agent           │  - Embeddings indexed for similarity search
│                  │  - Metadata preserved (source, chunk_id, doc_id)
└─────────────────┘
```

### Ingestion Crew Configuration

```python
# backend/agents/crew.py - IngestionCrew
Process: Sequential
Agents: [data_ingestion_agent, embedding_agent]
Tasks:
  1. Extract text from source file
  2. Chunk the extracted text
  3. Generate embeddings and store in vector DB
```

### Supported File Formats

| Format | Extraction Tool | Library |
|--------|----------------|---------|
| PDF | `extract_pdf_text` | pdfplumber |
| DOCX | `extract_docx_text` | python-docx |
| XLSX | `extract_xlsx_text` | openpyxl |
| TXT | `extract_txt_text` | Built-in (UTF-8) |
| URL | `extract_url_text` | httpx + BeautifulSoup |

---

## Workflow 2: Query Processing Pipeline

When a user asks a question, the query crew processes it through these stages:

```
┌─────────────────┐
│  User Query      │  "What does the document say about X?"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Retrieval       │  Search ChromaDB for relevant chunks
│  Agent           │  - Embed the query using same model
│                  │  - Cosine similarity search
│                  │  - Filter by similarity threshold (0.7)
│                  │  - Return top-K results (default: 5)
└────────┬────────┘
         │ Retrieved chunks with scores
         ▼
┌─────────────────┐
│  Answer          │  Generate response using LLM
│  Generation      │  - Context: retrieved chunks
│  Agent           │  - System prompt: grounding rules
│                  │  - Model: Ollama (Llama 3 / Mistral)
│                  │  - Source attribution in response
└────────┬────────┘
         │ Generated answer + sources
         ▼
┌─────────────────┐
│  Evaluation      │  Assess response quality
│  Agent           │  Metrics:
│                  │  - Relevance score (query-answer overlap)
│                  │  - Groundedness score (source citation check)
│                  │  - Hallucination risk (uncertainty detection)
└────────┬────────┘
         │ Quality metrics
         ▼
┌─────────────────┐
│  Response        │  Return to user:
│  Assembly        │  - Answer text
│                  │  - Source citations
│                  │  - Evaluation metrics
│                  │  - Session stored in chat history
└─────────────────┘
```

### Query Crew Configuration

```python
# backend/agents/crew.py - QueryCrew
Process: Sequential
Agents: [retrieval_agent, evaluation_agent]
Tasks:
  1. Retrieve relevant documents for query
  2. Generate answer from context
  3. Evaluate response quality
```

---

## Chunking Strategy

The chunking pipeline uses a semantic-aware approach:

1. **Sentence Splitting**: Text is split at sentence boundaries using regex patterns
2. **Semantic Grouping**: Adjacent sentences with high cosine similarity (embedding-based) are grouped together
3. **Size Enforcement**: Groups are merged or split to stay within `CHUNK_SIZE` (default: 512 tokens)
4. **Overlap**: Configurable overlap (`CHUNK_OVERLAP`: 50 tokens) ensures context continuity between chunks
5. **Fallback**: If semantic chunking fails, `RecursiveCharacterTextSplitter` from LangChain is used

### Configurable Parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `CHUNK_SIZE` | 512 | Target chunk size in tokens |
| `CHUNK_OVERLAP` | 50 | Overlap between consecutive chunks |
| `SIMILARITY_THRESHOLD` | 0.7 | Minimum score for retrieval results |
| `TOP_K_RETRIEVAL` | 5 | Number of chunks returned per query |

---

## Evaluation Metrics

The Evaluation Agent computes three metrics for every response:

### 1. Relevance Score
Measures how well the answer addresses the original query.
- Method: Keyword overlap between query tokens and answer tokens
- Range: 0.0 - 1.0

### 2. Groundedness Score
Measures whether the answer is supported by the retrieved sources.
- Method: Checks for source citations and content overlap with retrieved chunks
- Range: 0.0 - 1.0

### 3. Hallucination Risk
Detects whether the answer may contain fabricated information.
- Method: Scans for uncertainty phrases ("I think", "possibly", "it seems") and checks citation presence
- Range: 0.0 - 1.0 (lower is better)

### Quality Thresholds

| Metric | Good | Acceptable | Poor |
|--------|------|-----------|------|
| Relevance | >= 0.8 | 0.6 - 0.8 | < 0.6 |
| Groundedness | >= 0.8 | 0.6 - 0.8 | < 0.6 |
| Hallucination Risk | < 0.2 | 0.2 - 0.4 | > 0.4 |

---

## Self-Improvement Feedback Loop

When enabled (`ENABLE_FEEDBACK_LOOP=true`), the system collects evaluation metrics and uses them to improve future responses:

```
Query → Retrieval → Generation → Evaluation
                                      │
                                      ▼
                              ┌───────────────┐
                              │ Evaluation Log │
                              │ (SQLite DB)    │
                              └───────┬───────┘
                                      │
                                      ▼
                              Analysis of:
                              - Low-scoring queries
                              - Common retrieval failures
                              - Hallucination patterns
```

---

## Agent Communication

Agents communicate through the CrewAI framework:

1. **Task Output**: Each task produces a structured output that becomes the input for the next task
2. **Shared Context**: All agents in a crew share access to the same tools and configuration
3. **Error Propagation**: If an agent fails, the crew stops and returns an error to the caller
4. **Logging**: All agent actions are logged for debugging and evaluation

### Service Layer Integration

The `ChatService` and `DocumentService` in `backend/services/` act as the bridge between FastAPI routes and agent crews:

```python
# Simplified flow in ChatService
async def process_query(query, session_id):
    # 1. Retrieval Agent finds relevant chunks
    chunks = retriever.search(query, top_k=settings.top_k)

    # 2. Generator produces grounded answer
    answer = generator.generate(query, chunks)

    # 3. Evaluation Agent scores the response
    metrics = evaluator.evaluate(query, answer, chunks)

    # 4. Store in chat history
    save_to_history(session_id, query, answer, metrics)

    return {answer, sources, metrics}
```

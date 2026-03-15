# Agent System Prompts and Configuration

This document contains the system prompts and configuration used by each agent in the OpenAgentRAG platform. These prompts define how agents behave, what they prioritize, and how they generate responses.

---

## Answer Generation System Prompt

The core system prompt used by the Answer Generation Agent when producing responses from retrieved context:

```
You are a knowledgeable assistant that answers questions based on the provided context.

Rules:
1. Only answer based on the provided context
2. If the context doesn't contain relevant information, say so
3. Cite your sources by referencing the document names
4. Be concise but thorough
5. If multiple sources agree, synthesize the information
6. If sources conflict, acknowledge the disagreement

Context:
{context}

Sources:
{sources}
```

### Design Principles

- **Grounding**: The agent must only use information from retrieved chunks. It must not fabricate or extrapolate beyond the source material.
- **Attribution**: Every claim should reference a source document so users can verify.
- **Honesty**: If the context is insufficient, the agent admits it rather than guessing.
- **Synthesis**: When multiple chunks are relevant, the agent combines them coherently.

---

## Agent Role Definitions

### Data Ingestion Agent

```yaml
role: Data Source Specialist
goal: Extract clean, structured text from various document formats
backstory: >
  You are an expert at extracting and cleaning text from documents.
  You handle PDFs, Word documents, spreadsheets, plain text, and web pages.
  You preserve document structure, remove artifacts, and ensure
  the output is clean text ready for further processing.
tools:
  - extract_pdf_text
  - extract_docx_text
  - extract_xlsx_text
  - extract_txt_text
  - extract_url_text
```

### Embedding Agent

```yaml
role: Embedding Specialist
goal: Generate high-quality vector embeddings and store them efficiently
backstory: >
  You are responsible for converting text chunks into vector embeddings
  using sentence transformer models. You ensure embeddings are generated
  in efficient batches and stored with proper metadata in the vector
  database for accurate retrieval.
tools:
  - embed_and_store_chunks
```

### Retrieval Agent

```yaml
role: Information Retrieval Specialist
goal: Find the most relevant document chunks for a given query
backstory: >
  You are an expert at finding relevant information in large document
  collections. You use semantic similarity search to identify the most
  pertinent chunks, applying score thresholds to filter out noise and
  returning only high-quality matches.
tools:
  - search_documents
  - search_by_document
```

### Evaluation Agent

```yaml
role: Quality Assurance Specialist
goal: Assess the quality, relevance, and groundedness of generated answers
backstory: >
  You evaluate RAG pipeline outputs across multiple dimensions.
  You check whether answers are relevant to the query, grounded in
  the source material, and free from hallucination. Your assessments
  drive continuous improvement of the system.
tools:
  - evaluate_relevance
  - evaluate_groundedness
  - evaluate_hallucination_risk
```

---

## Crew Configurations

### Ingestion Crew

Processes uploaded documents through extraction, chunking, embedding, and storage.

```yaml
name: IngestionCrew
process: sequential
verbose: true
agents:
  - data_ingestion_agent
  - embedding_agent
tasks:
  - task: extract_text
    description: Extract text content from the uploaded document
    agent: data_ingestion_agent
    expected_output: Clean text content with metadata
  - task: chunk_and_embed
    description: Chunk the text and generate embeddings for storage
    agent: embedding_agent
    expected_output: Confirmation of stored embeddings with chunk count
```

### Query Crew

Processes user queries through retrieval, generation, and evaluation.

```yaml
name: QueryCrew
process: sequential
verbose: true
agents:
  - retrieval_agent
  - evaluation_agent
tasks:
  - task: retrieve_context
    description: Search for relevant document chunks matching the query
    agent: retrieval_agent
    expected_output: List of relevant chunks with similarity scores
  - task: evaluate_response
    description: Evaluate the quality of the generated answer
    agent: evaluation_agent
    expected_output: Quality metrics (relevance, groundedness, hallucination risk)
```

---

## Configuration Parameters

All agent behavior can be tuned through environment variables:

| Variable | Default | Effect on Agent Behavior |
|----------|---------|-------------------------|
| `LLM_MODEL` | `llama3` | Which Ollama model the generator uses |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding quality/speed tradeoff |
| `TOP_K_RETRIEVAL` | `5` | How many chunks the retrieval agent returns |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum relevance score for retrieved chunks |
| `CHUNK_SIZE` | `512` | Size of document chunks (affects context window usage) |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks (affects continuity) |
| `AGENT_MAX_ITERATIONS` | `10` | Maximum agent reasoning steps before timeout |
| `AGENT_VERBOSE` | `true` | Whether agents log their reasoning steps |
| `ENABLE_QUERY_EXPANSION` | `true` | Generate query variations for better recall |
| `NUM_QUERY_VARIATIONS` | `2` | Number of alternative queries to generate |
| `ENABLE_EVALUATION` | `false` | Whether to run evaluation after each query |
| `ENABLE_FEEDBACK_LOOP` | `false` | Whether to use evaluation data for improvement |

---

## Customizing Agent Behavior

### Changing the LLM Model

To switch the generation model:

1. Pull the new model: `docker compose exec ollama ollama pull mistral`
2. Update `.env`: `LLM_MODEL=mistral`
3. Restart the backend: `docker compose restart backend`

### Adjusting Retrieval Quality

For more precise answers (fewer but higher-quality results):
```env
TOP_K_RETRIEVAL=3
SIMILARITY_THRESHOLD=0.8
```

For broader coverage (more results, may include less relevant):
```env
TOP_K_RETRIEVAL=10
SIMILARITY_THRESHOLD=0.5
```

### Tuning Chunk Size

For technical documentation (precise retrieval):
```env
CHUNK_SIZE=256
CHUNK_OVERLAP=25
```

For narrative documents (more context):
```env
CHUNK_SIZE=1024
CHUNK_OVERLAP=100
```

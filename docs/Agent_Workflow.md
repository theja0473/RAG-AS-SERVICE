# Agent Workflow: OpenAgentRAG

## Overview

This document provides detailed documentation of the multi-agent workflow in OpenAgentRAG, including agent responsibilities, interaction patterns, pipeline flows, and self-improvement mechanisms.

---

## Agent Architecture Philosophy

### Why Agent-Based RAG?

Traditional RAG systems use a **monolithic pipeline** where each step is hardcoded and non-adaptive. OpenAgentRAG implements an **agent-based architecture** where autonomous agents collaborate to solve the retrieval and generation task.

**Key Principles**:

1. **Separation of Concerns**: Each agent has a specific, well-defined role
2. **Autonomy**: Agents make decisions based on their expertise and current context
3. **Collaboration**: Agents share information through structured workflows
4. **Adaptability**: Agents can adjust their strategies based on intermediate results
5. **Transparency**: Each agent's decisions are logged and explainable

### CrewAI Framework

**CrewAI** is used for agent orchestration because it provides:

- **Agent Abstraction**: Define agents with roles, goals, and backstories
- **Task Management**: Structure work as a sequence of tasks
- **Inter-Agent Communication**: Agents can pass data and context
- **LLM Integration**: Works seamlessly with Ollama and other LLM backends
- **Workflow Control**: Sequential, parallel, or hierarchical execution

---

## Agent Descriptions

### 1. Query Agent (Query Analyzer & Expander)

**Role**: Understanding user intent and generating effective query variations

**Goal**: Transform the user's query into multiple optimized search queries that maximize retrieval coverage

**Backstory**:
> "You are an expert at understanding user questions and reformulating them for better information retrieval. You consider synonyms, related concepts, different phrasings, and domain-specific terminology. You know when a query is ambiguous and needs clarification through multiple variations."

**Responsibilities**:
- Analyze the original user query for intent and key concepts
- Identify ambiguous terms that could benefit from expansion
- Generate 2-3 query variations using:
  - Synonym substitution
  - Concept expansion (e.g., "voltage" → "electrical potential")
  - Question reformulation (e.g., statement ↔ question)
- Preserve the core intent while improving retrieval coverage

**Input**:
```python
{
    "query": "What is the maximum voltage?",
    "context": {
        "previous_queries": [],  # Historical context if available
        "domain": "technical"     # Optional domain hint
    }
}
```

**Output**:
```python
{
    "original_query": "What is the maximum voltage?",
    "variations": [
        "What is the peak voltage threshold?",
        "What voltage limit should not be exceeded?"
    ],
    "intent": "information_seeking",
    "key_concepts": ["voltage", "maximum", "threshold"]
}
```

**Implementation**:

```python
# app/agents/query_agent.py
from crewai import Agent
from langchain_community.llms import Ollama

class QueryAgent:
    def __init__(self, llm: Ollama):
        self.agent = Agent(
            role="Query Analyzer",
            goal="Understand user intent and generate effective query variations",
            backstory="""You are an expert at understanding user questions...""",
            llm=llm,
            verbose=True
        )

    async def expand(self, query: str, num_variations: int = 2) -> dict:
        """Generate query variations using LLM."""
        prompt = f"""
        Analyze the following query and generate {num_variations} alternative
        phrasings that preserve the original intent but use different wording.

        Original Query: {query}

        Generate variations that:
        1. Use synonyms for key terms
        2. Reformulate the question structure
        3. Expand abbreviations or technical terms

        Return as JSON:
        {{
            "variations": ["variation1", "variation2"],
            "intent": "information_seeking|comparison|troubleshooting|definition",
            "key_concepts": ["concept1", "concept2"]
        }}
        """

        response = await self.agent.execute(prompt)
        return self._parse_response(response)
```

**Decision Logic**:
- If query is < 3 words → Generate expansions that add context
- If query contains domain jargon → Include lay-person alternatives
- If query is ambiguous → Generate variations covering multiple interpretations

---

### 2. Retrieval Agent (Information Retriever)

**Role**: Finding the most relevant documents for the query

**Goal**: Execute optimal retrieval strategies and return the top-k most relevant document chunks

**Backstory**:
> "You are a master librarian with deep expertise in information retrieval. You understand when to use semantic search, keyword search, or a hybrid approach. You know how to filter noise and identify truly relevant documents."

**Responsibilities**:
- Execute hybrid retrieval (semantic + keyword) for each query variation
- Apply metadata filters when appropriate
- Deduplicate results from multiple query variations
- Rerank results using Reciprocal Rank Fusion
- Filter results below similarity threshold

**Input**:
```python
{
    "queries": [
        "What is the maximum voltage?",
        "What is the peak voltage threshold?",
        "What voltage limit should not be exceeded?"
    ],
    "top_k": 5,
    "filters": {"document_type": "manual"}  # Optional
}
```

**Output**:
```python
{
    "documents": [
        {
            "id": "doc_123_chunk_5",
            "text": "The maximum operating voltage is 48V DC...",
            "metadata": {
                "source": "technical_manual.pdf",
                "page": 15,
                "section": "Electrical Specifications"
            },
            "score": 0.92,
            "retrieval_method": "hybrid"
        },
        # ... more documents
    ],
    "retrieval_stats": {
        "total_candidates": 45,
        "after_deduplication": 12,
        "after_threshold_filter": 8,
        "returned": 5
    }
}
```

**Implementation**:

```python
# app/agents/retrieval_agent.py
class RetrievalAgent:
    def __init__(self, vector_store, llm: Ollama):
        self.agent = Agent(
            role="Information Retriever",
            goal="Find the most relevant documents for the query",
            backstory="""You are a librarian with deep expertise...""",
            llm=llm,
            verbose=True
        )
        self.semantic_search = SemanticSearch(vector_store)
        self.keyword_search = BM25Search(vector_store)

    async def retrieve(self, queries: List[str], top_k: int = 5) -> dict:
        """Execute hybrid retrieval for multiple query variations."""
        all_results = []

        # Retrieve for each query variation
        for query in queries:
            semantic = await self.semantic_search.search(query, k=top_k*2)
            keyword = await self.keyword_search.search(query, k=top_k*2)

            # Hybrid fusion
            hybrid = self._fuse_results(semantic, keyword)
            all_results.extend(hybrid)

        # Deduplicate by document ID
        unique = self._deduplicate(all_results)

        # Rerank using RRF
        reranked = self._reciprocal_rank_fusion(unique)

        # Filter by threshold
        filtered = [doc for doc in reranked if doc.score >= 0.7]

        return {
            "documents": filtered[:top_k],
            "retrieval_stats": self._compute_stats(all_results, unique, filtered)
        }

    def _fuse_results(self, semantic, keyword, alpha=0.7):
        """Weighted combination of semantic and keyword results."""
        fused_scores = {}

        for doc in semantic:
            fused_scores[doc.id] = alpha * doc.score

        for doc in keyword:
            fused_scores[doc.id] = fused_scores.get(doc.id, 0) + (1-alpha) * doc.score

        # Create fused documents
        fused_docs = []
        for doc_id, score in fused_scores.items():
            doc = self._get_document_by_id(doc_id)
            doc.score = score
            doc.retrieval_method = "hybrid"
            fused_docs.append(doc)

        return sorted(fused_docs, key=lambda x: x.score, reverse=True)
```

**Search Strategies**:

1. **Semantic Search** (70% weight):
   - Uses sentence-transformers embeddings
   - ChromaDB cosine similarity
   - Good for conceptual matches

2. **Keyword Search** (30% weight):
   - BM25 algorithm
   - Term frequency-inverse document frequency
   - Good for exact phrase matches and entity names

3. **Reciprocal Rank Fusion**:
   ```
   RRF_score(d) = Σ(1 / (k + rank_i(d)))
   where k = 60 (constant), rank_i = rank in result list i
   ```

---

### 3. Synthesis Agent (Answer Generator)

**Role**: Creating accurate, well-grounded answers from retrieved context

**Goal**: Generate a coherent answer that directly addresses the user's question using only information from retrieved documents

**Backstory**:
> "You are a knowledge worker who excels at synthesizing information from multiple sources into clear, accurate answers. You always ground your responses in the provided context and cite your sources. You never make up information."

**Responsibilities**:
- Assemble retrieved chunks into coherent context
- Generate answer using LLM with strict grounding instructions
- Include source citations for all claims
- Handle cases where retrieved context is insufficient
- Format response for readability

**Input**:
```python
{
    "query": "What is the maximum voltage?",
    "documents": [
        {"text": "The maximum operating voltage is 48V DC...", "source": "manual.pdf", "page": 15},
        {"text": "Exceeding 48V may damage the system...", "source": "manual.pdf", "page": 16}
    ]
}
```

**Output**:
```python
{
    "answer": """
    The maximum operating voltage is 48V DC. Exceeding this voltage may
    damage the system.

    Sources:
    - Technical Manual (manual.pdf, page 15)
    - Technical Manual (manual.pdf, page 16)
    """,
    "grounded": True,
    "sources_used": ["manual.pdf:15", "manual.pdf:16"],
    "confidence": 0.95
}
```

**Implementation**:

```python
# app/agents/synthesis_agent.py
class SynthesisAgent:
    def __init__(self, llm: Ollama):
        self.agent = Agent(
            role="Answer Synthesizer",
            goal="Create accurate, well-grounded answers from retrieved context",
            backstory="""You are a knowledge worker who excels...""",
            llm=llm,
            verbose=True
        )

    async def generate(self, query: str, documents: List[dict]) -> dict:
        """Generate answer from retrieved documents."""
        context = self._assemble_context(documents)

        prompt = f"""
        You are a helpful assistant that answers questions based solely on
        the provided context. You must:
        1. Only use information from the context
        2. Cite sources for all claims
        3. Say "I don't know" if the context doesn't contain the answer
        4. Be concise but complete

        Context:
        {context}

        Question: {query}

        Answer:
        """

        response = await self.agent.execute(prompt)

        return {
            "answer": response,
            "grounded": self._check_grounding(response, documents),
            "sources_used": self._extract_sources(response, documents),
            "confidence": self._estimate_confidence(response)
        }

    def _assemble_context(self, documents: List[dict]) -> str:
        """Assemble documents into formatted context."""
        context_parts = []

        for i, doc in enumerate(documents, 1):
            source_label = f"[Source {i}: {doc['metadata']['source']}, " \
                          f"page {doc['metadata'].get('page', 'N/A')}]"
            context_parts.append(f"{source_label}\n{doc['text']}\n")

        return "\n".join(context_parts)

    def _check_grounding(self, answer: str, documents: List[dict]) -> bool:
        """Verify that answer claims are supported by documents."""
        # Extract claims from answer
        claims = self._extract_claims(answer)

        # Check each claim against documents
        for claim in claims:
            if not any(self._claim_supported(claim, doc['text']) for doc in documents):
                return False

        return True
```

**Prompt Engineering**:

The synthesis agent uses a carefully crafted system prompt:

```python
SYNTHESIS_SYSTEM_PROMPT = """
You are an expert assistant that synthesizes information from multiple sources.

RULES:
1. Answer ONLY using information from the provided context
2. If the context doesn't contain enough information, say "Based on the
   available information, I cannot answer this completely."
3. Cite sources using the format [Source X]
4. Be precise with numbers, dates, and technical terms
5. If sources contradict, mention both perspectives
6. Use clear, professional language

RESPONSE FORMAT:
[Your answer here, with inline citations]

Sources:
- [List of sources used]
"""
```

---

### 4. Evaluation Agent (Quality Assessor)

**Role**: Assessing the quality of generated answers

**Goal**: Provide multi-dimensional quality metrics and constructive feedback

**Backstory**:
> "You are a quality assurance specialist who evaluates answers for relevance, groundedness, coherence, and completeness. You provide objective metrics and actionable feedback for improvement."

**Responsibilities**:
- Measure retrieval relevance (precision, recall)
- Check answer groundedness (% of claims supported by context)
- Assess answer completeness (does it address all aspects of the query?)
- Evaluate coherence and fluency
- Detect potential hallucinations
- Provide feedback for self-improvement

**Input**:
```python
{
    "query": "What is the maximum voltage?",
    "retrieved_documents": [...],
    "generated_answer": "The maximum operating voltage is 48V DC...",
    "ground_truth": None  # Optional, for validation
}
```

**Output**:
```python
{
    "metrics": {
        "retrieval_relevance": 0.92,
        "groundedness": 0.98,
        "completeness": 0.95,
        "coherence": 0.96,
        "overall_quality": 0.95
    },
    "feedback": {
        "strengths": [
            "Answer is well-grounded in source material",
            "Clear citation of sources"
        ],
        "improvements": [
            "Could include safety implications"
        ],
        "potential_issues": []
    },
    "passed_threshold": True
}
```

**Implementation**:

```python
# app/agents/evaluation_agent.py
class EvaluationAgent:
    def __init__(self, llm: Ollama):
        self.agent = Agent(
            role="Quality Evaluator",
            goal="Assess the quality of generated answers",
            backstory="""You are a quality assurance specialist...""",
            llm=llm,
            verbose=True
        )

    async def evaluate(self, query: str, documents: List[dict],
                       answer: str) -> dict:
        """Evaluate answer quality across multiple dimensions."""

        # 1. Retrieval Relevance
        retrieval_score = self._evaluate_retrieval(query, documents)

        # 2. Groundedness
        groundedness = self._evaluate_groundedness(answer, documents)

        # 3. Completeness
        completeness = self._evaluate_completeness(query, answer)

        # 4. Coherence
        coherence = self._evaluate_coherence(answer)

        # 5. Overall quality (weighted average)
        overall = (
            0.25 * retrieval_score +
            0.35 * groundedness +
            0.25 * completeness +
            0.15 * coherence
        )

        # Generate feedback
        feedback = await self._generate_feedback(
            query, documents, answer, {
                "retrieval": retrieval_score,
                "groundedness": groundedness,
                "completeness": completeness,
                "coherence": coherence
            }
        )

        return {
            "metrics": {
                "retrieval_relevance": retrieval_score,
                "groundedness": groundedness,
                "completeness": completeness,
                "coherence": coherence,
                "overall_quality": overall
            },
            "feedback": feedback,
            "passed_threshold": overall >= 0.75
        }

    def _evaluate_groundedness(self, answer: str, documents: List[dict]) -> float:
        """Calculate percentage of answer claims supported by documents."""
        claims = self._extract_claims(answer)
        if not claims:
            return 1.0

        supported_count = 0
        for claim in claims:
            if any(self._is_claim_supported(claim, doc['text']) for doc in documents):
                supported_count += 1

        return supported_count / len(claims)

    def _extract_claims(self, answer: str) -> List[str]:
        """Extract factual claims from answer using LLM."""
        prompt = f"""
        Extract all factual claims from the following answer.
        Return as a JSON list of strings.

        Answer: {answer}
        """
        response = self.agent.llm.invoke(prompt)
        return json.loads(response)
```

**Evaluation Metrics**:

1. **Retrieval Relevance**: Are retrieved documents relevant to the query?
   ```python
   relevance = (# relevant documents) / (# retrieved documents)
   ```

2. **Groundedness**: Are answer claims supported by retrieved documents?
   ```python
   groundedness = (# supported claims) / (# total claims)
   ```

3. **Completeness**: Does the answer address all aspects of the query?
   ```python
   completeness = (# query aspects addressed) / (# total query aspects)
   ```

4. **Coherence**: Is the answer fluent and logically structured?
   - Uses LLM-as-judge with rubric
   - Checks for grammatical errors, logical flow, clarity

---

## Pipeline Flows

### Ingestion Pipeline

**Purpose**: Process uploaded documents and make them searchable

**Steps**:

1. **Document Upload** → User uploads file via API
2. **Format Detection** → MIME type analysis
3. **Parsing** → Format-specific text extraction
4. **Chunking** → Semantic or phase-based segmentation
5. **Embedding** → Convert chunks to vectors
6. **Storage** → Store in ChromaDB with metadata

**Agent Involvement**: No agents in ingestion (deterministic pipeline)

**Flow Diagram**:

```
┌───────────┐
│  Upload   │
└─────┬─────┘
      │
      ▼
┌──────────────┐     ┌──────────────────┐
│ Parse File   │────▶│ Extract Metadata │
└──────┬───────┘     └──────────────────┘
       │
       ▼
┌──────────────┐
│ Chunk Text   │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────────┐
│ Generate     │────▶│ Store in         │
│ Embeddings   │     │ ChromaDB         │
└──────────────┘     └──────────────────┘
```

---

### Query Pipeline (Agent Workflow)

**Purpose**: Answer user queries using multi-agent collaboration

**Stages**:

```
Stage 1: Query Understanding
├─ Agent: Query Agent
├─ Input: User query
└─ Output: Query variations

Stage 2: Document Retrieval
├─ Agent: Retrieval Agent
├─ Input: Query variations
└─ Output: Ranked documents

Stage 3: Answer Generation
├─ Agent: Synthesis Agent
├─ Input: Query + Documents
└─ Output: Grounded answer

Stage 4: Quality Evaluation
├─ Agent: Evaluation Agent
├─ Input: Query + Documents + Answer
└─ Output: Quality metrics + Feedback
```

**Detailed Workflow**:

```python
# app/agents/workflow.py
async def execute_query_workflow(query: str) -> dict:
    """Execute the complete multi-agent query workflow."""

    # Stage 1: Query Understanding
    logger.info(f"Stage 1: Analyzing query - {query}")
    query_result = await query_agent.expand(query, num_variations=2)

    queries = [query_result['original_query']] + query_result['variations']
    logger.info(f"Generated {len(queries)} query variations")

    # Stage 2: Document Retrieval
    logger.info("Stage 2: Retrieving documents")
    retrieval_result = await retrieval_agent.retrieve(queries, top_k=5)

    documents = retrieval_result['documents']
    logger.info(f"Retrieved {len(documents)} documents")

    # Stage 3: Answer Generation
    logger.info("Stage 3: Generating answer")
    synthesis_result = await synthesis_agent.generate(query, documents)

    answer = synthesis_result['answer']
    logger.info("Answer generated successfully")

    # Stage 4: Quality Evaluation
    logger.info("Stage 4: Evaluating quality")
    evaluation_result = await evaluation_agent.evaluate(query, documents, answer)

    logger.info(f"Overall quality: {evaluation_result['metrics']['overall_quality']:.2f}")

    # Assemble final response
    return {
        "query": query,
        "query_variations": queries,
        "answer": answer,
        "sources": [
            {
                "text": doc['text'][:200] + "...",
                "metadata": doc['metadata']
            }
            for doc in documents
        ],
        "evaluation": evaluation_result,
        "workflow_log": {
            "query_agent": query_result,
            "retrieval_agent": retrieval_result['retrieval_stats'],
            "synthesis_agent": synthesis_result,
            "evaluation_agent": evaluation_result
        }
    }
```

---

## Self-Improving Feedback Loop

### Overview

OpenAgentRAG implements a **feedback-driven self-improvement mechanism** where low-quality responses trigger adjustments to the retrieval and generation parameters.

### Feedback Collection

**Sources**:
1. **Evaluation Agent**: Automatic quality metrics
2. **User Ratings**: Thumbs up/down feedback
3. **Query Success Metrics**: Click-through rates, time-to-answer

**Storage**:
```python
# app/feedback/store.py
feedback_db.insert({
    "query_id": "uuid-123",
    "query": "What is the maximum voltage?",
    "answer": "...",
    "evaluation_metrics": {...},
    "user_rating": 1,  # 1 = thumbs up, -1 = thumbs down, 0 = no rating
    "timestamp": "2026-03-15T10:30:00Z"
})
```

### Improvement Mechanisms

**1. Parameter Tuning**:

If average quality score < 0.75 for a query type:
- Increase `top_k` retrieval (5 → 10)
- Adjust semantic/keyword weights
- Enable more query variations

**2. Retrieval Strategy Adaptation**:

```python
# app/feedback/optimizer.py
class RetrievalOptimizer:
    def analyze_failures(self, feedback_samples: List[dict]):
        """Analyze failed queries and adjust strategies."""
        for sample in feedback_samples:
            if sample['evaluation_metrics']['retrieval_relevance'] < 0.7:
                # Poor retrieval - adjust weights
                self._adjust_retrieval_weights(sample)

            if sample['evaluation_metrics']['groundedness'] < 0.8:
                # Hallucination detected - strengthen grounding
                self._increase_grounding_strictness(sample)

    def _adjust_retrieval_weights(self, sample):
        """Dynamically adjust semantic/keyword weights."""
        query_type = self._classify_query(sample['query'])

        if query_type == "entity_focused":
            # Increase keyword weight for entity queries
            self.retrieval_config['keyword_weight'] = 0.5
        elif query_type == "conceptual":
            # Increase semantic weight for conceptual queries
            self.retrieval_config['semantic_weight'] = 0.85
```

**3. Prompt Refinement**:

Low coherence scores trigger prompt template adjustments:
```python
if avg_coherence < 0.8:
    synthesis_prompt += "\nProvide a structured response with clear sections."
```

### Continuous Learning Loop

```
┌──────────────┐
│ User Query   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ RAG Pipeline     │
│ (Agent Workflow) │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐     ┌─────────────────┐
│ Evaluation       │────▶│ Store Metrics   │
│ Agent            │     │ & Feedback      │
└──────────────────┘     └────────┬────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Analyze Patterns │
                         │ & Failures       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Adjust           │
                         │ Parameters       │
                         └────────┬─────────┘
                                  │
                                  └─────────┐
                                            │
                                            ▼
                                  ┌──────────────────┐
                                  │ Updated Config   │
                                  │ for Next Query   │
                                  └──────────────────┘
```

---

## CrewAI Integration Details

### Crew Definition

```python
# app/agents/crew_config.py
from crewai import Crew, Process

rag_crew = Crew(
    agents=[
        query_agent.agent,
        retrieval_agent.agent,
        synthesis_agent.agent,
        evaluation_agent.agent
    ],
    tasks=[
        query_expansion_task,
        retrieval_task,
        synthesis_task,
        evaluation_task
    ],
    process=Process.sequential,  # Execute tasks in order
    verbose=True,
    memory=True  # Enable agent memory for context retention
)
```

### Task Definitions

```python
from crewai import Task

query_expansion_task = Task(
    description="""
    Analyze the user query: {query}
    Generate 2 alternative phrasings that preserve intent.
    """,
    agent=query_agent.agent,
    expected_output="JSON with query variations and intent analysis"
)

retrieval_task = Task(
    description="""
    Retrieve the top 5 most relevant documents for the query variations.
    Use hybrid search with semantic and keyword strategies.
    """,
    agent=retrieval_agent.agent,
    expected_output="List of documents with relevance scores",
    context=[query_expansion_task]  # Depends on query task output
)

synthesis_task = Task(
    description="""
    Generate a comprehensive answer using only the retrieved documents.
    Cite all sources and ensure factual accuracy.
    """,
    agent=synthesis_agent.agent,
    expected_output="Grounded answer with source citations",
    context=[retrieval_task]  # Depends on retrieval task output
)

evaluation_task = Task(
    description="""
    Evaluate the answer quality across multiple dimensions.
    Provide metrics and constructive feedback.
    """,
    agent=evaluation_agent.agent,
    expected_output="Quality metrics and feedback",
    context=[synthesis_task]  # Depends on synthesis task output
)
```

### Execution

```python
result = rag_crew.kickoff(inputs={"query": "What is the maximum voltage?"})

# Access outputs
query_variations = result.tasks[0].output
retrieved_docs = result.tasks[1].output
generated_answer = result.tasks[2].output
evaluation = result.tasks[3].output
```

---

## Performance Considerations

### Latency Breakdown

Typical query processing time: **3-5 seconds**

| Stage | Latency | Optimization |
|-------|---------|--------------|
| Query Expansion | 0.5-1.0s | Use smaller LLM (mistral) |
| Retrieval | 0.2-0.5s | HNSW indexing, caching |
| Generation | 2-3s | Streaming, model quantization |
| Evaluation | 0.3-0.5s | Parallel metrics computation |

### Scalability

- **Parallel query variations**: Retrieve for all variations concurrently
- **Batch embedding**: Process multiple queries together
- **Result caching**: Cache frequent queries (Redis)
- **Agent pooling**: Reuse agent instances across requests

---

## Next Steps

- See [Development Roadmap](Development_Roadmap.md) for planned enhancements
- See [Technical Architecture](Technical_Architecture.md) for system design
- See [Deployment Guide](Deployment_Guide.md) for production setup

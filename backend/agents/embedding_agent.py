"""Embedding agent for generating and storing document embeddings.

This module provides a CrewAI agent for generating embeddings from text chunks
and storing them in the vector database.
"""

from typing import List, Dict, Any

from crewai import Agent, Task

from rag.embedding import get_embedding_manager
from rag.retriever import get_retriever


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for text chunks.

    Args:
        texts: List of text chunks.

    Returns:
        List of embedding vectors.
    """
    embedding_manager = get_embedding_manager()
    return embedding_manager.embed_texts(texts)


def store_embeddings(
    texts: List[str],
    metadatas: List[Dict[str, Any]],
    ids: List[str] = None,
) -> Dict[str, Any]:
    """Store embeddings in ChromaDB.

    Args:
        texts: List of text chunks.
        metadatas: List of metadata dictionaries.
        ids: Optional list of chunk IDs.

    Returns:
        Dictionary with storage status.
    """
    retriever = get_retriever()
    retriever.add_documents(texts, metadatas, ids)

    return {
        "status": "success",
        "count": len(texts),
    }


def embed_and_store_chunks(
    chunks: List[Dict[str, Any]],
    document_id: int,
) -> Dict[str, Any]:
    """Generate embeddings and store chunks in vector database.

    Args:
        chunks: List of chunk dictionaries with text and metadata.
        document_id: Database document ID.

    Returns:
        Dictionary with embedding and storage status.
    """
    if not chunks:
        return {
            "status": "error",
            "message": "No chunks provided",
            "count": 0,
        }

    # Extract texts and metadatas
    texts = [chunk["text"] for chunk in chunks]
    metadatas = []

    for i, chunk in enumerate(chunks):
        metadata = chunk.get("metadata", {})
        metadata["document_id"] = str(document_id)
        metadata["chunk_id"] = f"{document_id}_{i}"
        metadatas.append(metadata)

    # Generate IDs
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]

    # Store in vector database
    result = store_embeddings(texts, metadatas, ids)

    return {
        "status": "success",
        "count": len(chunks),
        "document_id": document_id,
    }


def create_embedding_agent() -> Agent:
    """Create embedding agent.

    Returns:
        CrewAI Agent for embedding generation and storage.
    """
    return Agent(
        role="Embedding Specialist",
        goal="Generate high-quality embeddings and store them efficiently in the vector database",
        backstory="""You are an expert in vector embeddings and semantic search.
        Your specialty is generating embeddings that capture semantic meaning and
        organizing them in vector databases for fast retrieval.""",
        tools=[
            generate_embeddings,
            store_embeddings,
        ],
        verbose=True,
    )


def create_embedding_task(agent: Agent, chunks: List[Dict[str, Any]]) -> Task:
    """Create embedding task.

    Args:
        agent: Embedding agent.
        chunks: List of text chunks to embed.

    Returns:
        CrewAI Task for embedding generation.
    """
    return Task(
        description=f"Generate embeddings for {len(chunks)} text chunks and store them in the vector database",
        agent=agent,
        expected_output="Embeddings generated and stored successfully",
    )

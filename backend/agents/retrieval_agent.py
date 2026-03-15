"""Retrieval agent for finding relevant documents.

This module provides a CrewAI agent for retrieving relevant document chunks
from the vector database based on user queries.
"""

from typing import List, Dict, Any, Optional

from crewai import Agent, Task
from crewai_tools import tool

from rag.retriever import get_retriever


@tool("Search Vector Database")
def search_vector_database(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """Search vector database for relevant documents.

    Args:
        query: Search query.
        top_k: Number of results to return.
        score_threshold: Minimum similarity score.

    Returns:
        List of relevant document chunks.
    """
    retriever = get_retriever()

    if score_threshold > 0:
        results = retriever.retrieve_with_score_threshold(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
        )
    else:
        results = retriever.retrieve(query=query, top_k=top_k)

    return results


@tool("Get Document Chunks")
def get_document_chunks(document_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Get all chunks from a specific document.

    Args:
        document_id: Document ID.
        top_k: Maximum number of chunks.

    Returns:
        List of document chunks.
    """
    retriever = get_retriever()
    return retriever.retrieve_by_document_id(document_id, top_k)


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.5,
) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks for a query.

    Args:
        query: User query.
        top_k: Number of results to return.
        score_threshold: Minimum similarity score.

    Returns:
        List of relevant chunks with metadata.
    """
    results = search_vector_database.func(
        query=query,
        top_k=top_k,
        score_threshold=score_threshold,
    )

    return results


def create_retrieval_agent() -> Agent:
    """Create retrieval agent.

    Returns:
        CrewAI Agent for document retrieval.
    """
    return Agent(
        role="Information Retrieval Specialist",
        goal="Find the most relevant documents to answer user queries",
        backstory="""You are an expert in semantic search and information retrieval.
        Your specialty is understanding user queries and finding the most relevant
        documents using vector similarity search.""",
        tools=[
            search_vector_database,
            get_document_chunks,
        ],
        verbose=True,
    )


def create_retrieval_task(agent: Agent, query: str, top_k: int = 5) -> Task:
    """Create retrieval task.

    Args:
        agent: Retrieval agent.
        query: User query.
        top_k: Number of results to retrieve.

    Returns:
        CrewAI Task for document retrieval.
    """
    return Task(
        description=f"Find the top {top_k} most relevant documents for the query: '{query}'",
        agent=agent,
        expected_output="List of relevant document chunks with similarity scores",
    )

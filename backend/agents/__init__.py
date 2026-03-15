"""Agents module for OpenAgentRAG backend."""

from .data_ingestion_agent import (
    extract_text_from_file,
    extract_text_from_url,
)
from .embedding_agent import (
    create_embedding_agent,
    create_embedding_task,
    embed_and_store_chunks,
)
from .retrieval_agent import (
    create_retrieval_agent,
    create_retrieval_task,
    retrieve_relevant_chunks,
)
from .evaluation_agent import (
    create_evaluation_agent,
    create_evaluation_task,
    evaluate_answer,
    log_evaluation,
)

__all__ = [
    "extract_text_from_file",
    "extract_text_from_url",
    "create_embedding_agent",
    "create_embedding_task",
    "embed_and_store_chunks",
    "create_retrieval_agent",
    "create_retrieval_task",
    "retrieve_relevant_chunks",
    "create_evaluation_agent",
    "create_evaluation_task",
    "evaluate_answer",
    "log_evaluation",
]

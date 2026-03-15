"""Embedding generation for RAG pipeline.

This module provides text embedding functionality using SentenceTransformers
with support for batch processing and caching.
"""

from typing import List, Callable
import numpy as np

from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings

from config import get_settings


class EmbeddingManager:
    """Manager for generating text embeddings.

    Uses SentenceTransformers for efficient embedding generation with
    support for batch processing.
    """

    def __init__(self, model_name: str = None):
        """Initialize embedding manager.

        Args:
            model_name: Sentence transformer model name.
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.
            batch_size: Batch size for processing.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query.

        Args:
            query: Query text.

        Returns:
            Embedding vector.
        """
        embedding = self.model.encode(
            query,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        return embedding.tolist()

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Dimension of the embedding vectors.
        """
        return self.model.get_sentence_embedding_dimension()

    def get_embedding_function(self) -> "LangChainEmbeddingFunction":
        """Get LangChain-compatible embedding function.

        Returns:
            Embedding function compatible with LangChain.
        """
        return LangChainEmbeddingFunction(self)


class LangChainEmbeddingFunction(Embeddings):
    """LangChain-compatible embedding function wrapper.

    Wraps EmbeddingManager to provide LangChain Embeddings interface.
    """

    def __init__(self, embedding_manager: EmbeddingManager):
        """Initialize with embedding manager.

        Args:
            embedding_manager: EmbeddingManager instance.
        """
        self.embedding_manager = embedding_manager

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents.

        Args:
            texts: List of document texts.

        Returns:
            List of embedding vectors.
        """
        return self.embedding_manager.embed_texts(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query.

        Args:
            text: Query text.

        Returns:
            Embedding vector.
        """
        return self.embedding_manager.embed_query(text)


# Global embedding manager instance
_embedding_manager: EmbeddingManager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get global embedding manager instance.

    Returns:
        Singleton EmbeddingManager instance.
    """
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager

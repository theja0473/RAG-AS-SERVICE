"""ChromaDB client wrapper for vector storage operations.

This module provides a high-level interface to ChromaDB for storing and
retrieving document embeddings.
"""

from typing import List, Dict, Any, Optional
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import get_settings


class ChromaDBClient:
    """ChromaDB client wrapper.

    Provides methods for managing collections and performing vector operations.
    """

    def __init__(self):
        """Initialize ChromaDB client with settings from configuration."""
        settings = get_settings()
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            ),
        )

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get existing collection or create new one.

        Args:
            name: Collection name.

        Returns:
            ChromaDB collection instance.
        """
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(
        self,
        collection: chromadb.Collection,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to collection.

        Args:
            collection: ChromaDB collection.
            texts: List of document texts.
            embeddings: List of embedding vectors.
            metadatas: List of metadata dictionaries.
            ids: Optional list of document IDs. Generated if not provided.
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]

        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    def query(
        self,
        collection: chromadb.Collection,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query collection for similar documents.

        Args:
            collection: ChromaDB collection.
            query_embedding: Query embedding vector.
            top_k: Number of results to return.
            where: Optional metadata filter.

        Returns:
            Dictionary containing query results with ids, documents, metadatas, and distances.
        """
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

    def delete_collection(self, name: str) -> None:
        """Delete collection.

        Args:
            name: Collection name to delete.
        """
        try:
            self.client.delete_collection(name=name)
        except Exception:
            # Collection doesn't exist, ignore
            pass

    def list_collections(self) -> List[str]:
        """List all collections.

        Returns:
            List of collection names.
        """
        collections = self.client.list_collections()
        return [col.name for col in collections]

    def get_collection_count(self, collection: chromadb.Collection) -> int:
        """Get number of documents in collection.

        Args:
            collection: ChromaDB collection.

        Returns:
            Number of documents in the collection.
        """
        return collection.count()

    def delete_documents(
        self,
        collection: chromadb.Collection,
        ids: List[str]
    ) -> None:
        """Delete documents from collection.

        Args:
            collection: ChromaDB collection.
            ids: List of document IDs to delete.
        """
        collection.delete(ids=ids)

    def delete_documents_by_metadata(
        self,
        collection: chromadb.Collection,
        where: Dict[str, Any]
    ) -> None:
        """Delete documents by metadata filter.

        Args:
            collection: ChromaDB collection.
            where: Metadata filter for deletion.
        """
        collection.delete(where=where)


# Global client instance
_chroma_client: Optional[ChromaDBClient] = None


def get_chroma_client() -> ChromaDBClient:
    """Get global ChromaDB client instance.

    Returns:
        Singleton ChromaDB client.
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaDBClient()
    return _chroma_client

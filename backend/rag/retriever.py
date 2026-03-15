"""Document retrieval for RAG pipeline.

This module provides hybrid retrieval combining semantic search with
optional keyword filtering.
"""

from typing import List, Dict, Any, Optional
import chromadb

from rag.embedding import get_embedding_manager
from database.chromadb_client import get_chroma_client


class HybridRetriever:
    """Hybrid retriever combining semantic and keyword search.

    Uses ChromaDB for semantic vector search with optional metadata filtering.
    """

    def __init__(self, collection_name: str = "documents"):
        """Initialize hybrid retriever.

        Args:
            collection_name: Name of the ChromaDB collection.
        """
        self.collection_name = collection_name
        self.chroma_client = get_chroma_client()
        self.embedding_manager = get_embedding_manager()
        self.collection = self.chroma_client.get_or_create_collection(collection_name)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: Search query.
            top_k: Number of results to return.
            where: Optional metadata filter.

        Returns:
            List of retrieved document dictionaries with content, metadata, score, and source.
        """
        # Generate query embedding
        query_embedding = self.embedding_manager.embed_query(query)

        # Query ChromaDB
        results = self.chroma_client.query(
            collection=self.collection,
            query_embedding=query_embedding,
            top_k=top_k,
            where=where,
        )

        # Format results
        documents = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                doc = {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "score": 1 - results["distances"][0][i] if results.get("distances") else 0,  # Convert distance to similarity
                    "source": results["metadatas"][0][i].get("source", "Unknown") if results.get("metadatas") else "Unknown",
                }
                documents.append(doc)

        return documents

    def retrieve_with_score_threshold(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents with minimum similarity score.

        Args:
            query: Search query.
            top_k: Number of results to return.
            score_threshold: Minimum similarity score (0-1).
            where: Optional metadata filter.

        Returns:
            List of retrieved documents meeting the score threshold.
        """
        results = self.retrieve(query, top_k=top_k, where=where)
        return [doc for doc in results if doc["score"] >= score_threshold]

    def retrieve_by_document_id(
        self,
        document_id: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Retrieve chunks from a specific document.

        Args:
            document_id: Document ID to retrieve chunks from.
            top_k: Maximum number of chunks to return.

        Returns:
            List of document chunks.
        """
        return self.retrieve(
            query="",  # Empty query when filtering by metadata
            top_k=top_k,
            where={"document_id": document_id},
        )

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with collection statistics.
        """
        count = self.chroma_client.get_collection_count(self.collection)
        return {
            "collection_name": self.collection_name,
            "document_count": count,
        }

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to the collection.

        Args:
            texts: List of document texts.
            metadatas: List of metadata dictionaries.
            ids: Optional list of document IDs.
        """
        # Generate embeddings
        embeddings = self.embedding_manager.embed_texts(texts)

        # Add to ChromaDB
        self.chroma_client.add_documents(
            collection=self.collection,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunks for a specific document.

        Args:
            document_id: Document ID to delete.
        """
        self.chroma_client.delete_documents_by_metadata(
            collection=self.collection,
            where={"document_id": str(document_id)},
        )

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        self.chroma_client.delete_collection(self.collection_name)
        self.collection = self.chroma_client.get_or_create_collection(self.collection_name)


# Global retriever instance
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """Get global retriever instance.

    Returns:
        Singleton HybridRetriever instance.
    """
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever

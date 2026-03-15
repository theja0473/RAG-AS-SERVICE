"""Semantic text chunking for RAG pipeline.

This module provides intelligent text chunking that preserves semantic coherence
by grouping sentences based on similarity.
"""

from typing import List, Dict, Any
import logging
import re

from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from config import get_settings

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Semantic chunker that groups text by semantic similarity.

    Uses sentence embeddings to identify natural breakpoints in text,
    creating chunks that are semantically coherent.
    """

    def __init__(
        self,
        embedding_model: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        similarity_threshold: float = 0.6,
    ):
        """Initialize semantic chunker.

        Args:
            embedding_model: Sentence transformer model name.
            chunk_size: Maximum chunk size in characters.
            chunk_overlap: Overlap between chunks.
            similarity_threshold: Threshold for semantic similarity (0-1).
        """
        settings = get_settings()
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.similarity_threshold = similarity_threshold

        # Load embedding model for semantic analysis
        self.embedder = SentenceTransformer(self.embedding_model_name)

        # Fallback splitter for very long texts
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text.

        Returns:
            List of sentences.
        """
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _group_sentences_by_similarity(self, sentences: List[str]) -> List[List[str]]:
        """Group sentences into semantically coherent chunks.

        Args:
            sentences: List of sentences.

        Returns:
            List of sentence groups.
        """
        if not sentences:
            return []

        if len(sentences) == 1:
            return [sentences]

        # Compute embeddings for all sentences
        embeddings = self.embedder.encode(sentences)

        # Group sentences based on similarity
        groups = []
        current_group = [sentences[0]]
        current_embedding = embeddings[0:1]

        for i in range(1, len(sentences)):
            # Calculate similarity between current sentence and group centroid
            group_centroid = np.mean(current_embedding, axis=0).reshape(1, -1)
            sentence_embedding = embeddings[i:i+1]
            similarity = cosine_similarity(sentence_embedding, group_centroid)[0][0]

            # Check if adding this sentence would exceed chunk size
            current_text = " ".join(current_group + [sentences[i]])

            if similarity >= self.similarity_threshold and len(current_text) <= self.chunk_size:
                # Add to current group
                current_group.append(sentences[i])
                current_embedding = np.vstack([current_embedding, sentence_embedding])
            else:
                # Start new group
                if current_group:
                    groups.append(current_group)
                current_group = [sentences[i]]
                current_embedding = sentence_embedding

        # Add final group
        if current_group:
            groups.append(current_group)

        return groups

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Chunk text into semantically coherent pieces.

        Args:
            text: Input text to chunk.
            metadata: Optional metadata to attach to chunks.

        Returns:
            List of chunk dictionaries with text and metadata.
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}

        # Try semantic chunking
        try:
            sentences = self._split_into_sentences(text)

            if not sentences:
                return []

            # Group sentences semantically
            sentence_groups = self._group_sentences_by_similarity(sentences)

            # Create chunks from sentence groups
            chunks = []
            for i, group in enumerate(sentence_groups):
                chunk_text = " ".join(group)

                # If chunk is still too large, use fallback splitter
                if len(chunk_text) > self.chunk_size * 1.5:
                    sub_chunks = self.fallback_splitter.split_text(chunk_text)
                    for j, sub_chunk in enumerate(sub_chunks):
                        chunk_metadata = {
                            **metadata,
                            "chunk_index": len(chunks),
                            "sub_chunk_index": j,
                            "chunking_method": "semantic_fallback",
                        }
                        chunks.append({
                            "text": sub_chunk,
                            "metadata": chunk_metadata,
                        })
                else:
                    chunk_metadata = {
                        **metadata,
                        "chunk_index": i,
                        "chunking_method": "semantic",
                    }
                    chunks.append({
                        "text": chunk_text,
                        "metadata": chunk_metadata,
                    })

            return chunks

        except Exception as e:
            # Fallback to simple chunking if semantic chunking fails
            logger.warning("Semantic chunking failed: %s. Using fallback splitter.", e)
            text_chunks = self.fallback_splitter.split_text(text)
            return [
                {
                    "text": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "chunking_method": "fallback",
                    }
                }
                for i, chunk in enumerate(text_chunks)
            ]

    def chunk_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Chunk multiple documents.

        Args:
            documents: List of document dicts with 'text' and 'metadata' keys.

        Returns:
            List of chunk dictionaries.
        """
        all_chunks = []
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            chunks = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        return all_chunks

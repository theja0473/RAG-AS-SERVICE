"""Document processing service.

This module orchestrates the complete document processing pipeline from
upload through embedding and storage.
"""

from typing import Dict, Any, BinaryIO
from pathlib import Path
import uuid
import shutil

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import get_settings
from database.models import Document
from agents.data_ingestion_agent import extract_text_from_file, extract_text_from_url
from agents.embedding_agent import embed_and_store_chunks
from rag.chunking import SemanticChunker


class DocumentService:
    """Service for document processing operations."""

    def __init__(self):
        """Initialize document service."""
        self.settings = get_settings()
        self.chunker = SemanticChunker()

    async def process_document(
        self,
        db: AsyncSession,
        file: BinaryIO,
        filename: str,
        source_type: str,
    ) -> Document:
        """Process uploaded document.

        Args:
            db: Database session.
            file: File object.
            filename: Original filename.
            source_type: Type of document.

        Returns:
            Created Document instance.
        """
        # Create database record
        document = Document(
            filename=filename,
            source_type=source_type,
            status="processing",
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        try:
            # Save file
            upload_dir = self.settings.ensure_upload_dir()
            file_path = upload_dir / f"{document.id}_{filename}"

            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)

            # Extract text
            extracted = extract_text_from_file(str(file_path), source_type)
            text = extracted["text"]
            metadata = extracted["metadata"]
            metadata["document_id"] = document.id

            # Chunk text
            chunks = self.chunker.chunk_text(text, metadata)

            # Embed and store chunks
            embed_result = embed_and_store_chunks(chunks, document.id)

            # Update document record
            document.status = "completed"
            document.chunk_count = len(chunks)
            await db.commit()
            await db.refresh(document)

            return document

        except Exception as e:
            # Update status to failed
            document.status = "failed"
            await db.commit()
            raise e

    async def process_url(
        self,
        db: AsyncSession,
        url: str,
    ) -> Document:
        """Process URL document.

        Args:
            db: Database session.
            url: URL to process.

        Returns:
            Created Document instance.
        """
        # Create database record
        document = Document(
            filename=url,
            source_type="url",
            status="processing",
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        try:
            # Extract text from URL
            extracted = extract_text_from_url(url)
            text = extracted["text"]
            metadata = extracted["metadata"]
            metadata["document_id"] = document.id

            # Chunk text
            chunks = self.chunker.chunk_text(text, metadata)

            # Embed and store chunks
            embed_result = embed_and_store_chunks(chunks, document.id)

            # Update document record
            document.status = "completed"
            document.chunk_count = len(chunks)
            await db.commit()
            await db.refresh(document)

            return document

        except Exception as e:
            # Update status to failed
            document.status = "failed"
            await db.commit()
            raise e

    async def get_document(self, db: AsyncSession, document_id: int) -> Document:
        """Get document by ID.

        Args:
            db: Database session.
            document_id: Document ID.

        Returns:
            Document instance or None.
        """
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """List all documents.

        Args:
            db: Database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Document instances.
        """
        result = await db.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: int,
    ) -> bool:
        """Delete document and its embeddings.

        Args:
            db: Database session.
            document_id: Document ID.

        Returns:
            True if deleted, False if not found.
        """
        document = await self.get_document(db, document_id)
        if not document:
            return False

        # Delete from vector database
        from rag.retriever import get_retriever
        retriever = get_retriever()
        retriever.delete_by_document_id(str(document_id))

        # Delete file if it exists
        upload_dir = self.settings.ensure_upload_dir()
        file_path = upload_dir / f"{document_id}_{document.filename}"
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        await db.delete(document)
        await db.commit()

        return True


# Global service instance
_document_service: DocumentService = None


def get_document_service() -> DocumentService:
    """Get global document service instance.

    Returns:
        Singleton DocumentService instance.
    """
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service

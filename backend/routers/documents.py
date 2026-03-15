"""Documents router for file upload and management.

This module provides REST API endpoints for document upload, listing,
retrieval, and deletion.
"""

from typing import List
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl

from database import get_db
from services.document_service import get_document_service


router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    """Document response model."""
    id: int
    filename: str
    source_type: str
    status: str
    chunk_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class URLIngestRequest(BaseModel):
    """URL ingestion request model."""
    url: HttpUrl


class DocumentListResponse(BaseModel):
    """Document list response model."""
    documents: List[DocumentResponse]
    total: int


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a document.

    Args:
        file: Uploaded file.
        db: Database session.

    Returns:
        Created document metadata.

    Raises:
        HTTPException: If file type is not supported.
    """
    # Validate file type
    filename = file.filename
    suffix = Path(filename).suffix.lower()

    supported_types = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".xlsx": "xlsx",
        ".txt": "txt",
    }

    if suffix not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Supported types: {', '.join(supported_types.keys())}"
        )

    source_type = supported_types[suffix]

    # Process document
    try:
        document_service = get_document_service()
        document = await document_service.process_document(
            db=db,
            file=file.file,
            filename=filename,
            source_type=source_type,
        )

        return DocumentResponse(**document.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.post("/ingest-url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_url(
    request: URLIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingest document from URL.

    Args:
        request: URL ingestion request.
        db: Database session.

    Returns:
        Created document metadata.
    """
    try:
        document_service = get_document_service()
        document = await document_service.process_url(
            db=db,
            url=str(request.url),
        )

        return DocumentResponse(**document.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting URL: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all documents.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        db: Database session.

    Returns:
        List of documents.
    """
    document_service = get_document_service()
    documents = await document_service.list_documents(db, skip=skip, limit=limit)

    return DocumentListResponse(
        documents=[DocumentResponse(**doc.to_dict()) for doc in documents],
        total=len(documents),
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get document by ID.

    Args:
        document_id: Document ID.
        db: Database session.

    Returns:
        Document metadata.

    Raises:
        HTTPException: If document not found.
    """
    document_service = get_document_service()
    document = await document_service.get_document(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return DocumentResponse(**document.to_dict())


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete document and its embeddings.

    Args:
        document_id: Document ID.
        db: Database session.

    Raises:
        HTTPException: If document not found.
    """
    document_service = get_document_service()
    deleted = await document_service.delete_document(db, document_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return None

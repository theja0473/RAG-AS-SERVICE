"""Chat router for query processing and history management.

This module provides REST API endpoints for querying the RAG system
and managing chat history.
"""

from typing import List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from database import get_db
from services.chat_service import get_chat_service


router = APIRouter(prefix="/api/chat", tags=["chat"])


class QueryRequest(BaseModel):
    """Query request model."""
    question: str = Field(..., min_length=1, description="User question")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Chat session ID")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    use_graph_rag: bool = Field(default=True, description="Enable knowledge graph enrichment")


class SourceResponse(BaseModel):
    """Source response model."""
    id: int
    source: str
    content: str
    score: float


class EvaluationResponse(BaseModel):
    """Evaluation response model."""
    relevance_score: float
    groundedness_score: float
    hallucination_risk: float
    overall_quality: float


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    sources: List[SourceResponse]
    evaluation: EvaluationResponse
    session_id: str


class ChatMessage(BaseModel):
    """Chat message model."""
    id: int
    session_id: str
    role: str
    content: str
    sources: List[Dict[str, Any]] = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Chat history response model."""
    messages: List[ChatMessage]
    total: int


class SessionResponse(BaseModel):
    """Session response model."""
    session_id: str
    created_at: str


class SessionListResponse(BaseModel):
    """Session list response model."""
    sessions: List[SessionResponse]
    total: int


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a query to the RAG system.

    Args:
        request: Query request.
        db: Database session.

    Returns:
        RAG response with answer, sources, and evaluation.
    """
    try:
        chat_service = get_chat_service()
        result = await chat_service.query(
            db=db,
            question=request.question,
            session_id=request.session_id,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
        )

        return QueryResponse(
            answer=result["answer"],
            sources=[SourceResponse(**source) for source in result["sources"]],
            evaluation=EvaluationResponse(**result["evaluation"]),
            session_id=result["session_id"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a session.

    Args:
        session_id: Chat session ID.
        limit: Maximum number of messages to return.
        db: Database session.

    Returns:
        Chat history.
    """
    try:
        chat_service = get_chat_service()
        messages = await chat_service.get_history(
            db=db,
            session_id=session_id,
            limit=limit,
        )

        return ChatHistoryResponse(
            messages=[ChatMessage(**msg) for msg in messages],
            total=len(messages),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat history: {str(e)}"
        )


@router.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Clear chat history for a session.

    Args:
        session_id: Chat session ID.
        db: Database session.
    """
    try:
        chat_service = get_chat_service()
        await chat_service.clear_history(db=db, session_id=session_id)
        return None

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing chat history: {str(e)}"
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions.

    Args:
        db: Database session.

    Returns:
        List of chat sessions.
    """
    try:
        chat_service = get_chat_service()
        sessions = await chat_service.get_all_sessions(db=db)

        return SessionListResponse(
            sessions=[SessionResponse(**session) for session in sessions],
            total=len(sessions),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sessions: {str(e)}"
        )

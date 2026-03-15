"""SQLAlchemy database models for metadata storage.

This module defines all database models for tracking documents, chat history,
evaluation logs, and application settings.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, Float, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Document(Base):
    """Document metadata model.

    Tracks uploaded documents and their processing status.
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, docx, url, etc.
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, completed, failed
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the document.
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "source_type": self.source_type,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatHistory(Base):
    """Chat history model.

    Stores conversation history with source citations.
    """
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of sources
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the chat message.
        """
        import json
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sources": json.loads(self.sources_json) if self.sources_json else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EvaluationLog(Base):
    """Evaluation log model.

    Tracks quality metrics for generated answers.
    """
    __tablename__ = "evaluation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=True)
    groundedness_score: Mapped[float] = mapped_column(Float, nullable=True)
    hallucination_risk: Mapped[float] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the evaluation log.
        """
        return {
            "id": self.id,
            "query": self.query,
            "answer": self.answer,
            "relevance_score": self.relevance_score,
            "groundedness_score": self.groundedness_score,
            "hallucination_risk": self.hallucination_risk,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Settings(Base):
    """Application settings model.

    Stores dynamic configuration that can be updated at runtime.
    """
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the setting.
        """
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

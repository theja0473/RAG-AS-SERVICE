"""Chat service for query processing.

This module orchestrates the RAG query pipeline including retrieval,
generation, evaluation, and history storage.
"""

from typing import Dict, Any, List
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import ChatHistory
from agents.retrieval_agent import retrieve_relevant_chunks
from agents.evaluation_agent import evaluate_answer, log_evaluation
from rag.generator import get_generator


class ChatService:
    """Service for chat and query operations."""

    def __init__(self):
        """Initialize chat service."""
        self.generator = get_generator()

    async def query(
        self,
        db: AsyncSession,
        question: str,
        session_id: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Process a user query through the RAG pipeline.

        Args:
            db: Database session.
            question: User question.
            session_id: Chat session ID.
            top_k: Number of documents to retrieve.
            score_threshold: Minimum similarity score for retrieval.

        Returns:
            Dictionary with answer, sources, and evaluation metrics.
        """
        # Save user message
        user_message = ChatHistory(
            session_id=session_id,
            role="user",
            content=question,
        )
        db.add(user_message)
        await db.commit()

        # Retrieve relevant chunks
        contexts = retrieve_relevant_chunks(
            query=question,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        # Generate answer
        generation_result = self.generator.generate(question, contexts)
        answer = generation_result["answer"]
        sources = generation_result["sources"]

        # Evaluate answer
        evaluation = evaluate_answer(question, answer, contexts)

        # Log evaluation
        await log_evaluation(
            db=db,
            query=question,
            answer=answer,
            evaluation=evaluation,
        )

        # Save assistant message
        assistant_message = ChatHistory(
            session_id=session_id,
            role="assistant",
            content=answer,
            sources_json=json.dumps(sources),
        )
        db.add(assistant_message)
        await db.commit()

        return {
            "answer": answer,
            "sources": sources,
            "evaluation": evaluation,
            "session_id": session_id,
        }

    async def get_history(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get chat history for a session.

        Args:
            db: Database session.
            session_id: Chat session ID.
            limit: Maximum number of messages to return.

        Returns:
            List of chat messages.
        """
        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.asc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return [msg.to_dict() for msg in messages]

    async def clear_history(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> int:
        """Clear chat history for a session.

        Args:
            db: Database session.
            session_id: Chat session ID.

        Returns:
            Number of messages deleted.
        """
        result = await db.execute(
            select(ChatHistory).where(ChatHistory.session_id == session_id)
        )
        messages = result.scalars().all()
        count = len(messages)

        for msg in messages:
            await db.delete(msg)

        await db.commit()
        return count

    async def get_all_sessions(
        self,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """Get list of all chat sessions.

        Args:
            db: Database session.

        Returns:
            List of session information.
        """
        result = await db.execute(
            select(ChatHistory.session_id, ChatHistory.created_at)
            .distinct()
            .order_by(ChatHistory.created_at.desc())
        )

        sessions = []
        seen_sessions = set()

        for row in result:
            session_id = row[0]
            if session_id not in seen_sessions:
                seen_sessions.add(session_id)
                sessions.append({
                    "session_id": session_id,
                    "created_at": row[1].isoformat() if row[1] else None,
                })

        return sessions


# Global service instance
_chat_service: ChatService = None


def get_chat_service() -> ChatService:
    """Get global chat service instance.

    Returns:
        Singleton ChatService instance.
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service

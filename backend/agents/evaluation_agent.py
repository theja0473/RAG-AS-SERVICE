"""Evaluation agent for assessing answer quality.

This module provides a CrewAI agent for evaluating the quality of generated
answers based on relevance, groundedness, and hallucination risk.
"""

from typing import Dict, Any, List
import re

from crewai import Agent, Task
from crewai_tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag.generator import get_generator
from database.models import EvaluationLog


@tool("Evaluate Answer Relevance")
def evaluate_relevance(query: str, answer: str) -> float:
    """Evaluate how relevant the answer is to the query.

    Args:
        query: User query.
        answer: Generated answer.

    Returns:
        Relevance score between 0 and 1.
    """
    # Simple relevance check based on keyword overlap
    query_words = set(query.lower().split())
    answer_words = set(answer.lower().split())

    if not query_words:
        return 0.0

    overlap = len(query_words.intersection(answer_words))
    relevance = overlap / len(query_words)

    return min(relevance, 1.0)


@tool("Evaluate Answer Groundedness")
def evaluate_groundedness(answer: str, contexts: List[Dict[str, Any]]) -> float:
    """Evaluate how well the answer is grounded in the provided context.

    Args:
        answer: Generated answer.
        contexts: Retrieved context chunks.

    Returns:
        Groundedness score between 0 and 1.
    """
    if not contexts:
        return 0.0

    # Check for source citations in the answer
    citation_pattern = r'\[Source[^\]]*\]'
    citations = re.findall(citation_pattern, answer)

    # If answer cites sources, it's better grounded
    if citations:
        base_score = 0.7
    else:
        base_score = 0.3

    # Check if answer content overlaps with context
    answer_words = set(answer.lower().split())
    context_words = set()

    for ctx in contexts:
        context_words.update(ctx.get("content", "").lower().split())

    if not answer_words or not context_words:
        return base_score

    overlap = len(answer_words.intersection(context_words))
    overlap_ratio = overlap / len(answer_words)

    # Combine citation score with overlap score
    groundedness = (base_score + overlap_ratio) / 2

    return min(groundedness, 1.0)


@tool("Evaluate Hallucination Risk")
def evaluate_hallucination_risk(answer: str, contexts: List[Dict[str, Any]]) -> float:
    """Evaluate the risk of hallucination in the answer.

    Args:
        answer: Generated answer.
        contexts: Retrieved context chunks.

    Returns:
        Hallucination risk score between 0 and 1 (higher = more risk).
    """
    # Check if answer admits lack of information
    uncertainty_phrases = [
        "i don't have",
        "i don't know",
        "not enough information",
        "cannot answer",
        "no information",
    ]

    answer_lower = answer.lower()
    has_uncertainty = any(phrase in answer_lower for phrase in uncertainty_phrases)

    if has_uncertainty:
        return 0.1  # Low risk if model admits uncertainty

    # Check for source citations
    citation_pattern = r'\[Source[^\]]*\]'
    has_citations = bool(re.search(citation_pattern, answer))

    if not has_citations and not has_uncertainty:
        return 0.7  # Higher risk if no citations and no uncertainty

    # Check content overlap with context
    if not contexts:
        return 0.9  # Very high risk if no context

    answer_words = set(answer.lower().split())
    context_words = set()

    for ctx in contexts:
        context_words.update(ctx.get("content", "").lower().split())

    if not answer_words:
        return 0.5

    overlap = len(answer_words.intersection(context_words))
    overlap_ratio = overlap / len(answer_words)

    # Low overlap = higher hallucination risk
    hallucination_risk = 1.0 - overlap_ratio

    return min(hallucination_risk, 1.0)


def evaluate_answer(
    query: str,
    answer: str,
    contexts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluate answer quality across multiple metrics.

    Args:
        query: User query.
        answer: Generated answer.
        contexts: Retrieved context chunks.

    Returns:
        Dictionary with evaluation scores.
    """
    relevance_score = evaluate_relevance.func(query, answer)
    groundedness_score = evaluate_groundedness.func(answer, contexts)
    hallucination_risk = evaluate_hallucination_risk.func(answer, contexts)

    return {
        "relevance_score": round(relevance_score, 3),
        "groundedness_score": round(groundedness_score, 3),
        "hallucination_risk": round(hallucination_risk, 3),
        "overall_quality": round((relevance_score + groundedness_score + (1 - hallucination_risk)) / 3, 3),
    }


async def log_evaluation(
    db: AsyncSession,
    query: str,
    answer: str,
    evaluation: Dict[str, Any],
    feedback: str = None,
) -> EvaluationLog:
    """Log evaluation to database.

    Args:
        db: Database session.
        query: User query.
        answer: Generated answer.
        evaluation: Evaluation scores.
        feedback: Optional user feedback.

    Returns:
        Created EvaluationLog instance.
    """
    eval_log = EvaluationLog(
        query=query,
        answer=answer,
        relevance_score=evaluation.get("relevance_score"),
        groundedness_score=evaluation.get("groundedness_score"),
        hallucination_risk=evaluation.get("hallucination_risk"),
        feedback=feedback,
    )

    db.add(eval_log)
    await db.commit()
    await db.refresh(eval_log)

    return eval_log


def create_evaluation_agent() -> Agent:
    """Create evaluation agent.

    Returns:
        CrewAI Agent for answer evaluation.
    """
    return Agent(
        role="Quality Assurance Specialist",
        goal="Evaluate the quality and accuracy of generated answers",
        backstory="""You are an expert in evaluating AI-generated content.
        Your specialty is assessing answer quality, detecting hallucinations,
        and ensuring responses are well-grounded in source material.""",
        tools=[
            evaluate_relevance,
            evaluate_groundedness,
            evaluate_hallucination_risk,
        ],
        verbose=True,
    )


def create_evaluation_task(
    agent: Agent,
    query: str,
    answer: str,
    contexts: List[Dict[str, Any]],
) -> Task:
    """Create evaluation task.

    Args:
        agent: Evaluation agent.
        query: User query.
        answer: Generated answer.
        contexts: Retrieved contexts.

    Returns:
        CrewAI Task for answer evaluation.
    """
    return Task(
        description=f"Evaluate the quality of the generated answer for query: '{query}'",
        agent=agent,
        expected_output="Quality scores including relevance, groundedness, and hallucination risk",
    )

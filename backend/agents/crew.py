"""CrewAI Crew orchestration for RAG workflows.

This module provides high-level orchestration of agent workflows for
document ingestion and query processing.
"""

from typing import Dict, Any, List

from crewai import Crew, Process

from agents.data_ingestion_agent import create_data_ingestion_agent, create_data_ingestion_task
from agents.embedding_agent import create_embedding_agent, create_embedding_task
from agents.retrieval_agent import create_retrieval_agent, create_retrieval_task
from agents.evaluation_agent import create_evaluation_agent, create_evaluation_task


class IngestionCrew:
    """Crew for document ingestion workflow.

    Orchestrates data extraction, chunking, embedding, and storage.
    """

    def __init__(self):
        """Initialize ingestion crew with agents."""
        self.ingestion_agent = create_data_ingestion_agent()
        self.embedding_agent = create_embedding_agent()

    def process_document(self, file_path: str, source_type: str) -> Dict[str, Any]:
        """Process a document through the ingestion pipeline.

        Args:
            file_path: Path to document file.
            source_type: Type of document (pdf, docx, etc.).

        Returns:
            Dictionary with processing results.
        """
        # Create tasks
        ingestion_task = create_data_ingestion_task(
            self.ingestion_agent,
            file_path,
            source_type,
        )

        # Create crew
        crew = Crew(
            agents=[self.ingestion_agent],
            tasks=[ingestion_task],
            process=Process.sequential,
            verbose=True,
        )

        # Execute crew
        result = crew.kickoff()

        return {
            "status": "success",
            "result": result,
        }


class QueryCrew:
    """Crew for query processing workflow.

    Orchestrates retrieval, generation, and evaluation.
    """

    def __init__(self):
        """Initialize query crew with agents."""
        self.retrieval_agent = create_retrieval_agent()
        self.evaluation_agent = create_evaluation_agent()

    def process_query(
        self,
        query: str,
        answer: str,
        contexts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process a query through the RAG pipeline.

        Args:
            query: User query.
            answer: Generated answer.
            contexts: Retrieved contexts.

        Returns:
            Dictionary with evaluation results.
        """
        # Create evaluation task
        evaluation_task = create_evaluation_task(
            self.evaluation_agent,
            query,
            answer,
            contexts,
        )

        # Create crew
        crew = Crew(
            agents=[self.evaluation_agent],
            tasks=[evaluation_task],
            process=Process.sequential,
            verbose=True,
        )

        # Execute crew
        result = crew.kickoff()

        return {
            "status": "success",
            "result": result,
        }


# Global crew instances
_ingestion_crew: IngestionCrew = None
_query_crew: QueryCrew = None


def get_ingestion_crew() -> IngestionCrew:
    """Get global ingestion crew instance.

    Returns:
        Singleton IngestionCrew instance.
    """
    global _ingestion_crew
    if _ingestion_crew is None:
        _ingestion_crew = IngestionCrew()
    return _ingestion_crew


def get_query_crew() -> QueryCrew:
    """Get global query crew instance.

    Returns:
        Singleton QueryCrew instance.
    """
    global _query_crew
    if _query_crew is None:
        _query_crew = QueryCrew()
    return _query_crew

"""Graph-enhanced retrieval for RAG pipeline.

This module combines traditional vector retrieval with knowledge graph
traversal to provide richer, more connected context for answer generation.
"""

from typing import List, Dict, Any, Optional
import logging
import re

from config import get_settings
from rag.retriever import get_retriever, HybridRetriever
from database.neo4j_client import get_neo4j_client, Neo4jClient

logger = logging.getLogger(__name__)


class GraphRetriever:
    """Combines vector search with knowledge graph traversal.

    First performs standard vector retrieval, then enriches results
    with related entities and relationships from the knowledge graph.
    """

    def __init__(
        self,
        vector_retriever: Optional[HybridRetriever] = None,
        neo4j_client: Optional[Neo4jClient] = None,
    ):
        """Initialize graph retriever.

        Args:
            vector_retriever: Optional vector retriever instance.
            neo4j_client: Optional Neo4j client instance.
        """
        self.vector_retriever = vector_retriever or get_retriever()
        self.neo4j_client = neo4j_client or get_neo4j_client()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        graph_depth: int = 2,
        max_graph_results: int = 15,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Retrieve context using both vector search and graph traversal.

        Args:
            query: User query.
            top_k: Number of vector search results.
            score_threshold: Minimum similarity score.
            graph_depth: Max depth for graph traversal.
            max_graph_results: Max number of graph triples.
            where: Optional metadata filter for vector search.

        Returns:
            Dictionary with vector_results, graph_context, and merged context.
        """
        # Step 1: Vector retrieval
        vector_results = self.vector_retriever.retrieve_with_score_threshold(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            where=where,
        )

        # Step 2: Extract entity names from query and retrieved content
        entity_names = self._extract_entity_names_from_query(query)

        # Also extract entities mentioned in top vector results
        for result in vector_results[:3]:
            content = result.get("content", "")
            entity_names.extend(self._extract_entity_names_from_query(content))

        # Deduplicate
        entity_names = list(set(entity_names))

        # Step 3: Graph traversal
        graph_context = []
        if entity_names:
            try:
                graph_context = self.neo4j_client.get_entity_context_simple(
                    entity_names=entity_names,
                    max_depth=graph_depth,
                    max_results=max_graph_results,
                )
            except Exception as e:
                logger.warning("Graph retrieval failed: %s", e)

        # Step 4: Build enriched context
        graph_text = self._format_graph_context(graph_context)

        return {
            "vector_results": vector_results,
            "graph_context": graph_context,
            "graph_context_text": graph_text,
            "entity_names_used": entity_names,
        }

    def retrieve_as_contexts(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        graph_depth: int = 2,
        max_graph_results: int = 15,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve and merge vector + graph results into a flat context list.

        This is the drop-in replacement for the standard retriever's output,
        adding graph knowledge as an additional context entry.

        Args:
            query: User query.
            top_k: Number of vector search results.
            score_threshold: Minimum similarity score.
            graph_depth: Max depth for graph traversal.
            max_graph_results: Max number of graph triples.
            where: Optional metadata filter.

        Returns:
            List of context dictionaries compatible with the generator.
        """
        result = self.retrieve(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            graph_depth=graph_depth,
            max_graph_results=max_graph_results,
            where=where,
        )

        contexts = list(result["vector_results"])

        # Append graph context as an additional source if available
        graph_text = result["graph_context_text"]
        if graph_text:
            contexts.append({
                "content": graph_text,
                "metadata": {"source_type": "knowledge_graph"},
                "score": 1.0,
                "source": "Knowledge Graph",
            })

        return contexts

    def _extract_entity_names_from_query(self, text: str) -> List[str]:
        """Extract potential entity names from text using heuristics.

        Identifies capitalized phrases and quoted terms as potential entities.

        Args:
            text: Input text.

        Returns:
            List of potential entity name strings.
        """
        entities = []

        # Extract capitalized multi-word phrases (e.g., "New York", "John Smith")
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        entities.extend(capitalized)

        # Extract quoted terms
        quoted = re.findall(r'"([^"]+)"', text)
        entities.extend(quoted)

        # Extract terms after keywords like "about", "what is", "who is"
        keyword_patterns = [
            r'(?:about|regarding|concerning)\s+(.+?)(?:\?|$|\.)',
            r'(?:what|who|where|when)\s+(?:is|are|was|were)\s+(.+?)(?:\?|$|\.)',
        ]
        for pattern in keyword_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

        # Clean up and deduplicate
        cleaned = []
        for e in entities:
            e = e.strip()
            if len(e) > 1 and e.lower() not in {"the", "this", "that", "what", "who", "where"}:
                cleaned.append(e)

        return list(set(cleaned))

    def _format_graph_context(self, graph_context: List[Dict[str, Any]]) -> str:
        """Format graph triples into readable text for the LLM.

        Args:
            graph_context: List of relationship triple dictionaries.

        Returns:
            Formatted string of graph knowledge.
        """
        if not graph_context:
            return ""

        lines = ["Knowledge Graph relationships:"]
        for triple in graph_context:
            source = triple.get("source_name", "?")
            rel = triple.get("relationship", "RELATED_TO").replace("_", " ").lower()
            target = triple.get("target_name", "?")
            source_type = triple.get("source_type", "")
            target_type = triple.get("target_type", "")

            type_info = ""
            if source_type and target_type:
                type_info = f" [{source_type} -> {target_type}]"

            lines.append(f"- {source} {rel} {target}{type_info}")

        return "\n".join(lines)


# Global instance
_graph_retriever: Optional[GraphRetriever] = None


def get_graph_retriever() -> GraphRetriever:
    """Get global graph retriever instance.

    Returns:
        Singleton GraphRetriever instance.
    """
    global _graph_retriever
    if _graph_retriever is None:
        _graph_retriever = GraphRetriever()
    return _graph_retriever

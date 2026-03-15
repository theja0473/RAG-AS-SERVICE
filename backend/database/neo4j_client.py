"""Neo4j client wrapper for knowledge graph operations.

This module provides a high-level interface to Neo4j for storing and
querying entities and relationships extracted from documents.
"""

from typing import List, Dict, Any, Optional
import logging

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable

from config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j client for knowledge graph operations.

    Provides methods for managing entities, relationships, and graph queries.
    """

    def __init__(self):
        """Initialize Neo4j client with settings from configuration."""
        settings = get_settings()
        self._driver: Optional[Driver] = None
        self._uri = settings.neo4j_uri
        self._username = settings.neo4j_username
        self._password = settings.neo4j_password

    @property
    def driver(self) -> Driver:
        """Lazy-initialize Neo4j driver."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._username, self._password),
            )
        return self._driver

    def close(self) -> None:
        """Close Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        """Verify connectivity to Neo4j.

        Returns:
            True if connected, False otherwise.
        """
        try:
            self.driver.verify_connectivity()
            return True
        except ServiceUnavailable:
            logger.error("Cannot connect to Neo4j at %s", self._uri)
            return False

    def setup_indexes(self) -> None:
        """Create indexes for efficient graph queries."""
        queries = [
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_doc IF NOT EXISTS FOR (e:Entity) ON (e.document_id)",
            "CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.document_id)",
        ]
        with self.driver.session() as session:
            for query in queries:
                session.run(query)
        logger.info("Neo4j indexes created")

    def add_entities_and_relationships(
        self,
        document_id: str,
        entities: List[Dict[str, str]],
        relationships: List[Dict[str, str]],
    ) -> Dict[str, int]:
        """Add entities and relationships from a document to the graph.

        Args:
            document_id: Source document ID.
            entities: List of entity dicts with 'name' and 'type' keys.
            relationships: List of relationship dicts with 'source', 'target',
                           'type', and optional 'properties' keys.

        Returns:
            Dictionary with counts of created entities and relationships.
        """
        entity_count = 0
        rel_count = 0

        with self.driver.session() as session:
            # Create document node
            session.run(
                "MERGE (d:Document {document_id: $doc_id})",
                doc_id=document_id,
            )

            # Create entities
            for entity in entities:
                name = entity.get("name", "").strip()
                entity_type = entity.get("type", "UNKNOWN").strip().upper()
                if not name:
                    continue

                session.run(
                    """
                    MERGE (e:Entity {name: $name, type: $type})
                    ON CREATE SET e.created_at = datetime()
                    WITH e
                    MATCH (d:Document {document_id: $doc_id})
                    MERGE (e)-[:MENTIONED_IN]->(d)
                    """,
                    name=name,
                    type=entity_type,
                    doc_id=document_id,
                )
                entity_count += 1

            # Create relationships
            for rel in relationships:
                source = rel.get("source", "").strip()
                target = rel.get("target", "").strip()
                rel_type = rel.get("type", "RELATED_TO").strip().upper().replace(" ", "_")
                if not source or not target:
                    continue

                session.run(
                    f"""
                    MATCH (s:Entity {{name: $source}})
                    MATCH (t:Entity {{name: $target}})
                    MERGE (s)-[r:{rel_type}]->(t)
                    ON CREATE SET r.document_id = $doc_id, r.created_at = datetime()
                    """,
                    source=source,
                    target=target,
                    doc_id=document_id,
                )
                rel_count += 1

        return {"entities_created": entity_count, "relationships_created": rel_count}

    def get_entity_context(
        self,
        entity_names: List[str],
        max_depth: int = 2,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get graph context for given entities by traversing relationships.

        Args:
            entity_names: List of entity names to explore.
            max_depth: Maximum traversal depth.
            max_results: Maximum number of paths to return.

        Returns:
            List of relationship triples as dictionaries.
        """
        if not entity_names:
            return []

        with self.driver.session() as session:
            result = session.run(
                """
                UNWIND $names AS name
                MATCH (e:Entity)
                WHERE toLower(e.name) CONTAINS toLower(name)
                CALL apoc.path.subgraphAll(e, {maxLevel: $depth})
                YIELD relationships
                UNWIND relationships AS rel
                WITH startNode(rel) AS source, rel, endNode(rel) AS target
                WHERE source:Entity AND target:Entity
                RETURN DISTINCT
                    source.name AS source_name,
                    source.type AS source_type,
                    type(rel) AS relationship,
                    target.name AS target_name,
                    target.type AS target_type
                LIMIT $limit
                """,
                names=entity_names,
                depth=max_depth,
                limit=max_results,
            )
            return [dict(record) for record in result]

    def get_entity_context_simple(
        self,
        entity_names: List[str],
        max_depth: int = 2,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get graph context without APOC dependency (simpler traversal).

        Args:
            entity_names: List of entity names to explore.
            max_depth: Maximum traversal depth (1 or 2 supported).
            max_results: Maximum number of triples to return.

        Returns:
            List of relationship triples as dictionaries.
        """
        if not entity_names:
            return []

        depth_pattern = "-[r]-(b:Entity)" if max_depth == 1 else "-[r1]-(b:Entity)-[r2]-(c:Entity)"

        with self.driver.session() as session:
            if max_depth == 1:
                result = session.run(
                    """
                    UNWIND $names AS name
                    MATCH (a:Entity)-[r]-(b:Entity)
                    WHERE toLower(a.name) CONTAINS toLower(name)
                    RETURN DISTINCT
                        a.name AS source_name,
                        a.type AS source_type,
                        type(r) AS relationship,
                        b.name AS target_name,
                        b.type AS target_type
                    LIMIT $limit
                    """,
                    names=entity_names,
                    limit=max_results,
                )
            else:
                result = session.run(
                    """
                    UNWIND $names AS name
                    MATCH (a:Entity)-[r]-(b:Entity)
                    WHERE toLower(a.name) CONTAINS toLower(name)
                    WITH a, r, b
                    OPTIONAL MATCH (b)-[r2]-(c:Entity)
                    WHERE c <> a
                    WITH a, r, b, r2, c
                    RETURN DISTINCT
                        a.name AS source_name,
                        a.type AS source_type,
                        type(r) AS relationship,
                        b.name AS target_name,
                        b.type AS target_type
                    LIMIT $limit
                    """,
                    names=entity_names,
                    limit=max_results,
                )
            return [dict(record) for record in result]

    def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search entities by name with optional type filter.

        Args:
            query: Search query string.
            entity_type: Optional entity type filter.
            limit: Maximum number of results.

        Returns:
            List of matching entity dictionaries.
        """
        with self.driver.session() as session:
            if entity_type:
                result = session.run(
                    """
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($query)
                      AND e.type = $type
                    RETURN e.name AS name, e.type AS type,
                           size([(e)-[]-() | 1]) AS connection_count
                    ORDER BY connection_count DESC
                    LIMIT $limit
                    """,
                    query=query,
                    type=entity_type.upper(),
                    limit=limit,
                )
            else:
                result = session.run(
                    """
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($query)
                    RETURN e.name AS name, e.type AS type,
                           size([(e)-[]-() | 1]) AS connection_count
                    ORDER BY connection_count DESC
                    LIMIT $limit
                    """,
                    query=query,
                    limit=limit,
                )
            return [dict(record) for record in result]

    def get_document_entities(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all entities associated with a document.

        Args:
            document_id: Document ID.

        Returns:
            List of entity dictionaries.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity)-[:MENTIONED_IN]->(d:Document {document_id: $doc_id})
                RETURN e.name AS name, e.type AS type
                ORDER BY e.type, e.name
                """,
                doc_id=document_id,
            )
            return [dict(record) for record in result]

    def delete_document_data(self, document_id: str) -> Dict[str, int]:
        """Delete all graph data associated with a document.

        Args:
            document_id: Document ID to remove.

        Returns:
            Dictionary with count of deleted nodes and relationships.
        """
        with self.driver.session() as session:
            # Delete MENTIONED_IN relationships and orphan entities
            result = session.run(
                """
                MATCH (e:Entity)-[m:MENTIONED_IN]->(d:Document {document_id: $doc_id})
                DELETE m
                WITH e, d
                WHERE NOT (e)-[:MENTIONED_IN]->(:Document)
                DETACH DELETE e
                WITH d
                DETACH DELETE d
                """,
                doc_id=document_id,
            )
            summary = result.consume()
            return {
                "nodes_deleted": summary.counters.nodes_deleted,
                "relationships_deleted": summary.counters.relationships_deleted,
            }

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics.

        Returns:
            Dictionary with graph statistics.
        """
        with self.driver.session() as session:
            entity_count = session.run(
                "MATCH (e:Entity) RETURN count(e) AS count"
            ).single()["count"]

            rel_count = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS count"
            ).single()["count"]

            doc_count = session.run(
                "MATCH (d:Document) RETURN count(d) AS count"
            ).single()["count"]

            type_counts = session.run(
                """
                MATCH (e:Entity)
                RETURN e.type AS type, count(e) AS count
                ORDER BY count DESC
                """
            )
            entity_types = {record["type"]: record["count"] for record in type_counts}

        return {
            "total_entities": entity_count,
            "total_relationships": rel_count,
            "total_documents": doc_count,
            "entity_types": entity_types,
        }


# Global client instance
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get global Neo4j client instance.

    Returns:
        Singleton Neo4jClient.
    """
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client


def close_neo4j_client() -> None:
    """Close global Neo4j client connection."""
    global _neo4j_client
    if _neo4j_client is not None:
        _neo4j_client.close()
        _neo4j_client = None

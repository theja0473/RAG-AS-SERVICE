"""Knowledge graph router for entity and relationship management.

This module provides REST API endpoints for querying and managing
the knowledge graph used by Graph RAG.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from config import get_settings
from database.neo4j_client import get_neo4j_client

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])


class EntitySearchRequest(BaseModel):
    """Entity search request model."""
    query: str = Field(..., min_length=1, description="Search query")
    entity_type: Optional[str] = Field(default=None, description="Filter by entity type")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")


class EntityResponse(BaseModel):
    """Entity response model."""
    name: str
    type: str
    connection_count: int = 0


class RelationshipResponse(BaseModel):
    """Relationship response model."""
    source_name: str
    source_type: str
    relationship: str
    target_name: str
    target_type: str


class GraphContextRequest(BaseModel):
    """Graph context request model."""
    entity_names: List[str] = Field(..., min_length=1, description="Entity names to explore")
    max_depth: int = Field(default=2, ge=1, le=3, description="Traversal depth")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum results")


class GraphStatsResponse(BaseModel):
    """Graph statistics response model."""
    total_entities: int
    total_relationships: int
    total_documents: int
    entity_types: Dict[str, int]


@router.get("/stats", response_model=GraphStatsResponse)
async def get_graph_stats():
    """Get knowledge graph statistics."""
    settings = get_settings()
    if not settings.graph_rag_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Graph RAG is not enabled",
        )

    try:
        client = get_neo4j_client()
        stats = client.get_graph_stats()
        return GraphStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting graph stats: {str(e)}",
        )


@router.post("/search", response_model=List[EntityResponse])
async def search_entities(request: EntitySearchRequest):
    """Search entities in the knowledge graph."""
    settings = get_settings()
    if not settings.graph_rag_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Graph RAG is not enabled",
        )

    try:
        client = get_neo4j_client()
        results = client.search_entities(
            query=request.query,
            entity_type=request.entity_type,
            limit=request.limit,
        )
        return [EntityResponse(**r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching entities: {str(e)}",
        )


@router.post("/context", response_model=List[RelationshipResponse])
async def get_graph_context(request: GraphContextRequest):
    """Get graph context for given entities."""
    settings = get_settings()
    if not settings.graph_rag_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Graph RAG is not enabled",
        )

    try:
        client = get_neo4j_client()
        results = client.get_entity_context_simple(
            entity_names=request.entity_names,
            max_depth=request.max_depth,
            max_results=request.max_results,
        )
        return [RelationshipResponse(**r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting graph context: {str(e)}",
        )


@router.get("/documents/{document_id}/entities", response_model=List[EntityResponse])
async def get_document_entities(document_id: str):
    """Get entities associated with a document."""
    settings = get_settings()
    if not settings.graph_rag_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Graph RAG is not enabled",
        )

    try:
        client = get_neo4j_client()
        results = client.get_document_entities(document_id)
        return [EntityResponse(name=r["name"], type=r["type"], connection_count=0) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document entities: {str(e)}",
        )


@router.get("/health")
async def knowledge_graph_health():
    """Check Neo4j connectivity."""
    settings = get_settings()
    if not settings.graph_rag_enabled:
        return {"status": "disabled", "message": "Graph RAG is not enabled"}

    try:
        client = get_neo4j_client()
        connected = client.verify_connectivity()
        if connected:
            return {"status": "healthy", "message": "Connected to Neo4j"}
        return {"status": "unhealthy", "message": "Cannot connect to Neo4j"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

"""Settings router for configuration management.

This module provides REST API endpoints for managing application settings
and checking system health.
"""

from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from database import get_db
from database.models import Settings as SettingsModel, Document
from config import get_settings
from rag.generator import get_generator
from database.chromadb_client import get_chroma_client


router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingItem(BaseModel):
    """Setting item model."""
    key: str
    value: str
    updated_at: str = None


class SettingsResponse(BaseModel):
    """Settings response model."""
    settings: List[SettingItem]
    total: int


class SettingUpdateRequest(BaseModel):
    """Setting update request model."""
    key: str
    value: str


class HealthStatus(BaseModel):
    """Health status model."""
    status: str
    ollama_status: str
    chromadb_status: str
    database_status: str
    document_count: int
    details: Dict[str, Any] = None


@router.get("/", response_model=SettingsResponse)
async def get_settings_list(
    db: AsyncSession = Depends(get_db),
):
    """Get all application settings.

    Args:
        db: Database session.

    Returns:
        List of settings.
    """
    result = await db.execute(select(SettingsModel))
    settings = result.scalars().all()

    return SettingsResponse(
        settings=[SettingItem(**setting.to_dict()) for setting in settings],
        total=len(settings),
    )


@router.put("/", response_model=SettingItem, status_code=status.HTTP_200_OK)
async def update_setting(
    request: SettingUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update or create a setting.

    Args:
        request: Setting update request.
        db: Database session.

    Returns:
        Updated setting.
    """
    # Check if setting exists
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == request.key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        # Update existing setting
        setting.value = request.value
    else:
        # Create new setting
        setting = SettingsModel(
            key=request.key,
            value=request.value,
        )
        db.add(setting)

    await db.commit()
    await db.refresh(setting)

    return SettingItem(**setting.to_dict())


@router.get("/status", response_model=HealthStatus)
async def get_status(
    db: AsyncSession = Depends(get_db),
):
    """Get system health status.

    Args:
        db: Database session.

    Returns:
        System health status.
    """
    status_details = {
        "status": "healthy",
        "ollama_status": "unknown",
        "chromadb_status": "unknown",
        "database_status": "unknown",
        "document_count": 0,
        "details": {}
    }

    # Check Ollama
    try:
        generator = get_generator()
        ollama_result = generator.test_connection()
        if ollama_result["status"] == "success":
            status_details["ollama_status"] = "connected"
            status_details["details"]["ollama"] = {
                "model": ollama_result.get("model"),
                "message": ollama_result.get("message"),
            }
        else:
            status_details["ollama_status"] = "error"
            status_details["status"] = "degraded"
            status_details["details"]["ollama"] = {
                "error": ollama_result.get("message"),
            }
    except Exception as e:
        status_details["ollama_status"] = "error"
        status_details["status"] = "degraded"
        status_details["details"]["ollama"] = {"error": str(e)}

    # Check ChromaDB
    try:
        chroma_client = get_chroma_client()
        collections = chroma_client.list_collections()
        status_details["chromadb_status"] = "connected"
        status_details["details"]["chromadb"] = {
            "collections": collections,
        }
    except Exception as e:
        status_details["chromadb_status"] = "error"
        status_details["status"] = "degraded"
        status_details["details"]["chromadb"] = {"error": str(e)}

    # Check Database
    try:
        result = await db.execute(select(Document))
        documents = result.scalars().all()
        status_details["database_status"] = "connected"
        status_details["document_count"] = len(documents)
        status_details["details"]["database"] = {
            "document_count": len(documents),
        }
    except Exception as e:
        status_details["database_status"] = "error"
        status_details["status"] = "unhealthy"
        status_details["details"]["database"] = {"error": str(e)}

    return HealthStatus(**status_details)


@router.get("/config", response_model=Dict[str, Any])
async def get_config():
    """Get current configuration (non-sensitive values).

    Returns:
        Configuration dictionary.
    """
    settings = get_settings()

    return {
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "chroma_host": settings.chroma_host,
        "chroma_port": settings.chroma_port,
    }

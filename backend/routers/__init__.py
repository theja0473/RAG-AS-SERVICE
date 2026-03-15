"""Routers module for OpenAgentRAG backend."""

from .documents import router as documents_router
from .chat import router as chat_router
from .settings import router as settings_router
from .knowledge_graph import router as knowledge_graph_router

__all__ = [
    "documents_router",
    "chat_router",
    "settings_router",
    "knowledge_graph_router",
]

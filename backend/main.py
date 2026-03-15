"""FastAPI application entry point.

This module initializes the FastAPI application with CORS middleware,
routers, and lifecycle management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db, close_db
from database.neo4j_client import get_neo4j_client, close_neo4j_client
from routers import documents_router, chat_router, settings_router, knowledge_graph_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance.
    """
    # Startup
    print("Starting OpenAgentRAG backend...")

    # Initialize database
    await init_db()
    print("Database initialized")

    # Ensure required directories exist
    settings = get_settings()
    settings.ensure_upload_dir()
    settings.ensure_data_dir()
    print("Directories initialized")

    # Initialize Neo4j if Graph RAG is enabled
    if settings.graph_rag_enabled:
        try:
            neo4j_client = get_neo4j_client()
            if neo4j_client.verify_connectivity():
                neo4j_client.setup_indexes()
                print("Neo4j knowledge graph initialized")
            else:
                print("WARNING: Neo4j not available - Graph RAG features will be limited")
        except Exception as e:
            print(f"WARNING: Neo4j initialization failed: {e}")

    yield

    # Shutdown
    print("Shutting down OpenAgentRAG backend...")
    close_neo4j_client()
    await close_db()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="OpenAgentRAG API",
    description="Self-hostable agentic RAG platform backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(knowledge_graph_router)


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        Welcome message with API information.
    """
    return {
        "message": "OpenAgentRAG API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/settings/status",
    }


@app.get("/health")
async def health():
    """Health check endpoint.

    Returns:
        Health status.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )

"""FastAPI application entry point.

This module initializes the FastAPI application with CORS middleware,
routers, and lifecycle management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db, close_db
from routers import documents_router, chat_router, settings_router


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

    yield

    # Shutdown
    print("Shutting down OpenAgentRAG backend...")
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

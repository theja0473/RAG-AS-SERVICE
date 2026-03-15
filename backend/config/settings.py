"""Application settings and configuration management.

This module provides centralized configuration management using Pydantic Settings,
loading values from environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings.

    All settings are loaded from environment variables or .env file.
    Defaults are provided for local development.
    """

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://ollama:11434",
        description="Base URL for Ollama API"
    )
    llm_model: str = Field(
        default="llama3",
        description="LLM model name for Ollama"
    )

    # ChromaDB Configuration
    chroma_host: str = Field(
        default="chromadb",
        description="ChromaDB host"
    )
    chroma_port: int = Field(
        default=8000,
        description="ChromaDB port"
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )

    # Chunking Configuration
    chunk_size: int = Field(
        default=512,
        description="Maximum chunk size in characters"
    )
    chunk_overlap: int = Field(
        default=50,
        description="Overlap between chunks in characters"
    )

    # Neo4j Configuration
    neo4j_uri: str = Field(
        default="bolt://neo4j:7687",
        description="Neo4j connection URI"
    )
    neo4j_username: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: str = Field(
        default="openagentrag",
        description="Neo4j password"
    )
    graph_rag_enabled: bool = Field(
        default=True,
        description="Enable Graph RAG with knowledge graph"
    )

    # Database Configuration
    sqlite_url: str = Field(
        default="sqlite+aiosqlite:///./data/metadata.db",
        description="SQLite database URL"
    )

    # Upload Configuration
    upload_dir: str = Field(
        default="./data/uploads",
        description="Directory for uploaded files"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host"
    )
    api_port: int = Field(
        default=8000,
        description="API port"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def chroma_client_settings(self) -> dict:
        """Get ChromaDB client settings.

        Returns:
            Dictionary with ChromaDB client configuration.
        """
        return {
            "host": self.chroma_host,
            "port": self.chroma_port,
        }

    def ensure_upload_dir(self) -> Path:
        """Ensure upload directory exists.

        Returns:
            Path object for upload directory.
        """
        upload_path = Path(self.upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists.

        Returns:
            Path object for data directory.
        """
        data_path = Path("./data")
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Singleton Settings instance.
    """
    return Settings()

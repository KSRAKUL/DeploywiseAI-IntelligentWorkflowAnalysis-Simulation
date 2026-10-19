"""Deploywise AI — Application Configuration."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Deploywise AI"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./deploywise.db"

    # LLM
    llm_provider: str = "fake"  # "fake" | "ollama" | "gemini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    llm_timeout_seconds: int = 30
    llm_temperature: float = 0.1
    llm_max_retries: int = 1

    # Import limits
    max_import_size_bytes: int = 256 * 1024  # 256 KB
    max_stages: int = 100

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


settings = Settings()

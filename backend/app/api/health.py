"""Health check endpoint — includes real LLM and database status."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_session
from app.llm.factory import get_llm_provider

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health(db: AsyncSession = Depends(get_session)) -> dict:
    """Return backend, LLM provider, and database status. Never exposes credentials."""
    # LLM provider check
    llm_status = "unknown"
    llm_provider_name = settings.llm_provider
    try:
        provider = get_llm_provider()
        available = await provider.health_check()
        llm_status = "available" if available else "unavailable"
        llm_provider_name = provider.provider_name
    except Exception:
        llm_status = "unavailable"

    # Database check
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "llm": {
            "configured_provider": settings.llm_provider,
            "provider_name": llm_provider_name,
            "status": llm_status,
            "gemini_key_configured": bool(settings.gemini_api_key),
        },
        "database": db_status,
        "scanners": {
            "native_secret_scanner": "active",
            "native_dependency_scanner": "active",
            "native_docker_scanner": "active",
            "external_tools": "check /assessments for scanner execution status",
        },
    }

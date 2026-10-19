"""Pytest fixtures for Deploywise AI backend test suite."""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.schemas import WorkflowInput, Stage, StageType, Environment, ChangeType, BlastRadius, WorkflowMetadata
from app.db.models import Base
from app.db.session import get_session
from app.main import app


@pytest.fixture
def valid_workflow_dict() -> dict:
    return {
        "name": "Standard Delivery Pipeline",
        "schema_version": "1.0",
        "environment": "production",
        "change_type": "standard",
        "metadata": {
            "blast_radius": "low",
            "dependencies_changed": False,
        },
        "stages": [
            {
                "id": "build",
                "name": "Build Stage",
                "type": "build",
                "depends_on": [],
                "owner": "devops@company.com",
            },
            {
                "id": "unit_test",
                "name": "Unit Tests",
                "type": "unit_test",
                "depends_on": ["build"],
                "owner": "qa@company.com",
            },
            {
                "id": "sec_scan",
                "name": "Security Scan",
                "type": "security_scan",
                "depends_on": ["unit_test"],
                "owner": "security@company.com",
            },
            {
                "id": "staging_deploy",
                "name": "Deploy to Staging",
                "type": "staging_deploy",
                "depends_on": ["sec_scan"],
                "owner": "devops@company.com",
            },
            {
                "id": "staging_validation",
                "name": "Validate Staging",
                "type": "staging_validation",
                "depends_on": ["staging_deploy"],
                "owner": "qa@company.com",
            },
            {
                "id": "manual_approval",
                "name": "Release Approval",
                "type": "approval",
                "depends_on": ["staging_validation"],
                "owner": "lead@company.com",
            },
            {
                "id": "rollback",
                "name": "Rollback Plan",
                "type": "rollback_plan",
                "depends_on": ["manual_approval"],
                "owner": "devops@company.com",
            },
            {
                "id": "prod_deploy",
                "name": "Deploy to Production",
                "type": "deploy_production",
                "depends_on": ["rollback"],
                "owner": "devops@company.com",
            },
            {
                "id": "monitoring",
                "name": "Post-Deploy Monitoring",
                "type": "monitoring_check",
                "depends_on": ["prod_deploy"],
                "owner": "sre@company.com",
            },
        ],
    }


@pytest.fixture
def valid_workflow(valid_workflow_dict: dict) -> WorkflowInput:
    return WorkflowInput(**valid_workflow_dict)


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

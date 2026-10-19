"""Integration tests for Deploywise AI REST API endpoints (10+ tests)."""
from __future__ import annotations

import io
import json
import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "llm" in data
    assert data["llm"]["configured_provider"] == settings.llm_provider


@pytest.mark.asyncio
async def test_create_workflow_valid(client: AsyncClient, valid_workflow_dict: dict):
    response = await client.post("/workflows", json=valid_workflow_dict)
    assert response.status_code == 201
    data = response.json()
    assert "workflow_id" in data
    assert data["version_number"] == 1
    assert data["name"] == valid_workflow_dict["name"]


@pytest.mark.asyncio
async def test_import_workflow_file_size_limit(client: AsyncClient):
    # Oversized content > 256 KB
    oversized = b"a" * (settings.max_import_size_bytes + 100)
    files = {"file": ("oversized.json", io.BytesIO(oversized), "application/json")}
    response = await client.post("/workflows/import", files=files)
    assert response.status_code == 413
    data = response.json()
    assert data["detail"]["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_import_workflow_invalid_json(client: AsyncClient):
    bad_json = b"{not-valid-json"
    files = {"file": ("bad.json", io.BytesIO(bad_json), "application/json")}
    response = await client.post("/workflows/import", files=files)
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_JSON"


@pytest.mark.asyncio
async def test_list_and_get_workflow(client: AsyncClient, valid_workflow_dict: dict):
    create_res = await client.post("/workflows", json=valid_workflow_dict)
    wf_id = create_res.json()["workflow_id"]

    list_res = await client.get("/workflows")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(w["workflow_id"] == wf_id for w in items)

    get_res = await client.get(f"/workflows/{wf_id}")
    assert get_res.status_code == 200
    wf_data = get_res.json()
    assert wf_data["workflow_id"] == wf_id
    assert len(wf_data["versions"]) >= 1


@pytest.mark.asyncio
async def test_analyze_workflow(client: AsyncClient, valid_workflow_dict: dict):
    create_res = await client.post("/workflows", json=valid_workflow_dict)
    wf_id = create_res.json()["workflow_id"]

    analyze_res = await client.post(f"/workflows/{wf_id}/analyze")
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()
    assert "score" in analysis
    assert "verdict" in analysis
    assert "findings" in analysis
    assert "category_scores" in analysis

    get_analysis_res = await client.get(f"/workflows/{wf_id}/analysis")
    assert get_analysis_res.status_code == 200
    assert get_analysis_res.json()["analysis_id"] == analysis["analysis_id"]


@pytest.mark.asyncio
async def test_what_if_simulation_never_mutates_workflow(client: AsyncClient, valid_workflow_dict: dict):
    create_res = await client.post("/workflows", json=valid_workflow_dict)
    wf_id = create_res.json()["workflow_id"]

    # Trigger baseline analysis
    await client.post(f"/workflows/{wf_id}/analyze")

    # Run what-if simulation (e.g. remove a stage)
    what_if_payload = {
        "operations": [
            {
                "operation": "remove_stage",
                "stage_id": "unit_test",
            }
        ]
    }
    sim_res = await client.post(f"/workflows/{wf_id}/what-if", json=what_if_payload)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert "original_analysis" in sim_data
    assert "proposed_analysis" in sim_data
    assert "score_delta" in sim_data

    # Verify original workflow is unchanged in database
    get_wf = await client.get(f"/workflows/{wf_id}")
    assert len(get_wf.json()["versions"]) == 1


@pytest.mark.asyncio
async def test_record_reviewer_decision(client: AsyncClient, valid_workflow_dict: dict):
    create_res = await client.post("/workflows", json=valid_workflow_dict)
    wf_id = create_res.json()["workflow_id"]
    analyze_res = await client.post(f"/workflows/{wf_id}/analyze")
    analysis_id = analyze_res.json()["analysis_id"]

    decision_payload = {
        "decision_id": "dec-12345",
        "workflow_id": wf_id,
        "analysis_id": analysis_id,
        "choice": "approved",
        "notes": "Reviewed and verified safety gates",
        "actor": "lead-approver@company.com",
    }
    dec_res = await client.post(f"/workflows/{wf_id}/decision", json=decision_payload)
    assert dec_res.status_code == 201
    assert dec_res.json()["choice"] == "approved"


@pytest.mark.asyncio
async def test_reports_and_policy_endpoints(client: AsyncClient, valid_workflow_dict: dict):
    create_res = await client.post("/workflows", json=valid_workflow_dict)
    wf_id = create_res.json()["workflow_id"]
    analyze_res = await client.post(f"/workflows/{wf_id}/analyze")
    analysis_id = analyze_res.json()["analysis_id"]

    # Policy
    pol_res = await client.get("/policy")
    assert pol_res.status_code == 200
    assert "category_weights" in pol_res.json()

    # Report JSON
    rep_json = await client.get(f"/reports/{analysis_id}?format=json")
    assert rep_json.status_code == 200
    assert rep_json.json()["analysis_id"] == analysis_id

    # Report Markdown
    rep_md = await client.get(f"/reports/{analysis_id}?format=md")
    assert rep_md.status_code == 200
    assert "# Deploywise AI — Project Assessment Report" in rep_md.text


@pytest.mark.asyncio
async def test_audit_log_endpoint(client: AsyncClient):
    audit_res = await client.get("/audit")
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert "items" in data
    assert "page" in data

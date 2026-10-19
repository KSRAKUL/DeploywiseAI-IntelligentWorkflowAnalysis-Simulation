"""
Tests for Deploywise AI Project Ingestion, Scanners, Assessment Services, and PDF Export.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.ingestion.cicd_parser import parse_github_actions_yaml
from app.ingestion.zip_archive import SafeZipExtractor
from app.reporting.pdf_generator import generate_assessment_pdf
from app.scanners.native_dependencies import scan_dependencies
from app.scanners.native_docker import scan_dockerfiles
from app.scanners.native_secrets import scan_for_secrets


def test_parse_github_actions_yaml():
    """Verify parsing real GitHub Actions workflow with dependencies and classifications."""
    yaml_text = """
name: Production Deployment
on: [push]
jobs:
  unit-test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/
  security-scan:
    needs: unit-test
    runs-on: ubuntu-latest
    steps:
      - run: trivy fs .
  deploy:
    needs: security-scan
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: kubectl apply -f k8s/
"""
    wf = parse_github_actions_yaml(yaml_text)
    assert wf.name == "Production Deployment"
    assert len(wf.stages) == 3

    ids = [s.id for s in wf.stages]
    assert "unit-test" in ids
    assert "security-scan" in ids
    assert "deploy" in ids

    deploy_stage = next(s for s in wf.stages if s.id == "deploy")
    assert "security-scan" in deploy_stage.depends_on
    assert deploy_stage.type.value == "deploy_production"


def test_safe_zip_extractor_rejects_path_traversal(tmp_path: Path):
    """Verify that Zip-Slip path traversal attempts are caught and blocked."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:root")

    extractor = SafeZipExtractor()
    with pytest.raises(ValueError, match="Illegal path traversal"):
        extractor.extract(zip_buffer.getvalue(), base_dir=str(tmp_path))


def test_native_secret_scanner(tmp_path: Path):
    """Verify native scanner detects leaked credentials and redacts them in evidence."""
    leaked_file = tmp_path / "config.py"
    leaked_file.write_text("AWS_KEY = 'AKIA1234567890ABCDEF'\n", encoding="utf-8")

    findings = scan_for_secrets(tmp_path)
    assert len(findings) >= 1
    aws_finding = next(f for f in findings if "AWS" in f.title)
    assert aws_finding.blocking is True
    assert aws_finding.severity.value == "critical"
    assert "AKIA1234567890ABCDEF" not in aws_finding.evidence  # Redacted!
    assert "AKI...DEF" in aws_finding.evidence


def test_native_dependency_scanner(tmp_path: Path):
    """Verify detection of wildcard packages and missing lockfiles."""
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text('{"dependencies": {"express": "*"}}', encoding="utf-8")

    findings = scan_dependencies(tmp_path)
    rule_ids = [f.rule_id for f in findings]
    assert "DEP01" in rule_ids  # Missing lockfile
    assert "DEP02" in rule_ids  # Wildcard dependency


def test_native_docker_scanner(tmp_path: Path):
    """Verify detection of root execution and :latest tag in Dockerfile."""
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM python:latest\nRUN echo hello\n", encoding="utf-8")

    findings = scan_dockerfiles(tmp_path)
    rule_ids = [f.rule_id for f in findings]
    assert "DOC01" in rule_ids  # :latest tag
    assert "DOC03" in rule_ids  # Missing non-root USER


def test_pdf_report_generation():
    """Verify that generate_assessment_pdf creates a valid binary PDF with the correct magic bytes."""
    data = {
        "project_name": "Test App",
        "assessment_id": "test-id-1234",
        "risk_score": 45.0,
        "verdict": "NEEDS_REVIEW",
        "is_blocked": False,
        "coverage": {
            "coverage_percentage": 90.0,
            "executed_checks": 9,
            "total_checks": 10,
        },
        "findings": [],
        "scanner_results": [],
    }
    pdf_bytes = generate_assessment_pdf(data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")  # Valid PDF magic bytes!


@pytest.mark.asyncio
async def test_assessments_cicd_api(client: AsyncClient):
    """Verify POST /assessments/cicd parses workflow and runs full assessment."""
    yaml_payload = """
name: Microservice Delivery
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: deploy.sh
"""
    res = await client.post(
        "/assessments/cicd",
        json={"content": yaml_payload, "filename_hint": "deploy.yml"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "assessment_id" in data
    assert data["project_name"] == "Microservice Delivery"
    assert "risk_score" in data
    assert "coverage" in data
    assert "scanner_results" in data
    assert len(data["findings"]) > 0


@pytest.mark.asyncio
async def test_download_pdf_report_endpoint(client: AsyncClient, valid_workflow_dict: dict):
    """Verify GET /reports/{analysis_id}/pdf endpoint downloads valid PDF."""
    wf_res = await client.post("/workflows", json=valid_workflow_dict)
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["workflow_id"]

    analyze_res = await client.post(f"/workflows/{wf_id}/analyze")
    analysis_id = analyze_res.json()["analysis_id"]

    pdf_res = await client.get(f"/reports/{analysis_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_get_assessment_endpoints(client: AsyncClient, valid_workflow_dict: dict):
    """Verify GET /assessments list and GET /assessments/{id} retrieve persisted assessment records."""
    wf_res = await client.post("/workflows", json=valid_workflow_dict)
    assert wf_res.status_code == 201
    wf_id = wf_res.json()["workflow_id"]

    analyze_res = await client.post(f"/workflows/{wf_id}/analyze")
    assert analyze_res.status_code == 200
    analysis_id = analyze_res.json()["analysis_id"]

    # Test list assessments
    list_res = await client.get("/assessments")
    assert list_res.status_code == 200
    assessments = list_res.json()
    assert isinstance(assessments, list)
    assert any(a["assessment_id"] == analysis_id for a in assessments)

    # Test get single assessment
    get_res = await client.get(f"/assessments/{analysis_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["assessment_id"] == analysis_id
    assert "findings" in detail
    assert "risk_score" in detail
    assert "verdict" in detail

    # Test get assessment by workflow
    by_wf_res = await client.get(f"/assessments/by-workflow/{wf_id}")
    assert by_wf_res.status_code == 200
    assert by_wf_res.json()["assessment_id"] == analysis_id


def test_developer_encouragement_engine():
    """Verify DeveloperEncouragementService selects outcome-aligned messaging."""
    from app.core.schemas import Verdict
    from app.services.encouragement import DeveloperEncouragementService

    # 1. Blocked state
    enc_blocked = DeveloperEncouragementService.generate(
        verdict=Verdict.BLOCKED,
        is_blocked=True,
        blocking_count=2,
        findings_count=4,
        coverage_pct=100.0,
    )
    assert enc_blocked.status_level == "blocked"
    assert "2 mandatory release blockers" in enc_blocked.message
    assert "Clear Path to Production Readiness" in enc_blocked.headline

    # 2. Healthy state
    enc_healthy = DeveloperEncouragementService.generate(
        verdict=Verdict.PASS,
        is_blocked=False,
        blocking_count=0,
        findings_count=0,
        coverage_pct=100.0,
    )
    assert enc_healthy.status_level == "healthy"
    assert "Great work" in enc_healthy.message

    # 3. Partial evidence
    enc_partial = DeveloperEncouragementService.generate(
        verdict=Verdict.PASS,
        is_blocked=False,
        blocking_count=0,
        findings_count=0,
        coverage_pct=25.0,
        is_diagram_only=True,
    )
    assert enc_partial.status_level == "partial_evidence"
    assert "Promising Baseline" in enc_partial.headline


def test_workflow_diagram_generator():
    """Verify generation of both existing and recommended Mermaid diagrams with diff comparison."""
    from app.core.schemas import Environment, ChangeType, Stage, StageType, WorkflowInput, WorkflowMetadata
    from app.services.diagram_generator import WorkflowDiagramGenerator

    wf = WorkflowInput(
        name="Minimal Delivery Pipeline",
        schema_version="1.0",
        environment=Environment.PRODUCTION,
        change_type=ChangeType.STANDARD,
        stages=[
            Stage(id="build", name="Build Application", type=StageType.BUILD, owner="ci", depends_on=[]),
            Stage(id="deploy", name="Deploy to Prod", type=StageType.DEPLOY_PRODUCTION, owner="ops", depends_on=["build"]),
        ],
        metadata=WorkflowMetadata(blast_radius="high", dependencies_changed=False),
    )

    existing_diag, rec_diag, diff = WorkflowDiagramGenerator.generate_both(wf, [])

    # Existing diagram checks
    assert "graph LR" in existing_diag.mermaid_code
    assert "build" in existing_diag.mermaid_code
    assert "deploy" in existing_diag.mermaid_code
    assert len(existing_diag.nodes) == 2

    # Recommended diagram checks
    assert "graph LR" in rec_diag.mermaid_code
    assert len(diff) > 0  # Missing automated tests, security scan, approval, etc.
    assert any("Test" in d.title for d in diff)
    assert any("Security" in d.title for d in diff)
    assert len(rec_diag.nodes) > len(existing_diag.nodes)


def test_diagram_parser_svg():
    """Verify DiagramWorkflowParser extracts pipeline stages from SVG text nodes."""
    from app.ingestion.diagram_parser import DiagramWorkflowParser

    svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
      <text x="10" y="20">Source Build Stage</text>
      <text x="10" y="50">Automated Unit Test</text>
      <text x="10" y="80">Security Scan Snyk</text>
      <text x="10" y="110">Deploy to Production</text>
    </svg>"""

    parser = DiagramWorkflowParser()
    wf, facts, inferred, unknowns, boundaries = parser.parse_image_or_document(
        svg_content.encode("utf-8"),
        filename="pipeline_architecture.svg",
    )

    assert len(wf.stages) >= 3
    stage_ids = [s.id for s in wf.stages]
    assert "build" in stage_ids
    assert "test" in stage_ids
    assert len(facts) > 0
    assert len(boundaries) > 0


@pytest.mark.asyncio
async def test_assess_diagram_api_svg(client: AsyncClient):
    """Verify POST /assessments/diagram returns diagrams, diff, and developer guidance."""
    svg_bytes = b"""<svg xmlns="http://www.w3.org/2000/svg">
      <text x="10" y="20">Compile and Build</text>
      <text x="10" y="50">Run Pytest</text>
      <text x="10" y="80">Trivy Security Scan</text>
      <text x="10" y="110">Production Rollout</text>
    </svg>"""

    res = await client.post(
        "/assessments/diagram",
        files={"file": ("architecture.svg", svg_bytes, "image/svg+xml")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "assessment_id" in data
    assert "existing_workflow_diagram" in data
    assert "recommended_workflow_diagram" in data
    assert "diagram_comparison" in data
    assert "developer_encouragement" in data
    assert data["existing_workflow_diagram"]["mermaid_code"].startswith("graph LR")
    assert data["recommended_workflow_diagram"]["mermaid_code"].startswith("graph LR")
    assert len(data["diagram_comparison"]) > 0
    assert "headline" in data["developer_encouragement"]



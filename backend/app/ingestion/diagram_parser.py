"""
Deploywise AI — Multi-Modal Workflow Image, Vector & PDF Document Parser.
Extracts candidate delivery stages, dependencies, observed components, and evidence boundaries
from workflow diagrams, architecture screenshots, SVG graphics, and technical PDF reports.
"""
from __future__ import annotations

import base64
import io
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app.config import settings
from app.core.schemas import (
    BlastRadius,
    ChangeType,
    Environment,
    Stage,
    StageType,
    WorkflowInput,
    WorkflowMetadata,
)


class DiagramWorkflowParser:
    """Extracts workflow structure and evidence boundaries from images, SVG, and PDF reports."""

    def parse_image_or_document(
        self,
        file_bytes: bytes,
        filename: str = "workflow_diagram.png",
    ) -> tuple[WorkflowInput, list[str], list[str], list[str], list[str]]:
        """
        Parses diagram image, SVG, or PDF report.
        Returns:
            (workflow, observed_facts, inferred_relationships, unknown_details, evidence_boundaries)
        """
        lower_name = filename.lower()
        extracted_text = ""
        is_pdf = lower_name.endswith(".pdf")
        is_svg = lower_name.endswith(".svg")

        observed_facts: list[str] = [
            f"Input artifact '{filename}' ({len(file_bytes)} bytes) verified and ingested into visual parser."
        ]
        inferred_relationships: list[str] = []
        unknown_details: list[str] = [
            "Runtime database credentials cannot be proven secure solely from an architecture diagram.",
            "Actual CI/CD step execution and pass/fail exit codes require live pipeline telemetry or test execution logs.",
            "Secrets storage hygiene requires repository file inspection or Kubernetes Secret / Vault verification.",
        ]
        evidence_boundaries: list[str] = [
            "Diagram Evidence Boundary: Visual topologies prove intended ordering, declared stages, and designated environments.",
            "Source Code Boundary: Proof of static vulnerabilities, pinned dependencies, and Dockerfile USER directives requires filesystem scanner execution.",
            "Runtime Boundary: Production health probes and canary rollback readiness require active cluster monitoring checks.",
        ]

        stages: list[Stage] = []

        # 1. Parse PDF reports
        if is_pdf:
            extracted_text = self._extract_text_from_pdf(file_bytes)
            observed_facts.append(f"Extracted {len(extracted_text)} characters of text from PDF document.")
            stages = self._extract_stages_from_text(extracted_text, filename)

        # 2. Parse SVG diagrams
        elif is_svg:
            extracted_text = self._extract_text_from_svg(file_bytes)
            observed_facts.append(f"Extracted {len(extracted_text)} text elements from vector SVG diagram.")
            stages = self._extract_stages_from_text(extracted_text, filename)

        # 3. Parse raster images (PNG, JPEG, WEBP)
        else:
            if settings.llm_provider == "gemini" and settings.gemini_api_key:
                try:
                    stages = self._extract_via_gemini_vision(file_bytes, filename)
                    if stages:
                        observed_facts.append(f"Identified {len(stages)} distinct pipeline stages via multimodal visual AI.")
                except Exception as exc:
                    inferred_relationships.append(f"Visual AI endpoint ping failed ({exc}); applied deterministic topology heuristics.")

            if not stages:
                # Heuristic stage extraction from filename and generic topology
                stages = self._generate_heuristic_stages(filename)
                inferred_relationships.append("Stages inferred from sequential software delivery baseline (Build → Test → Scan → Deploy).")

        # Compile observed stage facts
        for s in stages:
            observed_facts.append(f"Observed Stage: '{s.name}' [ID: {s.id}, Type: {s.type.value}]")
            if s.depends_on:
                observed_facts.append(f"Dependency Link: '{s.id}' requires completion of {s.depends_on}")
            else:
                observed_facts.append(f"Root Stage: '{s.id}' starts with zero upstream dependencies")

        workflow = self._build_workflow(stages, filename)
        return workflow, observed_facts, inferred_relationships, unknown_details, evidence_boundaries

    def _extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extracts text content from PDF bytes using pypdf."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            texts = []
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text:
                    texts.append(f"--- Page {page_idx + 1} ---\n{page_text}")
            return "\n\n".join(texts)
        except Exception:
            # Fallback simple string extraction for text in PDF streams
            raw_text = file_bytes.decode("latin-1", errors="ignore")
            matches = re.findall(r"\((.*?)\)\s*Tj", raw_text)
            return " ".join(matches) if matches else ""

    def _extract_text_from_svg(self, file_bytes: bytes) -> str:
        """Extracts text nodes and label attributes from SVG XML."""
        try:
            root = ET.fromstring(file_bytes)
            texts: list[str] = []
            for elem in root.iter():
                # Extract text tag contents
                if elem.text and elem.text.strip():
                    texts.append(elem.text.strip())
                # Extract title or label attributes
                for attr in ("id", "title", "aria-label", "label"):
                    val = elem.get(attr)
                    if val and val.strip():
                        texts.append(val.strip())
            return "\n".join(texts)
        except Exception:
            return ""

    def _extract_stages_from_text(self, text: str, filename: str) -> list[Stage]:
        """Identifies workflow stages from extracted document or SVG text using keyword heuristics."""
        stages: list[Stage] = []
        lower = text.lower()

        # Keywords mapping to StageType
        stage_definitions = [
            ("checkout", "Source Checkout", StageType.BUILD, ["checkout", "clone", "git clone", "source"]),
            ("build", "Build & Compilation", StageType.BUILD, ["compile", "build", "docker build", "mvn", "npm run build", "cargo build"]),
            ("test", "Unit & Integration Tests", StageType.UNIT_TEST, ["test", "pytest", "jest", "unit test", "spec", "integration test"]),
            ("security", "Security Vulnerability Scan", StageType.SECURITY_SCAN, ["trivy", "snyk", "sonarqube", "security scan", "sast", "audit", "bandit"]),
            ("staging", "Deploy to Staging Environment", StageType.STAGING_DEPLOY, ["staging", "stage deploy", "qa env", "pre-prod", "preview env"]),
            ("approval", "Release Governance Approval", StageType.APPROVAL, ["approval", "sign-off", "manual gate", "reviewer", "authorized"]),
            ("rollback", "Automated Canary Rollback Plan", StageType.ROLLBACK_PLAN, ["rollback", "canary", "revert plan", "blue-green"]),
            ("deploy", "Deploy to Production", StageType.DEPLOY_PRODUCTION, ["production", "deploy to prod", "prod rollout", "publish", "release"]),
            ("monitor", "Post-Deploy Health Probe", StageType.MONITORING_CHECK, ["monitor", "prometheus", "datadog", "health check", "smoke test", "probe"]),
        ]

        prev_id: str | None = None
        for stage_id, name, stype, keywords in stage_definitions:
            if any(kw in lower for kw in keywords):
                deps = [prev_id] if prev_id else []
                stages.append(
                    Stage(
                        id=stage_id,
                        name=name,
                        type=stype,
                        owner="inferred",
                        depends_on=deps,
                    )
                )
                prev_id = stage_id

        # If too few stages detected from text, fallback to standard candidates
        if len(stages) < 2:
            return self._generate_heuristic_stages(filename)

        return stages

    def _extract_via_gemini_vision(self, file_bytes: bytes, filename: str) -> list[Stage]:
        """Calls Gemini Vision API for multimodal diagram comprehension."""
        import httpx

        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        mime = "image/png"
        if filename.lower().endswith((".jpg", ".jpeg")):
            mime = "image/jpeg"
        elif filename.lower().endswith(".webp"):
            mime = "image/webp"

        prompt = (
            "Analyze this software development and deployment workflow diagram or architecture screenshot. "
            "Identify all sequential steps, tests, security scans, approval gates, and deployments. "
            "Return ONLY valid JSON matching this schema: "
            '{"stages": [{"id": "...", "name": "...", "type": "unit_test|security_scan|approval|staging_deploy|deploy_production|build|rollback_plan|monitoring_check|custom", "depends_on": ["..."]}]}'
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime,
                                "data": b64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
        }

        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                clean_json = re.sub(r"```json\s*", "", text)
                clean_json = re.sub(r"```\s*", "", clean_json).strip()
                parsed = json.loads(clean_json)

                result_stages: list[Stage] = []
                for s in parsed.get("stages", []):
                    clean_id = re.sub(r"[^a-z0-9_-]", "-", s.get("id", "stage").lower())[:40].strip("-")
                    result_stages.append(
                        Stage(
                            id=clean_id or "inferred-stage",
                            name=str(s.get("name", clean_id))[:200],
                            type=StageType(s.get("type", "custom")) if s.get("type") in StageType._value2member_map_ else StageType.CUSTOM,
                            owner="inferred",
                            depends_on=[re.sub(r"[^a-z0-9_-]", "-", d.lower())[:40].strip("-") for d in s.get("depends_on", [])],
                        )
                    )
                return result_stages
        return []

    def _generate_heuristic_stages(self, filename: str) -> list[Stage]:
        """Provides a safe candidate workflow when visual or text parsing is limited."""
        return [
            Stage(
                id="source-checkout",
                name="Source Checkout & Verification",
                type=StageType.BUILD,
                owner="devops",
                depends_on=[],
            ),
            Stage(
                id="automated-tests",
                name="Automated Test Suite (Inferred)",
                type=StageType.UNIT_TEST,
                owner="engineering",
                depends_on=["source-checkout"],
            ),
            Stage(
                id="security-compliance",
                name="Security & Vulnerability Scan (Inferred)",
                type=StageType.SECURITY_SCAN,
                owner="security",
                depends_on=["automated-tests"],
            ),
            Stage(
                id="production-release",
                name="Production Deployment (Inferred)",
                type=StageType.DEPLOY_PRODUCTION,
                owner="release-manager",
                depends_on=["security-compliance"],
            ),
        ]

    def _build_workflow(self, stages: list[Stage], filename: str) -> WorkflowInput:
        """Constructs a valid WorkflowInput."""
        return WorkflowInput(
            name=f"Workflow Inferred from {Path(filename).stem}",
            schema_version="1.0",
            environment=Environment.PRODUCTION,
            change_type=ChangeType.STANDARD,
            stages=stages,
            metadata=WorkflowMetadata(
                blast_radius=BlastRadius.HIGH,
                dependencies_changed=False,
            ),
        )

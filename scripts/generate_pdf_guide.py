"""
Generate a complete, high-quality PDF documentation for Deploywise AI
covering Project Workflow, Architecture Structure, Sample Testing Guide,
and Real-World Supported Projects.
"""
from __future__ import annotations

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

# Palette matching Deploywise AI Design Tokens
COLOR_PRIMARY = colors.HexColor("#172033")
COLOR_ACCENT = colors.HexColor("#315A8C")
COLOR_SECONDARY = colors.HexColor("#5E6878")
COLOR_BG = colors.HexColor("#F6F8FB")
COLOR_BORDER = colors.HexColor("#E2E7EF")
COLOR_CRITICAL = colors.HexColor("#B42318")
COLOR_HIGH = colors.HexColor("#C2410C")
COLOR_MEDIUM = colors.HexColor("#A16207")
COLOR_LOW = colors.HexColor("#28704A")
COLOR_LIGHT_ACCENT = colors.HexColor("#EBF2F9")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page numbers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica", 8)
            self.setFillColor(COLOR_SECONDARY)
            self.drawString(54, 11 * inch - 36, "Deploywise AI — Workflow & Architecture Guide")
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

            # Footer
            self.line(54, 46, 8.5 * inch - 54, 46)
            self.drawString(54, 34, "CONFIDENTIAL & PROPRIETARY — GOVERNANCE PLATFORM")
            page_text = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(8.5 * inch - 54, 34, page_text)
        self.restoreState()


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=34,
        textColor=COLOR_PRIMARY,
        alignment=0,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=14,
        leading=18,
        textColor=COLOR_ACCENT,
        alignment=0,
    )

    h1_style = ParagraphStyle(
        "Heading1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=COLOR_PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=COLOR_ACCENT,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=COLOR_PRIMARY,
        spaceAfter=6,
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=COLOR_PRIMARY,
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=14,
        textColor=COLOR_ACCENT,
    )

    elements = []

    # -------------------------------------------------------------
    # COVER / HEADER SECTION
    # -------------------------------------------------------------
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("DEPLOYWISE AI", title_style))
    elements.append(Paragraph("Predictive Workflow Risk Detection & Prevention Copilot", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_ACCENT, spaceAfter=14))
    elements.append(
        Paragraph(
            "<b>Technical Architecture, Operating Workflow, and Testing Guide</b><br/>"
            "<i>Version 1.0 • Baseline Contracts: contracts-v1 • Golden Rule Enforced</i>",
            body_style,
        )
    )
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY & THE GOLDEN RULE
    # -------------------------------------------------------------
    elements.append(Paragraph("1. Executive Summary & The Golden Rule", h1_style))
    elements.append(
        Paragraph(
            "Deploywise AI is an automated governance copilot that evaluates software delivery, "
            "CI/CD, and operational deployment workflows <b>before they execute</b>. It detects missing controls "
            "(tests, security scans, approvals, rollback plans, monitoring) and risky dependency paths, "
            "calculates an explainable risk score, and provides speculative <b>What-If</b> simulations to "
            "allow engineering teams to test fixes before production release.",
            body_style,
        )
    )

    # Golden Rule Callout Box
    golden_box_data = [
        [
            Paragraph(
                "<b>THE GOLDEN RULE OF DEPLOYWISE AI:</b><br/>"
                "• <b>Deterministic Code Decides:</b> Pure Python deterministic rules decide the risk score, "
                "category penalties, and blocking verdicts.<br/>"
                "• <b>AI Reviewers are Advisory:</b> Specialist AI reviewers (QA, Security, Operations, Dependency) "
                "provide labelled, contextual advice only.<br/>"
                "• <b>Zero Hallucination Risk:</b> No AI agent can modify rule findings, severity, score, or blocking verdicts.",
                callout_style,
            )
        ]
    ]
    t_golden = Table(golden_box_data, colWidths=[500])
    t_golden.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_ACCENT),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_ACCENT),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    elements.append(t_golden)
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # SECTION 2: ARCHITECTURE & SYSTEM TOPOLOGY
    # -------------------------------------------------------------
    elements.append(Paragraph("2. System Architecture & Topology", h1_style))
    elements.append(
        Paragraph(
            "Deploywise AI is split into decoupled layers enforcing clean separation of concerns:",
            body_style,
        )
    )

    arch_table_data = [
        ["Layer", "Technology", "Role & Guarantees"],
        [
            "Frontend Console",
            "React 18 / TypeScript / Vite",
            "Enterprise light-theme UI. Provides DAG canvas, What-If console, finding drawer, and audit reports.",
        ],
        [
            "Transport API",
            "FastAPI / Pydantic v2",
            "Stateless routers. Enforces 256KB import limit, JSON schema validation, and structured error responses.",
        ],
        [
            "DAG Graph Engine",
            "NetworkX (DiGraph)",
            "Reachability and cycle analysis. Validates paths to production without exponential path enumeration.",
        ],
        [
            "Rule Engine",
            "Pure Python Classes",
            "10 versioned deterministic rules (R01-R10). Zero external network calls or random state.",
        ],
        [
            "Scoring Engine",
            "Policy Matrix (YAML)",
            "Weighted sum over 5 categories. Capped at 100 with banker's rounding round().",
        ],
        [
            "AI Reviewers",
            "Google Gemini 1.5 Flash",
            "Specialist advisory reviewers (Security, QA, Ops, Dependency). Strict schema isolation.",
        ],
        [
            "Persistence",
            "SQLite / SQLAlchemy Async",
            "Immutable workflow snapshots and append-only audit trail.",
        ],
    ]

    t_arch = Table(arch_table_data, colWidths=[110, 130, 260])
    t_arch.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(t_arch)
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # SECTION 3: THE 10 DETERMINISTIC RULES CATALOG
    # -------------------------------------------------------------
    elements.append(Paragraph("3. Deterministic Rules Catalog (R01–R10)", h1_style))
    elements.append(
        Paragraph(
            "Every workflow path reaching production must satisfy the following 10 safety controls:",
            body_style,
        )
    )

    rules_table_data = [
        ["ID", "Rule Name", "Category", "Severity", "Blocker?", "Enforced Condition"],
        ["R01", "Missing Tests", "Testing", "High", "No", "Must have unit_test or integration_test before prod."],
        ["R02", "Missing Security Scan", "Security", "Critical", "YES", "Every path to production must have security_scan."],
        ["R03", "Missing Approval Gate", "Governance", "Critical", "YES", "Manual approval gate must precede production deploy."],
        ["R04", "No Rollback Plan", "Recovery", "High / Crit", "No", "rollback_plan stage must exist (Crit if high blast radius)."],
        ["R05", "Unowned Stage", "Governance", "Medium / High", "No", "Every stage must have owner (High if deploy stage)."],
        ["R06", "Invalid Stage Order", "Dependency", "High", "No", "Approval and tests must not occur after production deploy."],
        ["R07", "Missing Monitoring", "Recovery", "Medium", "No", "monitoring_check must be reachable from production deploy."],
        ["R08", "Unverified Dependency", "Dependency", "High", "No", "dependency_check required if dependencies_changed=true."],
        ["R09", "Tests Bypassable", "Testing", "High", "No", "Tests cannot have continue_on_failure or skippable flags."],
        ["R10", "No Staging Validation", "Testing", "Medium", "No", "Must have staging_deploy and staging_validation before prod."],
    ]

    t_rules = Table(rules_table_data, colWidths=[35, 120, 65, 65, 45, 170])
    t_rules.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
                ("TEXTCOLOR", (4, 2), (4, 3), COLOR_CRITICAL),
                ("FONTNAME", (4, 2), (4, 3), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_rules)
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # SECTION 4: WHAT-IF SPECULATIVE SIMULATION
    # -------------------------------------------------------------
    elements.append(Paragraph("4. In-Memory What-If Speculative Simulation", h1_style))
    elements.append(
        Paragraph(
            "<b>How What-If Works:</b> The What-If simulation engine takes the original workflow DAG and applies "
            "a set of proposed operations (such as adding a missing security scan, connecting an approval gate, "
            "or removing a skippable flag) <b>strictly in-memory</b>.<br/>"
            "• The saved workflow in the database is <b>never mutated</b>.<br/>"
            "• The system recalculates the graph reachability and runs all deterministic rules.<br/>"
            "• A diff is generated comparing baseline score vs simulated score, verdict change, and exact resolved blockers.",
            body_style,
        )
    )

    elements.append(PageBreak())

    # -------------------------------------------------------------
    # SECTION 5: COMPLETE REPOSITORY CODE STRUCTURE
    # -------------------------------------------------------------
    elements.append(Paragraph("5. Complete Project File & Directory Structure", h1_style))
    elements.append(
        Paragraph(
            "The repository is organized following clean hexagonal architecture principles:",
            body_style,
        )
    )

    tree_text = """
deploywise-ai/
├── CLAUDE.md                   # Master engineering rules & frozen contract tag
├── README.md                   # Project overview & quickstart guide
├── docker-compose.yml          # Containerized orchestration
├── .env / .env.example         # Multi-provider config & Gemini API key
│
├── backend/
│   ├── pyproject.toml          # FastAPI, SQLAlchemy, NetworkX, Pydantic v2
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint, CORS, lifespan & error handlers
│   │   ├── config.py           # Typed pydantic-settings configuration
│   │   ├── api/                # HTTP transport routers (workflows, reports, audit, health)
│   │   ├── core/
│   │   │   ├── schemas.py      # Frozen Pydantic data contracts (contracts-v1)
│   │   │   ├── graph.py        # NetworkX DAG reachability & cycle detection
│   │   │   ├── scoring.py      # Frozen policy scoring engine & banker's round()
│   │   │   ├── policy.py       # YAML policy loader (default_policy_v1.yaml)
│   │   │   └── rules/          # R01-R10 pure Python deterministic rules & registry
│   │   ├── agents/             # Specialist reviewers (Security, QA, Ops, Dependency)
│   │   ├── llm/                # Adapters: FakeLLM, OllamaLLM, GeminiLLM
│   │   ├── services/           # Analysis orchestrator & What-If simulation service
│   │   └── db/                 # Async SQLAlchemy models (Analysis, Finding, Audit)
│   └── tests/                  # 57 passing tests (rules, scoring, validators, API)
│
├── frontend/
│   ├── package.json            # React 18, Vite, Lucide-react
│   ├── vite.config.ts          # Vite build with backend reverse proxy
│   └── src/
│       ├── App.tsx             # Main router & embedded 1-click sample workflow runner
│       ├── index.css           # Calm enterprise light-theme CSS tokens
│       ├── types/index.ts      # TypeScript definitions matching backend contracts
│       ├── lib/api.ts          # Typed REST API client
│       ├── components/         # AppShell, GraphCanvas DAG, RiskScoreGauge, FindingDrawer
│       └── views/              # Overview, Workflows, Builder, Analysis, WhatIf, Reports, Audit
│
├── data/
│   ├── policies/               # default_policy_v1.yaml (weights: Sec 25%, Test 25%, etc.)
│   └── sample_workflows/       # 6 pre-configured test scenarios
└── docs/                       # ARCHITECTURE.md, DECISIONS.md, DEMO_SCRIPT.md
"""
    elements.append(
        Table(
            [[Paragraph(f"<pre>{tree_text.strip()}</pre>", code_style)]],
            colWidths=[500],
            style=[
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 8),
            ],
        )
    )
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # SECTION 6: HOW TO TEST WITH SAMPLE WORKFLOWS
    # -------------------------------------------------------------
    elements.append(Paragraph("6. How to Test the Project with Sample Workflows", h1_style))
    elements.append(
        Paragraph(
            "Deploywise AI includes 6 pre-built test scenarios located in <code>data/sample_workflows/</code>. "
            "You can test them directly through the browser UI or programmatically via the API:",
            body_style,
        )
    )

    samples_data = [
        ["Sample File", "Target Scenario Tested", "Expected Violations & Result"],
        [
            "01_bad_release.json",
            "Pipeline with missing test, security scan, approval, and rollback stages.",
            "Score: ~49. Verdict: BLOCKED. Triggers R01, R02 (Blocker), R03 (Blocker), R04, R05, R07, R10.",
        ],
        [
            "02_improved_release.json",
            "Full enterprise pipeline with all 10 controls present in correct DAG order.",
            "Score: 0. Verdict: PASS. Clean baseline. All safety gates passed.",
        ],
        [
            "03_missing_owner.json",
            "Production deploy stage has owner=null / blank.",
            "Triggers R05 Unowned Stage with escalated High severity.",
        ],
        [
            "04_skip_tests_on_fail.json",
            "Unit test stage configured with continue_on_failure: true.",
            "Triggers R09 Tests Bypassable / Skippable.",
        ],
        [
            "05_dependency_change.json",
            "Workflow declares dependencies_changed: true without dependency_check.",
            "Triggers R08 Unverified Dependency Change.",
        ],
        [
            "malicious_oversized.json",
            "Oversized payload exceeding the 256 KB safety limit.",
            "HTTP 413 Payload Too Large returned safely before JSON parsing.",
        ],
    ]

    t_samples = Table(samples_data, colWidths=[130, 160, 210])
    t_samples.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_samples)
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # SECTION 7: WHAT REAL-WORLD PROJECTS CAN BE AUDITED
    # -------------------------------------------------------------
    elements.append(Paragraph("7. What Projects Can You Audit with Deploywise AI?", h1_style))
    elements.append(
        Paragraph(
            "Deploywise AI is designed as a universal release governance engine. It can audit any pipeline or "
            "workflow represented by stages and dependencies across diverse software engineering stacks:",
            body_style,
        )
    )

    projects_data = [
        ["Project Domain", "Real-World Pipeline Type", "Key Risks Detected by Deploywise AI"],
        [
            "Cloud Microservices",
            "Kubernetes / Docker release pipelines across backend services.",
            "Detects missing container security scans, missing staging smoke tests, and unowned deploy jobs.",
        ],
        [
            "Web Applications",
            "Next.js, React, Node.js frontend and API delivery workflows.",
            "Catches bypassable unit tests (continue_on_failure: true) and unverified npm dependency updates.",
        ],
        [
            "Fintech & Banking",
            "High-compliance payment gateways and core banking releases.",
            "Enforces mandatory dual-control human approval gates (R03) and automated rollback plans (R04).",
        ],
        [
            "Data & MLOps",
            "Model deployment & data engineering pipelines (Airflow, Kubeflow).",
            "Validates pre-deploy data validation stages and post-deployment model drift monitoring.",
        ],
        [
            "Mobile App Delivery",
            "iOS TestFlight & Android Play Store automated release tracks.",
            "Ensures integration test suites run prior to production tracks and ownership is documented.",
        ],
    ]

    t_proj = Table(projects_data, colWidths=[100, 150, 250])
    t_proj.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_proj)
    elements.append(Spacer(1, 14))

    # -------------------------------------------------------------
    # SECTION 8: STEP-BY-STEP HANDS-ON RUNNING GUIDE
    # -------------------------------------------------------------
    elements.append(Paragraph("8. Step-by-Step Hands-On Guide", h1_style))
    guide_steps = [
        "<b>Step 1 — Start the Servers:</b><br/>"
        "• Terminal 1 (Backend): <code>cd backend && python -m uvicorn app.main:app --port 8000</code><br/>"
        "• Terminal 2 (Frontend): <code>cd frontend && npm run dev</code>",
        "<b>Step 2 — Open the Console:</b><br/>"
        "Open <code>http://localhost:3000</code> in your browser. Verify the DEMO tag and 'Deterministic Core: Active' status.",
        "<b>Step 3 — Run a 1-Click Sample Test:</b><br/>"
        "On the Overview page, click <b>01 Bad Release</b>. Observe the score (49), verdict (BLOCKED), and 7 rule findings.",
        "<b>Step 4 — Inspect Findings:</b><br/>"
        "Click on <code>[R02] No security scan before production deploy</code> to see exact evidence, risk impact, and verification criteria.",
        "<b>Step 5 — Test What-If Simulation:</b><br/>"
        "Click 'Simulate Changes (What-If)'. Click <code>+ Security Scan Stage</code> and <code>+ Governance Approval Gate</code>. "
        "Click 'Execute Simulation' to watch the score drop and the verdict upgrade to PASS.",
        "<b>Step 6 — Log Governance Decision & Export:</b><br/>"
        "Record an approval decision with notes, view the immutable audit trail, and export the report in Markdown (.md) or JSON.",
    ]

    for step in guide_steps:
        elements.append(Paragraph(step, body_style))
        elements.append(Spacer(1, 4))

    # Build the document
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at: {output_path}")


if __name__ == "__main__":
    out_dir = Path("d:/Desktop File/Deploywise AI/docs")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "Deploywise_AI_Workflow_and_Architecture_Guide.pdf"
    build_pdf(str(pdf_path))

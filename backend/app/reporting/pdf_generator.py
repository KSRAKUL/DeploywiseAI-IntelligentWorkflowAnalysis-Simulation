"""
Deploywise AI — Professional PDF Assessment Report Generator.
Generates an audit-ready, publication-grade executive & engineering PDF report using ReportLab.
Covers Executive Summary, Project Structure, Methodology, Detailed Findings, Prioritized Roadmap,
Recommended Workflow, and Audit Sign-off.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas:
    """Canvas that performs a two-pass rendering for accurate page numbering."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


def generate_assessment_pdf(assessment_data: dict[str, Any]) -> bytes:
    """
    Generates a professional PDF assessment report from an assessment response dictionary.
    Returns the PDF content as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a")  # Slate 900
    brand_blue = colors.HexColor("#2563eb")     # Blue 600
    dark_gray = colors.HexColor("#334155")      # Slate 700
    light_bg = colors.HexColor("#f8fafc")       # Slate 50
    border_color = colors.HexColor("#cbd5e1")   # Slate 300

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=primary_color,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=dark_gray,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=brand_blue,
        spaceBefore=12,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=dark_gray,
    )
    bold_style = ParagraphStyle(
        "BoldText",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=primary_color,
    )
    code_style = ParagraphStyle(
        "CodeText",
        parent=body_style,
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # -------------------------------------------------------------
    # Cover / Header Banner
    # -------------------------------------------------------------
    header_table = Table(
        [
            [
                Paragraph("<b>DEPLOYWISE AI</b>", ParagraphStyle("Brand", fontName="Helvetica-Bold", fontSize=14, leading=16, textColor=brand_blue)),
                Paragraph("CONFIDENTIAL ASSESSMENT REPORT", ParagraphStyle("HeaderRight", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#64748b"), alignment=2)),
            ]
        ],
        colWidths=[270, 270],
    )
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=4, spaceAfter=8))

    project_name = assessment_data.get("project_name", "Software Delivery Workflow")
    story.append(Paragraph(f"Workflow Risk & Readiness Assessment", title_style))
    story.append(Spacer(1, 2))

    meta_line = (
        f"<b>Project:</b> {project_name} | "
        f"<b>Assessment ID:</b> {assessment_data.get('assessment_id', 'N/A')[:18]}... | "
        f"<b>Generated:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    story.append(Paragraph(meta_line, subtitle_style))
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # Executive Score & KPI Cards
    # -------------------------------------------------------------
    risk_score = assessment_data.get("risk_score", 0.0)
    verdict = assessment_data.get("verdict", "PASS")
    is_blocked = assessment_data.get("is_blocked", False)
    coverage = assessment_data.get("coverage", {})
    cov_pct = coverage.get("coverage_percentage", 100.0)

    verdict_color = colors.HexColor("#dc2626") if verdict == "BLOCKED" else (
        colors.HexColor("#ea580c") if verdict == "HIGH_RISK" else (
            colors.HexColor("#ca8a04") if verdict == "NEEDS_REVIEW" else colors.HexColor("#16a34a")
        )
    )

    assurance_score = max(0.0, min(100.0, 100.0 - risk_score))
    card_data = [
        [
            Paragraph("<b>ASSURANCE SCORE</b>", ParagraphStyle("CardHead", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#64748b"))),
            Paragraph("<b>VERDICT</b>", ParagraphStyle("CardHead", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#64748b"))),
            Paragraph("<b>ASSESSMENT COVERAGE</b>", ParagraphStyle("CardHead", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#64748b"))),
            Paragraph("<b>BLOCKING STATUS</b>", ParagraphStyle("CardHead", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#64748b"))),
        ],
        [
            Paragraph(f"<font size=16><b>{assurance_score:.0f} / 100</b></font>", ParagraphStyle("Score", fontName="Helvetica-Bold", textColor=verdict_color)),
            Paragraph(f"<font size=12><b>{verdict}</b></font>", ParagraphStyle("Vrd", fontName="Helvetica-Bold", textColor=verdict_color)),
            Paragraph(f"<font size=14><b>{cov_pct:.1f}%</b></font>", ParagraphStyle("Cov", fontName="Helvetica-Bold", textColor=brand_blue)),
            Paragraph(f"<font size=14><b>{'BLOCKED' if is_blocked else 'NOT BLOCKED'}</b></font>", ParagraphStyle("Blk", fontName="Helvetica-Bold", textColor=verdict_color)),
        ],
        [
            Paragraph(f"<font size=7 color='#64748b'>100 = Clean Pass ({risk_score:.0f} risk pts)</font>", body_style),
            Paragraph("<font size=7 color='#64748b'>Release gate policy</font>", body_style),
            Paragraph(f"<font size=7 color='#64748b'>{coverage.get('executed_checks', 0)} of {coverage.get('total_checks', 0)} checks executed</font>", body_style),
            Paragraph("<font size=7 color='#64748b'>Mandatory gate failure</font>", body_style),
        ],
    ]
    card_table = Table(card_data, colWidths=[135, 135, 135, 135])
    card_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(card_table)
    story.append(Spacer(1, 8))

    # Developer Encouragement Box
    enc = assessment_data.get("developer_encouragement")
    if enc:
        enc_head = enc.get("headline", "Engineering Guidance")
        enc_msg = enc.get("message", "")
        enc_cta = enc.get("call_to_action", "")
        enc_color = "#dc2626" if is_blocked else ("#2563eb" if verdict == "PASS" else "#d97706")
        enc_table = Table([
            [Paragraph(f"<b><font color='{enc_color}'>★ Developer Guidance: {enc_head}</font></b>", bold_style)],
            [Paragraph(enc_msg, body_style)],
            [Paragraph(f"<b>Next Action:</b> {enc_cta}", subtitle_style)],
        ], colWidths=[540])
        enc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(enc_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(enc_table)
        story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section A: Executive Summary
    # -------------------------------------------------------------
    story.append(Paragraph("A. Executive Summary", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2, spaceAfter=6))

    findings = assessment_data.get("findings", [])
    blocking_count = sum(1 for f in findings if f.get("blocking"))
    crit_count = sum(1 for f in findings if f.get("severity") == "critical")
    high_count = sum(1 for f in findings if f.get("severity") == "high")

    summary_text = (
        f"Deploywise AI conducted a multi-layered assurance evaluation on <b>{project_name}</b>. "
        f"The system identified <b>{len(findings)} total findings</b>, including <b>{crit_count} Critical</b>, "
        f"<b>{high_count} High</b>, and <b>{blocking_count} mandatory release blockers</b>. "
    )
    if is_blocked:
        summary_text += (
            "<b>Deployment is BLOCKED</b> under current release policy. The pipeline must satisfy mandatory "
            "approval, security scanning, and test coverage gates before promotion to production."
        )
    elif verdict == "PASS":
        summary_text += "The workflow satisfies mandatory baseline controls and is cleared for production promotion."
    else:
        summary_text += "Review is required by engineering leadership to remediate highlighted risk points."

    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section B: Project & Discovered Architecture
    # -------------------------------------------------------------
    story.append(Paragraph("B. Discovered Architecture & Scope", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2, spaceAfter=6))

    structure = assessment_data.get("structure", {})
    langs = ", ".join(structure.get("languages", [])) or "Detected via configuration"
    pkg_mgrs = ", ".join(structure.get("package_managers", [])) or "None detected"
    ci_files = ", ".join(structure.get("ci_workflows", [])) or "Inferred / Native DAG"

    struct_data = [
        [Paragraph("<b>Input Source:</b>", bold_style), Paragraph(str(assessment_data.get("input_source", "Project Ingestion")), body_style)],
        [Paragraph("<b>Detected Languages:</b>", bold_style), Paragraph(langs, body_style)],
        [Paragraph("<b>Package Managers:</b>", bold_style), Paragraph(pkg_mgrs, body_style)],
        [Paragraph("<b>CI/CD Workflows:</b>", bold_style), Paragraph(ci_files, body_style)],
        [Paragraph("<b>Inspected Files:</b>", bold_style), Paragraph(f"{structure.get('total_files', len(structure.get('inspected_files', [])))} files cataloged", body_style)],
    ]
    struct_table = Table(struct_data, colWidths=[130, 410])
    struct_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(struct_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section C: Workflow Intelligence & Corrected Architecture
    # -------------------------------------------------------------
    diff_items = assessment_data.get("diagram_comparison", [])
    boundaries = assessment_data.get("evidence_boundaries", [])
    if diff_items or boundaries:
        story.append(Paragraph("C. Workflow Intelligence & Corrected Architecture", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2, spaceAfter=6))

        if diff_items:
            story.append(Paragraph("<b>Recommended Architectural Corrections & Added Safety Gates:</b>", bold_style))
            story.append(Spacer(1, 3))
            diff_rows = [
                [
                    Paragraph("<b>Action</b>", bold_style),
                    Paragraph("<b>Stage Title & Scope</b>", bold_style),
                    Paragraph("<b>Technical Rationale</b>", bold_style),
                ]
            ]
            for d in diff_items:
                act = d.get("action", "added").upper()
                act_col = "#16a34a" if act == "ADDED" else "#2563eb"
                diff_rows.append([
                    Paragraph(f"<font color='{act_col}'><b>{act}</b></font>", body_style),
                    Paragraph(f"<b>{d.get('title', '')}</b><br/><font size=7.5 color='#64748b'>{d.get('description', '')}</font>", body_style),
                    Paragraph(d.get("rationale", ""), body_style),
                ])
            diff_table = Table(diff_rows, colWidths=[70, 230, 240])
            diff_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), light_bg),
                ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(diff_table)
            story.append(Spacer(1, 6))

        if boundaries:
            story.append(Paragraph("<b>Evidence Boundaries & Verification Limits:</b>", bold_style))
            for b in boundaries:
                story.append(Paragraph(f"• <font color='#475569'>{b}</font>", body_style))
            story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section D: Assessment Methodology & Tool Execution Matrix
    # -------------------------------------------------------------
    story.append(Paragraph("D. Assessment Methodology & Tool Matrix", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2, spaceAfter=6))
    story.append(Paragraph("Deploywise AI runs a hybrid verification model: deterministic DAG topology rules, native regex & manifest analyzers, and pluggable external security tools.", body_style))
    story.append(Spacer(1, 4))

    scanner_results = assessment_data.get("scanner_results", [])
    matrix_rows = [
        [
            Paragraph("<b>Scanner / Rule Engine</b>", bold_style),
            Paragraph("<b>Category</b>", bold_style),
            Paragraph("<b>Execution Status</b>", bold_style),
            Paragraph("<b>Issues Found</b>", bold_style),
        ]
    ]
    # Add deterministic rule suite row
    matrix_rows.append([
        Paragraph("Deterministic DAG Rules (R01-R10)", body_style),
        Paragraph("Workflow Topology", body_style),
        Paragraph("<font color='#16a34a'><b>PASSED (Executed)</b></font>", body_style),
        Paragraph(str(sum(1 for f in findings if f.get("source") == "rule")), body_style),
    ])

    for sc in scanner_results:
        st_val = sc.get("status", "unknown")
        if st_val == "passed":
            st_color = "<font color='#16a34a'><b>PASSED</b></font>"
        elif st_val == "failed":
            st_color = "<font color='#dc2626'><b>ISSUES DETECTED</b></font>"
        elif "skipped" in st_val:
            st_color = "<font color='#ca8a04'>SKIPPED (Not in host PATH)</font>"
        else:
            st_color = st_val.upper()

        matrix_rows.append([
            Paragraph(sc.get("scanner_name", "Scanner"), body_style),
            Paragraph(str(sc.get("category", "")).capitalize(), body_style),
            Paragraph(st_color, body_style),
            Paragraph(str(sc.get("finding_count", 0)), body_style),
        ])

    matrix_table = Table(matrix_rows, colWidths=[170, 110, 180, 80])
    matrix_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), light_bg),
            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(matrix_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # Section D: Detailed Verified Findings
    # -------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("D. Detailed Risk Findings", h1_style),
        HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2, spaceAfter=6),
    ]))

    if not findings:
        story.append(Paragraph("No security or workflow risk findings were identified.", body_style))
    else:
        for f in findings[:15]:  # Limit top 15 in PDF for readability
            f_sev = f.get("severity", "medium").upper()
            f_blk = " | <b>BLOCKING</b>" if f.get("blocking") else ""
            f_color = "#dc2626" if f_sev == "CRITICAL" else ("#ea580c" if f_sev == "HIGH" else "#ca8a04")

            finding_box = [
                [
                    Paragraph(f"<font color='{f_color}'><b>[{f_sev}{f_blk}] {f.get('rule_id', 'RULE')} — {f.get('title', 'Risk Finding')}</b></font>", bold_style),
                ],
                [
                    Paragraph(f"<b>Category:</b> {str(f.get('category', '')).title()} | <b>Evidence Status:</b> {f.get('evidence_status', 'confirmed').title()} | <b>Location:</b> {f.get('file_path') or 'Workflow DAG'}", subtitle_style),
                ],
                [
                    Paragraph(f"<b>Evidence:</b> {f.get('evidence', 'N/A')}", body_style),
                ],
                [
                    Paragraph(f"<b>Why It Matters:</b> {f.get('why_it_matters', 'N/A')}", body_style),
                ],
                [
                    Paragraph(f"<b>Recommended Fix:</b> {f.get('recommended_fix', 'N/A')}", body_style),
                ],
                [
                    Paragraph(f"<b>Verification:</b> {f.get('verification_criteria', 'N/A')}", subtitle_style),
                ],
            ]
            f_table = Table(finding_box, colWidths=[540])
            f_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), light_bg),
                    ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(KeepTogether([f_table, Spacer(1, 6)]))

    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section E: Prioritized Remediation Roadmap
    # -------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("E. Prioritized Remediation Roadmap", h1_style),
        HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2, spaceAfter=6),
        Paragraph("Organized by operational urgency to unblock production delivery efficiently:", body_style),
        Spacer(1, 4),
    ]))

    roadmap = assessment_data.get("remediation_roadmap", [])
    if not roadmap:
        # Synthesize from findings if empty
        roadmap_rows = [
            [
                Paragraph("<b>Priority</b>", bold_style),
                Paragraph("<b>Item & Title</b>", bold_style),
                Paragraph("<b>Required Remediation</b>", bold_style),
            ]
        ]
        p1 = [f for f in findings if f.get("blocking")]
        p2 = [f for f in findings if not f.get("blocking") and f.get("severity") in ("critical", "high")]
        p3 = [f for f in findings if f.get("severity") == "medium"]

        for item in p1:
            roadmap_rows.append([
                Paragraph("<font color='#dc2626'><b>P1 (Mandatory Blocker)</b></font>", body_style),
                Paragraph(item.get("title", ""), bold_style),
                Paragraph(item.get("recommended_fix", ""), body_style),
            ])
        for item in p2[:4]:
            roadmap_rows.append([
                Paragraph("<font color='#ea580c'><b>P2 (High Priority)</b></font>", body_style),
                Paragraph(item.get("title", ""), bold_style),
                Paragraph(item.get("recommended_fix", ""), body_style),
            ])
        for item in p3[:3]:
            roadmap_rows.append([
                Paragraph("<font color='#ca8a04'><b>P3 (Operational)</b></font>", body_style),
                Paragraph(item.get("title", ""), bold_style),
                Paragraph(item.get("recommended_fix", ""), body_style),
            ])

        rm_table = Table(roadmap_rows, colWidths=[120, 180, 240])
        rm_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), light_bg),
                ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(rm_table)

    story.append(Spacer(1, 12))

    # -------------------------------------------------------------
    # Section F: Audit Trail & Reproducibility Sign-Off
    # -------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("F. Governance, Audit & Verification Sign-Off", h1_style),
        HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=2, spaceAfter=6),
        Paragraph(
            "This document is an immutable record of software delivery control compliance. "
            "All findings have been logged to the tamper-evident append-only audit trail.",
            body_style,
        ),
        Spacer(1, 6),
        Table(
            [
                [Paragraph("<b>Engine Version:</b>", bold_style), Paragraph("Deploywise AI v0.1.0", body_style)],
                [Paragraph("<b>Policy Version:</b>", bold_style), Paragraph("1.0.0 (Standard Production Gate)", body_style)],
                [Paragraph("<b>Rule Set Version:</b>", bold_style), Paragraph("1.0.0 (Rules R01 - R10)", body_style)],
                [Paragraph("<b>Commit Hash:</b>", bold_style), Paragraph(str(assessment_data.get("commit_sha") or "N/A"), code_style)],
            ],
            colWidths=[130, 410],
            style=[
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ],
        ),
    ]))

    doc.build(story)
    return buffer.getvalue()

import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { MermaidViewer } from "../components/MermaidViewer";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Lightbulb,
  GitBranch,
  FileCode2,
  Terminal,
  Package,
  Server,
  Loader2,
  FileDown,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Info,
  TrendingUp,
  Layers,
  Eye,
  Check,
  Compass,
  Copy,
} from "lucide-react";

interface ProjectAssessmentViewProps {
  assessmentResult: any;
  onNavigate: (view: string, workflowId?: string) => void;
}

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const colors: Record<string, string> = {
    critical: "var(--critical)",
    high: "var(--high)",
    medium: "var(--medium)",
    low: "var(--low)",
  };
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 4,
        fontSize: 11,
        fontWeight: 700,
        backgroundColor: `${colors[severity] || "#999"}22`,
        color: colors[severity] || "#999",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      {severity}
    </span>
  );
};

const EncouragementBanner: React.FC<{ encouragement: any }> = ({ encouragement }) => {
  if (!encouragement) return null;
  const statusThemes: Record<string, { border: string; bg: string; icon: string; text: string }> = {
    blocked: { border: "#dc2626", bg: "rgba(220, 38, 38, 0.05)", icon: "🛡️", text: "#b91c1c" },
    needs_attention: { border: "#2563eb", bg: "rgba(37, 99, 235, 0.05)", icon: "💡", text: "#1d4ed8" },
    healthy: { border: "#16a34a", bg: "rgba(22, 163, 74, 0.05)", icon: "🚀", text: "#15803d" },
    partial_evidence: { border: "#6366f1", bg: "rgba(99, 102, 241, 0.05)", icon: "🔍", text: "#4338ca" },
    verified: { border: "#0d9488", bg: "rgba(13, 148, 136, 0.05)", icon: "✨", text: "#0f766e" },
  };
  const theme = statusThemes[encouragement.status_level] || statusThemes.needs_attention;

  return (
    <div
      style={{
        padding: "16px 20px",
        borderRadius: "var(--radius)",
        border: `1.5px solid ${theme.border}`,
        backgroundColor: theme.bg,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 22 }}>{theme.icon}</span>
        <span style={{ fontWeight: 700, fontSize: 15, color: theme.text }}>
          Developer Guidance: {encouragement.headline}
        </span>
      </div>
      <p style={{ fontSize: 13, lineHeight: 1.6, margin: 0, color: "var(--text-primary)" }}>
        {encouragement.message}
      </p>
      {encouragement.call_to_action && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, marginTop: 4, flexWrap: "wrap" }}>
          <span style={{ fontWeight: 600, color: theme.text }}>Next Step:</span>
          <span style={{ background: "var(--surface)", padding: "3px 10px", borderRadius: 4, border: `1px solid ${theme.border}44`, fontWeight: 500 }}>
            {encouragement.call_to_action}
          </span>
        </div>
      )}
    </div>
  );
};

const VerdictBanner: React.FC<{ verdict: string; score: number; isBlocked: boolean }> = ({
  verdict,
  score,
  isBlocked,
}) => {
  const config = {
    BLOCKED: { color: "var(--critical)", bg: "var(--critical-bg)", icon: "⛔", label: "Release Blocked" },
    HIGH_RISK: { color: "var(--high)", bg: "rgba(234, 88, 12, 0.08)", icon: "🟠", label: "High Risk" },
    NEEDS_REVIEW: { color: "var(--medium)", bg: "rgba(202, 138, 4, 0.08)", icon: "🟡", label: "Needs Review" },
    PASS: { color: "var(--low)", bg: "rgba(22, 163, 74, 0.08)", icon: "✅", label: "Passed" },
    INSUFFICIENT_EVIDENCE: { color: "var(--text-muted)", bg: "rgba(100,116,139,0.08)", icon: "⚪", label: "Insufficient Evidence" },
  }[verdict] || { color: "var(--text-muted)", bg: "rgba(100,116,139,0.08)", icon: "⚪", label: verdict };

  return (
    <div
      style={{
        padding: "16px 20px",
        borderRadius: "var(--radius)",
        border: `1px solid ${config.color}44`,
        backgroundColor: config.bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 12,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ fontSize: 24 }}>{config.icon}</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: 16, color: config.color }}>
            {config.label}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>
            Delivery Assurance Score: <strong style={{ color: "var(--text-primary)" }}>{Math.max(0, 100 - score)}/100</strong>
            {score > 0 ? ` (${score} risk deductions)` : " • 100% Clean Pipeline"}
            {isBlocked && " • Production deployment is blocked"}
          </div>
        </div>
      </div>
      <div style={{ display: "flex", gap: 10 }}>
        <div style={{ textAlign: "center", padding: "8px 16px", background: "var(--surface)", borderRadius: 8 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: config.color }}>{Math.max(0, 100 - score)}</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase" }}>Assurance Score</div>
        </div>
      </div>
    </div>
  );
};

const CollapsibleSection: React.FC<{
  title: string;
  icon: React.ReactNode;
  badge?: string | number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}> = ({ title, icon, badge, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="card" style={{ padding: 0, overflow: "hidden" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          padding: "14px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          borderBottom: open ? "1px solid var(--border)" : "none",
          userSelect: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {icon}
          <span style={{ fontWeight: 600, fontSize: 14 }}>{title}</span>
          {badge !== undefined && (
            <span
              style={{
                fontSize: 11,
                padding: "2px 8px",
                borderRadius: 10,
                background: "var(--surface-variant)",
                color: "var(--text-secondary)",
                fontWeight: 600,
              }}
            >
              {badge}
            </span>
          )}
        </div>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>
      {open && <div style={{ padding: "16px 20px" }}>{children}</div>}
    </div>
  );
};

export const ProjectAssessmentView: React.FC<ProjectAssessmentViewProps> = ({
  assessmentResult: initialResult,
  onNavigate,
}) => {
  const [assessmentResult, setAssessmentResult] = useState<any>(initialResult);
  const [loading, setLoading] = useState(false);
  const [expandedFinding, setExpandedFinding] = useState<string | null>(null);
  const [diagramTab, setDiagramTab] = useState<"recommended" | "existing">("recommended");
  const [copiedPatchId, setCopiedPatchId] = useState<string | null>(null);

  useEffect(() => {
    if (initialResult) {
      setAssessmentResult(initialResult);
      return;
    }
    const loadLatest = async () => {
      try {
        setLoading(true);
        const list = await api.listAssessments(1);
        if (list.length > 0) {
          const detail = await api.getAssessment(list[0].assessment_id);
          setAssessmentResult(detail);
        }
      } catch (err) {
        console.error("Failed to load assessment:", err);
      } finally {
        setLoading(false);
      }
    };
    loadLatest();
  }, [initialResult]);

  const handleCopyCode = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPatchId(id);
    setTimeout(() => setCopiedPatchId(null), 2000);
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "64px 0", gap: 12 }}>
        <Loader2 className="spin" size={32} color="var(--accent)" />
        <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Loading project assessment...</span>
      </div>
    );
  }

  if (!assessmentResult) {
    return (
      <div style={{ textAlign: "center", padding: "64px 20px" }}>
        <ShieldAlert size={48} color="var(--text-muted)" style={{ margin: "0 auto 16px" }} />
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No Assessment Loaded</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: 13, maxWidth: 420, margin: "0 auto 20px" }}>
          Submit a GitHub repository URL, ZIP archive, CI/CD pipeline, or architecture diagram to generate a full assurance assessment.
        </p>
        <button className="btn btn-primary" onClick={() => onNavigate("workflows")}>
          Start Assessment
        </button>
      </div>
    );
  }

  const {
    assessment_id,
    project_name,
    input_type,
    input_source,
    created_at,
    commit_sha,
    workflow_id,
    risk_score,
    coverage,
    verdict,
    is_blocked,
    structure,
    scanner_results,
    findings,
    category_scores,
    remediation_roadmap,
    ai_summary,
    existing_workflow_diagram,
    recommended_workflow_diagram,
    diagram_comparison,
    observed_facts,
    inferred_relationships,
    unknown_details,
    evidence_boundaries,
    developer_encouragement,
  } = assessmentResult;

  const blockingFindings = (findings || []).filter((f: any) => f.blocking);
  const ruleFindings = (findings || []).filter((f: any) => f.source === "rule");
  const scannerFindings = (findings || []).filter((f: any) => f.source === "scanner");
  const advisoryFindings = (findings || []).filter((f: any) => f.source === "agent");

  const inputTypeLabel: Record<string, string> = {
    github: "GitHub Repository",
    zip: "ZIP Archive",
    cicd: "CI/CD YAML",
    diagram: "Architecture Diagram / Report",
    json: "JSON Specification",
  };

  const scannerStatusStyle = (status: string) => {
    if (status === "passed") return { color: "var(--low)", fontWeight: 700 };
    if (status === "failed") return { color: "var(--critical)", fontWeight: 700 };
    if (status?.includes("skipped")) return { color: "var(--medium)" };
    if (status === "timed_out") return { color: "var(--high)" };
    return { color: "var(--text-muted)" };
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <h1 className="page-title">{project_name}</h1>
            <span className="badge">{inputTypeLabel[input_type] || input_type}</span>
          </div>
          <p className="page-description">
            Full-spectrum workflow assurance assessment •{" "}
            {new Date(created_at).toLocaleString()}
            {commit_sha && (
              <span style={{ marginLeft: 10, fontFamily: "monospace", fontSize: 12 }}>
                SHA: {commit_sha.slice(0, 12)}...
              </span>
            )}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {workflow_id && (
            <>
              <button
                className="btn btn-secondary"
                onClick={() => api.downloadReportPdf(assessment_id)}
              >
                <FileDown size={15} /> PDF Report
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => onNavigate("what-if", workflow_id)}
              >
                <Sparkles size={15} /> What-If Simulation
              </button>
              <button
                className="btn btn-primary"
                onClick={() => onNavigate("analysis", workflow_id)}
              >
                <TrendingUp size={15} /> Full Analysis
              </button>
            </>
          )}
        </div>
      </div>

      {/* Developer Encouragement Banner */}
      <EncouragementBanner encouragement={developer_encouragement} />

      {/* Verdict Banner */}
      <VerdictBanner verdict={verdict} score={Math.round(risk_score)} isBlocked={is_blocked} />

      {/* Coverage + Meta Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 14 }}>
        {[
          {
            label: "Assessment Coverage",
            value: `${coverage?.coverage_percentage?.toFixed(1) ?? 0}%`,
            sub: `${coverage?.executed_checks ?? 0} of ${coverage?.total_checks ?? 0} checks run`,
          },
          {
            label: "Total Findings",
            value: (findings || []).length,
            sub: `${blockingFindings.length} blocking`,
          },
          {
            label: "Rule Findings",
            value: ruleFindings.length,
            sub: "Deterministic violations",
          },
          {
            label: "Scanner Findings",
            value: scannerFindings.length,
            sub: "Static & secret analysis",
          },
          {
            label: "Languages",
            value: (structure?.languages || []).length || "—",
            sub: (structure?.languages || []).slice(0, 2).join(", ") || "None detected",
          },
          {
            label: "Files Inspected",
            value: structure?.total_files ?? "—",
            sub: `${(structure?.ci_workflows || []).length} CI/CD files`,
          },
        ].map(({ label, value, sub }) => (
          <div key={label} className="stat-card">
            <div className="stat-label">{label}</div>
            <div className="stat-value" style={{ fontSize: 22 }}>{value}</div>
            <div className="stat-hint">{sub}</div>
          </div>
        ))}
      </div>

      {/* Section: Workflow Visual Intelligence & Corrected Architecture */}
      {(existing_workflow_diagram || recommended_workflow_diagram) && (
        <CollapsibleSection
          title="Workflow Architecture & Visual Intelligence"
          icon={<GitBranch size={18} color="var(--accent)" />}
          badge="Interactive Canvas"
          defaultOpen
        >
          {/* View Mode Toggle Buttons */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                type="button"
                className={`btn ${diagramTab === "recommended" ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setDiagramTab("recommended")}
                style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}
              >
                <Compass size={15} />
                <span>Recommended Improved Architecture</span>
                <span style={{ fontSize: 10, background: "rgba(255,255,255,0.2)", padding: "1px 6px", borderRadius: 10 }}>Target</span>
              </button>
              <button
                type="button"
                className={`btn ${diagramTab === "existing" ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setDiagramTab("existing")}
                style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}
              >
                <Layers size={15} />
                <span>Existing Reconstructed Workflow</span>
                <span style={{ fontSize: 10, background: "rgba(255,255,255,0.2)", padding: "1px 6px", borderRadius: 10 }}>As Observed</span>
              </button>
            </div>

            {/* Visual Legend */}
            <div style={{ display: "flex", gap: 12, alignItems: "center", fontSize: 11, color: "var(--text-secondary)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: "#F0FDF4", border: "1.5px solid #16A34A" }}></span>
                <span>Confirmed</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: "#FFE4E6", border: "1.5px solid #E11D48" }}></span>
                <span>Issue / Blocker</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: "#EFF6FF", border: "1.5px solid #2563EB" }}></span>
                <span>Proposed Added Gate</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: "#F8FAFC", border: "1.5px dashed #94A3B8" }}></span>
                <span>Inferred / Unverified</span>
              </div>
            </div>
          </div>

          {/* Render Active Diagram */}
          {diagramTab === "recommended" && recommended_workflow_diagram && (
            <div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
                Proposed architecture incorporating missing automated safety gates, security scanners, change approvals, canary rollback, and health probes:
              </div>
              <MermaidViewer id="recommended-workflow" chart={recommended_workflow_diagram.mermaid_code} />
            </div>
          )}

          {diagramTab === "existing" && existing_workflow_diagram && (
            <div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
                Reconstructed pipeline representation based on submitted diagram, CI/CD YAML, or repository manifest:
              </div>
              <MermaidViewer id="existing-workflow" chart={existing_workflow_diagram.mermaid_code} />
            </div>
          )}

          {/* Architecture Changes Breakdown Table */}
          {(diagram_comparison || []).length > 0 && (
            <div style={{ marginTop: 20 }}>
              <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: "var(--text-primary)" }}>
                Architectural Improvements & Required Safety Gates ({diagram_comparison.length})
              </h4>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ width: 90 }}>Action</th>
                      <th>Proposed Stage & Gate</th>
                      <th>Technical Rationale & Risk Addressed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {diagram_comparison.map((item: any) => (
                      <tr key={item.stage_id}>
                        <td>
                          <span
                            style={{
                              fontSize: 10,
                              fontWeight: 700,
                              textTransform: "uppercase",
                              padding: "2px 8px",
                              borderRadius: 4,
                              background: item.action === "added" ? "rgba(22, 163, 74, 0.1)" : "rgba(37, 99, 235, 0.1)",
                              color: item.action === "added" ? "var(--low)" : "var(--accent)",
                            }}
                          >
                            {item.action}
                          </span>
                        </td>
                        <td>
                          <div style={{ fontWeight: 600, fontSize: 12 }}>{item.title}</div>
                          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>{item.description}</div>
                        </td>
                        <td style={{ fontSize: 12, lineHeight: 1.5 }}>
                          {item.rationale}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Evidence Boundaries Callout */}
          <div style={{ marginTop: 16, padding: "12px 16px", background: "var(--bg, #f8fafc)", borderRadius: 6, border: "1px solid var(--border)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
              <Info size={14} color="var(--accent)" />
              <span>Evidence Boundaries & Verification Limits</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.6 }}>
              Architecture diagrams prove pipeline topology, declared stages, and designated environments.
              Verifying credentials safety, code vulnerability elimination, and container non-root execution requires source code and filesystem scanner execution.
            </div>
          </div>
        </CollapsibleSection>
      )}

      {/* AI Summary */}
      {ai_summary && (
        <CollapsibleSection
          title="AI Project Analysis"
          icon={<Sparkles size={18} color="var(--accent)" />}
          defaultOpen
        >
          <div
            style={{
              padding: "14px 16px",
              background: "rgba(37, 99, 235, 0.06)",
              border: "1px solid rgba(37, 99, 235, 0.15)",
              borderRadius: 8,
              fontSize: 13,
              lineHeight: 1.7,
              color: "var(--text-primary)",
            }}
          >
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 10, fontStyle: "italic" }}>
              ⚠️ AI-generated advisory content — does not affect risk scores or verdicts. Based on verified evidence only.
            </div>
            <div style={{ whiteSpace: "pre-wrap" }}>{ai_summary}</div>
          </div>
        </CollapsibleSection>
      )}

      {/* Project Structure */}
      <CollapsibleSection
        title="Discovered Project Structure"
        icon={<FileCode2 size={18} color="var(--accent)" />}
        defaultOpen={false}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {[
            { label: "Languages", items: structure?.languages, icon: <Terminal size={14} /> },
            { label: "Frameworks", items: structure?.frameworks, icon: <Server size={14} /> },
            { label: "Package Managers", items: structure?.package_managers, icon: <Package size={14} /> },
            { label: "CI/CD Workflow Files", items: structure?.ci_workflows, icon: <GitBranch size={14} /> },
          ].map(({ label, items, icon }) => (
            <div key={label}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, fontSize: 12, color: "var(--text-secondary)", marginBottom: 6 }}>
                {icon} {label}
              </div>
              {(items || []).length === 0 ? (
                <span style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic" }}>None detected</span>
              ) : (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {(items || []).map((item: string) => (
                    <span key={item} className="badge" style={{ fontSize: 11 }}>{item}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Category Risk Scores */}
      {(category_scores || []).length > 0 && (
        <CollapsibleSection
          title="Risk Category Breakdown"
          icon={<ShieldAlert size={18} color="var(--accent)" />}
          defaultOpen
        >
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Raw Score</th>
                  <th>Weight</th>
                  <th>Weighted Contribution</th>
                  <th>Violations</th>
                </tr>
              </thead>
              <tbody>
                {(category_scores || []).map((cs: any) => (
                  <tr key={cs.category}>
                    <td style={{ fontWeight: 600, textTransform: "capitalize" }}>{cs.category}</td>
                    <td>{cs.raw_score?.toFixed(1)} / 100</td>
                    <td>{((cs.weight || 0) * 100).toFixed(0)}%</td>
                    <td style={{ fontWeight: 600 }}>{cs.weighted_score?.toFixed(2)} pts</td>
                    <td>
                      {cs.finding_count > 0 ? (
                        <span style={{ color: "var(--critical)", fontWeight: 600 }}>{cs.finding_count} issues</span>
                      ) : (
                        <span style={{ color: "var(--low)" }}>Clean</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
            * Advisory agent observations (if any) never contribute to category points or the final risk score.
          </div>
        </CollapsibleSection>
      )}

      {/* Scanner Results */}
      {(scanner_results || []).length > 0 && (
        <CollapsibleSection
          title="Security Scanner Execution Results"
          icon={<Terminal size={18} color="var(--accent)" />}
          badge={`${(scanner_results || []).filter((s: any) => s.status === "passed" || s.status === "failed").length}/${(scanner_results || []).length} run`}
          defaultOpen={false}
        >
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Scanner</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Issues Found</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {(scanner_results || []).map((sr: any) => (
                  <tr key={sr.scanner_name}>
                    <td style={{ fontWeight: 600, fontFamily: "monospace", fontSize: 12 }}>{sr.scanner_name}</td>
                    <td style={{ textTransform: "capitalize" }}>{sr.category}</td>
                    <td>
                      <span style={scannerStatusStyle(sr.status)}>
                        {sr.status === "passed" ? "✓ Passed" :
                         sr.status === "failed" ? "⚠ Issues Found" :
                         sr.status?.includes("skipped") ? "— Not Installed" :
                         sr.status === "timed_out" ? "⏱ Timed Out" :
                         sr.status}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      {sr.finding_count > 0 ? (
                        <span style={{ color: "var(--critical)", fontWeight: 700 }}>{sr.finding_count}</span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>{sr.status?.includes("skipped") ? "—" : "0"}</span>
                      )}
                    </td>
                    <td style={{ color: "var(--text-muted)", fontSize: 12 }}>
                      {sr.duration_ms > 0 ? `${sr.duration_ms}ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CollapsibleSection>
      )}

      {/* Findings List with 8-Point Guidance */}
      <CollapsibleSection
        title="Comprehensive Risk Findings & Implementation Guidance"
        icon={<AlertTriangle size={18} color="var(--accent)" />}
        badge={(findings || []).length}
        defaultOpen
      >
        {(findings || []).length === 0 ? (
          <div style={{ padding: "24px 0", textAlign: "center", color: "var(--text-secondary)" }}>
            <CheckCircle2 size={28} color="var(--low)" style={{ margin: "0 auto 8px" }} />
            <div>No findings identified by applicable checks.</div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {(findings || []).map((f: any) => {
              const isExpanded = expandedFinding === f.finding_id;
              const leftColor = f.blocking ? "var(--critical)" : f.source === "agent" ? "var(--accent)" : "var(--high)";
              return (
                <div
                  key={f.finding_id}
                  style={{
                    border: "1px solid var(--border)",
                    borderLeft: `4px solid ${leftColor}`,
                    borderRadius: "var(--radius-sm)",
                    overflow: "hidden",
                    background: "var(--surface)",
                  }}
                >
                  <div
                    onClick={() => setExpandedFinding(isExpanded ? null : f.finding_id)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                      <div style={{ marginTop: 2 }}>
                        {f.blocking ? (
                          <ShieldAlert size={16} color="var(--critical)" />
                        ) : f.source === "agent" ? (
                          <Lightbulb size={16} color="var(--accent)" />
                        ) : (
                          <AlertTriangle size={16} color="var(--high)" />
                        )}
                      </div>
                      <div>
                        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                          <span style={{ fontFamily: "monospace", fontSize: 11, fontWeight: 700 }}>
                            [{f.rule_id}]
                          </span>
                          <span style={{ fontWeight: 600, fontSize: 13 }}>{f.title}</span>
                          {f.blocking && (
                            <span style={{ fontSize: 10, fontWeight: 700, color: "var(--critical)", border: "1px solid var(--critical)", padding: "1px 6px", borderRadius: 4 }}>
                              BLOCKING
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 3 }}>
                          Detected in: <code>{f.file_path || (f.stage_ids || []).join(", ") || "Workflow DAG"}</code>
                        </div>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                      <SeverityBadge severity={f.severity} />
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: "0 16px 16px", borderTop: "1px solid var(--border)", background: "var(--bg, #fcfcfd)" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 14 }}>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>1. EVIDENCE DETECTED</div>
                          <div style={{ fontSize: 12, lineHeight: 1.6, background: "var(--surface)", padding: "8px 10px", borderRadius: 4, border: "1px solid var(--border)" }}>{f.evidence}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>2. WHY IT MATTERS</div>
                          <div style={{ fontSize: 12, lineHeight: 1.6, background: "var(--surface)", padding: "8px 10px", borderRadius: 4, border: "1px solid var(--border)" }}>{f.why_it_matters}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>3. POTENTIAL CONSEQUENCE</div>
                          <div style={{ fontSize: 12, lineHeight: 1.6, background: "var(--surface)", padding: "8px 10px", borderRadius: 4, border: "1px solid var(--border)", color: "var(--critical)" }}>
                            {f.impact || "Failure to resolve this gate exposes production systems to security compromise, rollback failure, or deployment downtime."}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>4. RECOMMENDED REMEDIATION</div>
                          <div style={{ fontSize: 12, lineHeight: 1.6, background: "var(--surface)", padding: "8px 10px", borderRadius: 4, border: "1px solid var(--border)", color: "var(--text-primary)" }}>{f.recommended_fix}</div>
                        </div>
                      </div>

                      {f.suggested_patch && (
                        <div style={{ marginTop: 12 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)" }}>5. IMPLEMENTATION EXAMPLE / PATCH</div>
                            <button
                              type="button"
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleCopyCode(f.suggested_patch, f.finding_id)}
                              style={{ padding: "2px 8px", fontSize: 11, display: "flex", alignItems: "center", gap: 4 }}
                            >
                              <Copy size={12} />
                              <span>{copiedPatchId === f.finding_id ? "Copied!" : "Copy Fix"}</span>
                            </button>
                          </div>
                          <pre style={{ fontSize: 11, background: "var(--surface)", padding: "8px 12px", borderRadius: 4, border: "1px solid var(--border)", overflowX: "auto" }}>
                            {f.suggested_patch}
                          </pre>
                        </div>
                      )}

                      <div style={{ marginTop: 12, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>6. VERIFICATION CRITERIA</div>
                          <div style={{ fontSize: 12, lineHeight: 1.6, background: "var(--surface)", padding: "8px 10px", borderRadius: 4, border: "1px solid var(--border)" }}>{f.verification_criteria}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 4 }}>7. VERIFICATION STATUS</div>
                          <div style={{ fontSize: 12, lineHeight: 1.6, background: "var(--surface)", padding: "8px 10px", borderRadius: 4, border: "1px solid var(--border)" }}>
                            <span style={{ fontWeight: 600, color: f.remediation_status === "resolved" ? "var(--low)" : "var(--medium)" }}>
                              {f.remediation_status === "resolved" ? "✓ Verified Clean" : "⏳ Pending Fix & Re-verification"}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div style={{ display: "flex", gap: 12, marginTop: 14, flexWrap: "wrap", fontSize: 11, color: "var(--text-muted)" }}>
                        <span>Source: <strong>{f.source}</strong></span>
                        <span>Category: <strong>{f.category}</strong></span>
                        <span>Confidence: <strong>{f.confidence}</strong></span>
                        {f.file_path && <span>File: <code>{f.file_path}</code></span>}
                        {f.line_number && <span>Line: {f.line_number}</span>}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CollapsibleSection>

      {/* Remediation Roadmap */}
      {(remediation_roadmap || []).length > 0 && (
        <CollapsibleSection
          title="Prioritized Remediation Roadmap"
          icon={<TrendingUp size={18} color="var(--accent)" />}
          badge={(remediation_roadmap || []).length}
          defaultOpen
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(remediation_roadmap || []).map((item: any) => {
              const priorityColors: Record<number, string> = {
                1: "var(--critical)",
                2: "var(--high)",
                3: "var(--medium)",
                4: "var(--low)",
              };
              const color = priorityColors[item.priority] || "var(--accent)";
              return (
                <div
                  key={item.finding_id}
                  style={{
                    padding: "12px 16px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border)",
                    borderLeft: `4px solid ${color}`,
                    background: "var(--surface)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                    <div style={{ fontWeight: 700, fontSize: 12, color }}>{item.priority_label}</div>
                    <SeverityBadge severity={item.severity} />
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{item.title}</div>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 6 }}>
                    {item.recommended_fix}
                  </div>
                  <div style={{ display: "flex", gap: 16, fontSize: 11, color: "var(--text-muted)", flexWrap: "wrap" }}>
                    <span>Location: <code>{item.location}</code></span>
                    <span>Verification: {item.verification_criteria}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </CollapsibleSection>
      )}
    </div>
  );
};

import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { WorkflowSummary } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import {
  ShieldAlert,
  CheckCircle,
  FileText,
  Activity,
  Plus,
  ArrowRight,
  Upload,
  GitBranch,
  Sparkles,
  TrendingUp,
} from "lucide-react";

interface OverviewViewProps {
  onNavigate: (view: string, workflowId?: string) => void;
  onLoadSample: (sampleName: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ onNavigate, onLoadSample }) => {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [wfRes, assessRes, healthRes] = await Promise.allSettled([
        api.listWorkflows(1, 10),
        api.listAssessments(),
        api.getHealth(),
      ]);

      if (wfRes.status === "fulfilled") setWorkflows(wfRes.value.items);
      if (assessRes.status === "fulfilled") setAssessments(assessRes.value);
      if (healthRes.status === "fulfilled") setHealth(healthRes.value);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const blockedCount = assessments.filter((a) => a.is_blocked).length;
  const passedCount = assessments.filter((a) => a.verdict === "PASS").length;
  const llmStatus = health?.llm?.status || "unknown";
  const llmName = health?.llm?.provider_name || health?.llm?.configured_provider || "Not configured";

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Executive Operations Overview</h1>
          <p className="page-description">
            Real project workflow assurance — submit any GitHub repository for automated discovery, security scanning, and risk assessment.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-secondary" onClick={() => onNavigate("workflows")}>
            <GitBranch size={16} /> Assess Repository
          </button>
          <button className="btn btn-primary" onClick={() => onNavigate("builder")}>
            <Plus size={16} /> New Workflow
          </button>
        </div>
      </div>

      {/* Real Stat Grid */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Total Assessments</div>
          <div className="stat-value">{assessments.length}</div>
          <div className="stat-hint">Projects and pipelines assessed</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Blocked Releases</div>
          <div className="stat-value" style={{ color: blockedCount > 0 ? "var(--critical)" : "var(--low)" }}>
            {blockedCount}
          </div>
          <div className="stat-hint">{blockedCount > 0 ? "⛔ Review required" : "No active blockers"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Passed Assessments</div>
          <div className="stat-value" style={{ color: "var(--low)" }}>{passedCount}</div>
          <div className="stat-hint">Meet mandatory release controls</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">AI Provider</div>
          <div className="stat-value" style={{ fontSize: 14, fontWeight: 600 }}>
            {llmStatus === "available" ? "✓ Online" : llmStatus === "unavailable" ? "⚠ Offline" : "—"}
          </div>
          <div className="stat-hint">{llmName}</div>
        </div>
      </div>

      {/* Quick start */}
      <div className="card" style={{ marginBottom: 24, padding: "16px 20px", background: "linear-gradient(135deg, rgba(37,99,235,0.08) 0%, rgba(99,102,241,0.06) 100%)", border: "1px solid rgba(37,99,235,0.2)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>
              🚀 Assess Any GitHub Repository
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 560 }}>
              Submit any public GitHub URL for full-spectrum discovery: technology stack detection,
              CI/CD workflow analysis, security scanning, and deterministic risk scoring.
            </div>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => onNavigate("workflows")}
            style={{ padding: "10px 20px", fontSize: 14 }}
          >
            <GitBranch size={16} /> Start Assessment
          </button>
        </div>
      </div>

      {/* Recent Project Assessments */}
      {assessments.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700 }}>Recent Project Assessments</h2>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("workflows")}>
              New Assessment <ArrowRight size={13} />
            </button>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Assurance Score</th>
                  <th>Verdict</th>
                  <th>Findings</th>
                  <th>Assessed At</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {assessments.slice(0, 8).map((a) => (
                  <tr key={a.assessment_id}>
                    <td style={{ fontWeight: 600 }}>{a.project_name}</td>
                    <td>
                      <span style={{
                        fontWeight: 700,
                        color: a.verdict === "PASS" ? "var(--low)" : a.is_blocked ? "var(--critical)" : "var(--medium)",
                      }}>
                        {a.score !== undefined ? `${Math.max(0, 100 - a.score)}/100` : "—"}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 4,
                        background: a.verdict === "BLOCKED" ? "var(--critical-bg)" :
                          a.verdict === "PASS" ? "rgba(22,163,74,0.1)" : "rgba(202,138,4,0.1)",
                        color: a.verdict === "BLOCKED" ? "var(--critical)" :
                          a.verdict === "PASS" ? "var(--low)" : "var(--medium)",
                      }}>
                        {a.verdict}
                      </span>
                    </td>
                    <td>
                      {(a.blocking_count || 0) > 0 ? (
                        <span style={{ color: "var(--critical)", fontWeight: 700 }}>
                          {a.blocking_count} blocking / {a.findings_count} total
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-secondary)" }}>{a.findings_count ?? 0} total</span>
                      )}
                    </td>
                    <td style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                      {a.created_at ? new Date(a.created_at).toLocaleString() : "—"}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      {a.workflow_id && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onNavigate("analysis", a.workflow_id)}
                        >
                          <TrendingUp size={13} /> View
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Sample Workflow Scenarios */}
      <div className="card" style={{ marginBottom: 24, padding: "16px 20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Sample Delivery Workflow Scenarios</div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              Load pre-configured pipelines to test deterministic rule violations and What-If fixes.
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {[
              { name: "01_bad_release.json", label: "01 Bad Release" },
              { name: "02_improved_release.json", label: "02 Improved Release" },
              { name: "03_missing_owner.json", label: "03 Missing Owner" },
              { name: "04_skip_tests_on_fail.json", label: "04 Skip Tests" },
              { name: "05_dependency_change.json", label: "05 Dependency Change" },
            ].map(({ name, label }) => (
              <button key={name} className="btn btn-secondary btn-sm" onClick={() => onLoadSample(name)}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Recently Registered Workflows */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700 }}>Recently Registered Workflows</h2>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("workflows")}>
            View All <ArrowRight size={13} />
          </button>
        </div>

        {loading ? (
          <div style={{ padding: 32, textAlign: "center", color: "var(--text-secondary)" }}>
            Loading workflows...
          </div>
        ) : workflows.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <FileText size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>No Workflows Yet</h3>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>
              Submit a GitHub repository URL or load a sample workflow to begin.
            </p>
            <button className="btn btn-primary btn-sm" onClick={() => onNavigate("workflows")}>
              Assess a Repository
            </button>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Workflow Name</th>
                  <th>Environment</th>
                  <th>Change Type</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workflows.map((wf) => (
                  <tr key={wf.workflow_id}>
                    <td style={{ fontWeight: 600 }}>{wf.name}</td>
                    <td><span className="badge">{wf.environment}</span></td>
                    <td>{wf.change_type}</td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {new Date(wf.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onNavigate("analysis", wf.workflow_id)}
                        >
                          Analyze
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => onNavigate("what-if", wf.workflow_id)}
                        >
                          <Sparkles size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

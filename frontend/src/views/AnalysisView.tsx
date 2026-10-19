import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AnalysisResult, Finding, WorkflowDetail } from "../types";
import { RiskScoreGauge } from "../components/RiskScoreGauge";
import { StatusBadge } from "../components/StatusBadge";
import { FindingDrawer } from "../components/FindingDrawer";
import { GraphCanvas } from "../components/GraphCanvas";
import {
  Play,
  RotateCw,
  Sparkles,
  FileDown,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  Lightbulb,
  Check,
  X,
  Filter,
} from "lucide-react";

interface AnalysisViewProps {
  workflowId: string | null;
  onNavigate: (view: string, workflowId?: string) => void;
}

export const AnalysisView: React.FC<AnalysisViewProps> = ({ workflowId, onNavigate }) => {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  // Decision state
  const [decisionChoice, setDecisionChoice] = useState<"approved" | "rejected" | "needs_changes">("approved");
  const [decisionNotes, setDecisionNotes] = useState("");
  const [decisionStatus, setDecisionStatus] = useState<string | null>(null);

  useEffect(() => {
    if (workflowId) {
      loadWorkflowAndAnalysis(workflowId);
    }
  }, [workflowId]);

  const loadWorkflowAndAnalysis = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const wf = await api.getWorkflow(id);
      setWorkflow(wf);

      // Attempt to load existing analysis; if 404, trigger a fresh analysis
      try {
        const existing = await api.getLatestAnalysis(id);
        setAnalysis(existing);
      } catch {
        const fresh = await api.analyzeWorkflow(id);
        setAnalysis(fresh);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!workflowId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.analyzeWorkflow(workflowId);
      setAnalysis(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordDecision = async () => {
    if (!workflowId || !analysis) return;
    try {
      await api.recordDecision(
        workflowId,
        analysis.analysis_id,
        decisionChoice,
        decisionNotes || "Recorded via Governance Review Console",
        "release-manager@company.com"
      );
      setDecisionStatus("Decision logged into append-only audit trail!");
      setTimeout(() => setDecisionStatus(null), 4000);
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (!workflowId) {
    return (
      <div className="card" style={{ padding: 48, textAlign: "center" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No Workflow Selected</h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: 16 }}>
          Select a workflow from the repository or overview dashboard to view analysis.
        </p>
        <button className="btn btn-primary" onClick={() => onNavigate("workflows")}>
          Browse Workflows
        </button>
      </div>
    );
  }

  // Filter findings
  const filteredFindings = (analysis?.findings || []).filter((f) => {
    if (severityFilter !== "all" && f.severity !== severityFilter) return false;
    if (sourceFilter !== "all" && f.source !== sourceFilter) return false;
    if (categoryFilter !== "all" && f.category !== categoryFilter) return false;
    return true;
  });

  const ruleFindingsCount = (analysis?.findings || []).filter((f) => f.source === "rule").length;
  const agentFindingsCount = (analysis?.findings || []).filter((f) => f.source === "agent").length;

  return (
    <div>
      <div className="page-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <h1 className="page-title">{workflow?.name || "Workflow Analysis"}</h1>
            {workflow?.environment && <span className="badge">{workflow.environment}</span>}
          </div>
          <p className="page-description">
            Transparent policy evaluation, deterministic risk scoring, and specialist advisory reviews.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {analysis && (
            <button className="btn btn-secondary" onClick={() => api.downloadReportPdf(analysis.analysis_id)}>
              <FileDown size={16} /> Download PDF Report
            </button>
          )}
          <button className="btn btn-secondary" onClick={() => onNavigate("what-if", workflowId)}>
            <Sparkles size={16} /> Simulate Changes (What-If)
          </button>
          <button className="btn btn-primary" onClick={handleRunAnalysis} disabled={loading}>
            <RotateCw size={16} className={loading ? "spin" : ""} /> {loading ? "Analyzing..." : "Rerun Analysis"}
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            backgroundColor: "var(--critical-bg)",
            border: "1px solid var(--critical-border)",
            color: "var(--critical)",
            padding: "12px 16px",
            borderRadius: "var(--radius-sm)",
            marginBottom: 20,
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 13,
          }}
        >
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {analysis && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Top Score Gauge Card */}
          <RiskScoreGauge
            score={analysis.score}
            verdict={analysis.verdict}
            isBlocked={analysis.is_blocked}
            policyVersion={analysis.policy_version}
            ruleSetVersion={analysis.rule_set_version}
          />

          {/* Category Breakdown Table */}
          <div className="card">
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 14 }}>
              Delivery Assurance & Category Risk Deductions
            </h2>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Risk Points</th>
                    <th>Category Weight</th>
                    <th>Weighted Deduction</th>
                    <th>Violation Count</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.category_scores.map((cs) => (
                    <tr key={cs.category}>
                      <td style={{ fontWeight: 600, textTransform: "capitalize" }}>{cs.category}</td>
                      <td>{cs.raw_score.toFixed(1)} pts</td>
                      <td>{(cs.weight * 100).toFixed(0)}%</td>
                      <td style={{ fontWeight: 600 }}>{cs.weighted_score.toFixed(2)} pts</td>
                      <td>
                        {cs.finding_count > 0 ? (
                          <span style={{ color: "var(--critical)", fontWeight: 600 }}>{cs.finding_count} failures</span>
                        ) : (
                          <span style={{ color: "var(--low)" }}>0 (Clean)</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 10 }}>
              * Delivery Assurance is evaluated from 100 base points (100 = Clean Pass). Category deductions lower the health score. Advisory agent findings never alter scoring.
            </div>
          </div>

          {/* Findings Filter & List */}
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
              <div>
                <h2 style={{ fontSize: 16, fontWeight: 700 }}>
                  Risk Findings ({filteredFindings.length})
                </h2>
                <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                  {ruleFindingsCount} Deterministic Rule findings • {agentFindingsCount} Advisory observations
                </div>
              </div>

              {/* Filter Controls */}
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  style={{ padding: "5px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>

                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  style={{ padding: "5px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                >
                  <option value="all">All Sources</option>
                  <option value="rule">Deterministic Rules Only</option>
                  <option value="agent">Advisory Agents Only</option>
                </select>

                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  style={{ padding: "5px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                >
                  <option value="all">All Categories</option>
                  <option value="security">Security</option>
                  <option value="testing">Testing</option>
                  <option value="recovery">Recovery</option>
                  <option value="dependency">Dependency</option>
                  <option value="governance">Governance</option>
                </select>
              </div>
            </div>

            {filteredFindings.length === 0 ? (
              <div style={{ padding: 32, textAlign: "center", color: "var(--text-secondary)" }}>
                No findings match the current filter selection.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {filteredFindings.map((finding) => (
                  <div
                    key={finding.finding_id}
                    onClick={() => setSelectedFinding(finding)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius-sm)",
                      cursor: "pointer",
                      backgroundColor: "var(--surface)",
                      transition: "all 0.15s ease",
                      borderLeft: finding.blocking
                        ? "4px solid var(--critical)"
                        : finding.source === "agent"
                        ? "4px solid var(--accent)"
                        : "4px solid var(--high)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                      <div style={{ marginTop: 2 }}>
                        {finding.blocking ? (
                          <ShieldAlert size={18} color="var(--critical)" />
                        ) : finding.source === "agent" ? (
                          <Lightbulb size={18} color="var(--accent)" />
                        ) : (
                          <AlertTriangle size={18} color="var(--high)" />
                        )}
                      </div>
                      <div>
                        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                          <span style={{ fontFamily: "monospace", fontSize: 12, fontWeight: 700 }}>
                            [{finding.rule_id}]
                          </span>
                          <span style={{ fontWeight: 600, fontSize: 14, color: "var(--text-primary)" }}>
                            {finding.title}
                          </span>
                        </div>
                        <div style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.4 }}>
                          {finding.evidence.slice(0, 140)}...
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
                      <StatusBadge type="severity" value={finding.severity} />
                      <StatusBadge type="source" value={finding.source} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Reviewer Decision Logger */}
          <div className="card" style={{ padding: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
              Record Reviewer Decision
            </h2>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 14 }}>
              Human governance sign-off. Log approval, rejection, or required changes into immutable audit log. (Does not deploy).
            </p>

            {decisionStatus && (
              <div style={{ padding: "8px 12px", background: "var(--low-bg)", color: "var(--low)", borderRadius: 6, marginBottom: 12, fontSize: 13 }}>
                {decisionStatus}
              </div>
            )}

            <div style={{ display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
              <div style={{ width: 180 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  Decision Choice
                </label>
                <select
                  value={decisionChoice}
                  onChange={(e) => setDecisionChoice(e.target.value as any)}
                  style={{ width: "100%", padding: "7px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)" }}
                >
                  <option value="approved">Approved</option>
                  <option value="needs_changes">Needs Changes</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              <div style={{ flex: 1, minWidth: 260 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  Review Notes
                </label>
                <input
                  type="text"
                  placeholder="e.g. Verified rollback procedures and staging testing run"
                  value={decisionNotes}
                  onChange={(e) => setDecisionNotes(e.target.value)}
                  style={{ width: "100%", padding: "7px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)" }}
                />
              </div>

              <button className="btn btn-primary" onClick={handleRecordDecision}>
                Log Review Decision
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Finding Detail Drawer */}
      <FindingDrawer
        finding={selectedFinding}
        onClose={() => setSelectedFinding(null)}
        onSimulateFix={() => {
          setSelectedFinding(null);
          onNavigate("what-if", workflowId);
        }}
      />
    </div>
  );
};

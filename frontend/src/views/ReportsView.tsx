import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AnalysisResult, WorkflowSummary } from "../types";
import { FileText, Download, Code, CheckCircle, AlertTriangle } from "lucide-react";

export const ReportsView: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selectedWfId, setSelectedWfId] = useState<string>("");
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [markdownReport, setMarkdownReport] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const res = await api.listWorkflows(1, 50);
      setWorkflows(res.items);
      if (res.items.length > 0) {
        setSelectedWfId(res.items[0].workflow_id);
        loadReportForWorkflow(res.items[0].workflow_id);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const loadReportForWorkflow = async (wfId: string) => {
    try {
      setLoading(true);
      setError(null);
      const ana = await api.getLatestAnalysis(wfId);
      setAnalysis(ana);
      const md = await api.getReportMarkdown(ana.analysis_id);
      setMarkdownReport(md);
    } catch (err: any) {
      setError("No completed analysis found for this workflow. Run an analysis first.");
      setAnalysis(null);
      setMarkdownReport("");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format: "json" | "md") => {
    if (!analysis) return;
    let content = "";
    let filename = `deploywise-report-${analysis.analysis_id.slice(0, 8)}`;

    if (format === "json") {
      content = JSON.stringify(analysis, null, 2);
      filename += ".json";
    } else {
      content = markdownReport;
      filename += ".md";
    }

    const blob = new Blob([content], { type: format === "json" ? "application/json" : "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Executive Risk Reports</h1>
          <p className="page-description">
            Audit-ready, exportable compliance and governance reports with policy and ruleset versions.
          </p>
        </div>
        {analysis && (
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-secondary" onClick={() => handleDownload("json")}>
              <Code size={15} /> Export JSON
            </button>
            <button className="btn btn-secondary" onClick={() => handleDownload("md")}>
              <Download size={15} /> Markdown (.md)
            </button>
            <button className="btn btn-primary" onClick={() => api.downloadReportPdf(analysis.analysis_id)}>
              <FileText size={15} /> Download PDF Report (.pdf)
            </button>
          </div>
        )}
      </div>

      {/* Workflow Selector */}
      <div className="card" style={{ marginBottom: 20, padding: "14px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)" }}>
            Select Target Workflow:
          </label>
          <select
            value={selectedWfId}
            onChange={(e) => {
              setSelectedWfId(e.target.value);
              loadReportForWorkflow(e.target.value);
            }}
            style={{ padding: "6px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 13 }}
          >
            {workflows.map((wf) => (
              <option key={wf.workflow_id} value={wf.workflow_id}>
                {wf.name} ({wf.environment})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error ? (
        <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--text-secondary)" }}>
          <AlertTriangle size={32} color="var(--medium)" style={{ margin: "0 auto 10px" }} />
          <div>{error}</div>
        </div>
      ) : loading ? (
        <div style={{ padding: 40, textAlign: "center", color: "var(--text-secondary)" }}>
          Loading analysis report...
        </div>
      ) : (
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid var(--border)", paddingBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <FileText size={18} color="var(--accent)" />
              <span style={{ fontWeight: 700, fontSize: 14 }}>Markdown Audit Report Preview</span>
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Analysis ID: {analysis?.analysis_id}
            </div>
          </div>

          <pre
            style={{
              background: "#F8FAFD",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              padding: 20,
              fontSize: 12.5,
              lineHeight: 1.6,
              color: "var(--text-primary)",
              overflowX: "auto",
              whiteSpace: "pre-wrap",
            }}
          >
            {markdownReport}
          </pre>
        </div>
      )}
    </div>
  );
};
